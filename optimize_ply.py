#!/usr/bin/env python3
import json
import subprocess
import os
import re
import numpy as np
from itertools import product

class PLYOptimizer:
    def __init__(self):
        self.base_config_path = "configs/DTU3D-PLY-geometry.json"
        self.test_config_path = "configs/DTU3D-PLY-test.json"
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.ply_file = "assets/files/class1/men/2.ply"
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
    
    def run_prediction(self):
        """Run prediction and extract RANSAC error"""
        cmd = [self.python_path, "predict.py", "--c", self.test_config_path, "--n", self.ply_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = result.stderr + result.stdout
            
            # Extract RANSAC error
            ransac_pattern = r"Ransac average error\s+([\d.]+)"
            match = re.search(ransac_pattern, output)
            
            if match:
                ransac_error = float(match.group(1))
                return ransac_error, output
            else:
                return None, output
                
        except subprocess.TimeoutExpired:
            return None, "Timeout"
        except Exception as e:
            return None, str(e)
    
    def optimize_parameters(self):
        """Iteratively optimize parameters"""
        print("=== PLY Hizalama Parametresi Optimizasyonu ===\n")
        
        # Parameter ranges to test
        alignment_options = [True, False]
        rotation_ranges = {
            'rot_x': [0, -90, 90, 180, -180],
            'rot_y': [0, -90, 90, 180, -180], 
            'rot_z': [0, -90, 90, 180, -180]
        }
        scale_options = [0.001, 0.01, 0.1, 1.0, 10.0]
        rendering_options = ["geometry", "geometry+depth", "depth"]
        
        best_error = float('inf')
        best_params = None
        
        iteration = 0
        
        # Test different combinations
        print("Phase 1: Testing scale and rendering combinations...")
        for scale in scale_options:
            for rendering in rendering_options:
                iteration += 1
                print(f"\nIterasyon {iteration}: scale={scale}, rendering={rendering}")
                
                self.create_test_config(
                    align_center=True,
                    scale=scale,
                    image_channels=rendering
                )
                
                error, output = self.run_prediction()
                
                if error is not None:
                    print(f"  RANSAC Error: {error:.2f}")
                    
                    result = {
                        'iteration': iteration,
                        'align_center': True,
                        'rot_x': 0, 'rot_y': 0, 'rot_z': 0,
                        'scale': scale,
                        'rendering': rendering,
                        'ransac_error': error
                    }
                    self.results.append(result)
                    
                    if error < best_error:
                        best_error = error
                        best_params = result.copy()
                        print(f"  *** Yeni en iyi sonuç! ***")
                else:
                    print(f"  Hata: {output[:100]}...")
        
        print(f"\nPhase 1 tamamlandı. En iyi sonuç: {best_error:.2f}")
        
        # Phase 2: Optimize rotations with best scale and rendering
        if best_params:
            print(f"\nPhase 2: En iyi parametrelerle rotasyon optimizasyonu...")
            print(f"Sabit parametreler: scale={best_params['scale']}, rendering={best_params['rendering']}")
            
            for rot_x in rotation_ranges['rot_x'][:3]:  # Test fewer combinations
                for rot_y in rotation_ranges['rot_y'][:3]:
                    iteration += 1
                    print(f"\nIterasyon {iteration}: rot_x={rot_x}, rot_y={rot_y}")
                    
                    self.create_test_config(
                        align_center=True,
                        rot_x=rot_x,
                        rot_y=rot_y,
                        rot_z=0,
                        scale=best_params['scale'],
                        image_channels=best_params['rendering']
                    )
                    
                    error, output = self.run_prediction()
                    
                    if error is not None:
                        print(f"  RANSAC Error: {error:.2f}")
                        
                        result = {
                            'iteration': iteration,
                            'align_center': True,
                            'rot_x': rot_x, 'rot_y': rot_y, 'rot_z': 0,
                            'scale': best_params['scale'],
                            'rendering': best_params['rendering'],
                            'ransac_error': error
                        }
                        self.results.append(result)
                        
                        if error < best_error:
                            best_error = error
                            best_params = result.copy()
                            print(f"  *** Yeni en iyi sonuç! ***")
                    else:
                        print(f"  Hata: {output[:100]}...")
        
        return best_params
    
    def save_results(self, best_params):
        """Save optimization results"""
        print("\n=== OPTİMİZASYON SONUÇLARI ===")
        
        # Sort results by error
        sorted_results = sorted(self.results, key=lambda x: x['ransac_error'])
        
        print("\nEn iyi 5 sonuç:")
        for i, result in enumerate(sorted_results[:5]):
            print(f"{i+1}. RANSAC Error: {result['ransac_error']:.2f}")
            print(f"   Parametreler: align={result['align_center']}, "
                  f"rot=({result['rot_x']},{result['rot_y']},{result['rot_z']}), "
                  f"scale={result['scale']}, rendering={result['rendering']}")
        
        # Create optimized config with best parameters
        if best_params:
            print(f"\n=== EN İYİ KONFIGÜRASYON ===")
            print(f"RANSAC Error: {best_params['ransac_error']:.2f}")
            print(f"Parametreler: {best_params}")
            
            optimized_config_path = "configs/DTU3D-PLY-optimized-final.json"
            self.create_test_config(
                align_center=best_params['align_center'],
                rot_x=best_params['rot_x'],
                rot_y=best_params['rot_y'], 
                rot_z=best_params['rot_z'],
                scale=best_params['scale'],
                image_channels=best_params['rendering']
            )
            
            # Save as final optimized config
            os.rename(self.test_config_path, optimized_config_path)
            print(f"\nOptimize edilmiş konfigürasyon kaydedildi: {optimized_config_path}")
        
        # Save detailed results
        with open("ply_optimization_results.json", 'w') as f:
            json.dump(self.results, f, indent=2)
        print("Detaylı sonuçlar 'ply_optimization_results.json' dosyasına kaydedildi.")

def main():
    optimizer = PLYOptimizer()
    best_params = optimizer.optimize_parameters()
    optimizer.save_results(best_params)

if __name__ == "__main__":
    main()
