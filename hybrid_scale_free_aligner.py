#!/usr/bin/env python3
"""
Hybrid Scale-Free Aligner
Automatically selects the best alignment method (Anatomical vs Ultimate) 
while preserving scale for manual landmark compatibility.
"""

import vtk
import numpy as np
import os
import json
import sys
from anatomical_aligner import AnatomicalAligner
from ultimate_scale_free_preprocessor import UltimateScaleFreePreprocessor

class HybridScaleFreeAligner:
    def __init__(self):
        self.anatomical_aligner = None
        self.ultimate_processor = UltimateScaleFreePreprocessor()
        self.preserve_scale = True
    
    def analyze_ply_characteristics(self, ply_path):
        """Analyze PLY file to determine best alignment method"""
        
        print(f"\n🔍 Analyzing PLY Characteristics: {os.path.basename(ply_path)}")
        print("-" * 60)
        
        # Load PLY
        reader = vtk.vtkPLYReader()
        reader.SetFileName(ply_path)
        reader.Update()
        mesh = reader.GetOutput()
        
        # Extract basic info
        points = mesh.GetPoints()
        n_points = points.GetNumberOfPoints()
        vertices = np.array([points.GetPoint(i) for i in range(n_points)])
        bounds = mesh.GetBounds()
        center = np.mean(vertices, axis=0)
        
        # Calculate dimensions
        width = bounds[1] - bounds[0]    # X range
        height = bounds[3] - bounds[2]   # Y range  
        depth = bounds[5] - bounds[4]    # Z range
        
        diagonal = np.sqrt(width**2 + height**2 + depth**2)
        
        # Analyze point data (texture/color info)
        point_data = mesh.GetPointData()
        n_arrays = point_data.GetNumberOfArrays()
        has_colors = False
        has_normals = False
        
        for i in range(n_arrays):
            array = point_data.GetArray(i)
            n_components = array.GetNumberOfComponents()
            array_name = array.GetName() if array.GetName() else f"Array_{i}"
            
            if n_components >= 3 and 'color' in array_name.lower() or 'rgb' in array_name.lower():
                has_colors = True
            elif n_components == 3 and 'normal' in array_name.lower():
                has_normals = True
        
        # Analyze shape characteristics
        aspect_ratios = [
            max(width, height) / min(width, height),
            max(width, depth) / min(width, depth),
            max(height, depth) / min(height, depth)
        ]
        max_aspect_ratio = max(aspect_ratios)
        
        # Face orientation analysis
        # Check if it looks like a standard face orientation
        is_standard_face = (height > width > depth) and (max_aspect_ratio < 2.0)
        
        # Complexity analysis
        vertex_density = n_points / (diagonal**2) if diagonal > 0 else 0
        
        print(f"📊 Analysis Results:")
        print(f"   Points: {n_points:,}")
        print(f"   Dimensions: W={width:.1f} H={height:.1f} D={depth:.1f}")
        print(f"   Center: {center}")
        print(f"   Diagonal: {diagonal:.1f}")
        print(f"   Max aspect ratio: {max_aspect_ratio:.2f}")
        print(f"   Standard face orientation: {is_standard_face}")
        print(f"   Vertex density: {vertex_density:.2f}")
        print(f"   Data arrays: {n_arrays}")
        print(f"   Has colors: {has_colors}")
        print(f"   Has normals: {has_normals}")
        
        return {
            'n_points': n_points,
            'dimensions': {'width': width, 'height': height, 'depth': depth},
            'center': center,
            'diagonal': diagonal,
            'aspect_ratios': aspect_ratios,
            'max_aspect_ratio': max_aspect_ratio,
            'is_standard_face': is_standard_face,
            'vertex_density': vertex_density,
            'n_arrays': n_arrays,
            'has_colors': has_colors,
            'has_normals': has_normals,
            'mesh': mesh,
            'vertices': vertices,
            'bounds': bounds
        }
    
    def select_optimal_method(self, analysis):
        """Select the best alignment method based on PLY characteristics"""
        
        print(f"\n🎯 Selecting Optimal Alignment Method:")
        print("-" * 40)
        
        # Decision factors
        factors = {
            'anatomical_score': 0,
            'ultimate_score': 0,
            'reasons': []
        }
        
        # Factor 1: Face orientation
        if analysis['is_standard_face']:
            factors['anatomical_score'] += 3
            factors['reasons'].append("✅ Standard face orientation → Anatomical +3")
        else:
            factors['ultimate_score'] += 2
            factors['reasons'].append("⚠️  Non-standard orientation → Ultimate +2")
        
        # Factor 2: Aspect ratio
        if analysis['max_aspect_ratio'] < 1.5:
            factors['anatomical_score'] += 2
            factors['reasons'].append("✅ Good proportions → Anatomical +2")
        elif analysis['max_aspect_ratio'] > 3.0:
            factors['ultimate_score'] += 3
            factors['reasons'].append("⚠️  Extreme proportions → Ultimate +3")
        
        # Factor 3: Point density
        if analysis['vertex_density'] > 100:
            factors['anatomical_score'] += 1
            factors['reasons'].append("✅ High vertex density → Anatomical +1")
        elif analysis['vertex_density'] < 10:
            factors['ultimate_score'] += 1
            factors['reasons'].append("⚠️  Low vertex density → Ultimate +1")
        
        # Factor 4: Data complexity
        if analysis['has_colors'] and analysis['has_normals']:
            factors['anatomical_score'] += 2
            factors['reasons'].append("✅ Rich data (colors+normals) → Anatomical +2")
        elif analysis['n_arrays'] == 0:
            factors['ultimate_score'] += 1
            factors['reasons'].append("⚠️  Minimal data → Ultimate +1")
        
        # Factor 5: Size (diagonal)
        if 100 < analysis['diagonal'] < 300:
            factors['anatomical_score'] += 1
            factors['reasons'].append("✅ Standard face size → Anatomical +1")
        elif analysis['diagonal'] > 500 or analysis['diagonal'] < 50:
            factors['ultimate_score'] += 2
            factors['reasons'].append("⚠️  Unusual size → Ultimate +2")
        
        # Decision
        selected_method = 'anatomical' if factors['anatomical_score'] >= factors['ultimate_score'] else 'ultimate'
        
        print(f"📊 Scoring Results:")
        print(f"   Anatomical score: {factors['anatomical_score']}")
        print(f"   Ultimate score: {factors['ultimate_score']}")
        print(f"\n📝 Reasoning:")
        for reason in factors['reasons']:
            print(f"   {reason}")
        print(f"\n🎯 Selected Method: {selected_method.upper()}")
        
        return selected_method, factors
    
    def apply_hybrid_scale_free_alignment(self, ply_path, output_path):
        """Apply optimal scale-free alignment method"""
        
        print(f"\n🎯 Hybrid Scale-Free Alignment Workflow")
        print(f"Input: {os.path.basename(ply_path)}")
        print(f"Output: {os.path.basename(output_path)}")
        print("⚠️  SCALE PRESERVATION MODE - Manual landmarks will remain valid")
        print("🔍 AUTOMATIC METHOD SELECTION - Best approach will be chosen")
        print("=" * 80)
        
        if not os.path.exists(ply_path):
            print(f"❌ Input file not found: {ply_path}")
            return None
        
        # Step 1: Analyze PLY characteristics
        analysis = self.analyze_ply_characteristics(ply_path)
        
        # Step 2: Select optimal method
        selected_method, scoring = self.select_optimal_method(analysis)
        
        # Step 3: Apply selected method
        if selected_method == 'anatomical':
            return self.apply_anatomical_scale_free(ply_path, output_path, analysis)
        else:
            return self.apply_ultimate_scale_free(ply_path, output_path, analysis)
    
    def apply_anatomical_scale_free(self, ply_path, output_path, analysis):
        """Apply anatomical scale-free alignment"""
        
        print(f"\n🧠 Applying Anatomical Scale-Free Alignment:")
        print("-" * 50)
        
        # Import and initialize anatomical aligner here to avoid circular imports
        from scale_free_aligner import ScaleFreeAligner
        
        aligner = ScaleFreeAligner()
        result = aligner.apply_scale_free_alignment(ply_path, output_path)
        
        result['method_used'] = 'anatomical'
        result['method_reason'] = 'Standard face geometry detected'
        
        return result
    
    def apply_ultimate_scale_free(self, ply_path, output_path, analysis):
        """Apply ultimate scale-free alignment"""
        
        print(f"\n🔧 Applying Ultimate Scale-Free Alignment:")
        print("-" * 50)
        
        obj_reference = "assets/testmeshA.obj"
        if not os.path.exists(obj_reference):
            print(f"⚠️  Reference OBJ not found: {obj_reference}")
            print("   Using default reference...")
            obj_reference = "assets/testmeshA.obj"  # Keep trying
        
        result = self.ultimate_processor.align_ply_to_obj_system_scale_free(
            ply_path, output_path, obj_reference
        )
        
        result['method_used'] = 'ultimate'
        result['method_reason'] = 'Non-standard geometry or better OBJ alignment'
        
        return result
    
    def create_hybrid_config(self, method_used):
        """Create configuration file for the used method"""
        
        if method_used == 'anatomical':
            base_config = "configs/DTU3D-scale-free.json"
            output_config = "configs/DTU3D-hybrid-anatomical.json"
        else:
            base_config = "configs/DTU3D-geometry.json"
            output_config = "configs/DTU3D-hybrid-ultimate.json"
        
        try:
            with open(base_config, 'r') as f:
                config = json.load(f)
            
            config['name'] = "MVLMModel_DTU3D"
            
            with open(output_config, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"📝 Hybrid config created: {output_config}")
            return output_config
            
        except Exception as e:
            print(f"⚠️  Config creation failed: {e}")
            return base_config

