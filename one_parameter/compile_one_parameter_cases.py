#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Default paths
DEFAULT_BASE = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/one_parameter"
DEFAULT_OUTPUT_BASE = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/one_parameter/output"
DEFAULT_LOGS_BASE = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/one_parameter/logs_batch_run"
DEFAULT_BASELINE = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf_json"
DEFAULT_COMPILED = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/compiled_one_parameter_cases"


def find_log_folder(logs_base_path, case_folder_name):
    """
    Find the log folder matching the case folder name
    e.g., cu_cases_02 -> 20251107_231743_cu_cases_02
    """
    if not os.path.exists(logs_base_path):
        return None
    
    dirs = [d for d in os.listdir(logs_base_path) if os.path.isdir(os.path.join(logs_base_path, d))]
    
    for dir_name in dirs:
        if case_folder_name in dir_name:
            return dir_name
    
    return None


def load_cases_delta(output_path, config_type):
    """Load all cases_delta.json files from case subdirectories for a config type"""
    type_path = os.path.join(output_path, config_type)
    
    if not os.path.exists(type_path):
        return []
    
    # Get all subdirectories in the type_path
    case_dirs = [d for d in os.listdir(type_path) 
                 if os.path.isdir(os.path.join(type_path, d))]
    
    all_cases = []
    for case_dir in sorted(case_dirs):
        delta_path = os.path.join(type_path, case_dir, "cases_delta.json")
        
        if os.path.exists(delta_path):
            try:
                with open(delta_path, 'r') as f:
                    cases = json.load(f)
                    if isinstance(cases, list):
                        # Fix the filename to match the directory name
                        for case in cases:
                            case['filename'] = f"{case_dir}.json"
                        all_cases.extend(cases)
            except Exception as e:
                print(f"⚠️  Error loading {delta_path}: {e}")
    
    return all_cases


def build_case_json(case, config_type, output_base, logs_base, baseline_path):
    """
    Build the compiled JSON structure for a single case
    
    Args:
        case: Case dict from cases_delta.json
        config_type: 'cu' or 'du'
        output_base: Base output directory
        logs_base: Base logs directory
        baseline_path: Path to baseline configs
    """
    # Extract case folder name from filename
    # e.g., "cu_cases_02.json" -> "cu_cases_02"
    if 'filename' not in case:
        print(f"⚠️  Case missing 'filename' field")
        return None
    
    case_name = case['filename'].replace('.json', '')
    case_folder = os.path.join(output_base, config_type, case_name)
    
    # Build temp_json structure
    temp_json = {}
    temp_json["misconfigured_param"] = f"{case.get('modified_key', 'unknown')}={case.get('error_value', 'unknown')}"
    temp_json["original_param"] = f"{case.get('modified_key', 'unknown')}={case.get('original_value', 'unknown')}"
    temp_json["logs"] = {"CU": [], "DU": [], "UE": []}
    
    # Find and load logs
    log_folder_name = find_log_folder(logs_base, case_name)
    
    if log_folder_name:
        log_folder_path = os.path.join(logs_base, log_folder_name)
        summary_file = os.path.join(log_folder_path, "tail100_summary.json")
        
        if os.path.exists(summary_file):
            try:
                with open(summary_file, "r") as f:
                    summary = json.load(f)
                    temp_json["logs"]["CU"] = summary.get("CU", [])
                    temp_json["logs"]["DU"] = summary.get("DU", [])
                    temp_json["logs"]["UE"] = summary.get("UE", [])
            except Exception as e:
                print(f"  ⚠️  Error loading logs for {case_name}: {e}")
    else:
        print(f"  ⚠️  No logs found for {case_name}")
    
    # Load network configs
    temp_json["network_config"] = {}
    
    # Load the modified config (CU or DU)
    modified_json_path = os.path.join(case_folder, f"{case_name}.json")
    if os.path.exists(modified_json_path):
        try:
            with open(modified_json_path, "r") as f:
                if config_type == "cu":
                    temp_json["network_config"]["cu_conf"] = json.load(f)
                else:
                    temp_json["network_config"]["du_conf"] = json.load(f)
        except Exception as e:
            print(f"  ⚠️  Error loading modified config for {case_name}: {e}")
            return None
    else:
        print(f"  ⚠️  Modified config not found: {modified_json_path}")
        return None
    
    # Load baseline configs for non-modified elements
    if config_type == "cu":
        # CU is modified, use baseline DU
        du_baseline = os.path.join(baseline_path, "du_gnb.json")
        if os.path.exists(du_baseline):
            with open(du_baseline, "r") as f:
                temp_json["network_config"]["du_conf"] = json.load(f)
    else:
        # DU is modified, use baseline CU
        cu_baseline = os.path.join(baseline_path, "cu_gnb.json")
        if os.path.exists(cu_baseline):
            with open(cu_baseline, "r") as f:
                temp_json["network_config"]["cu_conf"] = json.load(f)
    
    # Load baseline UE
    ue_baseline = os.path.join(baseline_path, "ue.json")
    if os.path.exists(ue_baseline):
        with open(ue_baseline, "r") as f:
            temp_json["network_config"]["ue_conf"] = json.load(f)
    
    return temp_json


