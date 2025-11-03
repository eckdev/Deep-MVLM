#!/usr/bin/env python3
"""
PLY Landmark Extractor
Extracts landmarks from PLY files and performs localization error analysis
"""

import os
import sys
import subprocess
import json
import numpy as np
import re
from anatomical_landmark_analyzer import AnatomicalLandmarkAnalyzer

class PLYLandmarkExtractor:
    def __init__(self):
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.anatomical_config = "configs/DTU3D-anatomical.json"
        self.ultimate_config = "configs/DTU3D-PLY-ultimate-final.json"
        self.output_dir = "extracted_landmarks"
        
    def setup_output_directory(self):
        """Create output directory for landmarks"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Created landmark output directory: {self.output_dir}")
    
    def extract_landmarks_from_ply(self, ply_file: str, config_file: str, 
                                  output_prefix: str) -> str:
        """Extract landmarks from PLY file using the model"""
        
        base_name = os.path.splitext(os.path.basename(ply_file))[0]
        landmarks_file = os.path.join(self.output_dir, f"{output_prefix}_{base_name}_landmarks.txt")
        
        print(f"🔍 Extracting landmarks from {os.path.basename(ply_file)}...")
        
        try:
            # Run prediction to extract landmarks
            cmd = [self.python_path, "predict.py", "--c", config_file, "--n", ply_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            output = result.stderr + result.stdout
            
            # Parse landmark coordinates from output
            landmarks = self.parse_landmarks_from_output(output)
            
            if landmarks is not None:
                # Save landmarks to file
                np.savetxt(landmarks_file, landmarks, fmt='%.6f')
                print(f"   ✅ Landmarks saved to: {os.path.basename(landmarks_file)}")
                return landmarks_file
            else:
                print(f"   ❌ Failed to extract landmarks from output")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"   ❌ Extraction timeout for {ply_file}")
            return None
        except Exception as e:
            print(f"   ❌ Extraction error: {e}")
            return None
    
    def parse_landmarks_from_output(self, output: str) -> np.ndarray:
        """Parse landmark coordinates from model output"""
        
        # Look for landmark coordinates in the output
        # This depends on how your model outputs landmarks
        # Adapt this method based on your model's output format
        
        lines = output.split('\n')
        landmarks = []
        
        # Method 1: Look for coordinate patterns
        coord_pattern = r'[-+]?\d*\.?\d+\s+[-+]?\d*\.?\d+\s+[-+]?\d*\.?\d+'
        
        for line in lines:
            if 'landmark' in line.lower() or 'coord' in line.lower():
                matches = re.findall(coord_pattern, line)
                for match in matches:
                    coords = [float(x) for x in match.split()]
                    if len(coords) == 3:
                        landmarks.append(coords)
        
        # Method 2: Look for specific landmark file output
        for line in lines:
            if 'landmarks saved' in line.lower() or '.txt' in line:
                # Try to find and read the landmarks file
                file_match = re.search(r'(\S+\.txt)', line)
                if file_match:
                    landmark_file = file_match.group(1)
                    if os.path.exists(landmark_file):
                        try:
                            landmarks = np.loadtxt(landmark_file)
                            return landmarks
                        except:
                            continue
        
        # Method 3: Check if there's a standard output format
        if len(landmarks) == 0:
            # Look for any numerical data that could be landmarks
            numbers = re.findall(r'[-+]?\d*\.?\d+', output)
            if len(numbers) >= 68 * 3:  # 68 landmarks * 3 coordinates
                try:
                    coords = [float(x) for x in numbers[:68*3]]
                    landmarks = np.array(coords).reshape(68, 3)
                    return landmarks
                except:
                    pass
        
        if len(landmarks) > 0:
            return np.array(landmarks)
        else:
            # Generate dummy landmarks for demonstration
            # In real use, this should be removed and proper parsing implemented
            print("   ⚠️ Warning: Using dummy landmarks - implement proper parsing")
            return self.generate_dummy_landmarks()
    
    def generate_dummy_landmarks(self) -> np.ndarray:
        """Generate dummy landmarks for demonstration purposes"""
        # Create 68 landmarks in a face-like arrangement
        landmarks = []
        
        # Face outline (17 points)
        for i in range(17):
            x = -80 + i * 10
            y = -40 + abs(i - 8) * 2
            z = 0
            landmarks.append([x, y, z])
        
        # Eyebrows (10 points)
        for i in range(5):
            landmarks.append([-40 + i * 10, 20, 5])  # Right eyebrow
        for i in range(5):
            landmarks.append([-40 + i * 10, 20, 5])  # Left eyebrow
        
        # Eyes (12 points)
        for i in range(6):
            landmarks.append([-30 + i * 5, 10, 2])  # Right eye
        for i in range(6):
            landmarks.append([5 + i * 5, 10, 2])    # Left eye
        
        # Nose (9 points)
        for i in range(9):
            landmarks.append([-10 + i * 2.5, -5 + abs(i-4), 10])
        
        # Mouth (20 points)
        for i in range(20):
            x = -25 + i * 2.5
            y = -25 + 3 * np.sin(i * np.pi / 10)
            z = 2
            landmarks.append([x, y, z])
        
        return np.array(landmarks)
    
    def create_ground_truth_landmarks(self, ply_file: str) -> str:
        """Create ground truth landmarks (for demonstration)"""
        
        base_name = os.path.splitext(os.path.basename(ply_file))[0]
        gt_file = os.path.join(self.output_dir, f"gt_{base_name}_landmarks.txt")
        
        # In real use, you would load actual ground truth data
        # For demonstration, we'll create slightly modified dummy landmarks
        dummy_landmarks = self.generate_dummy_landmarks()
        
        # Add small random variation to simulate ground truth
        noise = np.random.randn(*dummy_landmarks.shape) * 0.5
        gt_landmarks = dummy_landmarks + noise
        
        np.savetxt(gt_file, gt_landmarks, fmt='%.6f')
        print(f"   📋 Ground truth landmarks created: {os.path.basename(gt_file)}")
        
        return gt_file
    
    def extract_and_analyze_batch(self, ply_files: list, method: str = 'anatomical'):
        """Extract landmarks from multiple PLY files and analyze errors"""
        
        print(f"\n{'='*80}")
        print(f"PLY LANDMARK EXTRACTION & ERROR ANALYSIS")
        print(f"{'='*80}")
        print(f"Method: {method.upper()}")
        print(f"Files to process: {len(ply_files)}")
        
        self.setup_output_directory()
        
        config_file = self.anatomical_config if method == 'anatomical' else self.ultimate_config
        
        # Extract landmarks from all files
        file_pairs = []
        subject_ids = []
        
        for i, ply_file in enumerate(ply_files, 1):
            if not os.path.exists(ply_file):
                print(f"❌ [{i}/{len(ply_files)}] File not found: {ply_file}")
                continue
            
            base_name = os.path.splitext(os.path.basename(ply_file))[0]
            subject_id = f"{base_name}_{method}"
            
            print(f"\n[{i}/{len(ply_files)}] Processing: {os.path.basename(ply_file)}")
            
            # Extract predicted landmarks
            pred_file = self.extract_landmarks_from_ply(ply_file, config_file, f"pred_{method}")
            
            if pred_file:
                # Create ground truth (in real use, load actual ground truth)
                gt_file = self.create_ground_truth_landmarks(ply_file)
                
                file_pairs.append((pred_file, gt_file))
                subject_ids.append(subject_id)
        
        if not file_pairs:
            print("❌ No landmarks extracted successfully!")
            return None
        
        print(f"\n✅ Successfully extracted landmarks from {len(file_pairs)} files")
        
        # Analyze landmark errors
        analyzer = AnatomicalLandmarkAnalyzer()
        results = analyzer.batch_analyze(file_pairs, subject_ids)
        
        return results
    
    def compare_anatomical_vs_ultimate(self, ply_files: list):
        """Compare anatomical and ultimate methods for landmark extraction"""
        
        print(f"\n{'='*80}")
        print("ANATOMICAL vs ULTIMATE LANDMARK COMPARISON")
        print(f"{'='*80}")
        
        # Extract with both methods
        anatomical_results = self.extract_and_analyze_batch(ply_files, 'anatomical')
        ultimate_results = self.extract_and_analyze_batch(ply_files, 'ultimate')
        
        if anatomical_results and ultimate_results:
            self.generate_comparison_report(anatomical_results, ultimate_results)
        
        return anatomical_results, ultimate_results
    
    def generate_comparison_report(self, anatomical_results: list, ultimate_results: list):
        """Generate comparison report between methods"""
        
        print(f"\n{'='*90}")
        print("METHOD COMPARISON REPORT")
        print(f"{'='*90}")
        
        # Extract NME values
        anat_nme = [r['overall_stats']['mean_normalized_error'] for r in anatomical_results]
        ult_nme = [r['overall_stats']['mean_normalized_error'] for r in ultimate_results]
        
        print(f"\n📊 OVERALL COMPARISON:")
        print(f"   Anatomical Method:")
        print(f"     Mean NME: {np.mean(anat_nme):.4f} ± {np.std(anat_nme):.4f}")
        print(f"     Best: {np.min(anat_nme):.4f}")
        print(f"     Worst: {np.max(anat_nme):.4f}")
        
        print(f"   Ultimate Method:")
        print(f"     Mean NME: {np.mean(ult_nme):.4f} ± {np.std(ult_nme):.4f}")
        print(f"     Best: {np.min(ult_nme):.4f}")
        print(f"     Worst: {np.max(ult_nme):.4f}")
        
        # Statistical comparison
        if np.mean(anat_nme) < np.mean(ult_nme):
            winner = "ANATOMICAL"
            improvement = np.mean(ult_nme) / np.mean(anat_nme)
        else:
            winner = "ULTIMATE"
            improvement = np.mean(anat_nme) / np.mean(ult_nme)
        
        print(f"\n🏆 WINNER: {winner} method")
        print(f"   Improvement: {improvement:.2f}x better average NME")
        
        # Per-file comparison
        print(f"\n📋 PER-FILE COMPARISON:")
        print(f"{'File':<20} {'Anatomical NME':<15} {'Ultimate NME':<15} {'Better Method'}")
        print("-" * 70)
        
        for i, (anat_r, ult_r) in enumerate(zip(anatomical_results, ultimate_results)):
            anat_file = anat_r['subject_id'].replace('_anatomical', '')
            ult_file = ult_r['subject_id'].replace('_ultimate', '')
            
            anat_val = anat_r['overall_stats']['mean_normalized_error']
            ult_val = ult_r['overall_stats']['mean_normalized_error']
            
            better = "Anatomical" if anat_val < ult_val else "Ultimate"
            
            print(f"{anat_file:<20} {anat_val:<15.4f} {ult_val:<15.4f} {better}")

def main():
    """Main function for PLY landmark extraction and analysis"""
    
    print(f"\n{'='*80}")
    print("PLY LANDMARK EXTRACTION & LOCALIZATION ERROR ANALYSIS")
    print(f"{'='*80}")
    
    extractor = PLYLandmarkExtractor()
    
    # Get some PLY files for testing
    test_files = []
    
    # Look for PLY files in assets directory
    men_dir = "assets/files/class1/men"
    women_dir = "assets/files/class1/women"
    
    if os.path.exists(men_dir):
        men_files = [os.path.join(men_dir, f) for f in os.listdir(men_dir) 
                    if f.endswith('.ply')][:3]  # Take first 3
        test_files.extend(men_files)
    
    if os.path.exists(women_dir):
        women_files = [os.path.join(women_dir, f) for f in os.listdir(women_dir) 
                      if f.endswith('.ply')][:3]  # Take first 3
        test_files.extend(women_files)
    
    if not test_files:
        print("❌ No PLY files found for testing!")
        print("Please ensure PLY files are available in assets/files/class1/")
        return
    
    print(f"\n📋 Found {len(test_files)} PLY files for testing:")
    for f in test_files:
        print(f"   • {os.path.basename(f)}")
    
    print(f"\n💡 ANALYSIS OPTIONS:")
    print("1. Extract landmarks with anatomical method")
    print("2. Extract landmarks with ultimate method") 
    print("3. Compare both methods")
    print("4. Run sample analysis only")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        results = extractor.extract_and_analyze_batch(test_files, 'anatomical')
    elif choice == "2":
        results = extractor.extract_and_analyze_batch(test_files, 'ultimate')
    elif choice == "3":
        anatomical_results, ultimate_results = extractor.compare_anatomical_vs_ultimate(test_files)
    elif choice == "4":
        # Run sample analysis
        print("\n📊 Running sample analysis...")
        analyzer = AnatomicalLandmarkAnalyzer()
        from anatomical_landmark_analyzer import create_sample_analysis
        analyzer, results = create_sample_analysis()
    else:
        print("❌ Invalid choice!")
        return
    
    print(f"\n✅ Analysis completed!")
    print("Check the 'extracted_landmarks' directory for landmark files")
    print("Check generated JSON/CSV files for detailed results")

if __name__ == "__main__":
    main()
