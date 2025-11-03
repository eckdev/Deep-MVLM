#!/usr/bin/env python3
"""
Poor Performance Analyzer
Analyzes which files performed poorly in both anatomical and ultimate methods
"""

import json
import os

def analyze_poor_performers():
    """Analyze comprehensive test results to find files poor in both methods"""
    
    if not os.path.exists('comprehensive_test_results.json'):
        print("❌ comprehensive_test_results.json not found!")
        return
    
    with open('comprehensive_test_results.json', 'r') as f:
        results = json.load(f)
    
    print(f"\n{'='*80}")
    print("POOR PERFORMANCE ANALYSIS")
    print(f"{'='*80}")
    
    # Define thresholds
    poor_threshold = 10000  # RANSAC error >= 10000 is considered poor
    
    # Categorize results
    both_tested = []
    both_poor = []
    anatomical_poor_ultimate_good = []
    anatomical_good_ultimate_poor = []
    anatomical_only = []
    ultimate_only = []
    
    for result in results:
        file_name = result['file']
        anat_result = result.get('anatomical_result')
        ult_result = result.get('ultimate_result')
        
        has_anatomical = anat_result is not None
        has_ultimate = ult_result is not None
        
        if has_anatomical and has_ultimate:
            both_tested.append(result)
            
            anat_ransac = anat_result['ransac_error']
            ult_ransac = ult_result['ransac_error']
            
            anat_poor = anat_ransac >= poor_threshold
            ult_poor = ult_ransac >= poor_threshold
            
            if anat_poor and ult_poor:
                both_poor.append({
                    'file': file_name,
                    'category': result['category'],
                    'anatomical_ransac': anat_ransac,
                    'ultimate_ransac': ult_ransac
                })
            elif anat_poor and not ult_poor:
                anatomical_poor_ultimate_good.append({
                    'file': file_name,
                    'category': result['category'],
                    'anatomical_ransac': anat_ransac,
                    'ultimate_ransac': ult_ransac
                })
            elif not anat_poor and ult_poor:
                anatomical_good_ultimate_poor.append({
                    'file': file_name,
                    'category': result['category'],
                    'anatomical_ransac': anat_ransac,
                    'ultimate_ransac': ult_ransac
                })
        
        elif has_anatomical and not has_ultimate:
            anatomical_only.append(result)
        elif not has_anatomical and has_ultimate:
            ultimate_only.append(result)
    
    print(f"\n📊 TESTING COVERAGE:")
    print(f"   Files tested with both methods: {len(both_tested)}")
    print(f"   Files tested with anatomical only: {len(anatomical_only)}")
    print(f"   Files tested with ultimate only: {len(ultimate_only)}")
    print(f"   Total files: {len(results)}")
    
    print(f"\n⚠️ POOR PERFORMERS (RANSAC ≥ {poor_threshold:,}):")
    
    if both_poor:
        print(f"\n🔴 FILES POOR IN BOTH METHODS ({len(both_poor)} files):")
        print(f"{'File':<12} {'Category':<8} {'Anatomical RANSAC':<18} {'Ultimate RANSAC':<16}")
        print("-" * 70)
        
        for item in both_poor:
            print(f"{item['file']:<12} {item['category']:<8} "
                  f"{item['anatomical_ransac']:<18,.0f} {item['ultimate_ransac']:<16,.0f}")
        
        print(f"\n⚠️ CRITICAL: These {len(both_poor)} files need urgent investigation!")
        print("Both preprocessing methods failed to achieve good results.")
        
    else:
        print(f"\n✅ NO FILES POOR IN BOTH METHODS!")
        print("Hybrid system provides successful fallback for all files.")
    
    if anatomical_poor_ultimate_good:
        print(f"\n🟡 ANATOMICAL POOR, ULTIMATE GOOD ({len(anatomical_poor_ultimate_good)} files):")
        print(f"{'File':<12} {'Category':<8} {'Anatomical':<12} {'Ultimate':<12} {'Improvement'}")
        print("-" * 70)
        
        for item in anatomical_poor_ultimate_good:
            improvement = item['anatomical_ransac'] / item['ultimate_ransac']
            print(f"{item['file']:<12} {item['category']:<8} "
                  f"{item['anatomical_ransac']:<12,.0f} {item['ultimate_ransac']:<12.2f} "
                  f"{improvement:.0f}x better")
    
    if anatomical_good_ultimate_poor:
        print(f"\n🟠 ANATOMICAL GOOD, ULTIMATE POOR ({len(anatomical_good_ultimate_poor)} files):")
        print(f"{'File':<12} {'Category':<8} {'Anatomical':<12} {'Ultimate':<12}")
        print("-" * 60)
        
        for item in anatomical_good_ultimate_poor:
            print(f"{item['file']:<12} {item['category']:<8} "
                  f"{item['anatomical_ransac']:<12.2f} {item['ultimate_ransac']:<12,.0f}")
    
    # Analysis by category
    print(f"\n📈 CATEGORY ANALYSIS:")
    
    if both_poor:
        men_both_poor = [x for x in both_poor if x['category'] == 'men']
        women_both_poor = [x for x in both_poor if x['category'] == 'women']
        
        print(f"   Both methods poor:")
        print(f"     Men: {len(men_both_poor)} files")
        print(f"     Women: {len(women_both_poor)} files")
    
    # Method effectiveness
    print(f"\n🔄 METHOD EFFECTIVENESS:")
    
    total_anatomical = len([r for r in results if r.get('anatomical_result')])
    total_ultimate = len([r for r in results if r.get('ultimate_result')])
    
    anatomical_poor_count = len([r for r in results if r.get('anatomical_result') and 
                                r['anatomical_result']['ransac_error'] >= poor_threshold])
    ultimate_poor_count = len([r for r in results if r.get('ultimate_result') and 
                              r['ultimate_result']['ransac_error'] >= poor_threshold])
    
    if total_anatomical > 0:
        anatomical_success_rate = (total_anatomical - anatomical_poor_count) / total_anatomical * 100
        print(f"   Anatomical success rate: {anatomical_success_rate:.1f}% ({total_anatomical - anatomical_poor_count}/{total_anatomical})")
    
    if total_ultimate > 0:
        ultimate_success_rate = (total_ultimate - ultimate_poor_count) / total_ultimate * 100
        print(f"   Ultimate success rate: {ultimate_success_rate:.1f}% ({total_ultimate - ultimate_poor_count}/{total_ultimate})")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not both_poor:
        print("   ✅ EXCELLENT: No files poor in both methods")
        print("   🎉 Hybrid system provides 100% coverage")
        print("   🚀 System ready for production deployment")
    else:
        print(f"   ⚠️ ATTENTION: {len(both_poor)} files need special handling")
        print("   🔬 Consider manual investigation of these files")
        print("   📋 Possible issues: file corruption, unusual geometry, coordinate system problems")
    
    # Save analysis results
    analysis_results = {
        'both_poor': both_poor,
        'anatomical_poor_ultimate_good': anatomical_poor_ultimate_good,
        'anatomical_good_ultimate_poor': anatomical_good_ultimate_poor,
        'summary': {
            'total_files': len(results),
            'both_tested': len(both_tested),
            'both_poor_count': len(both_poor),
            'anatomical_only_count': len(anatomical_only),
            'ultimate_only_count': len(ultimate_only)
        }
    }
    
    with open('poor_performance_analysis.json', 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    print(f"\n💾 Analysis saved to: poor_performance_analysis.json")
    
    return both_poor

def main():
    both_poor_files = analyze_poor_performers()
    
    print(f"\n{'='*80}")
    if both_poor_files:
        print(f"ANALYSIS COMPLETED - {len(both_poor_files)} CRITICAL FILES IDENTIFIED")
    else:
        print("ANALYSIS COMPLETED - HYBRID SYSTEM FULLY SUCCESSFUL")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
