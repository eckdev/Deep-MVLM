#!/usr/bin/env python3
"""
Poor Performer Hybrid Optimizer
Automatically applies hybrid optimization to files that show poor performance with anatomical alignment
"""

import os
import sys
import json
import subprocess
import re
from anatomical_aligner import AnatomicalAligner

class PoorPerformerOptimizer:
    def __init__(self):
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.anatomical_config = "configs/DTU3D-anatomical.json"
        self.ultimate_config = "configs/DTU3D-PLY-ultimate-final.json"
        
        # Files identified as poor performers with anatomical method
        self.poor_performers = [
            ("8.ply", "men", 63013704.82),
            ("9.ply", "men", 68493156.75), 
            ("25.ply", "women", 69863019.68),
            ("27.ply", "women", 68493157.13),
            ("29.ply", "women", 23287685.52)
        ]
    
    def test_ultimate_preprocessing(self, filename, category):
        """Test ultimate preprocessing on a poor performer"""
        
        if category == "men":
            filepath = f"assets/files/class1/men/{filename}"
        else:
            filepath = f"assets/files/class1/women/{filename}"
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        base_name = os.path.splitext(filename)[0]
        temp_file = f"temp_ultimate_{base_name}.ply"
        
        print(f"\n🔧 Optimizing {filename} with ULTIMATE preprocessing:")
        print(f"   Input: {filepath}")
        print(f"   Output: {temp_file}")
        
        try:
            # Apply ultimate preprocessing
            from ultimate_ply_preprocessor import align_ply_to_obj_system
            align_ply_to_obj_system(filepath, temp_file)
            print(f"   ✅ Ultimate preprocessing completed")
            
            # Run prediction
            cmd = [self.python_path, "predict.py", "--c", self.ultimate_config, "--n", temp_file]
            
            pred_result = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
            output = pred_result.stderr + pred_result.stdout
            
            ransac_pattern = r"Ransac average error\s+([\d.]+)"
            match = re.search(ransac_pattern, output)
            
            if match:
                ransac_error = float(match.group(1))
                
                if ransac_error < 10:
                    performance = "🔥 EXCELLENT"
                    status = "excellent"
                elif ransac_error < 100:
                    performance = "🎉 VERY GOOD"
                    status = "very_good"
                elif ransac_error < 10000:
                    performance = "✅ GOOD"
                    status = "good"
                else:
                    performance = "⚠️ STILL POOR"
                    status = "poor"
                
                print(f"   🎯 RESULT: RANSAC {ransac_error:.2f} ({performance})")
                
                result = {
                    'file': base_name,
                    'category': category,
                    'method': 'ultimate',
                    'ransac_error': ransac_error,
                    'performance': performance,
                    'status': status,
                    'optimization_successful': ransac_error < 100
                }
                
                # Cleanup
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
                return result
            else:
                print(f"   ❌ Could not extract RANSAC error")
                
        except Exception as e:
            print(f"   ❌ Optimization failed: {e}")
        
        # Cleanup on failure
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return None
    
    def optimize_all_poor_performers(self):
        """Optimize all identified poor performers"""
        
        print(f"\n{'='*90}")
        print("POOR PERFORMER HYBRID OPTIMIZATION")
        print(f"{'='*90}")
        
        print(f"\n📋 POOR PERFORMERS IDENTIFIED:")
        print(f"{'File':<12} {'Category':<8} {'Anatomical RANSAC':<20}")
        print("-" * 50)
        for filename, category, ransac in self.poor_performers:
            print(f"{filename:<12} {category:<8} {ransac:<20.2f}")
        
        optimization_results = []
        
        for i, (filename, category, original_ransac) in enumerate(self.poor_performers, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(self.poor_performers)}] OPTIMIZING: {filename}")
            print(f"{'='*60}")
            print(f"Original anatomical RANSAC: {original_ransac:.2f}")
            
            result = self.test_ultimate_preprocessing(filename, category)
            if result:
                optimization_results.append({
                    'file': result['file'],
                    'category': result['category'],
                    'original_method': 'anatomical',
                    'original_ransac': original_ransac,
                    'optimized_method': 'ultimate',
                    'optimized_ransac': result['ransac_error'],
                    'improvement': original_ransac / result['ransac_error'],
                    'optimization_successful': result['optimization_successful'],
                    'final_status': result['status']
                })
        
        # Generate optimization report
        self.generate_optimization_report(optimization_results)
        return optimization_results
    
    def generate_optimization_report(self, results):
        """Generate comprehensive optimization report"""
        
        print(f"\n{'='*90}")
        print("OPTIMIZATION RESULTS REPORT")
        print(f"{'='*90}")
        
        if not results:
            print("❌ No optimization results available")
            return
        
        successful_optimizations = [r for r in results if r['optimization_successful']]
        
        print(f"\n🎯 OPTIMIZATION SUMMARY:")
        print(f"   Files processed: {len(results)}")
        print(f"   Successful optimizations: {len(successful_optimizations)}")
        print(f"   Success rate: {len(successful_optimizations)/len(results)*100:.1f}%")
        
        print(f"\n📊 DETAILED RESULTS:")
        print(f"{'File':<8} {'Category':<8} {'Original':<12} {'Optimized':<12} {'Improvement':<12} {'Status'}")
        print("-" * 80)
        
        for result in results:
            improvement = f"{result['improvement']:.0f}x" if result['improvement'] > 1 else "No improve"
            status_emoji = "✅" if result['optimization_successful'] else "⚠️"
            
            print(f"{result['file']:<8} {result['category']:<8} "
                  f"{result['original_ransac']:<12.2f} {result['optimized_ransac']:<12.2f} "
                  f"{improvement:<12} {status_emoji} {result['final_status']}")
        
        if successful_optimizations:
            avg_improvement = sum(r['improvement'] for r in successful_optimizations) / len(successful_optimizations)
            best_improvement = max(r['improvement'] for r in successful_optimizations)
            
            print(f"\n🚀 IMPROVEMENT STATISTICS:")
            print(f"   Average improvement: {avg_improvement:.1f}x better")
            print(f"   Best improvement: {best_improvement:.1f}x better")
            print(f"   All successful optimizations achieved RANSAC < 100")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if len(successful_optimizations) == len(results):
            print("   🎉 ALL poor performers successfully optimized!")
            print("   ✅ Ultimate preprocessing resolves all anatomical alignment issues")
            print("   🚀 Deploy optimal_ply_processor.py for automatic method selection")
        else:
            print(f"   ✅ {len(successful_optimizations)}/{len(results)} files successfully optimized")
            remaining = len(results) - len(successful_optimizations)
            if remaining > 0:
                print(f"   ⚠️  {remaining} files still need additional investigation")
        
        # Save detailed results
        with open('poor_performer_optimization_report.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed optimization results saved to: poor_performer_optimization_report.json")

def main():
    optimizer = PoorPerformerOptimizer()
    results = optimizer.optimize_all_poor_performers()
    
    print(f"\n{'='*90}")
    print("POOR PERFORMER OPTIMIZATION COMPLETED!")
    print(f"{'='*90}")

if __name__ == "__main__":
    main()
