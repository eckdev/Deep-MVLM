#!/usr/bin/env python3
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