def load_all_cases_delta(output_path, logs_base, baseline_path, compiled_output):
    """Load all cases from both CU and DU directories and compile them together"""
    print("🚀 Starting Combined Cases Compilation")
    print("=" * 80)
    print(f"Output base:      {output_path}")
    print(f"Logs base:        {logs_base}")
    print(f"Baseline configs: {baseline_path}")
    print(f"Compiled output:  {compiled_output}")
    print("=" * 80)
    
    # Check directories exist
    if not os.path.exists(output_path):
        print(f"❌ Error: Output base directory not found: {output_path}")
        return
    
    if not os.path.exists(logs_base):
        print(f"❌ Error: Logs base directory not found: {logs_base}")
        return
    
    if not os.path.exists(baseline_path):
        print(f"❌ Error: Baseline directory not found: {baseline_path}")
        return
    
    # Load CU cases
    cu_cases = load_cases_delta(output_path, 'cu')
    print(f"Found {len(cu_cases)} CU cases")
    
    # Load DU cases  
    du_cases = load_cases_delta(output_path, 'du')
    print(f"Found {len(du_cases)} DU cases")
    
    all_cases = cu_cases + du_cases
    total_cases = len(all_cases)
    
    if not all_cases:
        print("⚠️  No cases found")
        return 0, 0
    
    print(f"Total cases to compile: {total_cases}")
    
    # Create output directory
    os.makedirs(compiled_output, exist_ok=True)
    
    # Prepare combined JSONL file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_filename = f"all_cases_compiled_{timestamp}.jsonl"
    jsonl_path = os.path.join(compiled_output, jsonl_filename)
    
    success_count = 0
    failed_count = 0
    
    with open(jsonl_path, 'w') as jsonl_file:
        for i, case in enumerate(all_cases, 1):
            case_name = case.get('filename', f'unknown_{i}').replace('.json', '')
            config_type = 'cu' if case in cu_cases else 'du'
            
            print(f"\n  [{i}/{total_cases}] Processing: {case_name} ({config_type.upper()})")
            
            try:
                # Build compiled JSON
                compiled_json = build_case_json(case, config_type, output_path, logs_base, baseline_path)
                
                if compiled_json is None:
                    print(f"  ❌ Failed to compile {case_name}")
                    failed_count += 1
                    continue
                
                # Save individual JSON file
                individual_filename = f"case_{case_name}_compiled.json"
                individual_path = os.path.join(compiled_output, individual_filename)
                
                with open(individual_path, 'w') as f:
                    json.dump(compiled_json, f, indent=2)
                
                # Append to JSONL
                jsonl_file.write(json.dumps(compiled_json) + '\n')
                
                print(f"  ✅ Compiled: {individual_filename}")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ Error compiling {case_name}: {e}")
                import traceback
                traceback.print_exc()
                failed_count += 1
    
    print(f"\n{'=' * 80}")
    print("📊 COMPILATION SUMMARY")
    print("=" * 80)
    print(f"Total cases processed: {total_cases}")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Failed:  {failed_count}")
    print(f"  📄 JSONL file: {jsonl_filename}")
    print(f"\n📁 Output directory: {compiled_output}")
    print("🏁 Compilation completed")
    
    return success_count, failed_count


def main():
    parser = argparse.ArgumentParser(
        description='Compile one_parameter cases into JSONL format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script:
1. Loads cases from cases_delta.json files in cu/ and du/ subdirectories
2. Finds matching log folders
3. Combines case data, logs, and configs into compiled JSON
4. Saves individual JSON files and one combined JSONL file

Output structure:
  compiled_one_parameter_cases/
  ├── case_cu_cases_01_compiled.json
  ├── case_cu_cases_02_compiled.json
  ├── case_du_cases_01_compiled.json
  └── all_cases_compiled_TIMESTAMP.jsonl
        """
    )
    
    parser.add_argument(
        '--output-base',
        default=DEFAULT_OUTPUT_BASE,
        help=f'Base output directory containing cu/ and du/ folders (default: {DEFAULT_OUTPUT_BASE})'
    )
    parser.add_argument(
        '--logs-base',
        default=DEFAULT_LOGS_BASE,
        help=f'Base logs directory (default: {DEFAULT_LOGS_BASE})'
    )
    parser.add_argument(
        '--baseline',
        default=DEFAULT_BASELINE,
        help=f'Baseline configs directory (default: {DEFAULT_BASELINE})'
    )
    parser.add_argument(
        '--compiled-output',
        default=DEFAULT_COMPILED,
        help=f'Output directory for compiled files (default: {DEFAULT_COMPILED})'
    )
    
    args = parser.parse_args()
    
    # Run combined compilation
    success_count, failed_count = load_all_cases_delta(
        args.output_base,
        args.logs_base,
        args.baseline,
        args.compiled_output
    )


if __name__ == "__main__":
    main()