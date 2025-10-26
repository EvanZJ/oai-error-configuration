#!/usr/bin/env python3
"""
根據 cases_delta.json 中的錯誤描述，修改 baseline CU conf 並輸出新的錯誤 conf
處理 multiple_parameter/output/cases_XX 資料夾結構
每個修改的地方會自動加上中英雙語註解
"""

import os
import json
import re
import glob

BASELINE_CONF = r"/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/cu_gnb.conf"
CASES_ROOT = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output"


def replace_key_value(conf_text: str, modified_key: str, error_value, original_value=None) -> str:
    """
    根據 modified_key 在 conf_text 裡替換值，並加上中英對照註解
    支援 array index，例如 security.integrity_algorithms[0]
    支援整個 section 的替換，例如 NETWORK_INTERFACES 或 log_config
    """

    # 定義哪些 key 是真正的 sections 以及它們的格式
    section_formats = {
        "NETWORK_INTERFACES": r"({}\s*:\s*)\{{[^}}]*\}}",  # key : { ... }
        "log_config": r"({}\s*:\s*)\{{[^}}]*\}}",          # key : { ... }
        "security": r"({}\s*=\s*)\{{[^}}]*\}}",            # key = { ... }
        "gNBs": r"({}\s*=\s*)\([^)]*\);",                  # key = ( ... );
        "SCTP": r"({}\s*:\s*)\{{[^}}]*\}}",                # key : { ... } (nested under gNBs)
    }

    # 檢查是否是要替換整個 section (當 error_value 是 None 或 {} 且 key 是已知的 section)
    key = modified_key.split(".")[-1]
    if (error_value is None or (isinstance(error_value, dict) and len(error_value) == 0)) and key in section_formats:
        # 對於 section 的替換，使用對應的 pattern
        if error_value is None:
            formatted_value = "None"
        else:
            formatted_value = "{}"

        pattern = section_formats[key].format(key)
        def replacer(match):
            if original_value is not None:
                comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            else:
                comment = f"  # 修改為 {error_value} / Modified to {error_value}"
            if key == "gNBs":
                return f"{match.group(1)}({{{formatted_value}}});{comment}"
            elif error_value is None:
                # For null values, replace the entire section with just None
                return f"{match.group(1)}{formatted_value};{comment}"
            else:
                return f"{match.group(1)}{{{formatted_value}}}{comment}"

        new_conf, count = re.subn(pattern, replacer, conf_text, flags=re.DOTALL)
        if count == 0:
            print(f"⚠️ 警告: section '{key}' 未在 baseline.conf 中找到，跳過此修改 / Warning: section '{key}' not found in baseline.conf, skipping this modification")
            return None
        return new_conf

    if "[" in modified_key and "]" in modified_key:
        # e.g. integrity_algorithms[0]
        key = modified_key.split(".")[-1].split("[")[0].strip()
        index = int(modified_key.split("[")[-1].split("]")[0])

        pattern = rf"({key}\s*=\s*\()(.*?)(\);)"
        def replacer(match):
            values_str = match.group(2)
            items = [v.strip() for v in values_str.split(",")]
            if 0 <= index < len(items):
                old_val = items[index].strip().strip("\"")
                new_val = f"\"{error_value}\"" if not str(error_value).startswith("0x") else str(error_value)
                items[index] = new_val
                if original_value is not None:
                    comment = f"  # 修改: 原始值 {old_val} → 錯誤值 {error_value} / Modified: original {old_val} → error {error_value}"
                else:
                    comment = f"  # 修改為 {error_value} / Modified to {error_value}"
                return f"{match.group(1)}{', '.join(items)}{match.group(3)}{comment}"
            return match.group(0)
        new_conf, count = re.subn(pattern, replacer, conf_text, flags=re.DOTALL)
        if count == 0:
            print(f"⚠️ 警告: 陣列參數 '{key}[{index}]' 未在 baseline.conf 中找到，跳過此修改 / Warning: array key '{key}[{index}]' not found in baseline.conf, skipping this modification")
            return None
        return new_conf

    else:
        # 普通的 key = value;
        key = modified_key.split(".")[-1]
        pattern = rf"({key}\s*=\s*)([^;]+)(;)"

        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)

        def replacer(match):
            if original_value is not None:
                comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            else:
                comment = f"  # 修改為 {error_value} / Modified to {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"

        new_conf, count = re.subn(pattern, replacer, conf_text)
        if count == 0:
            print(f"⚠️ 警告: 參數 '{key}' 未在 baseline.conf 中找到，跳過此修改 / Warning: key '{key}' not found in baseline.conf, skipping this modification")
            return None
        return new_conf


