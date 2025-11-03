#!/usr/bin/env python3
"""
Comprehensive PLY Test Suite - No Visualization
Tests all PLY files in assets/files/class4 without visualization windows
Provides detailed hybrid analysis and recommendations
"""

import os
import sys
import subprocess
import json
import numpy as np
import re
from datetime import datetime
from anatomical_aligner import AnatomicalAligner

class ComprehensivePLYTestSuite:
    def __init__(self):
        self.python_path = "/Users/eck/Documents/Projects/Face-Landmark/Deep-MVLM/env/bin/python"
        self.anatomical_config = "configs/DTU3D-anatomical.json"
        self.ultimate_config = "configs/DTU3D-PLY-ultimate-final.json"
        self.anatomical_aligner = AnatomicalAligner()
        self.output_dir = "comprehensive_test_results"
        self.results = []
        
        # Performance thresholds
        self.excellent_threshold = 10.0
        self.good_threshold = 100.0
        self.poor_threshold = 10000.0
        
    def setup_output_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Created output directory: {self.output_dir}")
        else:
            print(f"📁 Using existing output directory: {self.output_dir}")
    
    def get_all_ply_files(self):
        """Get all PLY files from men and women directories"""
        men_dir = "assets/files/class4/men"
        women_dir = "assets/files/class4/women"
        
        all_files = []
        
        # Get men files
        if os.path.exists(men_dir):
            men_ply = [f for f in os.listdir(men_dir) if f.endswith('.ply')]
            men_ply.sort(key=lambda x: int(x.split('.')[0]))
            for ply_file in men_ply:
                all_files.append({
                    'filename': ply_file,
                    'filepath': os.path.join(men_dir, ply_file),
                    'category': 'men',
                    'file_number': int(ply_file.split('.')[0])
                })
        
        # Get women files
        if os.path.exists(women_dir):
            women_ply = [f for f in os.listdir(women_dir) if f.endswith('.ply')]
            women_ply.sort(key=lambda x: int(x.split('.')[0]))
            for ply_file in women_ply:
                all_files.append({
                    'filename': ply_file,
                    'filepath': os.path.join(women_dir, ply_file),
                    'category': 'women',
                    'file_number': int(ply_file.split('.')[0])
                })
        
        # Sort by file number
        all_files.sort(key=lambda x: x['file_number'])
        return all_files
    
    def test_anatomical_method(self, file_info):
        """Test anatomical alignment method"""
        base_name = os.path.splitext(file_info['filename'])[0]
        temp_file = os.path.join(self.output_dir, f"temp_anatomical_{base_name}.ply")
        
        try:
            # Apply anatomical alignment
            result = self.anatomical_aligner.apply_anatomical_alignment(
                file_info['filepath'], temp_file
            )
            
            # Run prediction
            cmd = [self.python_path, "predict.py", "--c", self.anatomical_config, "--n", temp_file]
            pred_result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = pred_result.stderr + pred_result.stdout
            
            # Extract RANSAC error
            ransac_pattern = r"Ransac average error\s+([\d.]+)"
            match = re.search(ransac_pattern, output)
            
            if match:
                ransac_error = float(match.group(1))
                
                # Cleanup temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
                return {
                    'success': True,
                    'ransac_error': ransac_error,
                    'scale_factor': result["transform_params"]["scale_factor"],
                    'anatomy_guess': result["transform_params"]["anatomy_guess"]
                }
            else:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return {'success': False, 'error': 'Could not extract RANSAC'}
                
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return {'success': False, 'error': str(e)}
    
    def test_ultimate_method(self, file_info):
        """Test ultimate preprocessing method"""
        base_name = os.path.splitext(file_info['filename'])[0]
        temp_file = os.path.join(self.output_dir, f"temp_ultimate_{base_name}.ply")
        
        try:
            # Apply ultimate preprocessing
            from ultimate_ply_preprocessor import align_ply_to_obj_system
            align_ply_to_obj_system(file_info['filepath'], temp_file)
            
            # Run prediction
            cmd = [self.python_path, "predict.py", "--c", self.ultimate_config, "--n", temp_file]
            pred_result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = pred_result.stderr + pred_result.stdout
            
            # Extract RANSAC error
            ransac_pattern = r"Ransac average error\s+([\d.]+)"
            match = re.search(ransac_pattern, output)
            
            if match:
                ransac_error = float(match.group(1))
                
                # Cleanup temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
                return {
                    'success': True,
                    'ransac_error': ransac_error
                }
            else:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return {'success': False, 'error': 'Could not extract RANSAC'}
                
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return {'success': False, 'error': str(e)}
    
    def classify_performance(self, ransac_error):
        """Classify performance based on RANSAC error"""
        if ransac_error < self.excellent_threshold:
            return "🔥 EXCELLENT", "excellent"
        elif ransac_error < self.good_threshold:
            return "🎉 VERY GOOD", "very_good"
        elif ransac_error < self.poor_threshold:
            return "✅ GOOD", "good"
        else:
            return "⚠️ POOR", "poor"
    
    def test_single_file_hybrid(self, file_info):
        """Test single file with both methods and determine best approach"""
        
        print(f"\n{'='*80}")
        print(f"Testing: {file_info['filename']} ({file_info['category'].upper()})")
        print(f"{'='*80}")
        
        result = {
            'file': file_info['filename'],
            'file_number': file_info['file_number'],
            'category': file_info['category'],
            'anatomical_result': None,
            'ultimate_result': None,
            'best_method': None,
            'best_ransac': None,
            'best_performance': None,
            'needs_optimization': False,
            'recommendation': None
        }
        
        # Test anatomical method first
        print("🔧 Testing ANATOMICAL alignment...")
        anatomical_result = self.test_anatomical_method(file_info)
        
        if anatomical_result['success']:
            ransac = anatomical_result['ransac_error']
            performance, status = self.classify_performance(ransac)
            
            result['anatomical_result'] = {
                'ransac_error': ransac,
                'performance': performance,
                'status': status,
                'scale_factor': anatomical_result.get('scale_factor'),
                'anatomy_guess': anatomical_result.get('anatomy_guess')
            }
            
            print(f"   ✅ RANSAC: {ransac:.2f} ({performance})")
            
            # If anatomical is excellent, no need to test ultimate
            if status == 'excellent':
                result['best_method'] = 'anatomical'
                result['best_ransac'] = ransac
                result['best_performance'] = performance
                result['recommendation'] = "Use anatomical alignment - excellent results"
                return result
        else:
            print(f"   ❌ Anatomical failed: {anatomical_result['error']}")
        
        # Test ultimate method
        print("🔧 Testing ULTIMATE preprocessing...")
        ultimate_result = self.test_ultimate_method(file_info)
        
        if ultimate_result['success']:
            ransac = ultimate_result['ransac_error']
            performance, status = self.classify_performance(ransac)
            
            result['ultimate_result'] = {
                'ransac_error': ransac,
                'performance': performance,
                'status': status
            }
            
            print(f"   ✅ RANSAC: {ransac:.2f} ({performance})")
        else:
            print(f"   ❌ Ultimate failed: {ultimate_result['error']}")
        
        # Determine best method
        if result['anatomical_result'] and result['ultimate_result']:
            anat_ransac = result['anatomical_result']['ransac_error']
            ult_ransac = result['ultimate_result']['ransac_error']
            
            if anat_ransac <= ult_ransac:
                result['best_method'] = 'anatomical'
                result['best_ransac'] = anat_ransac
                result['best_performance'] = result['anatomical_result']['performance']
                improvement = ult_ransac / anat_ransac if anat_ransac > 0 else 1
                result['recommendation'] = f"Use anatomical alignment (RANSAC: {anat_ransac:.2f})"
            else:
                result['best_method'] = 'ultimate'
                result['best_ransac'] = ult_ransac
                result['best_performance'] = result['ultimate_result']['performance']
                improvement = anat_ransac / ult_ransac if ult_ransac > 0 else 1
                result['recommendation'] = f"Use ultimate preprocessing (RANSAC: {ult_ransac:.2f}, {improvement:.1f}x better)"
        
        elif result['anatomical_result']:
            result['best_method'] = 'anatomical'
            result['best_ransac'] = result['anatomical_result']['ransac_error']
            result['best_performance'] = result['anatomical_result']['performance']
            result['recommendation'] = "Use anatomical alignment - ultimate failed"
        
        elif result['ultimate_result']:
            result['best_method'] = 'ultimate'
            result['best_ransac'] = result['ultimate_result']['ransac_error']
            result['best_performance'] = result['ultimate_result']['performance']
            result['recommendation'] = "Use ultimate preprocessing - anatomical failed"
        
        else:
            result['recommendation'] = "❌ Both methods failed - needs manual investigation"
            result['needs_optimization'] = True
        
        # Check if needs optimization
        if result['best_ransac'] and result['best_ransac'] > self.good_threshold:
            result['needs_optimization'] = True
        
        print(f"🎯 RESULT: {result['recommendation']}")
        
        return result
    
    def run_comprehensive_test(self):
        """Run comprehensive test on all PLY files"""
        
        print(f"\n{'='*100}")
        print("COMPREHENSIVE PLY TEST SUITE - NO VISUALIZATION")
        print(f"{'='*100}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Setup
        self.setup_output_directory()
        
        # Get all files
        all_files = self.get_all_ply_files()
        
        if not all_files:
            print("❌ No PLY files found!")
            return
        
        print(f"\n📊 DATASET OVERVIEW:")
        men_count = sum(1 for f in all_files if f['category'] == 'men')
        women_count = sum(1 for f in all_files if f['category'] == 'women')
        print(f"   Total files: {len(all_files)}")
        print(f"   Men: {men_count} files")
        print(f"   Women: {women_count} files")
        
        # Test all files
        all_results = []
        
        for i, file_info in enumerate(all_files, 1):
            print(f"\n[{i}/{len(all_files)}] Processing {file_info['filename']}...")
            result = self.test_single_file_hybrid(file_info)
            all_results.append(result)
        
        # Generate comprehensive report
        self.generate_final_report(all_results)
        
        # Save results
        self.save_results(all_results)
        
        return all_results
    
    def generate_final_report(self, results):
        """Generate comprehensive final report"""
        
        print(f"\n{'='*100}")
        print("FINAL COMPREHENSIVE TEST REPORT")
        print(f"{'='*100}")
        
        # Filter successful results
        successful_results = [r for r in results if r['best_ransac'] is not None]
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total files tested: {len(results)}")
        print(f"   Successful tests: {len(successful_results)}")
        print(f"   Success rate: {len(successful_results)/len(results)*100:.1f}%")
        
        if not successful_results:
            print("❌ No successful results to analyze!")
            return
        
        # Performance statistics
        ransac_errors = [r['best_ransac'] for r in successful_results]
        
        print(f"\n📈 PERFORMANCE STATISTICS:")
        print(f"   Best RANSAC: {min(ransac_errors):.2f}")
        print(f"   Worst RANSAC: {max(ransac_errors):.2f}")
        print(f"   Average RANSAC: {np.mean(ransac_errors):.2f}")
        print(f"   Median RANSAC: {np.median(ransac_errors):.2f}")
        
        # Performance classification
        excellent = [r for r in successful_results if r['best_ransac'] < self.excellent_threshold]
        very_good = [r for r in successful_results if self.excellent_threshold <= r['best_ransac'] < self.good_threshold]
        good = [r for r in successful_results if self.good_threshold <= r['best_ransac'] < self.poor_threshold]
        poor = [r for r in successful_results if r['best_ransac'] >= self.poor_threshold]
        
        print(f"\n🎯 PERFORMANCE BREAKDOWN:")
        print(f"   🔥 Excellent (<{self.excellent_threshold}): {len(excellent)} files ({len(excellent)/len(successful_results)*100:.1f}%)")
        print(f"   🎉 Very Good (<{self.good_threshold}): {len(very_good)} files ({len(very_good)/len(successful_results)*100:.1f}%)")
        print(f"   ✅ Good (<{self.poor_threshold}): {len(good)} files ({len(good)/len(successful_results)*100:.1f}%)")
        print(f"   ⚠️ Poor (≥{self.poor_threshold}): {len(poor)} files ({len(poor)/len(successful_results)*100:.1f}%)")
        
        # Method analysis
        anatomical_best = [r for r in successful_results if r['best_method'] == 'anatomical']
        ultimate_best = [r for r in successful_results if r['best_method'] == 'ultimate']
        
        print(f"\n🔄 METHOD ANALYSIS:")
        print(f"   Anatomical best: {len(anatomical_best)} files ({len(anatomical_best)/len(successful_results)*100:.1f}%)")
        print(f"   Ultimate best: {len(ultimate_best)} files ({len(ultimate_best)/len(successful_results)*100:.1f}%)")
        
        if anatomical_best:
            anat_errors = [r['best_ransac'] for r in anatomical_best]
            print(f"   Anatomical avg RANSAC: {np.mean(anat_errors):.2f}")
        
        if ultimate_best:
            ult_errors = [r['best_ransac'] for r in ultimate_best]
            print(f"   Ultimate avg RANSAC: {np.mean(ult_errors):.2f}")
        
        # Top performers
        top_performers = sorted(successful_results, key=lambda x: x['best_ransac'])[:10]
        
        print(f"\n🏆 TOP 10 PERFORMERS:")
        print(f"{'Rank':<4} {'File':<12} {'Category':<8} {'Method':<10} {'RANSAC':<12} {'Performance'}")
        print("-" * 80)
        
        for i, result in enumerate(top_performers, 1):
            print(f"{i:<4} {result['file']:<12} {result['category']:<8} "
                  f"{result['best_method']:<10} {result['best_ransac']:<12.2f} "
                  f"{result['best_performance']}")
        
        # Poor performers that need optimization
        poor_performers = [r for r in results if r['needs_optimization']]
        
        if poor_performers:
            print(f"\n⚠️ FILES NEEDING OPTIMIZATION ({len(poor_performers)} files):")
            print(f"{'File':<12} {'Category':<8} {'Best Method':<12} {'RANSAC':<12} {'Issue'}")
            print("-" * 70)
            
            for result in poor_performers:
                ransac_str = f"{result['best_ransac']:.2f}" if result['best_ransac'] else "FAILED"
                method_str = result['best_method'] if result['best_method'] else "NONE"
                issue = "High RANSAC" if result['best_ransac'] and result['best_ransac'] > self.good_threshold else "Failed"
                
                print(f"{result['file']:<12} {result['category']:<8} "
                      f"{method_str:<12} {ransac_str:<12} {issue}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        success_rate = len(excellent) / len(successful_results) * 100
        
        if success_rate >= 70:
            print("   ✅ System performance is excellent!")
            print("   🚀 Ready for production use")
        elif success_rate >= 50:
            print("   ✅ System performance is good")
            print("   🔧 Consider optimizing poor performers")
        else:
            print("   ⚠️ System needs improvement")
            print("   🔬 Focus on optimizing poor performers")
        
        if poor_performers:
            print(f"\n🛠️ OPTIMIZATION STRATEGY:")
            print(f"   1. {len(poor_performers)} files need attention")
            print("   2. Consider manual parameter tuning for poor performers")
            print("   3. Investigate file quality and coordinate systems")
        
        print(f"\n📁 OUTPUT FILES:")
        print(f"   • comprehensive_test_results.json - Detailed test results")
        print(f"   • poor_performers_list.json - Files needing optimization")
        print(f"   • test_summary_report.json - Summary statistics")
    
    def save_results(self, results):
        """Save comprehensive results to JSON files"""
        
        # Main results file
        with open('comprehensive_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Poor performers file
        poor_performers = [r for r in results if r['needs_optimization']]
        with open('poor_performers_list.json', 'w') as f:
            json.dump(poor_performers, f, indent=2, default=str)
        
        # Summary statistics
        successful_results = [r for r in results if r['best_ransac'] is not None]
        
        if successful_results:
            ransac_errors = [r['best_ransac'] for r in successful_results]
            
            summary = {
                'test_date': datetime.now().isoformat(),
                'total_files': len(results),
                'successful_tests': len(successful_results),
                'success_rate': len(successful_results) / len(results) * 100,
                'statistics': {
                    'best_ransac': min(ransac_errors),
                    'worst_ransac': max(ransac_errors),
                    'average_ransac': np.mean(ransac_errors),
                    'median_ransac': np.median(ransac_errors)
                },
                'method_distribution': {
                    'anatomical_best': len([r for r in successful_results if r['best_method'] == 'anatomical']),
                    'ultimate_best': len([r for r in successful_results if r['best_method'] == 'ultimate'])
                },
                'performance_breakdown': {
                    'excellent': len([r for r in successful_results if r['best_ransac'] < 10]),
                    'very_good': len([r for r in successful_results if 10 <= r['best_ransac'] < 100]),
                    'good': len([r for r in successful_results if 100 <= r['best_ransac'] < 10000]),
                    'poor': len([r for r in successful_results if r['best_ransac'] >= 10000])
                },
                'poor_performers_count': len(poor_performers)
            }
            
            with open('test_summary_report.json', 'w') as f:
                json.dump(summary, f, indent=2)
        
        print(f"\n💾 Results saved:")
        print(f"   • comprehensive_test_results.json")
        print(f"   • poor_performers_list.json") 
        print(f"   • test_summary_report.json")

def main():
    test_suite = ComprehensivePLYTestSuite()
    results = test_suite.run_comprehensive_test()
    
    print(f"\n{'='*100}")
    print("COMPREHENSIVE PLY TEST SUITE COMPLETED!")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}")

if __name__ == "__main__":
    main()

