#!/usr/bin/env python3
"""
Ultimate PLY Preprocessing for Deep-MVLM
This script aligns PLY files to OBJ coordinate system for optimal results
"""
import vtk
import numpy as np
import sys
try:
    from scipy.spatial import procrustes
except ImportError:
    print("Warning: scipy.spatial.procrustes not available, using basic alignment")
    procrustes = None

def align_ply_to_obj_system(ply_path, output_path, obj_reference="assets/testmeshA.obj"):
    """Align PLY to OBJ coordinate system"""
    
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
    
    # Create alignment transform
    transform = vtk.vtkTransform()
    transform.Translate(-ply_center)
    
    scale_factor = obj_diagonal / ply_diagonal
    transform.Scale(scale_factor, scale_factor, scale_factor)
    transform.Translate(obj_center)
    
    # Apply transform
    transform_filter = vtk.vtkTransformPolyDataFilter()
    transform_filter.SetInputData(ply_mesh)
    transform_filter.SetTransform(transform)
    transform_filter.Update()
    
    # Save result
    writer = vtk.vtkPLYWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(transform_filter.GetOutput())
    writer.Write()
    
    print(f"PLY aligned and saved to: {output_path}")
    print(f"Scale factor: {scale_factor:.6f}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python ultimate_ply_preprocessor.py input.ply output.ply")
        sys.exit(1)
    
    align_ply_to_obj_system(sys.argv[1], sys.argv[2])