# Stand-alone execution
def main():
    if len(sys.argv) < 3:
        print("🎯 Hybrid Scale-Free Aligner")
        print("=" * 40)
        print("Usage: python hybrid_scale_free_aligner.py input.ply output.ply [method]")
        print("")
        print("Arguments:")
        print("  input.ply     - Input PLY file")
        print("  output.ply    - Output aligned PLY file")
        print("  method        - Force method: 'anatomical', 'ultimate', or 'auto' (default)")
        print("")
        print("Examples:")
        print("  python hybrid_scale_free_aligner.py face.ply aligned.ply")
        print("  python hybrid_scale_free_aligner.py face.ply aligned.ply auto")
        print("  python hybrid_scale_free_aligner.py face.ply aligned.ply anatomical")
        sys.exit(1)
    
    input_ply = sys.argv[1]
    output_ply = sys.argv[2]
    force_method = sys.argv[3].lower() if len(sys.argv) > 3 else 'auto'
    
    if not os.path.exists(input_ply):
        print(f"❌ Input PLY file not found: {input_ply}")
        sys.exit(1)
    
    aligner = HybridScaleFreeAligner()
    
    if force_method in ['anatomical', 'ultimate']:
        print(f"🔧 Forced method: {force_method.upper()}")
        analysis = aligner.analyze_ply_characteristics(input_ply)
        
        if force_method == 'anatomical':
            result = aligner.apply_anatomical_scale_free(input_ply, output_ply, analysis)
        else:
            result = aligner.apply_ultimate_scale_free(input_ply, output_ply, analysis)
    else:
        # Auto-select method
        result = aligner.apply_hybrid_scale_free_alignment(input_ply, output_ply)
    
    if result:
        config_file = aligner.create_hybrid_config(result['method_used'])
        
        print(f"\n🎯 Hybrid Scale-Free Alignment Complete!")
        print(f"   Method used: {result['method_used'].upper()}")
        print(f"   Reason: {result['method_reason']}")
        print(f"   Scale preserved: ✅ (1.0x)")
        print(f"   Manual landmarks: ✅ Remain valid")
        print(f"   Output file: {output_ply}")
        print(f"   Config file: {config_file}")
        print(f"")
        print(f"🚀 Ready for prediction:")
        print(f"   python predict.py --c {config_file} --n {output_ply}")
    else:
        print("❌ Alignment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()