def process_case_folder(case_folder_path: str, baseline_text: str):
    """
    處理單一 cases_XX 資料夾
    讀取 cases_delta.json，生成對應的 .conf 檔案
    """
    case_name = os.path.basename(case_folder_path)
    delta_file = os.path.join(case_folder_path, "cases_delta.json")
    
    if not os.path.exists(delta_file):
        print(f"⚠️ 跳過 {case_name}: 找不到 cases_delta.json / Skip {case_name}: cases_delta.json not found")
        return False
    
    # 讀取 cases_delta.json
    try:
        with open(delta_file, "r", encoding="utf-8") as f:
            cases_delta = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ 錯誤: {case_name}/cases_delta.json 格式錯誤 / Error: Invalid JSON in {case_name}/cases_delta.json")
        print(f"   {e}")
        return False
    
    # 尋找 CU 相關的錯誤描述
    cu_case = None
    for case in cases_delta:
        if "cu" in case and isinstance(case["cu"], dict):
            cu_case = case["cu"]
            break
    
    if cu_case is None:
        print(f"⚠️ 跳過 {case_name}: 找不到 CU 錯誤描述 / Skip {case_name}: CU error description not found")
        return False
    
    # 提取必要資訊
    modified_key = cu_case.get("modified_key")
    error_value = cu_case.get("error_value")
    original_value = cu_case.get("original_value")
    
    if modified_key is None or error_value is None:
        print(f"⚠️ 跳過 {case_name}: CU 錯誤描述不完整 / Skip {case_name}: Incomplete CU error description")
        return False
    
    # 生成修改後的 conf
    new_conf = replace_key_value(baseline_text, modified_key, error_value, original_value)
    
    if new_conf is None:
        print(f"❌ 失敗: {case_name} CU conf 生成失敗 / Failed: {case_name} CU conf generation failed")
        return False
    
    # 找出對應的 cu_case_XX.json 檔案名稱
    cu_json_files = glob.glob(os.path.join(case_folder_path, "cu_case_*.json"))
    if cu_json_files:
        json_filename = os.path.basename(cu_json_files[0])
        conf_filename = json_filename.replace(".json", ".conf")
    else:
        # 如果找不到 cu_case_XX.json，使用 case folder 名稱
        conf_filename = f"{case_name}_cu.conf"
    
    # 輸出 .conf 檔案到同一資料夾
    output_path = os.path.join(case_folder_path, conf_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_conf)
    
    # 輸出成功訊息
    print(f"✅ {case_name}/{conf_filename} 已生成 / Generated")
    print(f"   參數修改: {modified_key} → {error_value}")
    print(f"   Parameter modified: {modified_key} → {error_value}")
    
    return True


def main():
    # 載入 baseline.conf
    if not os.path.exists(BASELINE_CONF):
        print(f"❌ 錯誤: 找不到 baseline conf: {BASELINE_CONF}")
        print(f"❌ Error: Baseline conf not found: {BASELINE_CONF}")
        return
    
    with open(BASELINE_CONF, "r", encoding="utf-8") as f:
        baseline_text = f.read()
    
    # 尋找所有 cases_XX 資料夾
    case_folders = sorted(glob.glob(os.path.join(CASES_ROOT, "cases_*")))
    
    if not case_folders:
        print(f"❌ 錯誤: 在 {CASES_ROOT} 找不到 cases_* 資料夾")
        print(f"❌ Error: No cases_* folders found in {CASES_ROOT}")
        return
    
    print(f"🔍 找到 {len(case_folders)} 個 case 資料夾 / Found {len(case_folders)} case folders")
    print("=" * 80)
    
    success_count = 0
    failed_count = 0
    
    for case_folder in case_folders:
        if process_case_folder(case_folder, baseline_text):
            success_count += 1
        else:
            failed_count += 1
        print("-" * 80)
    
    # 總結
    print("=" * 80)
    print(f"📊 處理完成 / Processing completed")
    print(f"   成功 / Success: {success_count}")
    print(f"   失敗 / Failed: {failed_count}")
    print(f"   總計 / Total: {len(case_folders)}")


if __name__ == "__main__":
    main()