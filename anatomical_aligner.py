#!/usr/bin/env python3
"""
Anatomical Coordinate System Alignment for PLY files
Align PLY files to the standard anatomical coordinate system:
- Center: around origin (0,0,0)  
- Nose: pointing in z-direction (positive Z)
- Head up: aligned with y-axis (positive Y)
"""

import vtk
import numpy as np
import os
import json
from scipy.spatial.distance import pdist

class AnatomicalAligner:
    def __init__(self):
        self.anatomical_standard = {
            'center': np.array([0.0, 0.0, 0.0]),
            'nose_direction': np.array([0.0, 0.0, 1.0]),  # Positive Z
            'up_direction': np.array([0.0, 1.0, 0.0]),    # Positive Y
            'right_direction': np.array([1.0, 0.0, 0.0])  # Positive X (right ear)
        }
        
    def analyze_ply_anatomy(self, ply_path):
        """Analyze PLY file to detect anatomical landmarks and orientation"""
        
        print(f"🔍 Anatomical Analysis: {os.path.basename(ply_path)}")
        print("-" * 50)
        
        # Load PLY
        reader = vtk.vtkPLYReader()
        reader.SetFileName(ply_path)
        reader.Update()
        mesh = reader.GetOutput()
        
        # Extract vertices
        points = mesh.GetPoints()
        n_points = points.GetNumberOfPoints()
        vertices = np.array([points.GetPoint(i) for i in range(n_points)])
        
        # Basic metrics
        bounds = mesh.GetBounds()
        center = np.mean(vertices, axis=0)
        
        print(f"📊 Basic Metrics:")
        print(f"   Points: {n_points:,}")
        print(f"   Current center: {center}")
        print(f"   Bounds: X[{bounds[0]:.1f}, {bounds[1]:.1f}] Y[{bounds[2]:.1f}, {bounds[3]:.1f}] Z[{bounds[4]:.1f}, {bounds[5]:.1f}]")
        
        # Anatomical analysis
        anatomy = self.detect_anatomical_features(vertices, bounds)
        
        return {
            'vertices': vertices,
            'center': center,
            'bounds': bounds,
            'anatomy': anatomy,
            'mesh': mesh
        }
    
    def detect_anatomical_features(self, vertices, bounds):
        """Detect anatomical features to determine proper orientation"""
        
        print(f"\n🧠 Anatomical Feature Detection:")
        
        # 1. Detect face orientation based on point distribution
        x_range = bounds[1] - bounds[0]  # Width (left-right)
        y_range = bounds[3] - bounds[2]  # Height (up-down)
        z_range = bounds[5] - bounds[4]  # Depth (front-back)
        
        print(f"   Dimensions: W={x_range:.1f} H={y_range:.1f} D={z_range:.1f}")
        
        # 2. Estimate nose tip (furthest point in expected direction)
        # Assume nose is at extreme of smallest dimension
        dimensions = {'x': x_range, 'y': y_range, 'z': z_range}
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1])
        
        # Face is usually widest in X, tallest in Y, shortest in Z (depth)
        # But PLY orientation might be different
        
        # Find extremal points
        extremes = {
            'x_min': vertices[np.argmin(vertices[:, 0])],
            'x_max': vertices[np.argmax(vertices[:, 0])],
            'y_min': vertices[np.argmin(vertices[:, 1])],
            'y_max': vertices[np.argmax(vertices[:, 1])],
            'z_min': vertices[np.argmin(vertices[:, 2])],
            'z_max': vertices[np.argmax(vertices[:, 2])]
        }
        
        print(f"   Smallest dimension: {sorted_dims[0][0]}-axis ({sorted_dims[0][1]:.1f})")
        print(f"   Largest dimension: {sorted_dims[2][0]}-axis ({sorted_dims[2][1]:.1f})")
        
        # 3. Estimate current orientation
        # Face height usually largest, width second, depth smallest
        if y_range > x_range > z_range:
            orientation_guess = "standard"  # Y=up, X=width, Z=depth
            estimated_nose_dir = np.array([0, 0, 1])
            estimated_up_dir = np.array([0, 1, 0])
        elif z_range > y_range > x_range:
            orientation_guess = "z_up"  # Z=up, Y=width, X=depth  
            estimated_nose_dir = np.array([1, 0, 0])
            estimated_up_dir = np.array([0, 0, 1])
        elif x_range > z_range > y_range:
            orientation_guess = "x_up"  # X=up, Z=width, Y=depth
            estimated_nose_dir = np.array([0, 1, 0])
            estimated_up_dir = np.array([1, 0, 0])
        else:
            orientation_guess = "unknown"
            estimated_nose_dir = np.array([0, 0, 1])  # Default
            estimated_up_dir = np.array([0, 1, 0])
        
        print(f"   Orientation guess: {orientation_guess}")
        print(f"   Estimated nose direction: {estimated_nose_dir}")
        print(f"   Estimated up direction: {estimated_up_dir}")
        
        # 4. Find probable nose tip and top of head
        if orientation_guess == "standard":
            nose_candidate = extremes['z_max']  # Furthest in Z
            head_top_candidate = extremes['y_max']  # Highest in Y
        elif orientation_guess == "z_up":
            nose_candidate = extremes['x_max']  # Furthest in X
            head_top_candidate = extremes['z_max']  # Highest in Z
        elif orientation_guess == "x_up":
            nose_candidate = extremes['y_max']  # Furthest in Y
            head_top_candidate = extremes['x_max']  # Highest in X
        else:
            nose_candidate = extremes['z_max']  # Default
            head_top_candidate = extremes['y_max']
        
        print(f"   Probable nose tip: {nose_candidate}")
        print(f"   Probable head top: {head_top_candidate}")
        
        return {
            'orientation_guess': orientation_guess,
            'estimated_nose_dir': estimated_nose_dir,
            'estimated_up_dir': estimated_up_dir,
            'nose_candidate': nose_candidate,
            'head_top_candidate': head_top_candidate,
            'extremes': extremes,
            'dimensions': {'x': x_range, 'y': y_range, 'z': z_range}
        }
    
    def calculate_anatomical_transform(self, ply_analysis):
        """Calculate transform to align PLY to anatomical coordinate system"""
        
        print(f"\n🔧 Calculating Anatomical Transform:")
        
        current_center = ply_analysis['center']
        anatomy = ply_analysis['anatomy']
        
        # Step 1: Translation to center at origin
        translation = -current_center
        print(f"   Translation: {translation}")
        
        # Step 2: Determine rotation needed
        current_nose_dir = anatomy['estimated_nose_dir']
        current_up_dir = anatomy['estimated_up_dir']
        
        target_nose_dir = self.anatomical_standard['nose_direction']
        target_up_dir = self.anatomical_standard['up_direction']
        
        # Calculate rotation matrix
        rotation_matrix = self.calculate_rotation_matrix(
            current_nose_dir, current_up_dir,
            target_nose_dir, target_up_dir
        )
        
        print(f"   Current nose direction: {current_nose_dir}")
        print(f"   Target nose direction: {target_nose_dir}")
        print(f"   Current up direction: {current_up_dir}")
        print(f"   Target up direction: {target_up_dir}")
        
        # Step 3: Calculate appropriate scale
        # Use a reasonable face size (based on average human face)
        bounds = ply_analysis['bounds']
        current_face_height = bounds[3] - bounds[2]  # Assuming Y is currently height
        
        # Average human face height is approximately 180-200mm
        target_face_height = 190.0  # mm
        scale_factor = target_face_height / abs(current_face_height)
        
        print(f"   Current face height: {abs(current_face_height):.1f}")
        print(f"   Target face height: {target_face_height:.1f}")
        print(f"   Scale factor: {scale_factor:.3f}")
        
        return {
            'translation': translation,
            'rotation_matrix': rotation_matrix,
            'scale_factor': scale_factor,
            'anatomy_guess': anatomy['orientation_guess']
        }
    
    def calculate_rotation_matrix(self, from_nose, from_up, to_nose, to_up):
        """Calculate rotation matrix to align coordinate systems"""
        
        # Normalize vectors
        from_nose = from_nose / np.linalg.norm(from_nose)
        from_up = from_up / np.linalg.norm(from_up)
        to_nose = to_nose / np.linalg.norm(to_nose)
        to_up = to_up / np.linalg.norm(to_up)
        
        # Create orthogonal coordinate systems
        from_right = np.cross(from_up, from_nose)
        from_right = from_right / np.linalg.norm(from_right)
        from_up = np.cross(from_nose, from_right)  # Ensure orthogonality
        
        to_right = np.cross(to_up, to_nose)
        to_right = to_right / np.linalg.norm(to_right)
        to_up = np.cross(to_nose, to_right)
        
        # Build transformation matrices
        from_matrix = np.column_stack([from_right, from_up, from_nose])
        to_matrix = np.column_stack([to_right, to_up, to_nose])
        
        # Rotation matrix: R = to_matrix * from_matrix^T
        rotation_matrix = to_matrix @ from_matrix.T
        
        return rotation_matrix
    
    def apply_anatomical_alignment(self, ply_path, output_path):
        """Apply anatomical alignment to PLY file"""
        
        print(f"\n🎯 Applying Anatomical Alignment")
        print(f"Input: {os.path.basename(ply_path)}")
        print(f"Output: {os.path.basename(output_path)}")
        print("=" * 60)
        
        # Analyze PLY
        ply_analysis = self.analyze_ply_anatomy(ply_path)
        
        # Calculate transform
        transform_params = self.calculate_anatomical_transform(ply_analysis)
        
        # Apply transform using VTK
        mesh = ply_analysis['mesh']
        
        # Create VTK transform
        vtk_transform = vtk.vtkTransform()
        
        # Apply in correct order: Scale -> Rotate -> Translate
        vtk_transform.PostMultiply()
        
        # 1. Translate to origin first
        vtk_transform.Translate(transform_params['translation'])
        
        # 2. Apply rotation
        rotation_matrix = transform_params['rotation_matrix']
        vtk_matrix = vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                vtk_matrix.SetElement(i, j, rotation_matrix[i, j])
        vtk_transform.Concatenate(vtk_matrix)
        
        # 3. Apply scale
        scale = transform_params['scale_factor']
        vtk_transform.Scale(scale, scale, scale)
        
        # Apply transform to mesh
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputData(mesh)
        transform_filter.SetTransform(vtk_transform)
        transform_filter.Update()
        
        # Clean up the result
        clean_filter = vtk.vtkCleanPolyData()
        clean_filter.SetInputData(transform_filter.GetOutput())
        clean_filter.Update()
        
        # Generate smooth normals
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(clean_filter.GetOutput())
        normals.ComputePointNormalsOn()
        normals.ComputeCellNormalsOn()
        normals.SplittingOff()
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        normals.Update()
        
        final_mesh = normals.GetOutput()
        
        # Save result
        writer = vtk.vtkPLYWriter()
        writer.SetFileName(output_path)
        writer.SetInputData(final_mesh)
        writer.Write()
        
        # Verify result
        final_bounds = final_mesh.GetBounds()
        final_center = np.mean([[final_bounds[0], final_bounds[2], final_bounds[4]],
                               [final_bounds[1], final_bounds[3], final_bounds[5]]], axis=0)
        
        print(f"\n✅ Anatomical Alignment Complete!")
        print(f"   Final center: {final_center}")
        print(f"   Final bounds: X[{final_bounds[0]:.1f}, {final_bounds[1]:.1f}] Y[{final_bounds[2]:.1f}, {final_bounds[3]:.1f}] Z[{final_bounds[4]:.1f}, {final_bounds[5]:.1f}]")
        print(f"   Scale applied: {scale:.3f}")
        print(f"   Orientation: {transform_params['anatomy_guess']}")
        
        return {
            'transform_params': transform_params,
            'final_center': final_center,
            'final_bounds': final_bounds,
            'output_file': output_path
        }
    
    def create_anatomical_config(self, base_config_path="configs/DTU3D-geometry.json", 
                                output_config_path="configs/DTU3D-anatomical.json"):
        """Create configuration file optimized for anatomically aligned PLY files"""
        
        print(f"\n📝 Creating Anatomical Configuration")
        print("-" * 40)
        
        # Load base config
        with open(base_config_path, 'r') as f:
            config = json.load(f)
        
        # Modify for anatomical alignment
        config['name'] = "MVLMModel_DTU3D_Anatomical"
        
        # Update pre-alignment settings for anatomical standard
        config['pre-align'] = {
            "align_center_of_mass": False,  # Already centered
            "rot_x": 0,  # No additional rotation needed
            "rot_y": 0,
            "rot_z": 0,
            "scale": 1,  # Already properly scaled
            "write_pre_aligned": True
        }
        
        # Optimize data loader for anatomical coordinates
        config['data_loader']['args']['image_size'] = 256
        config['data_loader']['args']['heatmap_size'] = 256
        config['data_loader']['args']['n_views'] = 96  # Full coverage
        
        # Add anatomical-specific comments
        config['_comments'] = {
            "anatomical_alignment": "PLY files pre-aligned to anatomical coordinate system",
            "coordinate_system": "Center at origin, nose points +Z, head up is +Y",
            "scale": "Normalized to average human face dimensions (~190mm height)",
            "pre_align": "No additional alignment needed - already anatomically correct"
        }
        
        # Save new config
        with open(output_config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"✅ Anatomical config saved: {output_config_path}")
        print(f"   Coordinate system: Anatomical standard")
        print(f"   Pre-alignment: Disabled (already aligned)")
        print(f"   Image channels: {config['arch']['args']['image_channels']}")
        
        return output_config_path

