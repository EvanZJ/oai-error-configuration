#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

# Import the conversion functions from the existing converters
try:
    import importlib.util
    
    def load_converter_module(script_path):
        """Dynamically load a Python module from a file path"""
        spec = importlib.util.spec_from_file_location("converter", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    # Get the directory where this script is located
    SCRIPT_DIR = Path(__file__).resolve().parent
    
    # Load the CU and DU converter modules
    cu_converter_path = SCRIPT_DIR / "1_to_2_cu_conf_to_json.py"
    du_converter_path = SCRIPT_DIR / "1_to_2_du_conf_to_json.py"
    
    if not cu_converter_path.exists() or not du_converter_path.exists():
        print("Error: Converter scripts not found in the same directory!")
        print(f"Expected: {cu_converter_path}")
        print(f"Expected: {du_converter_path}")
        sys.exit(1)
    
    cu_converter = load_converter_module(cu_converter_path)
    du_converter = load_converter_module(du_converter_path)
    
except Exception as e:
    print(f"Error loading converter modules: {e}")
    sys.exit(1)


def process_case_folder(case_folder_path):
    """
    Process a single case folder containing both cu_case_XX.conf and du_case_XX.conf
    Output JSON files in the same folder
    
    Args:
        case_folder_path: Path to the case folder (e.g., cases_10/)
    
    Returns:
        tuple: (cu_success, du_success) - boolean flags for each conversion
    """
    case_folder_name = os.path.basename(case_folder_path)
    
    # Extract case number from folder name (e.g., "cases_10" -> "10")
    try:
        case_num = case_folder_name.replace("cases_", "")
    except:
        print(f"  ⚠️  Warning: Could not extract case number from {case_folder_name}")
        return False, False
    
    # Expected file names
    cu_conf_filename = f"cu_case_{case_num}.conf"
    du_conf_filename = f"du_case_{case_num}.conf"
    
    cu_conf_path = os.path.join(case_folder_path, cu_conf_filename)
    du_conf_path = os.path.join(case_folder_path, du_conf_filename)
    
    cu_json_filename = f"cu_case_{case_num}.json"
    du_json_filename = f"du_case_{case_num}.json"
    
    cu_json_path = os.path.join(case_folder_path, cu_json_filename)
    du_json_path = os.path.join(case_folder_path, du_json_filename)
    
    cu_success = False
    du_success = False
    
    # Process CU
    if os.path.exists(cu_conf_path):
        try:
            print(f"  🔄 Converting CU: {case_folder_name}/{cu_conf_filename}")
            conf_text = cu_converter.read_text(cu_conf_path)
            data = cu_converter.parse_conf_to_json(conf_text)
            cu_converter.write_json(cu_json_path, data)
            print(f"  ✅ Created CU: {case_folder_name}/{cu_json_filename}")
            cu_success = True
        except Exception as e:
            print(f"  ❌ Error converting CU in {case_folder_name}: {e}")
    else:
        print(f"  ⚠️  CU file not found: {cu_conf_filename}")
    
    # Process DU
    if os.path.exists(du_conf_path):
        try:
            print(f"  🔄 Converting DU: {case_folder_name}/{du_conf_filename}")
            conf_text = du_converter.read_text(du_conf_path)
            data = du_converter.parse_conf_to_json(conf_text)
            du_converter.write_json(du_json_path, data)
            print(f"  ✅ Created DU: {case_folder_name}/{du_json_filename}")
            du_success = True
        except Exception as e:
            print(f"  ❌ Error converting DU in {case_folder_name}: {e}")
    else:
        print(f"  ⚠️  DU file not found: {du_conf_filename}")
    
    return cu_success, du_success


def process_all_cases(base_path, config_filter='both'):
    """
    Process all case folders in the base path
    
    Args:
        base_path: Base directory containing cases_XX folders
        config_filter: 'cu', 'du', or 'both' - which files to process
    
    Returns:
        tuple: (cu_success_count, cu_failed_count, du_success_count, du_failed_count)
    """
    if not os.path.exists(base_path):
        print(f"❌ Error: Directory not found: {base_path}")
        return 0, 0, 0, 0
    
    print(f"\n{'=' * 80}")
    print(f"Processing paired cases from: {base_path}")
    print(f"Filter: {config_filter.upper()}")
    print(f"{'=' * 80}")
    
    # Get all case folders (e.g., cases_01, cases_02, etc.)
    case_folders = []
    for item in sorted(os.listdir(base_path)):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith("cases_"):
            case_folders.append(item_path)
    
    if not case_folders:
        print(f"  ⚠️  No cases_* folders found")
        return 0, 0, 0, 0
    
    print(f"Found {len(case_folders)} case folders\n")
    
    cu_success = 0
    cu_failed = 0
    du_success = 0
    du_failed = 0
    
    for case_folder in case_folders:
        cu_ok, du_ok = process_case_folder(case_folder)
        
        # Only count based on filter
        if config_filter in ['cu', 'both']:
            if cu_ok:
                cu_success += 1
            else:
                cu_failed += 1
        
        if config_filter in ['du', 'both']:
            if du_ok:
                du_success += 1
            else:
                du_failed += 1
        
        print()  # Empty line between cases
    
    return cu_success, cu_failed, du_success, du_failed


def main():
    parser = argparse.ArgumentParser(
        description='Batch convert paired CU/DU .conf files to .json (multiple_parameter structure)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example directory structure:
  Input/Output (same directory):
    /path/to/output/
    ├── cases_01/
    │   ├── cu_case_01.conf
    │   ├── cu_case_01.json  ← created here
    │   ├── du_case_01.conf
    │   └── du_case_01.json  ← created here
    ├── cases_02/
    │   ├── cu_case_02.conf
    │   ├── cu_case_02.json  ← created here
    │   ├── du_case_02.conf
    │   └── du_case_02.json  ← created here
    └── ...

Usage:
  python batch_paired_conf_to_json_converter.py
  python batch_paired_conf_to_json_converter.py --input /path/to/output
  python batch_paired_conf_to_json_converter.py --input /path/to/output --type cu
  python batch_paired_conf_to_json_converter.py --input /path/to/output --type du
        """
    )
    
    # Default path
    default_input = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output"
    
    parser.add_argument(
        '--input',
        default=default_input,
        help=f'Input/Output base directory containing cases_* folders (default: {default_input})'
    )
    parser.add_argument(
        '--type',
        choices=['cu', 'du', 'both'],
        default='both',
        help='Process only CU, only DU, or both (default: both)'
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting Batch Paired .conf to .json Conversion")
    print("=" * 80)
    print(f"Directory:  {args.input}")
    print(f"Processing: {args.type.upper()}")
    print(f"Output:     Same folder as input .conf files")
    print("=" * 80)
    
    # Check input directory exists
    if not os.path.exists(args.input):
        print(f"❌ Error: Input directory not found: {args.input}")
        sys.exit(1)
    
    # Process all cases
    cu_success, cu_failed, du_success, du_failed = process_all_cases(args.input, args.type)
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    if args.type in ['cu', 'both']:
        print(f"CU conversions:")
        print(f"  ✅ Success: {cu_success}")
        print(f"  ❌ Failed:  {cu_failed}")
    
    if args.type in ['du', 'both']:
        print(f"DU conversions:")
        print(f"  ✅ Success: {du_success}")
        print(f"  ❌ Failed:  {du_failed}")
    
    total_success = cu_success + du_success
    total_failed = cu_failed + du_failed
    
    print(f"\nTotal:")
    print(f"  ✅ Success: {total_success}")
    print(f"  ❌ Failed:  {total_failed}")
    print(f"\n📁 JSON files created in the same folders as .conf files")
    print("🏁 Conversion completed")


if __name__ == "__main__":
    main()