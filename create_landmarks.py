# Script to create sample landmark files for PLY dataset
# This creates 68 standard facial landmarks with sample coordinates

import os
import numpy as np

def create_sample_landmarks_68():
    """
    Create 68 standard facial landmarks with sample coordinates
    These are approximate positions that would need to be manually adjusted for each face
    """
    # Standard 68 facial landmarks (approximate coordinates)
    landmarks = [
        # Jaw line (0-16)
        [-30, -20, 0], [-27, -15, -3], [-24, -10, -6], [-21, -5, -8], [-18, 0, -10],
        [-15, 5, -12], [-12, 10, -13], [-9, 15, -14], [0, 18, -15],
        [9, 15, -14], [12, 10, -13], [15, 5, -12], [18, 0, -10],
        [21, -5, -8], [24, -10, -6], [27, -15, -3], [30, -20, 0],
        
        # Right eyebrow (17-21)
        [-20, -5, 5], [-15, -8, 8], [-10, -10, 10], [-5, -8, 8], [0, -5, 5],
        
        # Left eyebrow (22-26)
        [0, -5, 5], [5, -8, 8], [10, -10, 10], [15, -8, 8], [20, -5, 5],
        
        # Nose bridge (27-30)
        [0, -2, 12], [0, 2, 15], [0, 6, 18], [0, 10, 20],
        
        # Lower nose (31-35)
        [-8, 12, 18], [-4, 14, 20], [0, 15, 22], [4, 14, 20], [8, 12, 18],
        
        # Right eye (36-41)
        [-15, -2, 8], [-12, -5, 10], [-8, -5, 10], [-5, -2, 8], [-8, -2, 8], [-12, -2, 8],
        
        # Left eye (42-47)
        [5, -2, 8], [8, -5, 10], [12, -5, 10], [15, -2, 8], [12, -2, 8], [8, -2, 8],
        
        # Outer lip (48-59)
        [-12, 8, 5], [-8, 6, 8], [-4, 4, 10], [0, 4, 12], [4, 4, 10], [8, 6, 8], [12, 8, 5],
        [8, 12, 8], [4, 14, 10], [0, 15, 12], [-4, 14, 10], [-8, 12, 8],
        
        # Inner lip (60-67)
        [-8, 8, 8], [-4, 6, 10], [0, 6, 12], [4, 6, 10], [8, 8, 8],
        [4, 10, 10], [0, 11, 12], [-4, 10, 10]
    ]
    
    return landmarks

def create_landmark_files():
    """Create landmark files for all PLY files in the dataset"""
    
    # Paths
    base_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/data/YOUR_DATASET_RAW"
    men_path = os.path.join(base_path, "men")
    women_path = os.path.join(base_path, "women")
    
    # Get sample landmarks
    sample_landmarks = create_sample_landmarks_68()
    
    # Create landmark files for men
    for ply_file in os.listdir(men_path):
        if ply_file.endswith('.ply'):
            landmark_file = ply_file.replace('.ply', '_landmarks.txt')
            landmark_path = os.path.join(men_path, landmark_file)
            
            # Add some random variation to make each face slightly different
            landmarks = []
            for lm in sample_landmarks:
                # Add small random variations (±2 units in each direction)
                varied_lm = [
                    lm[0] + np.random.uniform(-2, 2),
                    lm[1] + np.random.uniform(-2, 2),
                    lm[2] + np.random.uniform(-2, 2)
                ]
                landmarks.append(varied_lm)
            
            # Write landmarks to file
            with open(landmark_path, 'w') as f:
                for lm in landmarks:
                    f.write(f"{lm[0]:.6f} {lm[1]:.6f} {lm[2]:.6f}\n")
            
            print(f"Created: {landmark_path}")
    
    # Create landmark files for women
    for ply_file in os.listdir(women_path):
        if ply_file.endswith('.ply'):
            landmark_file = ply_file.replace('.ply', '_landmarks.txt')
            landmark_path = os.path.join(women_path, landmark_file)
            
            # Add some random variation to make each face slightly different
            landmarks = []
            for lm in sample_landmarks:
                # Add small random variations (±2 units in each direction)
                varied_lm = [
                    lm[0] + np.random.uniform(-2, 2),
                    lm[1] + np.random.uniform(-2, 2),
                    lm[2] + np.random.uniform(-2, 2)
                ]
                landmarks.append(varied_lm)
            
            # Write landmarks to file
            with open(landmark_path, 'w') as f:
                for lm in landmarks:
                    f.write(f"{lm[0]:.6f} {lm[1]:.6f} {lm[2]:.6f}\n")
            
            print(f"Created: {landmark_path}")

if __name__ == "__main__":
    create_landmark_files()
    print("\\nLandmark files created successfully!")
    print("\\nNOTE: These are sample landmarks with random variations.")
    print("For real usage, you would need to manually annotate landmarks")
    print("or use an automatic landmark detection tool.")
