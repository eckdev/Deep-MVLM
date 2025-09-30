#!/usr/bin/env python3
import vtk
import numpy as np
import json
import os
import subprocess
import re
from scipy.spatial.distance import pdist
try:
    from scipy.spatial import procrustes
except ImportError:
    print("Warning: scipy.spatial.procrustes not available, using basic alignment")
    procrustes = None

class PLYTestSuite:
    def __init__(self):
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.obj_reference = "assets/testmeshA.obj"
        self.obj_config = "configs/DTU3D-RGB.json"
        self.test_config_path = "configs/DTU3D-PLY-test-suite.json"
        self.results = []
        
    def load_obj_reference(self):
        """Load reference OBJ and extract its properties"""
        reader = vtk.vtkOBJReader()
        reader.SetFileName(self.obj_reference)
        reader.Update()
        mesh = reader.GetOutput()
        
        # Get vertices
        points = mesh.GetPoints()
        n_points = points.GetNumberOfPoints()
        vertices = np.zeros((n_points, 3))
        for i in range(n_points):
            vertices[i] = points.GetPoint(i)
        
        bounds = mesh.GetBounds()
        center = np.mean(vertices, axis=0)
        diagonal = np.sqrt(np.sum((np.array([bounds[1], bounds[3], bounds[5]]) - 
                                 np.array([bounds[0], bounds[2], bounds[4]]))**2))
        
        return {
            'vertices': vertices,
            'bounds': bounds,
            'center': center,
            'diagonal': diagonal,
            'n_points': n_points
        }
    
    def get_ply_file_info(self, ply_file):
        """Get basic info about PLY file"""
        try:
            reader = vtk.vtkPLYReader()
            reader.SetFileName(ply_file)
            reader.Update()
            mesh = reader.GetOutput()
            
            bounds = mesh.GetBounds()
            points = mesh.GetPoints()
            n_points = points.GetNumberOfPoints()
            
            file_size = os.path.getsize(ply_file)
            
            vertices = np.zeros((min(n_points, 1000), 3))  # Sample for speed
            for i in range(min(n_points, 1000)):
                vertices[i] = points.GetPoint(i)
            
            center = np.mean(vertices, axis=0)
            diagonal = np.sqrt(np.sum((np.array([bounds[1], bounds[3], bounds[5]]) - 
                                     np.array([bounds[0], bounds[2], bounds[4]]))**2))
            
            return {
                'file_size_mb': file_size / (1024*1024),
                'n_points': n_points,
                'center': center,
                'diagonal': diagonal,
                'bounds': bounds
            }
        except Exception as e:
            return {'error': str(e)}
    
    def align_ply_to_obj_coordinate_system(self, ply_file, output_file):
        """Align PLY mesh to match OBJ coordinate system"""
        
        # Load reference OBJ properties
        obj_ref = self.load_obj_reference()
        
        # Load PLY mesh
        reader = vtk.vtkPLYReader()
        reader.SetFileName(ply_file)
        reader.Update()
        ply_mesh = reader.GetOutput()
        
        # Get PLY vertices
        points = ply_mesh.GetPoints()
        n_points = points.GetNumberOfPoints()
        ply_vertices = np.zeros((n_points, 3))
        for i in range(n_points):
            ply_vertices[i] = points.GetPoint(i)
        
        ply_bounds = ply_mesh.GetBounds()
        ply_center = np.mean(ply_vertices, axis=0)
        ply_diagonal = np.sqrt(np.sum((np.array([ply_bounds[1], ply_bounds[3], ply_bounds[5]]) - 
                                     np.array([ply_bounds[0], ply_bounds[2], ply_bounds[4]]))**2))
        
        # Create transformation
        transform = vtk.vtkTransform()
        
        # Step 1: Center PLY
        transform.Translate(-ply_center)
        
        # Step 2: Scale to match OBJ size
        scale_factor = obj_ref['diagonal'] / ply_diagonal
        transform.Scale(scale_factor, scale_factor, scale_factor)
        
        # Step 3: Translate to OBJ center
        transform.Translate(obj_ref['center'])
        
        # Apply transformation
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputData(ply_mesh)
        transform_filter.SetTransform(transform)
        transform_filter.Update()
        
        # Save aligned PLY
        writer = vtk.vtkPLYWriter()
        writer.SetFileName(output_file)
        writer.SetInputData(transform_filter.GetOutput())
        writer.Write()
        
        return {
            'scale_factor': scale_factor,
            'obj_diagonal': obj_ref['diagonal'],
            'ply_diagonal': ply_diagonal,
            'ply_center': ply_center,
            'obj_center': obj_ref['center']
        }
    
    def create_optimal_config(self, rendering_type="geometry"):
        """Create optimal configuration based on our findings"""
        with open(self.obj_config, 'r') as f:
            config = json.load(f)
        
        # Use optimal settings discovered
        config["arch"]["args"]["image_channels"] = rendering_type
        config["data_loader"]["args"]["image_channels"] = rendering_type
        
        # Minimal pre-align (since we handle alignment in preprocessing)
        config["pre-align"] = {
            "align_center_of_mass": False,
            "rot_x": 0,
            "rot_y": 0,
            "rot_z": 0,
            "scale": 1.0,
            "write_pre_aligned": False
        }
        
        # Proven optimal parameters
        config["process_3d"]["heatmap_max_quantile"] = 0.5
        config["process_3d"]["heatmap_abs_threshold"] = 0.5
        
        with open(self.test_config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def test_single_ply(self, ply_file, rendering_type="geometry"):
        """Test a single PLY file with optimal pipeline"""
        base_name = os.path.splitext(os.path.basename(ply_file))[0]
        aligned_file = f"temp_aligned_{base_name}.ply"
        
        print(f"\n{'='*70}")
        print(f"Testing: {os.path.basename(ply_file)}")
        print(f"{'='*70}")
        
        # Get file info first
        ply_info = self.get_ply_file_info(ply_file)
        if 'error' in ply_info:
            print(f"❌ Error reading PLY: {ply_info['error']}")
            return None
        
        print(f"File info:")
        print(f"  Size: {ply_info['file_size_mb']:.1f} MB")
        print(f"  Points: {ply_info['n_points']:,}")
        print(f"  Center: ({ply_info['center'][0]:.1f}, {ply_info['center'][1]:.1f}, {ply_info['center'][2]:.1f})")
        print(f"  Diagonal: {ply_info['diagonal']:.1f}")
        
        # Step 1: Align to OBJ coordinate system
        print(f"\nStep 1: Aligning to OBJ coordinate system...")
        try:
            alignment_info = self.align_ply_to_obj_coordinate_system(ply_file, aligned_file)
            print(f"✅ Aligned (scale factor: {alignment_info['scale_factor']:.3f})")
        except Exception as e:
            print(f"❌ Alignment failed: {e}")
            return None
        
        # Step 2: Create optimal config
        self.create_optimal_config(rendering_type)
        
        # Step 3: Run prediction
        print(f"Step 2: Running prediction with {rendering_type} rendering...")
        cmd = [self.python_path, "predict.py", "--c", self.test_config_path, "--n", aligned_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
            output = result.stderr + result.stdout
            
            # Extract RANSAC error
            ransac_pattern = r"Ransac average error\s+([\d.]+)"
            match = re.search(ransac_pattern, output)
            
            if match:
                ransac_error = float(match.group(1))
                print(f"✅ RANSAC Error: {ransac_error:.2f}")
                
                # Determine performance level
                if ransac_error < 10:
                    print(f"🔥 EXCELLENT: Comparable to OBJ performance!")
                elif ransac_error < 100:
                    print(f"🎉 VERY GOOD: High quality result")
                elif ransac_error < 10000:
                    print(f"✅ GOOD: Acceptable quality")
                elif ransac_error < 1000000:
                    print(f"⚠️  FAIR: Needs improvement")
                else:
                    print(f"❌ POOR: Significant issues")
                
                result_data = {
                    'file': base_name,
                    'rendering': rendering_type,
                    'ransac_error': ransac_error,
                    'file_info': ply_info,
                    'alignment_info': alignment_info
                }
                
                return result_data
            else:
                print(f"❌ Failed to extract RANSAC error")
                print(f"Output: {output[:200]}...")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout during prediction")
            return None
        except Exception as e:
            print(f"❌ Error during prediction: {e}")
            return None
        finally:
            # Clean up
            if os.path.exists(aligned_file):
                os.remove(aligned_file)
    
    def test_multiple_ply_files(self, file_list):
        """Test multiple PLY files"""
        print("=== PLY FILE TEST SUITE ===")
        print(f"Testing {len(file_list)} files with optimal pipeline\n")
        
        results = []
        
        for ply_file in file_list:
            if not os.path.exists(ply_file):
                print(f"❌ File not found: {ply_file}")
                continue
            
            result = self.test_single_ply(ply_file, "geometry")  # Use optimal rendering
            if result:
                results.append(result)
        
        return results
    
    def generate_test_report(self, results):
        """Generate comprehensive test report"""
        if not results:
            print("\n❌ No results to report")
            return
        
        print(f"\n{'='*80}")
        print("PLY TEST SUITE RESULTS")
        print(f"{'='*80}")
        
        # Sort by performance
        sorted_results = sorted(results, key=lambda x: x['ransac_error'])
        
        print(f"\nPerformance Ranking:")
        print(f"{'Rank':<4} {'File':<15} {'RANSAC Error':<15} {'Size (MB)':<10} {'Points':<10} {'Quality'}")
        print("-" * 80)
        
        for i, result in enumerate(sorted_results):
            file_info = result['file_info']
            error = result['ransac_error']
            
            # Quality assessment
            if error < 10:
                quality = "🔥 EXCELLENT"
            elif error < 100:
                quality = "🎉 VERY GOOD"
            elif error < 10000:
                quality = "✅ GOOD"
            elif error < 1000000:
                quality = "⚠️  FAIR"
            else:
                quality = "❌ POOR"
            
            print(f"{i+1:<4} {result['file']:<15} {error:<15.2f} "
                  f"{file_info['file_size_mb']:<10.1f} {file_info['n_points']:<10,} {quality}")
        
        # Statistics
        errors = [r['ransac_error'] for r in results]
        print(f"\nStatistics:")
        print(f"  Best result: {min(errors):.2f}")
        print(f"  Worst result: {max(errors):.2f}")
        print(f"  Average: {np.mean(errors):.2f}")
        print(f"  Median: {np.median(errors):.2f}")
        
        # Compare with OBJ baseline
        obj_baseline = 1.57
        best_ply = min(errors)
        
        print(f"\nComparison with OBJ baseline:")
        print(f"  OBJ baseline: {obj_baseline}")
        print(f"  Best PLY: {best_ply:.2f}")
        print(f"  Performance ratio: {best_ply/obj_baseline:.1f}x")
        
        # Success rate
        excellent_count = sum(1 for e in errors if e < 10)
        good_count = sum(1 for e in errors if e < 100)
        
        print(f"\nSuccess Analysis:")
        print(f"  Excellent results (< 10): {excellent_count}/{len(results)} ({excellent_count/len(results)*100:.1f}%)")
        print(f"  Very good results (< 100): {good_count}/{len(results)} ({good_count/len(results)*100:.1f}%)")

def main():
    tester = PLYTestSuite()
    
    # Define test files - mix of different sizes and genders
    test_files = [
        # Men - different sizes
        "assets/files/class1/men/6.ply",    # Largest file (5.6MB)
        "assets/files/class1/men/15.ply",   # Large file (2.4MB)
        "assets/files/class1/men/4.ply",    # Medium file (2.1MB)
        "assets/files/class1/men/7.ply",    # Small file (0.9MB)
        "assets/files/class1/men/14.ply",   # Small file (1.1MB)
        
        # Women - variety
        "assets/files/class1/women/25.ply",
        "assets/files/class1/women/35.ply", 
        "assets/files/class1/women/45.ply",
        "assets/files/class1/women/55.ply",
        "assets/files/class1/women/65.ply"
    ]
    
    # Test all files
    results = tester.test_multiple_ply_files(test_files)
    
    # Generate report
    tester.generate_test_report(results)
    
    print(f"\n{'='*80}")
    print("PLY TEST SUITE COMPLETED")
    print(f"Optimal configuration: geometry rendering with OBJ coordinate alignment")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
