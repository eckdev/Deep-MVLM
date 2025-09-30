#!/usr/bin/env python3
import json
import subprocess
import os
import re
import numpy as np

class PLYOptimizerAdvanced:
    def __init__(self):
        self.base_config_path = "configs/DTU3D-PLY-geometry.json"
        self.test_config_path = "configs/DTU3D-PLY-test-advanced.json"
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.ply_files = [
            "assets/files/class1/men/1.ply",
            "assets/files/class1/men/2.ply"
        ]
        self.results = []
        
    def load_base_config(self):
        """Load base configuration"""
        with open(self.base_config_path, 'r') as f:
            return json.load(f)
    
    def create_test_config(self, align_center=True, rot_x=0, rot_y=0, rot_z=0, scale=1.0, image_channels="geometry"):
        """Create test configuration with specific parameters"""
        config = self.load_base_config()
        
        # Update pre-align parameters
        config["pre-align"]["align_center_of_mass"] = align_center
        config["pre-align"]["rot_x"] = rot_x
        config["pre-align"]["rot_y"] = rot_y
        config["pre-align"]["rot_z"] = rot_z
        config["pre-align"]["scale"] = scale
        config["pre-align"]["write_pre_aligned"] = True
        
        # Update image channels
        config["arch"]["args"]["image_channels"] = image_channels
        config["data_loader"]["args"]["image_channels"] = image_channels
        
        # Write test config
        with open(self.test_config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def run_prediction(self, ply_file):
        """Run prediction and extract RANSAC error"""
        cmd = [self.python_path, "predict.py", "--c", self.test_config_path, "--n", ply_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            output = result.stderr + result.stdout
            
            # Extract RANSAC error
            ransac_pattern = r"Ransac average error\s+([\d.]+)"
            match = re.search(ransac_pattern, output)
            
            # Check for "Not enough valid view lines" warnings
            view_lines_warnings = output.count("Not enough valid view lines")
            
            if match:
                ransac_error = float(match.group(1))
                return ransac_error, view_lines_warnings, output
            else:
                return None, view_lines_warnings, output
                
        except subprocess.TimeoutExpired:
            return None, 0, "Timeout"
        except Exception as e:
            return None, 0, str(e)
    
    def optimize_practical_parameters(self):
        """Focus on practical parameter ranges"""
        print("=== PLY Pratik Parametre Optimizasyonu ===\n")
        
        # More practical parameter ranges
        scale_options = [0.01, 0.05, 0.1, 0.2, 0.5]
        rendering_options = ["geometry", "geometry+depth"]
        rotation_options = [
            (0, 0, 0),      # No rotation
            (-90, 0, 0),    # X axis rotation
            (0, 180, 0),    # Y axis rotation  
            (0, -90, 0),    # Y axis rotation
            (90, 180, 0),   # Combined rotation
        ]
        
        best_error = float('inf')
        best_params = None
        iteration = 0
        
        print("Testing practical parameter combinations...")
        
        for scale in scale_options:
            for rendering in rendering_options:
                for rot_x, rot_y, rot_z in rotation_options:
                    iteration += 1
                    print(f"\nIterasyon {iteration}: scale={scale}, rendering={rendering}, rot=({rot_x},{rot_y},{rot_z})")
                    
                    self.create_test_config(
                        align_center=True,
                        rot_x=rot_x,
                        rot_y=rot_y,
                        rot_z=rot_z,
                        scale=scale,
                        image_channels=rendering
                    )
                    
                    # Test on both PLY files
                    total_error = 0
                    total_warnings = 0
                    valid_tests = 0
                    
                    for ply_file in self.ply_files:
                        ply_name = os.path.basename(ply_file)
                        error, warnings, output = self.run_prediction(ply_file)
                        
                        if error is not None and warnings < 30:  # Less than 30 warnings is acceptable
                            total_error += error
                            total_warnings += warnings
                            valid_tests += 1
                            print(f"    {ply_name}: RANSAC={error:.2f}, Warnings={warnings}")
                        else:
                            print(f"    {ply_name}: Failed or too many warnings ({warnings})")
                    
                    if valid_tests > 0:
                        avg_error = total_error / valid_tests
                        avg_warnings = total_warnings / valid_tests
                        
                        result = {
                            'iteration': iteration,
                            'align_center': True,
                            'rot_x': rot_x, 'rot_y': rot_y, 'rot_z': rot_z,
                            'scale': scale,
                            'rendering': rendering,
                            'avg_ransac_error': avg_error,
                            'avg_warnings': avg_warnings,
                            'valid_tests': valid_tests
                        }
                        self.results.append(result)
                        
                        print(f"    Ortalama RANSAC Error: {avg_error:.2f}, Warnings: {avg_warnings:.1f}")
                        
                        if avg_error < best_error and avg_warnings < 20:
                            best_error = avg_error
                            best_params = result.copy()
                            print(f"    *** Yeni en iyi sonuç! ***")
        
        return best_params
    
    def save_practical_results(self, best_params):
        """Save practical optimization results"""
        print("\n=== PRATİK OPTİMİZASYON SONUÇLARI ===")
        
        # Filter valid results (low warnings)
        valid_results = [r for r in self.results if r['avg_warnings'] < 20]
        
        if not valid_results:
            print("Geçerli sonuç bulunamadı!")
            return
        
        # Sort results by error
        sorted_results = sorted(valid_results, key=lambda x: x['avg_ransac_error'])
        
        print("\nEn iyi 5 pratik sonuç:")
        for i, result in enumerate(sorted_results[:5]):
            print(f"{i+1}. Ortalama RANSAC Error: {result['avg_ransac_error']:.2f}")
            print(f"   Ortalama Warnings: {result['avg_warnings']:.1f}")
            print(f"   Parametreler: rot=({result['rot_x']},{result['rot_y']},{result['rot_z']}), "
                  f"scale={result['scale']}, rendering={result['rendering']}")
        
        # Create practical optimized config
        if best_params:
            print(f"\n=== EN İYİ PRATİK KONFIGÜRASYON ===")
            print(f"Ortalama RANSAC Error: {best_params['avg_ransac_error']:.2f}")
            print(f"Ortalama Warnings: {best_params['avg_warnings']:.1f}")
            print(f"Parametreler: {best_params}")
            
            practical_config_path = "configs/DTU3D-PLY-practical.json"
            self.create_test_config(
                align_center=best_params['align_center'],
                rot_x=best_params['rot_x'],
                rot_y=best_params['rot_y'], 
                rot_z=best_params['rot_z'],
                scale=best_params['scale'],
                image_channels=best_params['rendering']
            )
            
            # Save as practical optimized config
            os.rename(self.test_config_path, practical_config_path)
            print(f"\nPratik optimize edilmiş konfigürasyon kaydedildi: {practical_config_path}")
        
        # Save detailed results
        with open("ply_practical_optimization_results.json", 'w') as f:
            json.dump(self.results, f, indent=2)
        print("Detaylı sonuçlar 'ply_practical_optimization_results.json' dosyasına kaydedildi.")

def main():
    optimizer = PLYOptimizerAdvanced()
    best_params = optimizer.optimize_practical_parameters()
    optimizer.save_practical_results(best_params)

if __name__ == "__main__":
    main()
