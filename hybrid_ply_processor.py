#!/usr/bin/env python3
"""
Hybrid PLY Preprocessor
Combines anatomical and ultimate preprocessing approaches to achieve optimal results
"""

import os
import sys
import subprocess
import json
import re
import numpy as np
from anatomical_aligner import AnatomicalAligner
from ultimate_ply_preprocessor import align_ply_to_obj_system

class HybridPLYProcessor:
    def __init__(self):
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.anatomical_config = "configs/DTU3D-anatomical.json"
        self.ultimate_config = "configs/DTU3D-PLY-ultimate-final.json"
        self.anatomical_aligner = AnatomicalAligner()
        self.threshold_ransac = 100  # If anatomical RANSAC > threshold, try ultimate
        
    def apply_anatomical_alignment(self, input_file, output_file):
        """Apply anatomical alignment"""
        try:
            result = self.anatomical_aligner.apply_anatomical_alignment(input_file, output_file)
            return {
                'success': True,
                'method': 'anatomical',
                'transform_params': result["transform_params"],
                'scale_factor': result["transform_params"]["scale_factor"],
                'final_center': result["final_center"],
                'anatomy_guess': result["transform_params"]["anatomy_guess"]
            }
        except Exception as e:
            return {
                'success': False,
                'method': 'anatomical',
                'error': str(e)
            }
    
    def apply_ultimate_alignment(self, input_file, output_file):
        """Apply ultimate (OBJ-based) alignment"""
        try:
            align_ply_to_obj_system(input_file, output_file)
            return {
                'success': True,
                'method': 'ultimate',
                'obj_reference': 'assets/testmeshA.obj'
            }
        except Exception as e:
            return {
                'success': False,
                'method': 'ultimate',
                'error': str(e)
            }
    
    def run_prediction(self, aligned_file, config_path):
        """Run prediction and extract RANSAC error"""
        cmd = [self.python_path, "predict.py", "--c", config_path, "--n", aligned_file]
        
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
                'error': 'Prediction timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_single_file_hybrid(self, input_file, force_method=None):
        """
        Process single file with hybrid approach
        force_method: 'anatomical', 'ultimate', or None for automatic selection
        """
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        print(f"\n{'='*80}")
        print(f"HYBRID PROCESSING: {os.path.basename(input_file)}")
        print(f"{'='*80}")
        
        results = {}
        
        if force_method == 'ultimate':
            # Force ultimate method only
            methods_to_try = ['ultimate']
        elif force_method == 'anatomical':
            # Force anatomical method only
            methods_to_try = ['anatomical']
        else:
            # Try both methods and compare
            methods_to_try = ['anatomical', 'ultimate']
        
        for method in methods_to_try:
            print(f"\n🔧 Testing {method.upper()} alignment...")
            
            if method == 'anatomical':
                aligned_file = f"temp_anatomical_{base_name}.ply"
                config_path = self.anatomical_config
                alignment_result = self.apply_anatomical_alignment(input_file, aligned_file)
            else:  # ultimate
                aligned_file = f"temp_ultimate_{base_name}.ply"
                config_path = self.ultimate_config
                alignment_result = self.apply_ultimate_alignment(input_file, aligned_file)
            
            if not alignment_result['success']:
                print(f"❌ {method.upper()} alignment failed: {alignment_result['error']}")
                continue
            
            print(f"✅ {method.upper()} alignment completed")
            if method == 'anatomical':
                print(f"   Transform: {alignment_result['anatomy_guess']}")
                print(f"   Scale factor: {alignment_result['scale_factor']:.3f}")
            
            # Run prediction
            print(f"🎯 Running prediction with {method} config...")
            prediction_result = self.run_prediction(aligned_file, config_path)
            
            # Clean up temporary file
            if os.path.exists(aligned_file):
                os.remove(aligned_file)
            
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
                
                print(f"✅ RANSAC Error: {ransac_error:.2f} ({performance})")
                
                results[method] = {
                    'alignment_result': alignment_result,
                    'ransac_error': ransac_error,
                    'performance': performance,
                    'status': status,
                    'config': config_path
                }
            else:
                print(f"❌ Prediction failed: {prediction_result['error']}")
        
        # Select best method if multiple were tested
        if len(results) > 1:
            best_method = min(results.keys(), key=lambda k: results[k]['ransac_error'])
            best_ransac = results[best_method]['ransac_error']
            
            print(f"\n🏆 COMPARISON RESULTS:")
            for method, result in results.items():
                marker = "⭐ BEST" if method == best_method else ""
                print(f"   {method.upper()}: {result['ransac_error']:.2f} {marker}")
            
            print(f"\n✨ WINNER: {best_method.upper()} (RANSAC: {best_ransac:.2f})")
            
            return {
                'file': base_name,
                'best_method': best_method,
                'best_result': results[best_method],
                'all_results': results,
                'improvement': None if len(results) == 1 else min(results.values(), key=lambda x: x['ransac_error'])['ransac_error']
            }
        elif len(results) == 1:
            method = list(results.keys())[0]
            return {
                'file': base_name,
                'best_method': method,
                'best_result': results[method],
                'all_results': results,
                'improvement': None
            }
        else:
            print("❌ No successful results")
            return None
    
    def process_poor_performers_from_batch(self, batch_results_file="batch_results.json"):
        """Process files that performed poorly with anatomical alignment"""
        
        # Load previous results
        with open(batch_results_file, 'r') as f:
            batch_results = json.load(f)
        
        poor_files = [r for r in batch_results if r['status'] == 'poor']
        
        if not poor_files:
            print("No poor performing files found in batch results!")
            return []
        
        print(f"\n{'='*90}")
        print("HYBRID PROCESSING FOR POOR PERFORMERS")
        print(f"{'='*90}")
        print(f"Found {len(poor_files)} files that performed poorly with anatomical alignment")
        print("Testing ultimate preprocessing for these files...")
        
        hybrid_results = []
        
        for i, poor_result in enumerate(poor_files, 1):
            filename = poor_result['file']
            category = poor_result['category']
            original_ransac = poor_result['ransac_error']
            
            # Find original file path
            if category == 'men':
                input_file = f"assets/files/class1/men/{filename}.ply"
            else:
                input_file = f"assets/files/class1/women/{filename}.ply"
            
            if not os.path.exists(input_file):
                print(f"❌ [{i}/{len(poor_files)}] File not found: {input_file}")
                continue
            
            print(f"\n[{i}/{len(poor_files)}] Processing: {filename}.ply ({category})")
            print(f"   Previous anatomical RANSAC: {original_ransac:.2f}")
            
            # Test ultimate method
            result = self.process_single_file_hybrid(input_file, force_method='ultimate')
            
            if result:
                new_ransac = result['best_result']['ransac_error']
                improvement = original_ransac - new_ransac
                improvement_pct = (improvement / original_ransac) * 100 if original_ransac > 0 else 0
                
                result['original_anatomical_ransac'] = original_ransac
                result['improvement'] = improvement
                result['improvement_percentage'] = improvement_pct
                result['category'] = category
                
                if improvement > 0:
                    print(f"🎉 IMPROVEMENT: {improvement:.2f} ({improvement_pct:.1f}% better)")
                else:
                    print(f"⚠️ NO IMPROVEMENT: {abs(improvement):.2f} worse")
                
                hybrid_results.append(result)
        
        return hybrid_results
    
    def generate_hybrid_report(self, hybrid_results):
        """Generate comprehensive hybrid processing report"""
        if not hybrid_results:
            print("\n❌ No hybrid results to report")
            return
        
        print(f"\n{'='*90}")
        print("HYBRID PROCESSING REPORT")
        print(f"{'='*90}")
        
        print(f"\n📊 HYBRID RESULTS SUMMARY:")
        print(f"{'File':<8} {'Category':<8} {'Method':<10} {'Original':<12} {'New':<12} {'Improvement':<15} {'Status'}")
        print("-" * 90)
        
        improved_count = 0
        total_improvement = 0
        
        for result in hybrid_results:
            original = result['original_anatomical_ransac']
            new = result['best_result']['ransac_error']
            improvement = result['improvement']
            improvement_pct = result['improvement_percentage']
            
            if improvement > 0:
                improved_count += 1
                total_improvement += improvement_pct
                status = f"✅ +{improvement_pct:.1f}%"
            else:
                status = f"❌ {improvement_pct:.1f}%"
            
            print(f"{result['file']:<8} {result['category']:<8} {result['best_method']:<10} "
                  f"{original:<12.2f} {new:<12.2f} {improvement:<15.2f} {status}")
        
        print(f"\n📈 IMPROVEMENT STATISTICS:")
        print(f"  Files processed: {len(hybrid_results)}")
        print(f"  Files improved: {improved_count}/{len(hybrid_results)} ({improved_count/len(hybrid_results)*100:.1f}%)")
        
        if improved_count > 0:
            avg_improvement = total_improvement / improved_count
            print(f"  Average improvement: {avg_improvement:.1f}%")
        
        # Best improvements
        sorted_by_improvement = sorted(hybrid_results, key=lambda x: x['improvement'], reverse=True)
        best_improvements = [r for r in sorted_by_improvement if r['improvement'] > 0][:3]
        
        if best_improvements:
            print(f"\n🏆 TOP IMPROVEMENTS:")
            for i, result in enumerate(best_improvements, 1):
                improvement_pct = result['improvement_percentage']
                print(f"  {i}. {result['file']}.ply: {improvement_pct:.1f}% improvement")
    
    def save_hybrid_results(self, hybrid_results, filename="hybrid_results.json"):
        """Save hybrid results to JSON"""
        json_results = []
        for result in hybrid_results:
            json_result = {
                'file': result['file'],
                'category': result['category'],
                'best_method': result['best_method'],
                'new_ransac_error': result['best_result']['ransac_error'],
                'original_anatomical_ransac': result['original_anatomical_ransac'],
                'improvement': result['improvement'],
                'improvement_percentage': result['improvement_percentage'],
                'performance': result['best_result']['performance'],
                'status': result['best_result']['status']
            }
            json_results.append(json_result)
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)
        print(f"\n💾 Hybrid results saved to: {filename}")

def main():
    processor = HybridPLYProcessor()
    
    if len(sys.argv) == 3:
        # Single file processing
        input_file = sys.argv[1]
        method = sys.argv[2] if sys.argv[2] in ['anatomical', 'ultimate'] else None
        
        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return
        
        result = processor.process_single_file_hybrid(input_file, force_method=method)
        if result:
            print(f"\n✅ Best method for {result['file']}: {result['best_method'].upper()}")
            print(f"   RANSAC Error: {result['best_result']['ransac_error']:.2f}")
    
    elif len(sys.argv) == 2 and sys.argv[1] == "--poor":
        # Process poor performers from batch results
        hybrid_results = processor.process_poor_performers_from_batch()
        
        if hybrid_results:
            processor.generate_hybrid_report(hybrid_results)
            processor.save_hybrid_results(hybrid_results)
    
    else:
        print("Hybrid PLY Preprocessor Usage:")
        print("  python hybrid_ply_processor.py input.ply [anatomical|ultimate]  # Test single file")
        print("  python hybrid_ply_processor.py --poor                           # Process poor performers from batch")
        print("  python hybrid_ply_processor.py                                  # Show this help")

if __name__ == "__main__":
    main()
