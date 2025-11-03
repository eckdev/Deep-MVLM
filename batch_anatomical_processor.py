#!/usr/bin/env python3
"""
Batch Anatomical PLY Processor
Processes multiple PLY files with anatomical alignment and runs predictions
"""

import os
import sys
import subprocess
import json
import numpy as np
import re
from anatomical_aligner import AnatomicalAligner

class BatchAnatomicalProcessor:
    def __init__(self):
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.config_path = "configs/DTU3D-anatomical.json"
        self.anatomical_aligner = AnatomicalAligner()
        self.output_dir = "batch_anatomical_processed"
        self.results = []
        
    def setup_output_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Created output directory: {self.output_dir}")
        else:
            print(f"📁 Using existing output directory: {self.output_dir}")
    
    def get_available_ply_files(self, max_men=None, max_women=None):
        """Get available PLY files from men and women directories"""
        men_dir = "assets/files/class1/men"
        women_dir = "assets/files/class1/women"
        
        men_files = []
        women_files = []
        
        # Get men files
        if os.path.exists(men_dir):
            all_men = [f for f in os.listdir(men_dir) if f.endswith('.ply')]
            all_men.sort(key=lambda x: int(x.split('.')[0]))  # Sort numerically
            if max_men is None:
                men_files = [os.path.join(men_dir, f) for f in all_men]
            else:
                men_files = [os.path.join(men_dir, f) for f in all_men[:max_men]]
        
        # Get women files
        if os.path.exists(women_dir):
            all_women = [f for f in os.listdir(women_dir) if f.endswith('.ply')]
            all_women.sort(key=lambda x: int(x.split('.')[0]))  # Sort numerically
            if max_women is None:
                women_files = [os.path.join(women_dir, f) for f in all_women]
            else:
                women_files = [os.path.join(women_dir, f) for f in all_women[:max_women]]
        
        return men_files, women_files
    
    def anatomical_align_single_file(self, input_file, output_file):
        """Apply anatomical alignment to a single PLY file"""
        try:
            result = self.anatomical_aligner.apply_anatomical_alignment(input_file, output_file)
            return {
                'success': True,
                'transform_params': result["transform_params"],
                'scale_factor': result["transform_params"]["scale_factor"],
                'final_center': result["final_center"],
                'anatomy_guess': result["transform_params"]["anatomy_guess"]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_prediction(self, anatomical_file):
        """Run prediction on anatomically aligned PLY file"""
        cmd = [self.python_path, "predict.py", "--c", self.config_path, "--n", anatomical_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = result.stderr + result.stdout
            
            # Extract RANSAC error
            ransac_pattern = r"Ransac average error\s+([\d.]+)"
            match = re.search(ransac_pattern, output)
            
            if match:
                ransac_error = float(match.group(1))
                return {
                    'success': True,
                    'ransac_error': ransac_error,
                    'output': output
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not extract RANSAC error',
                    'output': output[:500]
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Prediction timeout',
                'output': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': ''
            }
    
    def process_batch(self, input_files):
        """Process multiple PLY files with anatomical alignment and prediction"""
        print(f"\n{'='*80}")
        print("BATCH ANATOMICAL PROCESSING & PREDICTION")
        print(f"{'='*80}")
        print(f"Processing {len(input_files)} PLY files...")
        print(f"Output directory: {self.output_dir}")
        print(f"Config: {self.config_path}")
        print("=" * 80)
        
        batch_results = []
        
        for i, input_file in enumerate(input_files, 1):
            if not os.path.exists(input_file):
                print(f"❌ [{i}/{len(input_files)}] File not found: {input_file}")
                continue
            
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            anatomical_file = os.path.join(self.output_dir, f"anatomical_{base_name}.ply")
            
            print(f"\n[{i}/{len(input_files)}] Processing: {os.path.basename(input_file)}")
            print("-" * 60)
            
            # Step 1: Anatomical alignment
            print("🔧 Step 1: Applying anatomical alignment...")
            alignment_result = self.anatomical_align_single_file(input_file, anatomical_file)
            
            if not alignment_result['success']:
                print(f"❌ Anatomical alignment failed: {alignment_result['error']}")
                continue
            
            print(f"✅ Anatomically aligned:")
            print(f"   Transform: {alignment_result['anatomy_guess']}")
            print(f"   Scale factor: {alignment_result['scale_factor']:.3f}")
            print(f"   Final center: {alignment_result['final_center']}")
            
            # Step 2: Prediction
            print("🎯 Step 2: Running prediction...")
            prediction_result = self.run_prediction(anatomical_file)
            
            if prediction_result['success']:
                ransac_error = prediction_result['ransac_error']
                
                # Performance assessment
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
                    performance = "⚠️ NEEDS IMPROVEMENT"
                    status = "poor"
                
                print(f"✅ Prediction completed:")
                print(f"   RANSAC Error: {ransac_error:.2f}")
                print(f"   Performance: {performance}")
                
                batch_results.append({
                    'file': base_name,
                    'input_path': input_file,
                    'anatomical_path': anatomical_file,
                    'category': 'men' if '/men/' in input_file else 'women',
                    'alignment_result': alignment_result,
                    'ransac_error': ransac_error,
                    'performance': performance,
                    'status': status
                })
            else:
                print(f"❌ Prediction failed: {prediction_result['error']}")
                if prediction_result['output']:
                    print(f"   Output preview: {prediction_result['output'][:150]}...")
        
        return batch_results
    
    def generate_comprehensive_report(self, results):
        """Generate detailed analysis report"""
        if not results:
            print("\n❌ No results to report")
            return
        
        print(f"\n{'='*90}")
        print("COMPREHENSIVE BATCH PROCESSING REPORT")
        print(f"{'='*90}")
        
        # Sort by performance
        sorted_results = sorted(results, key=lambda x: x['ransac_error'])
        
        print(f"\n📊 PERFORMANCE RANKING:")
        print(f"{'Rank':<4} {'File':<12} {'Category':<6} {'RANSAC':<10} {'Transform':<10} {'Scale':<7} {'Performance'}")
        print("-" * 90)
        
        for i, result in enumerate(sorted_results, 1):
            alignment = result['alignment_result']
            print(f"{i:<4} {result['file']:<12} {result['category']:<6} "
                  f"{result['ransac_error']:<10.2f} {alignment['anatomy_guess']:<10} "
                  f"{alignment['scale_factor']:<7.3f} {result['performance']}")
        
        # Statistics
        errors = [r['ransac_error'] for r in results]
        scales = [r['alignment_result']['scale_factor'] for r in results]
        
        print(f"\n📈 OVERALL STATISTICS:")
        print(f"  Total files processed: {len(results)}")
        print(f"  Best RANSAC error: {min(errors):.2f}")
        print(f"  Worst RANSAC error: {max(errors):.2f}")
        print(f"  Average RANSAC error: {np.mean(errors):.2f}")
        print(f"  Median RANSAC error: {np.median(errors):.2f}")
        print(f"  Standard deviation: {np.std(errors):.2f}")
        print(f"  Average scale factor: {np.mean(scales):.3f}")
        print(f"  Scale range: {min(scales):.3f} - {max(scales):.3f}")
        
        # Performance breakdown
        excellent = sum(1 for r in results if r['status'] == 'excellent')
        very_good = sum(1 for r in results if r['status'] == 'very_good')
        good = sum(1 for r in results if r['status'] == 'good')
        poor = sum(1 for r in results if r['status'] == 'poor')
        
        print(f"\n🎯 PERFORMANCE BREAKDOWN:")
        print(f"  🔥 Excellent (< 10): {excellent}/{len(results)} ({excellent/len(results)*100:.1f}%)")
        print(f"  🎉 Very Good (< 100): {very_good}/{len(results)} ({very_good/len(results)*100:.1f}%)")
        print(f"  ✅ Good (< 10000): {good}/{len(results)} ({good/len(results)*100:.1f}%)")
        print(f"  ⚠️ Poor (≥ 10000): {poor}/{len(results)} ({poor/len(results)*100:.1f}%)")
        
        # Gender analysis
        men_results = [r for r in results if r['category'] == 'men']
        women_results = [r for r in results if r['category'] == 'women']
        
        if men_results and women_results:
            men_errors = [r['ransac_error'] for r in men_results]
            women_errors = [r['ransac_error'] for r in women_results]
            
            print(f"\n👥 GENDER ANALYSIS:")
            print(f"  Men ({len(men_results)} files):")
            print(f"    Average RANSAC: {np.mean(men_errors):.2f}")
            print(f"    Best: {min(men_errors):.2f}")
            print(f"    Worst: {max(men_errors):.2f}")
            print(f"  Women ({len(women_results)} files):")
            print(f"    Average RANSAC: {np.mean(women_errors):.2f}")
            print(f"    Best: {min(women_errors):.2f}")
            print(f"    Worst: {max(women_errors):.2f}")
        
        # Transform analysis
        transform_stats = {}
        for result in results:
            transform = result['alignment_result']['anatomy_guess']
            if transform not in transform_stats:
                transform_stats[transform] = []
            transform_stats[transform].append(result['ransac_error'])
        
        print(f"\n🔄 TRANSFORM TYPE ANALYSIS:")
        for transform, errors in transform_stats.items():
            avg_error = np.mean(errors)
            print(f"  {transform}: {len(errors)} files, avg RANSAC: {avg_error:.2f}")
        
        # Top performers
        top_5 = sorted_results[:min(5, len(sorted_results))]
        print(f"\n🏆 TOP 5 PERFORMERS:")
        for i, result in enumerate(top_5, 1):
            print(f"  {i}. {result['file']}.ply ({result['category']}) - RANSAC: {result['ransac_error']:.2f}")
        
        # File listing
        print(f"\n📁 GENERATED FILES:")
        for result in sorted_results:
            print(f"  {os.path.basename(result['anatomical_path'])} -> RANSAC: {result['ransac_error']:.2f}")
    
    def save_results_json(self, results, filename="batch_results.json"):
        """Save results to JSON file for further analysis"""
        json_results = []
        for result in results:
            json_result = {
                'file': result['file'],
                'category': result['category'],
                'ransac_error': result['ransac_error'],
                'performance': result['performance'],
                'status': result['status'],
                'scale_factor': result['alignment_result']['scale_factor'],
                'anatomy_guess': result['alignment_result']['anatomy_guess'],
                'final_center': result['alignment_result']['final_center'].tolist() if hasattr(result['alignment_result']['final_center'], 'tolist') else result['alignment_result']['final_center']
            }
            json_results.append(json_result)
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")

def main():
    processor = BatchAnatomicalProcessor()
    
    # Setup
    processor.setup_output_directory()
    
    # Get available files - process ALL files
    men_files, women_files = processor.get_available_ply_files()  # No limits = process all
    all_files = men_files + women_files
    
    if not all_files:
        print("❌ No PLY files found to process!")
        return
    
    print(f"\n📋 Found files to process:")
    print(f"   Men: {len(men_files)} files")
    print(f"   Women: {len(women_files)} files")
    print(f"   Total: {len(all_files)} files")
    
    # Process batch
    results = processor.process_batch(all_files)
    
    if results:
        # Generate comprehensive report
        processor.generate_comprehensive_report(results)
        
        # Save results
        processor.save_results_json(results)
        
        print(f"\n{'='*90}")
        print("BATCH PROCESSING COMPLETED SUCCESSFULLY!")
        print(f"Processed: {len(results)} files")
        print(f"Output directory: {processor.output_dir}")
        print(f"{'='*90}")
    else:
        print("\n❌ No files were successfully processed!")

if __name__ == "__main__":
    main()