def main():
    aligner = AnatomicalAligner()
    
    print("🧠 ANATOMICAL COORDINATE SYSTEM ALIGNMENT")
    print("=" * 60)
    print("Standard: Center at origin, nose points +Z, head up is +Y")
    print()
    
    # Find test PLY files
    test_files = []
    for root, dirs, files in os.walk("assets/files"):
        for file in files:
            if file.endswith('.ply'):
                test_files.append(os.path.join(root, file))
                if len(test_files) >= 3:  # Test with 3 files
                    break
        if len(test_files) >= 3:
            break
    
    if not test_files:
        print("❌ No PLY files found in assets/files")
        return
    
    # Process test files
    processed_files = []
    
    for i, ply_file in enumerate(test_files[:2]):  # Test 2 files
        basename = os.path.splitext(os.path.basename(ply_file))[0]
        output_file = f"anatomical_aligned_{basename}.ply"
        
        print(f"\n🔧 Processing {i+1}: {basename}")
        print("=" * 50)
        
        try:
            result = aligner.apply_anatomical_alignment(ply_file, output_file)
            processed_files.append({
                'input': ply_file,
                'output': output_file,
                'result': result
            })
            
            print(f"✅ Success: {output_file}")
            
        except Exception as e:
            print(f"❌ Error processing {ply_file}: {e}")
            import traceback
            traceback.print_exc()
    
    # Create anatomical configuration
    if processed_files:
        print(f"\n📝 Creating Anatomical Configuration")
        config_path = aligner.create_anatomical_config()
        
        print(f"\n🧪 Ready for Testing!")
        print("=" * 30)
        print(f"Anatomically aligned files:")
        for pf in processed_files:
            print(f"   {pf['output']}")
        
        print(f"\nTest command:")
        if processed_files:
            test_file = processed_files[0]['output']
            print(f"python predict.py --c {config_path} --n {test_file}")

if __name__ == "__main__":
    main()
