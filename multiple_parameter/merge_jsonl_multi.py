#!/usr/bin/env python3
"""
Merge paired test results (logs + configs) into JSONL format
Read test results from logs_batch_run folder and merge with corresponding CU/DU configurations
"""

import json
import os
from pathlib import Path
import glob

# *******************************************************************
# 1. Path Configuration
# *******************************************************************
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Path settings
LOGS_ROOT = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/logs_batch_run"
CASES_ROOT = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output"
BASELINE_UE_JSON = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf_json/ue_oai.json"

# Output paths
OUTPUT_DIR = Path("/home/sionna/evan/CursorAutomation/cursor_gen_conf")
OUTPUT_FILE = OUTPUT_DIR / 'merged_paired_test_results.jsonl'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# *******************************************************************
# 2. Helper Functions
# *******************************************************************

def load_ue_baseline():
    """Load baseline UE configuration"""
    try:
        with open(BASELINE_UE_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Warning: Unable to load UE baseline configuration: {e}")
        return {}


def load_tail100_summary(log_dir):
    """Load tail100_summary.json from log directory"""
    tail100_file = os.path.join(log_dir, "tail100_summary.json")
    try:
        with open(tail100_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


def load_config_json(config_path):
    """Load configuration JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


def extract_case_name_from_log_folder(log_folder_name):
    """
    Extract case name from log folder name
    Example: "20250101_120000_cases_01" -> "cases_01"
    """
    parts = log_folder_name.split('_')
    # Find "cases_XX" part
    for i, part in enumerate(parts):
        if part == "cases" and i + 1 < len(parts):
            return f"cases_{parts[i + 1]}"
    return None


def load_cases_delta(case_folder):
    """Load cases_delta.json from case folder"""
    delta_file = os.path.join(case_folder, "cases_delta.json")
    try:
        with open(delta_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


def build_misconfigured_param_string(modified_key, error_value):
    """Build misconfigured_param string"""
    # Convert modified_key to dot-separated format
    # Example: "security.integrity_algorithms[0]" -> "gNBs.security.integrity_algorithms[0]"
    
    # Add gNBs prefix if not already present
    if not modified_key.startswith("gNBs"):
        key = f"gNBs.{modified_key}"
    else:
        key = modified_key
    
    # Format value
    if isinstance(error_value, str):
        value_str = error_value
    else:
        value_str = str(error_value)
    
    return f"{key}={value_str}"


def build_correct_param_string(modified_key, original_value):
    """Build correct_param string"""
    if not modified_key.startswith("gNBs"):
        key = f"gNBs.{modified_key}"
    else:
        key = modified_key
    
    if isinstance(original_value, str):
        value_str = original_value
    else:
        value_str = str(original_value)
    
    return f"{key}={value_str}"


# *******************************************************************
# 3. Main Processing Logic
# *******************************************************************

all_records = []
total_processed = 0
failed_cases = []

# Load baseline UE configuration
baseline_ue_config = load_ue_baseline()

print("🔄 Starting to process test results...")
print(f"📂 Log directory: {LOGS_ROOT}")
print(f"📂 Cases directory: {CASES_ROOT}")
print("-" * 80)

# Iterate through all log folders
log_folders = sorted([d for d in os.listdir(LOGS_ROOT) if os.path.isdir(os.path.join(LOGS_ROOT, d))])

for log_folder_name in log_folders:
    log_folder_path = os.path.join(LOGS_ROOT, log_folder_name)
    
    # Extract case name
    case_name = extract_case_name_from_log_folder(log_folder_name)
    if not case_name:
        failed_cases.append(f"Unable to extract case name from {log_folder_name}")
        continue
    
    print(f"🔍 Processing: {log_folder_name} -> {case_name}")
    
    # Find corresponding case folder
    case_folder = os.path.join(CASES_ROOT, case_name)
    if not os.path.exists(case_folder):
        failed_cases.append(f"Corresponding case folder not found: {case_name}")
        continue
    
    # Load tail100_summary.json (logs)
    logs = load_tail100_summary(log_folder_path)
    if not logs:
        failed_cases.append(f"{case_name}: Unable to load tail100_summary.json")
        continue
    
    # Load cases_delta.json
    cases_delta = load_cases_delta(case_folder)
    if not cases_delta:
        failed_cases.append(f"{case_name}: Unable to load cases_delta.json")
        continue
    
    # Find CU and DU JSON configuration files
    cu_json_files = glob.glob(os.path.join(case_folder, "cu_case_*.json"))
    du_json_files = glob.glob(os.path.join(case_folder, "du_case_*.json"))
    
    if not cu_json_files or not du_json_files:
        failed_cases.append(f"{case_name}: CU or DU JSON configuration not found")
        continue
    
    # Load CU and DU configurations
    cu_config = load_config_json(cu_json_files[0])
    du_config = load_config_json(du_json_files[0])
    
    if not cu_config or not du_config:
        failed_cases.append(f"{case_name}: Unable to load CU or DU configuration")
        continue
    
    # Extract CU and DU error descriptions from cases_delta
    cu_case = None
    du_case = None
    
    for case in cases_delta:
        if "cu" in case:
            cu_case = case["cu"]
        if "du" in case:
            du_case = case["du"]
    
    if not cu_case or not du_case:
        failed_cases.append(f"{case_name}: CU or DU information missing in cases_delta.json")
        continue
    
    # Build misconfigured_param and correct_param
    cu_misconfigured = build_misconfigured_param_string(
        cu_case.get("modified_key", ""),
        cu_case.get("error_value", "")
    )
    cu_correct = build_correct_param_string(
        cu_case.get("modified_key", ""),
        cu_case.get("original_value", "")
    )
    
    du_misconfigured = build_misconfigured_param_string(
        du_case.get("modified_key", ""),
        du_case.get("error_value", "")
    )
    du_correct = build_correct_param_string(
        du_case.get("modified_key", ""),
        du_case.get("original_value", "")
    )
    
    # Build complete record
    record = {
        "misconfigured_param": {
            "cu": cu_misconfigured,
            "du": du_misconfigured
        },
        "correct_param": {
            "cu": cu_correct,
            "du": du_correct
        },
        "logs": logs,
        "network_config": {
            "cu_conf": cu_config,
            "du_conf": du_config,
            "ue_conf": baseline_ue_config
        },
        "metadata": {
            "case_name": case_name,
            "log_folder": log_folder_name,
            "cu_error_type": cu_case.get("error_type", "unknown"),
            "du_error_type": du_case.get("error_type", "unknown")
        }
    }
    
    all_records.append(record)
    total_processed += 1
    print(f"   ✅ Successfully processed")

# *******************************************************************
# 4. Write Results
# *******************************************************************

if all_records:
    try:
        with open(str(OUTPUT_FILE), 'w', encoding='utf-8') as outfile:
            for record in all_records:
                json_line = json.dumps(record, ensure_ascii=False)
                outfile.write(json_line + '\n')
        
        print("\n" + "=" * 80)
        print(f"✅ Success! Merged results saved to:")
        print(f"   {OUTPUT_FILE}")
        print(f"📊 Statistics:")
        print(f"   - Successfully processed: {total_processed} records")
        print(f"   - Failed: {len(failed_cases)} records")
        
        if failed_cases:
            print(f"\n⚠️ Failed cases (first 10):")
            for failed in failed_cases[:10]:
                print(f"   - {failed}")
            if len(failed_cases) > 10:
                print(f"   ... and {len(failed_cases) - 10} more")
        
        print("=" * 80)
        
        # Show sample record
        if all_records:
            print("\n📋 Output format example (first record):")
            print("-" * 80)
            sample = all_records[0]
            # Show only partial fields for readability
            sample_preview = {
                "misconfigured_param": sample["misconfigured_param"],
                "correct_param": sample["correct_param"],
                "logs": {
                    "CU": sample["logs"]["CU"][:3] + ["..."],
                    "DU": sample["logs"]["DU"][:3] + ["..."],
                    "UE": sample["logs"]["UE"][:3] + ["..."]
                },
                "metadata": sample["metadata"]
            }
            print(json.dumps(sample_preview, ensure_ascii=False, indent=2))
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Error writing to file: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ No records were successfully processed")