import argparse
from parse_config import ConfigParser
import os
import socket
import vtk
import numpy as np
import glob


def create_lock_file(name):
    f = open(name, "w")
    f.write(socket.gethostname())
    f.close()


def delete_lock_file(name):
    if os.path.exists(name):
        os.remove(name)


def random_transform(config):
    min_x = config['process_3d']['min_x_angle']
    max_x = config['process_3d']['max_x_angle']
    min_y = config['process_3d']['min_y_angle']
    max_y = config['process_3d']['max_y_angle']
    min_z = config['process_3d']['min_z_angle']
    max_z = config['process_3d']['max_z_angle']

    rx = np.double(np.random.randint(min_x, max_x, 1))
    ry = np.double(np.random.randint(min_y, max_y, 1))
    rz = np.double(np.random.randint(min_z, max_z, 1))
    scale = np.double(np.random.uniform(1.4, 1.9, 1))
    tx = np.double(np.random.randint(-20, 20, 1))
    ty = np.double(np.random.randint(-20, 20, 1))

    return rx, ry, rz, scale, tx, ty


def process_file_ply_dataset(config, file_name, output_dir):
    """Process PLY files with landmarks for custom dataset"""
    
    raw_data_dir = config['preparedata']['raw_data_dir']
    base_name = os.path.splitext(os.path.basename(file_name))[0]
    
    # Construct file paths
    name_pd = file_name  # PLY file path
    name_lm = os.path.join(os.path.dirname(file_name), base_name + '_landmarks.txt')
    
    print(f"Processing: {name_pd}")
    print(f"Landmarks: {name_lm}")
    
    # Check if landmark file exists
    if not os.path.exists(name_lm):
        print(f"Warning: Landmark file not found: {name_lm}")
        return
    
    # Create output directories
    relative_path = os.path.relpath(os.path.dirname(file_name), raw_data_dir)
    o_dir_image = os.path.join(output_dir, 'images', relative_path)
    o_dir_lm = os.path.join(output_dir, '2D LM', relative_path)
    
    os.makedirs(o_dir_image, exist_ok=True)
    os.makedirs(o_dir_lm, exist_ok=True)
    
    # Load landmarks
    lms = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    
    with open(name_lm) as f:
        for line in f:
            line = line.strip()
            if line:
                x, y, z = map(float, line.split())
                points.InsertNextPoint(x, y, z)
    
    lms.SetPoints(points)
    
    # Load PLY file
    reader = vtk.vtkPLYReader()
    reader.SetFileName(name_pd)
    reader.Update()
    pd = reader.GetOutput()
    
    # Remove any existing scalars to ensure clean geometry rendering
    pd.GetPointData().SetScalars(None)
    
    # Rendering parameters
    win_size = config['data_loader']['args']['image_size']
    off_screen_rendering = config['preparedata']['off_screen_rendering']
    n_views = config['data_loader']['args']['n_views']
    
    # Initialize Camera
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)  # White background
    camera = ren.GetActiveCamera()
    camera.SetPosition(0, 0, 200)
    camera.SetFocalPoint(0, 0, 0)
    camera.SetViewUp(0, 1, 0)
    camera.SetParallelProjection(1)
    
    # Initialize RenderWindow
    ren_win = vtk.vtkRenderWindow()
    ren_win.AddRenderer(ren)
    ren_win.SetSize(win_size, win_size)
    ren_win.SetOffScreenRendering(off_screen_rendering)
    
    # Window to image filter
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(ren_win)
    w2if.SetScale(1)
    
    # PNG writer
    writer = vtk.vtkPNGWriter()
    writer.SetInputConnection(w2if.GetOutputPort())
    
    # Process multiple views
    for view_idx in range(n_views):
        # Generate random transformation
        rx, ry, rz, scale, tx, ty = random_transform(config)
        
        # Initialize Transform
        t = vtk.vtkTransform()
        t.Identity()
        t.RotateX(rx)
        t.RotateY(ry) 
        t.RotateZ(rz)
        t.Scale(scale, scale, scale)
        t.Translate(tx, ty, 0)
        t.Update()
        
        # Transform mesh
        trans = vtk.vtkTransformPolyDataFilter()
        trans.SetInputData(pd)
        trans.SetTransform(t)
        trans.Update()
        
        # Transform landmarks
        trans_lm = vtk.vtkTransformPolyDataFilter()
        trans_lm.SetInputData(lms)
        trans_lm.SetTransform(t)
        trans_lm.Update()
        
        # Create mapper and actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(trans.GetOutput())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.8, 0.8, 0.8)  # Gray color for geometry
        actor.GetProperty().SetAmbient(0.3)
        actor.GetProperty().SetDiffuse(0.7)
        actor.GetProperty().SetSpecular(0.0)
        
        # Clear previous actors and add new one
        ren.RemoveAllViewProps()
        ren.AddActor(actor)
        
        # Auto-adjust camera to fit the object
        ren.ResetCamera()
        camera.SetParallelScale(100)  # Adjust this value as needed
        
        # Render
        ren_win.Render()
        
        # Save rendered image
        image_name = f"{base_name}_{view_idx}_geometry.png"
        image_path = os.path.join(o_dir_image, image_name)
        w2if.Modified()
        writer.SetFileName(image_path)
        writer.Write()
        
        # Project 3D landmarks to 2D
        landmarks_2d = []
        transformed_landmarks = trans_lm.GetOutput()
        
        for i in range(transformed_landmarks.GetNumberOfPoints()):
            point_3d = transformed_landmarks.GetPoint(i)
            
            # Project 3D point to 2D screen coordinates
            ren.SetWorldPoint(point_3d[0], point_3d[1], point_3d[2], 1.0)
            ren.WorldToDisplay()
            display_point = ren.GetDisplayPoint()
            
            # Convert to image coordinates (flip Y axis)
            x_2d = display_point[0]
            y_2d = win_size - display_point[1]  # Flip Y coordinate
            
            landmarks_2d.append([x_2d, y_2d])
        
        # Save 2D landmarks
        lm_2d_name = f"{base_name}_{view_idx}_landmarks.txt"
        lm_2d_path = os.path.join(o_dir_lm, lm_2d_name)
        
        with open(lm_2d_path, 'w') as f:
            for lm in landmarks_2d:
                f.write(f"{lm[0]:.6f} {lm[1]:.6f}\n")
        
        print(f"  View {view_idx + 1}/{n_views}: {image_name}")


