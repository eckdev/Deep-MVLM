import os
import sys
from anatomical_aligner import AnatomicalAligner
    
def anatomical_align_ply(ply_path,output_path):
    aligner = AnatomicalAligner()
    ply_file = ply_path
    output_file = output_path

    print('<0001f9e0> Testing Anatomical Alignment for 14.ply')
    print('=' * 50)

    try:
        result = aligner.apply_anatomical_alignment(ply_file, output_file)
        print(f'✅ Success: {output_file}')
        print(f'   Transform applied: {result["transform_params"]["anatomy_guess"]}')
        print(f'   Scale factor: {result["transform_params"]["scale_factor"]:.3f}')
        print(f'   Final center: {result["final_center"]}')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python ultimate_ply_preprocessor.py input.ply output.ply")
        sys.exit(1)

    anatomical_align_ply(sys.argv[1], sys.argv[2])