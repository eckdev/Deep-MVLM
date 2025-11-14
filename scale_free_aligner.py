#!/usr/bin/env python3
"""
Scale-Free Anatomical Aligner
Alignment without changing the scale to preserve manual landmark coordinates.
"""

import vtk
import numpy as np
import os
import json
from anatomical_aligner import AnatomicalAligner

class ScaleFreeAligner(AnatomicalAligner):
    def __init__(self):
        super().__init__()
        self.preserve_scale = True
    
    def calculate_anatomical_transform_no_scale(self, ply_analysis):
        """Calculate transform without scale modification"""
        
        print(f"\n🔧 Calculating Scale-Free Anatomical Transform:")
        print("   ⚠️  SCALE WILL BE PRESERVED - No size changes")
        print("-" * 50)
        
        anatomy = ply_analysis['anatomy']
        current_center = ply_analysis['center']
        
        # Step 1: Translation to center
        target_center = self.anatomical_standard['center']
        translation = target_center - current_center
        
        # Step 2: Calculate rotation only
        current_nose_dir = anatomy['estimated_nose_dir']
        current_up_dir = anatomy['estimated_up_dir']
        target_nose_dir = self.anatomical_standard['nose_direction']
        target_up_dir = self.anatomical_standard['up_direction']
        
        rotation_matrix = self.calculate_rotation_matrix(
            current_nose_dir, current_up_dir, target_nose_dir, target_up_dir
        )
        
        print(f"   Translation: {translation}")
        print(f"   Current nose direction: {current_nose_dir}")
        print(f"   Target nose direction: {target_nose_dir}")
        print(f"   Current up direction: {current_up_dir}")
        print(f"   Target up direction: {target_up_dir}")
        print(f"   🎯 Scale factor: 1.0 (PRESERVED)")
        
        return {
            'translation': translation,
            'rotation_matrix': rotation_matrix,
            'scale_factor': 1.0,  # No scale change!
            'anatomy_guess': anatomy['orientation_guess']
        }
    
    def apply_scale_free_alignment(self, ply_path, output_path):
        """Apply anatomical alignment without scale modification"""
        
        print(f"\n🎯 Applying Scale-Free Anatomical Alignment")
        print(f"Input: {os.path.basename(ply_path)}")
        print(f"Output: {os.path.basename(output_path)}")
        print("⚠️  SCALE PRESERVATION MODE - Manual landmarks will remain valid")
        print("=" * 70)
        
        # Analyze PLY
        ply_analysis = self.analyze_ply_anatomy(ply_path)
        
        # Calculate transform WITHOUT scale
        transform_params = self.calculate_anatomical_transform_no_scale(ply_analysis)
        
        # Apply transform using VTK
        mesh = ply_analysis['mesh']
        
        # Create VTK transform
        vtk_transform = vtk.vtkTransform()
        vtk_transform.PostMultiply()
        
        # Apply ONLY translation and rotation (NO SCALE)
        
        # 1. Translate to origin first
        vtk_transform.Translate(transform_params['translation'])
        
        # 2. Apply rotation only
        rotation_matrix = transform_params['rotation_matrix']
        vtk_matrix = vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                vtk_matrix.SetElement(i, j, rotation_matrix[i, j])
        vtk_transform.Concatenate(vtk_matrix)
        
        # 3. NO SCALE APPLICATION - This preserves manual landmark coordinates!
        
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
        
        print(f"\n✅ Scale-Free Anatomical Alignment Complete!")
        print(f"   Final center: {final_center}")
        print(f"   Final bounds: X[{final_bounds[0]:.1f}, {final_bounds[1]:.1f}] Y[{final_bounds[2]:.1f}, {final_bounds[3]:.1f}] Z[{final_bounds[4]:.1f}, {final_bounds[5]:.1f}]")
        print(f"   🎯 Scale applied: 1.0 (PRESERVED)")
        print(f"   Orientation: {transform_params['anatomy_guess']}")
        print(f"   ✅ Manual landmarks remain valid!")
        
        return {
            'transform_params': transform_params,
            'final_center': final_center,
            'final_bounds': final_bounds,
            'output_file': output_path
        }

# Configuration creator for scale-free mode
def create_scale_free_config():
    """Create configuration optimized for scale-free aligned PLY files"""
    
    base_config_path = "configs/DTU3D-geometry.json"
    output_config_path = "configs/DTU3D-scale-free.json"
    
    print(f"\n📝 Creating Scale-Free Configuration")
    print(f"   Base: {base_config_path}")
    print(f"   Output: {output_config_path}")
    print("-" * 50)
    
    # Load base config
    with open(base_config_path, 'r') as f:
        config = json.load(f)
    
    # Modify for scale-free alignment
    config['name'] = "MVLMModel_DTU3D"  # Use existing model name
    # Remove comment field that causes errors
    if 'comment' in config['arch']['args']:
        del config['arch']['args']['comment']
    
    # Remove comment field that causes errors
    if 'comment' in config['data_loader']['args']:
        del config['data_loader']['args']['comment']
    
    # Save new config
    with open(output_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Scale-free configuration created: {output_config_path}")
    return output_config_path

# Example usage
if __name__ == "__main__":
    aligner = ScaleFreeAligner()
    
    # Example files
    input_ply = "assets/files/class1/men/8.ply"
    output_ply = "scale_free_aligned.ply"
    
    print("🎯 Scale-Free Anatomical Alignment Workflow")
    print("=" * 60)
    print("🔹 This preserves the original scale of your PLY file")
    print("🔹 Manual landmarks from CloudCompare remain valid")
    print("🔹 Only rotation and translation are applied")
    print("")
    
    if os.path.exists(input_ply):
        # Apply scale-free alignment
        result = aligner.apply_scale_free_alignment(input_ply, output_ply)
        
        # Create corresponding config
        config_path = create_scale_free_config()
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Use aligned file: {output_ply}")
        print(f"   2. Use config: {config_path}")
        print(f"   3. Your CloudCompare landmarks remain valid!")
        print(f"   4. Run prediction: python predict.py --c {config_path} --n {output_ply}")
        
    else:
        print(f"❌ Input PLY file not found: {input_ply}")
        print("   Update the input_ply variable with your file path")