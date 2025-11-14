#!/usr/bin/env python3
"""
Ultimate Scale-Free PLY Preprocessor
This script aligns PLY files to OBJ coordinate system WITHOUT scale changes
"""
import vtk
import numpy as np
import sys
import os
try:
    from scipy.spatial import procrustes
except ImportError:
    print("Warning: scipy.spatial.procrustes not available, using basic alignment")
    procrustes = None

class UltimateScaleFreePreprocessor:
    def __init__(self):
        self.preserve_scale = True
    
    def align_ply_to_obj_system_scale_free(self, ply_path, output_path, obj_reference="assets/testmeshA.obj"):
        """Align PLY to OBJ coordinate system without scale changes"""
        
        print(f"\n🎯 Ultimate Scale-Free PLY Preprocessing")
        print(f"Input: {os.path.basename(ply_path)}")
        print(f"Output: {os.path.basename(output_path)}")
        print(f"Reference OBJ: {obj_reference}")
        print("⚠️  SCALE PRESERVATION MODE - Manual landmarks will remain valid")
        print("=" * 70)
        
        # Load OBJ reference
        obj_reader = vtk.vtkOBJReader()
        obj_reader.SetFileName(obj_reference)
        obj_reader.Update()
        obj_mesh = obj_reader.GetOutput()
        
        obj_points = obj_mesh.GetPoints()
        obj_vertices = np.array([obj_points.GetPoint(i) for i in range(obj_points.GetNumberOfPoints())])
        obj_bounds = obj_mesh.GetBounds()
        obj_center = np.mean(obj_vertices, axis=0)
        obj_diagonal = np.sqrt(np.sum((np.array([obj_bounds[1], obj_bounds[3], obj_bounds[5]]) - 
                                     np.array([obj_bounds[0], obj_bounds[2], obj_bounds[4]]))**2))
        
        print(f"\n📊 OBJ Reference Analysis:")
        print(f"   Points: {obj_points.GetNumberOfPoints():,}")
        print(f"   Center: {obj_center}")
        print(f"   Diagonal: {obj_diagonal:.1f}")
        print(f"   Bounds: X[{obj_bounds[0]:.1f}, {obj_bounds[1]:.1f}] Y[{obj_bounds[2]:.1f}, {obj_bounds[3]:.1f}] Z[{obj_bounds[4]:.1f}, {obj_bounds[5]:.1f}]")
        
        # Load PLY
        ply_reader = vtk.vtkPLYReader()
        ply_reader.SetFileName(ply_path)
        ply_reader.Update()
        ply_mesh = ply_reader.GetOutput()
        
        ply_points = ply_mesh.GetPoints()
        ply_vertices = np.array([ply_points.GetPoint(i) for i in range(ply_points.GetNumberOfPoints())])
        ply_bounds = ply_mesh.GetBounds()
        ply_center = np.mean(ply_vertices, axis=0)
        ply_diagonal = np.sqrt(np.sum((np.array([ply_bounds[1], ply_bounds[3], ply_bounds[5]]) - 
                                     np.array([ply_bounds[0], ply_bounds[2], ply_bounds[4]]))**2))
        
        print(f"\n📊 PLY Input Analysis:")
        print(f"   Points: {ply_points.GetNumberOfPoints():,}")
        print(f"   Center: {ply_center}")
        print(f"   Diagonal: {ply_diagonal:.1f}")
        print(f"   Bounds: X[{ply_bounds[0]:.1f}, {ply_bounds[1]:.1f}] Y[{ply_bounds[2]:.1f}, {ply_bounds[3]:.1f}] Z[{ply_bounds[4]:.1f}, {ply_bounds[5]:.1f}]")
        
        # Calculate transformation WITHOUT scale
        print(f"\n🔧 Calculating Ultimate Scale-Free Transform:")
        
        # Calculate original scale factor (but won't apply it)
        original_scale_factor = obj_diagonal / ply_diagonal
        print(f"   Original scale factor would be: {original_scale_factor:.6f}")
        print(f"   🎯 Scale factor used: 1.0 (PRESERVED)")
        
        # Calculate translation to align centers
        translation = obj_center - ply_center
        print(f"   Translation vector: {translation}")
        
        # Estimate rotation by comparing orientations
        rotation_matrix = self.estimate_rotation_alignment(ply_vertices, obj_vertices)
        print(f"   Rotation matrix computed: {rotation_matrix.shape}")
        
        # Create alignment transform WITHOUT SCALE
        transform = vtk.vtkTransform()
        transform.PostMultiply()
        
        # 1. Center PLY to origin
        transform.Translate(-ply_center)
        
        # 2. Apply rotation if computed
        if rotation_matrix is not None:
            vtk_matrix = vtk.vtkMatrix4x4()
            for i in range(3):
                for j in range(3):
                    vtk_matrix.SetElement(i, j, rotation_matrix[i, j])
            transform.Concatenate(vtk_matrix)
            print(f"   ✅ Rotation applied")
        else:
            print(f"   ⚠️  No rotation applied (using translation only)")
        
        # 3. NO SCALE APPLIED - This preserves manual landmark coordinates!
        
        # 4. Translate to OBJ center
        transform.Translate(obj_center)
        
        # Apply transform
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputData(ply_mesh)
        transform_filter.SetTransform(transform)
        transform_filter.Update()
        
        # Preserve color and texture data if present
        transformed_mesh = transform_filter.GetOutput()
        
        # Clean up the result (minimal processing)
        clean_filter = vtk.vtkCleanPolyData()
        clean_filter.SetInputData(transformed_mesh)
        clean_filter.Update()
        
        final_mesh = clean_filter.GetOutput()
        
        # Save result
        writer = vtk.vtkPLYWriter()
        writer.SetFileName(output_path)
        writer.SetInputData(final_mesh)
        writer.SetDataByteOrderToLittleEndian()
        writer.Write()
        
        # Verify result
        final_bounds = final_mesh.GetBounds()
        final_center = np.mean([[final_bounds[0], final_bounds[2], final_bounds[4]],
                               [final_bounds[1], final_bounds[3], final_bounds[5]]], axis=0)
        final_diagonal = np.sqrt(np.sum((np.array([final_bounds[1], final_bounds[3], final_bounds[5]]) - 
                                       np.array([final_bounds[0], final_bounds[2], final_bounds[4]]))**2))
        
        print(f"\n✅ Ultimate Scale-Free Alignment Complete!")
        print(f"   Final center: {final_center}")
        print(f"   Final diagonal: {final_diagonal:.1f}")
        print(f"   Final bounds: X[{final_bounds[0]:.1f}, {final_bounds[1]:.1f}] Y[{final_bounds[2]:.1f}, {final_bounds[3]:.1f}] Z[{final_bounds[4]:.1f}, {final_bounds[5]:.1f}]")
        print(f"   🎯 Scale preserved: 1.0x")
        print(f"   ✅ Manual landmarks remain valid!")
        print(f"   📁 Saved to: {output_path}")
        
        return {
            'original_scale_factor': original_scale_factor,
            'applied_scale_factor': 1.0,
            'translation': translation,
            'rotation_applied': rotation_matrix is not None,
            'final_center': final_center,
            'final_diagonal': final_diagonal,
            'output_file': output_path
        }
    
    def estimate_rotation_alignment(self, ply_vertices, obj_vertices):
        """Estimate rotation to align PLY with OBJ orientation"""
        try:
            # Use PCA to estimate principal axes
            def compute_pca_axes(vertices):
                center = np.mean(vertices, axis=0)
                centered = vertices - center
                cov_matrix = np.cov(centered.T)
                eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
                # Sort by eigenvalues (descending)
                idx = np.argsort(eigenvalues)[::-1]
                return eigenvectors[:, idx]
            
            ply_axes = compute_pca_axes(ply_vertices)
            obj_axes = compute_pca_axes(obj_vertices)
            
            # Calculate rotation matrix: R = obj_axes * ply_axes^T
            rotation_matrix = obj_axes @ ply_axes.T
            
            # Ensure proper rotation matrix (det = 1)
            if np.linalg.det(rotation_matrix) < 0:
                rotation_matrix[:, -1] *= -1
            
            return rotation_matrix
            
        except Exception as e:
            print(f"   ⚠️  Rotation estimation failed: {e}")
            return None

# Stand-alone execution
def main():
    if len(sys.argv) < 3:
        print("Usage: python ultimate_scale_free_preprocessor.py input.ply output.ply [obj_reference]")
        print("Example: python ultimate_scale_free_preprocessor.py input.ply aligned.ply assets/testmeshA.obj")
        sys.exit(1)
    
    input_ply = sys.argv[1]
    output_ply = sys.argv[2]
    obj_reference = sys.argv[3] if len(sys.argv) > 3 else "assets/testmeshA.obj"
    
    if not os.path.exists(input_ply):
        print(f"❌ Input PLY file not found: {input_ply}")
        sys.exit(1)
    
    if not os.path.exists(obj_reference):
        print(f"❌ OBJ reference file not found: {obj_reference}")
        sys.exit(1)
    
    processor = UltimateScaleFreePreprocessor()
    result = processor.align_ply_to_obj_system_scale_free(input_ply, output_ply, obj_reference)
    
    print(f"\n🎯 Ultimate Scale-Free Processing Summary:")
    print(f"   Input: {input_ply}")
    print(f"   Output: {output_ply}")
    print(f"   Scale preserved: ✅")
    print(f"   Ready for prediction with manual landmarks!")

if __name__ == "__main__":
    main()