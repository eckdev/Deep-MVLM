#!/usr/bin/env python3
import vtk
import numpy as np
import json
import os
import subprocess
import re
from scipy.spatial.distance import pdist
from sklearn.decomposition import PCA

class AdvancedPLYOptimizer:
    def __init__(self):
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.base_config_path = "configs/DTU3D-RGB.json"  # Use RGB as base for comparison
        self.test_config_path = "configs/DTU3D-PLY-advanced.json"
        self.results = []
        
    def analyze_mesh_properties(self, file_path):
        """Analyze mesh properties to understand the data"""
        reader = vtk.vtkPLYReader()
        reader.SetFileName(file_path)
        reader.Update()
        mesh = reader.GetOutput()
        
        # Get bounds
        bounds = mesh.GetBounds()
        points = mesh.GetPoints()
        n_points = points.GetNumberOfPoints()
        
        # Convert to numpy for analysis
        vertices = np.zeros((n_points, 3))
        for i in range(n_points):
            vertices[i] = points.GetPoint(i)
        
        # Calculate mesh statistics
        center = np.mean(vertices, axis=0)
        std = np.std(vertices, axis=0)
        diagonal = np.sqrt(np.sum((np.array([bounds[1], bounds[3], bounds[5]]) - 
                                 np.array([bounds[0], bounds[2], bounds[4]]))**2))
        
        # PCA analysis for orientation
        pca = PCA(n_components=3)
        pca.fit(vertices)
        
        mesh_info = {
            'bounds': bounds,
            'center': center,
            'std': std,
            'diagonal': diagonal,
            'n_points': n_points,
            'pca_components': pca.components_,
            'pca_variance': pca.explained_variance_ratio_
        }
        
        return mesh_info, vertices
    
    def normalize_and_align_mesh(self, file_path, output_path, target_scale=100):
        """Advanced mesh normalization and alignment"""
        # Load mesh
        reader = vtk.vtkPLYReader()
        reader.SetFileName(file_path)
        reader.Update()
        mesh = reader.GetOutput()
        
        # Get mesh info
        mesh_info, vertices = self.analyze_mesh_properties(file_path)
        
        print(f"Original mesh stats:")
        print(f"  Bounds: {mesh_info['bounds']}")
        print(f"  Center: {mesh_info['center']}")
        print(f"  Diagonal: {mesh_info['diagonal']:.2f}")
        print(f"  Points: {mesh_info['n_points']}")
        
        # Step 1: Center the mesh
        center_transform = vtk.vtkTransform()
        center_transform.Translate(-mesh_info['center'])
        
        # Step 2: PCA-based rotation for better alignment
        pca_rotation = vtk.vtkTransform()
        
        # Find the main axis (usually face direction)
        main_axis = mesh_info['pca_components'][0]  # First principal component
        
        # Align main axis with Z-axis for face scans
        if abs(main_axis[2]) < 0.8:  # If not already aligned with Z
            # Calculate rotation to align with Z-axis
            target = np.array([0, 0, 1])
            axis = np.cross(main_axis, target)
            axis = axis / np.linalg.norm(axis)
            angle = np.arccos(np.dot(main_axis, target)) * 180 / np.pi
            
            pca_rotation.RotateWXYZ(angle, axis)
        
        # Step 3: Scale to target size
        scale_factor = target_scale / mesh_info['diagonal']
        scale_transform = vtk.vtkTransform()
        scale_transform.Scale(scale_factor, scale_factor, scale_factor)
        
        # Combine transforms
        combined_transform = vtk.vtkTransform()
        combined_transform.PostMultiply()
        combined_transform.Concatenate(center_transform)
        combined_transform.Concatenate(pca_rotation)
        combined_transform.Concatenate(scale_transform)
        
        # Apply transform
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputData(mesh)
        transform_filter.SetTransform(combined_transform)
        transform_filter.Update()
        
        # Save normalized mesh
        writer = vtk.vtkPLYWriter()
        writer.SetFileName(output_path)
        writer.SetInputData(transform_filter.GetOutput())
        writer.Write()
        
        return {
            'original_diagonal': mesh_info['diagonal'],
            'scale_factor': scale_factor,
            'center_offset': mesh_info['center'],
            'rotation_applied': abs(main_axis[2]) < 0.8
        }
    
    def create_adaptive_config(self, image_channels="RGB", target_scale=100):
        """Create adaptive configuration based on analysis"""
        with open(self.base_config_path, 'r') as f:
            config = json.load(f)
        
        # Update for PLY-specific settings
        config["arch"]["args"]["image_channels"] = image_channels
        config["data_loader"]["args"]["image_channels"] = image_channels
        
        # Advanced pre-align settings
        config["pre-align"] = {
            "align_center_of_mass": False,  # We handle this in pre-processing
            "rot_x": 0,
            "rot_y": 0,
            "rot_z": 0,
            "scale": 1.0,  # Already normalized
            "write_pre_aligned": True
        }
        
        # Optimize process_3d parameters
        config["process_3d"]["heatmap_max_quantile"] = 0.7  # Higher threshold
        config["process_3d"]["heatmap_abs_threshold"] = 0.7
        config["process_3d"]["filter_view_lines"] = "quantile"
        
        # Save config
        with open(self.test_config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def run_prediction_with_preprocessing(self, ply_file, rendering_type="RGB"):
        """Run prediction with advanced preprocessing"""
        base_name = os.path.splitext(os.path.basename(ply_file))[0]
        normalized_file = f"temp_normalized_{base_name}.ply"
        
        # Step 1: Advanced normalization
        print(f"\n=== Processing {base_name} ===")
        print("Step 1: Advanced mesh normalization...")
        norm_info = self.normalize_and_align_mesh(ply_file, normalized_file)
        
        # Step 2: Create adaptive config
        print("Step 2: Creating adaptive configuration...")
        self.create_adaptive_config(rendering_type)
        
        # Step 3: Run prediction
        print("Step 3: Running prediction...")
        cmd = [self.python_path, "predict.py", "--c", self.test_config_path, "--n", normalized_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = result.stderr + result.stdout
            
            # Extract RANSAC error
            ransac_pattern = r"Ransac average error\s+([\d.]+)"
            match = re.search(ransac_pattern, output)
            
            if match:
                ransac_error = float(match.group(1))
                
                # Clean up
                if os.path.exists(normalized_file):
                    os.remove(normalized_file)
                
                return ransac_error, norm_info, output
            else:
                return None, norm_info, output
                
        except subprocess.TimeoutExpired:
            return None, norm_info, "Timeout"
        except Exception as e:
            return None, norm_info, str(e)
        finally:
            # Clean up
            if os.path.exists(normalized_file):
                os.remove(normalized_file)
    
    def comprehensive_ply_optimization(self):
        """Comprehensive PLY optimization with advanced techniques"""
        print("=== GELİŞMİŞ PLY OPTİMİZASYONU ===\n")
        
        ply_files = [
            "assets/files/class1/men/1.ply",
            "assets/files/class1/men/2.ply",
            "assets/files/class1/men/3.ply"
        ]
        
        rendering_types = ["RGB", "geometry", "depth", "RGB+depth", "geometry+depth"]
        
        best_error = float('inf')
        best_config = None
        best_result = None
        
        for ply_file in ply_files:
            if not os.path.exists(ply_file):
                continue
                
            base_name = os.path.basename(ply_file)
            print(f"\n{'='*50}")
            print(f"Testing file: {base_name}")
            print(f"{'='*50}")
            
            for rendering in rendering_types:
                print(f"\nTesting rendering type: {rendering}")
                
                error, norm_info, output = self.run_prediction_with_preprocessing(ply_file, rendering)
                
                if error is not None:
                    print(f"✅ RANSAC Error: {error:.6f}")
                    print(f"   Normalization info: Scale factor={norm_info['scale_factor']:.6f}")
                    
                    result = {
                        'file': base_name,
                        'rendering': rendering,
                        'ransac_error': error,
                        'normalization_info': norm_info
                    }
                    self.results.append(result)
                    
                    if error < best_error:
                        best_error = error
                        best_config = rendering
                        best_result = result
                        print(f"🎉 NEW BEST RESULT!")
                else:
                    print(f"❌ Failed: {output[:100]}...")
        
        return best_result
    
    def create_final_optimized_config(self, best_result):
        """Create final optimized configuration"""
        if not best_result:
            print("No successful results to create config from")
            return
        
        print(f"\n=== CREATING FINAL OPTIMIZED CONFIG ===")
        print(f"Best result:")
        print(f"  File: {best_result['file']}")
        print(f"  Rendering: {best_result['rendering']}")
        print(f"  RANSAC Error: {best_result['ransac_error']:.6f}")
        
        # Create final config
        self.create_adaptive_config(best_result['rendering'])
        
        # Save as final config
        final_config_path = "configs/DTU3D-PLY-advanced-final.json"
        os.rename(self.test_config_path, final_config_path)
        
        print(f"Final optimized config saved: {final_config_path}")
        
        # Create preprocessing script
        self.create_ply_preprocessing_script()
        
        return final_config_path
    
    def create_ply_preprocessing_script(self):
        """Create a standalone PLY preprocessing script"""
        script_content = '''#!/usr/bin/env python3
"""
Advanced PLY Preprocessing Script for Deep-MVLM
Usage: python preprocess_ply.py input.ply output.ply [target_scale]
"""
import vtk
import numpy as np
import sys
from sklearn.decomposition import PCA

def preprocess_ply_file(input_path, output_path, target_scale=100):
    """Preprocess PLY file for optimal Deep-MVLM results"""
    
    # Load mesh
    reader = vtk.vtkPLYReader()
    reader.SetFileName(input_path)
    reader.Update()
    mesh = reader.GetOutput()
    
    # Get vertices
    points = mesh.GetPoints()
    n_points = points.GetNumberOfPoints()
    vertices = np.zeros((n_points, 3))
    for i in range(n_points):
        vertices[i] = points.GetPoint(i)
    
    # Calculate properties
    bounds = mesh.GetBounds()
    center = np.mean(vertices, axis=0)
    diagonal = np.sqrt(np.sum((np.array([bounds[1], bounds[3], bounds[5]]) - 
                             np.array([bounds[0], bounds[2], bounds[4]]))**2))
    
    print(f"Original mesh diagonal: {diagonal:.2f}")
    print(f"Original center: {center}")
    
    # PCA for orientation
    pca = PCA(n_components=3)
    pca.fit(vertices)
    main_axis = pca.components_[0]
    
    # Create transforms
    # 1. Center
    center_transform = vtk.vtkTransform()
    center_transform.Translate(-center)
    
    # 2. Rotate to align with standard orientation
    rotation_transform = vtk.vtkTransform()
    if abs(main_axis[2]) < 0.8:
        target = np.array([0, 0, 1])
        axis = np.cross(main_axis, target)
        if np.linalg.norm(axis) > 0:
            axis = axis / np.linalg.norm(axis)
            angle = np.arccos(np.clip(np.dot(main_axis, target), -1, 1)) * 180 / np.pi
            rotation_transform.RotateWXYZ(angle, axis)
    
    # 3. Scale
    scale_factor = target_scale / diagonal
    scale_transform = vtk.vtkTransform()
    scale_transform.Scale(scale_factor, scale_factor, scale_factor)
    
    # Combine transforms
    combined_transform = vtk.vtkTransform()
    combined_transform.PostMultiply()
    combined_transform.Concatenate(center_transform)
    combined_transform.Concatenate(rotation_transform)
    combined_transform.Concatenate(scale_transform)
    
    # Apply transform
    transform_filter = vtk.vtkTransformPolyDataFilter()
    transform_filter.SetInputData(mesh)
    transform_filter.SetTransform(combined_transform)
    transform_filter.Update()
    
    # Save result
    writer = vtk.vtkPLYWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(transform_filter.GetOutput())
    writer.Write()
    
    print(f"Processed mesh saved to: {output_path}")
    print(f"Scale factor applied: {scale_factor:.6f}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python preprocess_ply.py input.ply output.ply [target_scale]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    target_scale = float(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    preprocess_ply_file(input_file, output_file, target_scale)
'''
        
        with open('preprocess_ply.py', 'w') as f:
            f.write(script_content)
        
        print("Standalone preprocessing script created: preprocess_ply.py")
    
    def save_comprehensive_results(self, best_result):
        """Save comprehensive results analysis"""
        print(f"\n=== COMPREHENSIVE RESULTS ===")
        
        if not self.results:
            print("No results to analyze")
            return
        
        # Sort by error
        sorted_results = sorted(self.results, key=lambda x: x['ransac_error'])
        
        print(f"\nTop 5 Results:")
        for i, result in enumerate(sorted_results[:5]):
            print(f"{i+1}. {result['file']} ({result['rendering']}): {result['ransac_error']:.6f}")
        
        # Compare with OBJ baseline
        obj_baseline = 1.57  # testmeshA.obj result
        best_ply = sorted_results[0]['ransac_error']
        
        print(f"\nComparison with OBJ baseline:")
        print(f"  OBJ (testmeshA.obj): {obj_baseline}")
        print(f"  Best PLY: {best_ply:.6f}")
        print(f"  Ratio: {best_ply/obj_baseline:.1f}x")
        
        if best_ply < 10:  # If we got close to OBJ performance
            print(f"🎉 SUCCESS: PLY performance is now comparable to OBJ!")
        elif best_ply < 1000:
            print(f"✅ GOOD: PLY performance significantly improved")
        else:
            print(f"⚠️  PARTIAL: Some improvement but still needs work")
        
        # Save detailed results
        with open('advanced_ply_optimization_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

def main():
    optimizer = AdvancedPLYOptimizer()
    best_result = optimizer.comprehensive_ply_optimization()
    final_config = optimizer.create_final_optimized_config(best_result)
    optimizer.save_comprehensive_results(best_result)

if __name__ == "__main__":
    main()
