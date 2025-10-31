#!/usr/bin/env python3
"""
合併配對測試結果 (logs + configs) 到 JSONL 格式
從 logs_batch_run 資料夾讀取測試結果，並與對應的 CU/DU 配置合併
"""

import json
import os
from pathlib import Path
import glob

# *******************************************************************
# 1. 設定路徑
# *******************************************************************
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# 路徑設定
LOGS_ROOT = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/logs_batch_run"
CASES_ROOT = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output"
BASELINE_UE_JSON = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf_json/ue_oai.json"

# 輸出路徑
OUTPUT_DIR = Path("/home/sionna/evan/CursorAutomation/cursor_gen_conf")
OUTPUT_FILE = OUTPUT_DIR / 'merged_paired_test_results.jsonl'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# *******************************************************************
# 2. 輔助函數
# *******************************************************************

def load_ue_baseline():
    """載入 baseline UE 配置"""
    try:
        with open(BASELINE_UE_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 警告: 無法載入 UE baseline 配置: {e}")
        return {}


def load_tail100_summary(log_dir):
    """從 log 目錄載入 tail100_summary.json"""
    tail100_file = os.path.join(log_dir, "tail100_summary.json")
    try:
        with open(tail100_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


def load_config_json(config_path):
    """載入配置 JSON 檔案"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


def extract_case_name_from_log_folder(log_folder_name):
    """
    從 log 資料夾名稱提取 case 名稱
    例如: "20250101_120000_cases_01" -> "cases_01"
    """
    parts = log_folder_name.split('_')
    # 找到 "cases_XX" 部分
    for i, part in enumerate(parts):
        if part == "cases" and i + 1 < len(parts):
            return f"cases_{parts[i + 1]}"
    return None


def load_cases_delta(case_folder):
    """從 case 資料夾載入 cases_delta.json"""
    delta_file = os.path.join(case_folder, "cases_delta.json")
    try:
        with open(delta_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


def build_misconfigured_param_string(modified_key, error_value):
    """建構 misconfigured_param 字串"""
    # 將 modified_key 轉換為點分隔格式
    # 例如: "security.integrity_algorithms[0]" -> "gNBs.security.integrity_algorithms[0]"
    
    # 如果不是以 gNBs 開頭，加上 gNBs 前綴
    if not modified_key.startswith("gNBs"):
        key = f"gNBs.{modified_key}"
    else:
        key = modified_key
    
    # 格式化值
    if isinstance(error_value, str):
        value_str = error_value
    else:
        value_str = str(error_value)
    
    return f"{key}={value_str}"


def build_correct_param_string(modified_key, original_value):
    """建構 correct_param 字串"""
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
# 3. 主處理邏輯
# *******************************************************************

all_records = []
total_processed = 0
failed_cases = []

# 載入 baseline UE 配置
baseline_ue_config = load_ue_baseline()

print("🔄 開始處理測試結果...")
print(f"📂 Log 目錄: {LOGS_ROOT}")
print(f"📂 Cases 目錄: {CASES_ROOT}")
print("-" * 80)

# 遍歷所有 log 資料夾
log_folders = sorted([d for d in os.listdir(LOGS_ROOT) if os.path.isdir(os.path.join(LOGS_ROOT, d))])

for log_folder_name in log_folders:
    log_folder_path = os.path.join(LOGS_ROOT, log_folder_name)
    
    # 提取 case 名稱
    case_name = extract_case_name_from_log_folder(log_folder_name)
    if not case_name:
        failed_cases.append(f"無法從 {log_folder_name} 提取 case 名稱")
        continue
    
    print(f"🔍 處理: {log_folder_name} -> {case_name}")
    
    # 找到對應的 case 資料夾
    case_folder = os.path.join(CASES_ROOT, case_name)
    if not os.path.exists(case_folder):
        failed_cases.append(f"找不到對應的 case 資料夾: {case_name}")
        continue
    
    # 載入 tail100_summary.json (logs)
    logs = load_tail100_summary(log_folder_path)
    if not logs:
        failed_cases.append(f"{case_name}: 無法載入 tail100_summary.json")
        continue
    
    # 載入 cases_delta.json
    cases_delta = load_cases_delta(case_folder)
    if not cases_delta:
        failed_cases.append(f"{case_name}: 無法載入 cases_delta.json")
        continue
    
    # 找到 CU 和 DU 的 JSON 配置檔案
    cu_json_files = glob.glob(os.path.join(case_folder, "cu_case_*.json"))
    du_json_files = glob.glob(os.path.join(case_folder, "du_case_*.json"))
    
    if not cu_json_files or not du_json_files:
        failed_cases.append(f"{case_name}: 找不到 CU 或 DU JSON 配置")
        continue
    
    # 載入 CU 和 DU 配置
    cu_config = load_config_json(cu_json_files[0])
    du_config = load_config_json(du_json_files[0])
    
    if not cu_config or not du_config:
        failed_cases.append(f"{case_name}: 無法載入 CU 或 DU 配置")
        continue
    
    # 從 cases_delta 提取 CU 和 DU 的錯誤描述
    cu_case = None
    du_case = None
    
    for case in cases_delta:
        if "cu" in case:
            cu_case = case["cu"]
        if "du" in case:
            du_case = case["du"]
    
    if not cu_case or not du_case:
        failed_cases.append(f"{case_name}: cases_delta.json 中缺少 CU 或 DU 資訊")
        continue
    
    # 建構 misconfigured_param 和 correct_param
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
    
    # 建構完整記錄
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
    print(f"   ✅ 成功處理")

# *******************************************************************
# 4. 寫入結果
# *******************************************************************

if all_records:
    try:
        with open(str(OUTPUT_FILE), 'w', encoding='utf-8') as outfile:
            for record in all_records:
                json_line = json.dumps(record, ensure_ascii=False)
                outfile.write(json_line + '\n')
        
        print("\n" + "=" * 80)
        print(f"✅ 成功! 合併結果已儲存至：")
        print(f"   {OUTPUT_FILE}")
        print(f"📊 統計:")
        print(f"   - 成功處理: {total_processed} 筆")
        print(f"   - 失敗: {len(failed_cases)} 筆")
        
        if failed_cases:
            print(f"\n⚠️ 失敗案例 (前 10 項):")
            for failed in failed_cases[:10]:
                print(f"   - {failed}")
            if len(failed_cases) > 10:
                print(f"   ... 還有 {len(failed_cases) - 10} 項")
        
        print("=" * 80)
        
        # 顯示範例記錄
        if all_records:
            print("\n📋 輸出格式範例 (第 1 筆記錄):")
            print("-" * 80)
            sample = all_records[0]
            # 只顯示部分欄位以保持可讀性
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
        print(f"❌ 寫入檔案時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ 沒有成功處理任何記錄")