def main():
    args = argparse.ArgumentParser(description='Prepare data for training')
    args.add_argument('-c', '--config', default=None, type=str,
                      help='config file path (default: None)')
    args.add_argument('-r', '--resume', default=None, type=str,
                      help='path to latest checkpoint (default: None)')
    args.add_argument('-d', '--device', default=None, type=str,
                      help='indices of GPUs to enable (default: all)')

    config = ConfigParser(args)
    
    # Get directory paths
    raw_data_dir = config['preparedata']['raw_data_dir']
    processed_data_dir = config['preparedata']['processed_data_dir']
    
    print(f"Raw data directory: {raw_data_dir}")
    print(f"Processed data directory: {processed_data_dir}")
    
    # Create processed data directory
    os.makedirs(processed_data_dir, exist_ok=True)
    
    # Find all PLY files
    ply_files = []
    for root, dirs, files in os.walk(raw_data_dir):
        for file in files:
            if file.endswith('.ply'):
                ply_files.append(os.path.join(root, file))
    
    print(f"Found {len(ply_files)} PLY files")
    
    # Process each PLY file
    for i, ply_file in enumerate(ply_files):
        print(f"\nProcessing file {i + 1}/{len(ply_files)}: {ply_file}")
        try:
            process_file_ply_dataset(config, ply_file, processed_data_dir)
        except Exception as e:
            print(f"Error processing {ply_file}: {str(e)}")
            continue
    
    # Create dataset split files
    train_files = []
    test_files = []
    
    # Use 80% for training, 20% for testing
    np.random.shuffle(ply_files)
    split_idx = int(len(ply_files) * 0.8)
    train_files = ply_files[:split_idx]
    test_files = ply_files[split_idx:]
    
    # Write dataset split files
    train_file_path = os.path.join(processed_data_dir, 'dataset_train.txt')
    test_file_path = os.path.join(processed_data_dir, 'dataset_test.txt')
    
    with open(train_file_path, 'w') as f:
        for file_path in train_files:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            relative_path = os.path.relpath(os.path.dirname(file_path), raw_data_dir)
            if relative_path != '.':
                f.write(f"{relative_path}/{base_name}\n")
            else:
                f.write(f"{base_name}\n")
    
    with open(test_file_path, 'w') as f:
        for file_path in test_files:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            relative_path = os.path.relpath(os.path.dirname(file_path), raw_data_dir)
            if relative_path != '.':
                f.write(f"{relative_path}/{base_name}\n")
            else:
                f.write(f"{base_name}\n")
    
    print(f"\nDataset preparation completed!")
    print(f"Training files: {len(train_files)} (saved to {train_file_path})")
    print(f"Test files: {len(test_files)} (saved to {test_file_path})")


if __name__ == '__main__':
    main()
