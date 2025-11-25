#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

# Import the conversion functions from the existing converters
# Assuming 1_to_2_cu_conf_to_json.py and 1_to_2_du_conf_to_json.py are in the same directory
try:
    # Try to import from the conversion scripts
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


def process_case_folder(case_folder_path, config_type):
    """
    Process a single case folder containing a .conf file
    Output .json in the same folder as the .conf file
    
    Args:
        case_folder_path: Path to the case folder (e.g., cu_cases_02/)
        config_type: Either 'cu' or 'du'
    """
    case_folder_name = os.path.basename(case_folder_path)
    
    # Expected .conf file name matches the folder name
    conf_filename = f"{case_folder_name}.conf"
    conf_path = os.path.join(case_folder_path, conf_filename)
    
    if not os.path.exists(conf_path):
        print(f"  ⚠️  Warning: {conf_filename} not found in {case_folder_name}")
        return False
    
    # Output .json file in the SAME folder as .conf
    json_filename = f"{case_folder_name}.json"
    output_path = os.path.join(case_folder_path, json_filename)
    
    try:
        print(f"  🔄 Converting: {case_folder_name}/{conf_filename}")
        
        # Use appropriate converter based on config type
        if config_type == "cu":
            conf_text = cu_converter.read_text(conf_path)
            data = cu_converter.parse_conf_to_json(conf_text)
            cu_converter.write_json(output_path, data)
        else:  # du
            conf_text = du_converter.read_text(conf_path)
            data = du_converter.parse_conf_to_json(conf_text)
            du_converter.write_json(output_path, data)
        
        print(f"  ✅ Created: {case_folder_name}/{json_filename}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error converting {case_folder_name}: {e}")
        return False


def process_config_type(input_base, config_type):
    """
    Process all case folders for a specific config type (cu or du)
    
    Args:
        input_base: Base input directory containing cu/ and du/
        config_type: Either 'cu' or 'du'
    """
    input_dir = os.path.join(input_base, config_type)
    
    if not os.path.exists(input_dir):
        print(f"⚠️  {config_type.upper()} directory not found: {input_dir}")
        return 0, 0
    
    print(f"\n{'=' * 80}")
    print(f"Processing {config_type.upper()} cases from: {input_dir}")
    print(f"{'=' * 80}")
    
    # Get all case folders (e.g., cu_cases_01, cu_cases_02, etc.)
    case_folders = []
    for item in sorted(os.listdir(input_dir)):
        item_path = os.path.join(input_dir, item)
        if os.path.isdir(item_path) and item.startswith(f"{config_type}_cases_"):
            case_folders.append(item_path)
    
    if not case_folders:
        print(f"  ⚠️  No {config_type}_cases_* folders found")
        return 0, 0
    
    print(f"Found {len(case_folders)} case folders")
    
    success_count = 0
    failed_count = 0
    
    for case_folder in case_folders:
        if process_case_folder(case_folder, config_type):
            success_count += 1
        else:
            failed_count += 1
    
    print(f"\n{config_type.upper()} Summary: ✅ {success_count} succeeded, ❌ {failed_count} failed")
    return success_count, failed_count


def main():
    parser = argparse.ArgumentParser(
        description='Batch convert CU/DU .conf files to .json in the same folders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example directory structure:
  Input/Output (same directory):
    /path/to/output/
    ├── cu/
    │   ├── cu_cases_01/
    │   │   ├── cu_cases_01.conf
    │   │   └── cu_cases_01.json  ← created here
    │   ├── cu_cases_02/
    │   │   ├── cu_cases_02.conf
    │   │   └── cu_cases_02.json  ← created here
    │   └── ...
    └── du/
        ├── du_cases_01/
        │   ├── du_cases_01.conf
        │   └── du_cases_01.json  ← created here
        └── ...

Usage:
  python batch_conf_to_json_converter.py
  python batch_conf_to_json_converter.py --input /path/to/output
  python batch_conf_to_json_converter.py --input /path/to/output --type cu
  python batch_conf_to_json_converter.py --input /path/to/output --type du
        """
    )
    
    # Default path
    default_input = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/one_parameter/output"
    
    parser.add_argument(
        '--input',
        default=default_input,
        help=f'Input/Output base directory containing cu/ and du/ folders (default: {default_input})'
    )
    parser.add_argument(
        '--type',
        choices=['cu', 'du', 'both'],
        default='both',
        help='Process only CU, only DU, or both (default: both)'
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting Batch .conf to .json Conversion")
    print("=" * 80)
    print(f"Directory:  {args.input}")
    print(f"Processing: {args.type.upper()}")
    print(f"Output:     Same folder as input .conf files")
    print("=" * 80)
    
    # Check input directory exists
    if not os.path.exists(args.input):
        print(f"❌ Error: Input directory not found: {args.input}")
        sys.exit(1)
    
    total_success = 0
    total_failed = 0
    
    # Process based on type argument
    if args.type in ['cu', 'both']:
        cu_success, cu_failed = process_config_type(args.input, 'cu')
        total_success += cu_success
        total_failed += cu_failed
    
    if args.type in ['du', 'both']:
        du_success, du_failed = process_config_type(args.input, 'du')
        total_success += du_success
        total_failed += du_failed
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"Total conversions:")
    print(f"  ✅ Success: {total_success}")
    print(f"  ❌ Failed:  {total_failed}")
    print(f"\n📁 JSON files created in the same folders as .conf files")
    print("🏁 Conversion completed")


if __name__ == "__main__":
    main()