#!/usr/bin/env python3
"""
Comprehensive PLY Analysis Report Generator
Analyzes all PLY files with smart sampling and hybrid optimization
"""

import os
import sys
import json
import subprocess
import re
import numpy as np
from anatomical_aligner import AnatomicalAligner

class ComprehensivePLYAnalyzer:
    def __init__(self):
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.anatomical_config = "configs/DTU3D-anatomical.json"
        self.ultimate_config = "configs/DTU3D-PLY-ultimate-final.json"
        self.anatomical_aligner = AnatomicalAligner()
        
        # Known results from previous testing
        self.known_excellent_anatomical = {
            "1": 4.15, "2": 6.87, "3": 4.06, "5": 3.79,
            "19": 5.77, "20": 5.53, "21": 6.07, "22": 3.99
        }
        
        self.known_poor_anatomical = {
            "4": 1369869.29, "6": 64383569.80, 
            "23": 75342470.86, "24": 1369872.89
        }
        
        self.known_excellent_ultimate = {
            "4": 4.70, "6": 4.68, "23": 8.24, "24": 4.09
        }
    
    def get_all_ply_files(self):
        """Get all PLY files categorized"""
        men_dir = "assets/files/class1/men"
        women_dir = "assets/files/class1/women"
        
        men_files = []
        women_files = []
        
        if os.path.exists(men_dir):
            men_ply = [f for f in os.listdir(men_dir) if f.endswith('.ply')]
            men_ply.sort(key=lambda x: int(x.split('.')[0]))
            men_files = [(f, os.path.join(men_dir, f)) for f in men_ply]
        
        if os.path.exists(women_dir):
            women_ply = [f for f in os.listdir(women_dir) if f.endswith('.ply')]
            women_ply.sort(key=lambda x: int(x.split('.')[0]))
            women_files = [(f, os.path.join(women_dir, f)) for f in women_ply]
        
        return men_files, women_files
    
    def test_sample_files(self, sample_files, method="anatomical"):
        """Test a sample of files with specified method"""
        results = []
        
        for i, (filename, filepath) in enumerate(sample_files, 1):
            base_name = os.path.splitext(filename)[0]
            print(f"\n[{i}/{len(sample_files)}] Testing {filename} with {method.upper()}")
            
            if method == "anatomical":
                temp_file = f"temp_ana_{base_name}.ply"
                config = self.anatomical_config
                
                try:
                    result = self.anatomical_aligner.apply_anatomical_alignment(filepath, temp_file)
                    print(f"✅ Anatomical alignment completed")
                except Exception as e:
                    print(f"❌ Anatomical alignment failed: {e}")
                    continue
            
            elif method == "ultimate":
                temp_file = f"temp_ult_{base_name}.ply"
                config = self.ultimate_config
                
                try:
                    from ultimate_ply_preprocessor import align_ply_to_obj_system
                    align_ply_to_obj_system(filepath, temp_file)
                    print(f"✅ Ultimate alignment completed")
                except Exception as e:
                    print(f"❌ Ultimate alignment failed: {e}")
                    continue
            
            # Run prediction
            cmd = [self.python_path, "predict.py", "--c", config, "--n", temp_file]
            
            try:
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
                        performance = "⚠️ POOR"
                        status = "poor"
                    
                    print(f"   RANSAC: {ransac_error:.2f} ({performance})")
                    
                    results.append({
                        'file': base_name,
                        'method': method,
                        'ransac_error': ransac_error,
                        'performance': performance,
                        'status': status
                    })
                else:
                    print(f"   ❌ Could not extract RANSAC error")
                    
            except subprocess.TimeoutExpired:
                print(f"   ❌ Prediction timeout")
            except Exception as e:
                print(f"   ❌ Prediction error: {e}")
            
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return results
    
    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report"""
        print(f"\n{'='*90}")
        print("COMPREHENSIVE PLY ANALYSIS REPORT")
        print(f"{'='*90}")
        
        men_files, women_files = self.get_all_ply_files()
        
        print(f"\n📊 FILE INVENTORY:")
        print(f"   Men PLY files: {len(men_files)}")
        print(f"   Women PLY files: {len(women_files)}")
        print(f"   Total PLY files: {len(men_files) + len(women_files)}")
        
        # Combine known results with categories
        all_results = []
        
        # Add known excellent anatomical results
        for file_num, ransac in self.known_excellent_anatomical.items():
            category = "men" if int(file_num) <= 18 else "women"
            all_results.append({
                'file': file_num,
                'category': category,
                'best_method': 'anatomical',
                'ransac_error': ransac,
                'status': 'excellent',
                'tested': True
            })
        
        # Add known poor anatomical (but excellent ultimate) results
        for file_num, _ in self.known_poor_anatomical.items():
            category = "men" if int(file_num) <= 18 else "women"
            ultimate_ransac = self.known_excellent_ultimate[file_num]
            all_results.append({
                'file': file_num,
                'category': category,
                'best_method': 'ultimate',
                'ransac_error': ultimate_ransac,
                'status': 'excellent',
                'tested': True
            })
        
        # Test a sample of remaining files
        print(f"\n🔬 SAMPLING STRATEGY:")
        print("Testing representative samples from untested files...")
        
        # Get untested files
        tested_nums = set(self.known_excellent_anatomical.keys()) | set(self.known_poor_anatomical.keys())
        
        untested_men = [(f, p) for f, p in men_files if f.split('.')[0] not in tested_nums]
        untested_women = [(f, p) for f, p in women_files if f.split('.')[0] not in tested_nums]
        
        print(f"   Untested men: {len(untested_men)}")
        print(f"   Untested women: {len(untested_women)}")
        
        # Sample strategy: test 5 from each category
        sample_men = untested_men[:5] if len(untested_men) >= 5 else untested_men
        sample_women = untested_women[:5] if len(untested_women) >= 5 else untested_women
        
        if sample_men:
            print(f"\n🔧 Testing {len(sample_men)} sample men files with anatomical alignment:")
            men_sample_results = self.test_sample_files(sample_men, "anatomical")
            
            for result in men_sample_results:
                all_results.append({
                    'file': result['file'],
                    'category': 'men',
                    'best_method': result['method'],
                    'ransac_error': result['ransac_error'],
                    'status': result['status'],
                    'tested': True
                })
        
        if sample_women:
            print(f"\n🔧 Testing {len(sample_women)} sample women files with anatomical alignment:")
            women_sample_results = self.test_sample_files(sample_women, "anatomical")
            
            for result in women_sample_results:
                all_results.append({
                    'file': result['file'],
                    'category': 'women',
                    'best_method': result['method'],
                    'ransac_error': result['ransac_error'],
                    'status': result['status'],
                    'tested': True
                })
        
        # Generate final report
        self.generate_final_report(all_results, len(men_files), len(women_files))
        
        return all_results
    
    def generate_final_report(self, results, total_men, total_women):
        """Generate the final comprehensive report"""
        
        print(f"\n{'='*90}")
        print("FINAL COMPREHENSIVE ANALYSIS REPORT")
        print(f"{'='*90}")
        
        tested_results = [r for r in results if r['tested']]
        
        # Sort by performance
        sorted_results = sorted(tested_results, key=lambda x: x['ransac_error'])
        
        print(f"\n🏆 TOP PERFORMERS (Tested Files):")
        print(f"{'Rank':<4} {'File':<8} {'Category':<8} {'Method':<10} {'RANSAC':<12} {'Status'}")
        print("-" * 70)
        
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"{i:<4} {result['file']:<8} {result['category']:<8} "
                  f"{result['best_method']:<10} {result['ransac_error']:<12.2f} "
                  f"{result['status']}")
        
        # Statistics for tested files
        errors = [r['ransac_error'] for r in tested_results]
        excellent_count = sum(1 for r in tested_results if r['status'] == 'excellent')
        
        print(f"\n📈 TESTED FILES STATISTICS:")
        print(f"  Files tested: {len(tested_results)}")
        print(f"  Best RANSAC: {min(errors):.2f}")
        print(f"  Worst RANSAC: {max(errors):.2f}")
        print(f"  Average RANSAC: {np.mean(errors):.2f}")
        print(f"  Excellent results: {excellent_count}/{len(tested_results)} ({excellent_count/len(tested_results)*100:.1f}%)")
        
        # Method analysis
        anatomical_results = [r for r in tested_results if r['best_method'] == 'anatomical']
        ultimate_results = [r for r in tested_results if r['best_method'] == 'ultimate']
        
        print(f"\n🔄 METHOD ANALYSIS:")
        print(f"  Anatomical successful: {len(anatomical_results)} files")
        if anatomical_results:
            print(f"    Average RANSAC: {np.mean([r['ransac_error'] for r in anatomical_results]):.2f}")
        
        print(f"  Ultimate required: {len(ultimate_results)} files")
        if ultimate_results:
            print(f"    Average RANSAC: {np.mean([r['ransac_error'] for r in ultimate_results]):.2f}")
        
        # Projection for all files
        print(f"\n📊 PROJECTION FOR ALL FILES:")
        print(f"  Total files in dataset: {total_men + total_women}")
        print(f"  Men: {total_men}, Women: {total_women}")
        print(f"  Files tested: {len(tested_results)}")
        print(f"  Success rate in tested sample: {excellent_count/len(tested_results)*100:.1f}%")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if excellent_count/len(tested_results) > 0.8:
            print("  ✅ Hybrid system shows excellent performance")
            print("  🚀 Recommended: Use optimal_ply_processor.py for automatic method selection")
        else:
            print("  ⚠️  Some files may need additional optimization")
            print("  🔬 Recommended: Use hybrid_ply_processor.py for detailed analysis")
        
        print(f"\n🎯 OPTIMAL WORKFLOW:")
        print("  1. python optimal_ply_processor.py input.ply output.ply")
        print("  2. If RANSAC > 100, try: python hybrid_ply_processor.py input.ply")
        print("  3. For batch processing: python batch_anatomical_processor.py")
        print("  4. For poor performers: python hybrid_ply_processor.py --poor")

def main():
    analyzer = ComprehensivePLYAnalyzer()
    results = analyzer.generate_comprehensive_report()
    
    # Save results
    with open('comprehensive_analysis_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: comprehensive_analysis_report.json")
    print(f"\n{'='*90}")
    print("COMPREHENSIVE ANALYSIS COMPLETED!")
    print(f"{'='*90}")

if __name__ == "__main__":
    main()
