#!/usr/bin/env python3
"""
根據 cases_delta.json 中的錯誤描述，修改 baseline DU conf 並輸出新的錯誤 conf
處理 multiple_parameter/output/cases_XX 資料夾結構
每個修改的地方會自動加上中英雙語註解
"""

import os
import json
import re
import glob

BASELINE_CONF = r"/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/du_gnb.conf"
CASES_ROOT = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output"


def replace_key_value(conf_text: str, modified_key: str, error_value, original_value=None) -> str:
    """
    根據 modified_key 在 conf_text 裡替換值，並加上中英對照註解
    支援:
      - 普通 key = value;
      - 陣列元素 key[index]
      - 巢狀結構 key[index].subkey
    """

    # Special case for gNBs[0].* and fhi_72.fh_config[0].* - search directly in conf_text
    # Only for simple parameters, not array elements
    if (modified_key.startswith("gNBs[0].") or modified_key.startswith("fhi_72.fh_config[0].")) and "[" not in modified_key.split(".")[-1]:
        # Extract the final key name (everything after the last dot)
        final_key = modified_key.split(".")[-1]
        pattern = rf"({final_key}\s*=\s*)([^;]+)(;)"

        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)

        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"

        result = re.sub(pattern, replacer, conf_text)
        if result != conf_text:
            return result
        else:
            print(f"⚠️ 警告: 參數 '{final_key}' 未找到 / Warning: parameter '{final_key}' not found")
            return None

    # case: plmn_list[0].mnc_length
    if "[" in modified_key and "]" in modified_key and "." in modified_key.split("]")[-1]:
        block_name = modified_key.split("[")[0]
        index = int(modified_key.split("[")[-1].split("]")[0])
        subkey = modified_key.split("].")[-1]

        # 找 block
        pattern = rf"({block_name}\s*=\s*\(\s*{{.*?}}\s*\);)"
        matches = list(re.finditer(pattern, conf_text, flags=re.DOTALL))
        if not matches:
            print(f"⚠️ 警告: 區塊 '{block_name}' 未找到 / Warning: block '{block_name}' not found")
            return None

        # 取 index-th block
        if index >= len(matches):
            print(f"⚠️ 警告: 索引 {index} 超出範圍 / Warning: index {index} out of range")
            return None
            
        match = matches[index]
        block_text = match.group(1)

        # 替換 block 內部 subkey
        sub_pattern = rf"({subkey}\s*=\s*)([^;]+)(;)"
        def sub_replacer(m):
            old_val = m.group(2).strip()
            if isinstance(error_value, str) and not error_value.startswith("0x"):
                new_val = f"\"{error_value}\""
            else:
                new_val = str(error_value)
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{m.group(1)}{new_val}{m.group(3)}{comment}"

        new_block, count = re.subn(sub_pattern, sub_replacer, block_text)
        if count == 0:
            print(f"⚠️ 警告: 子參數 '{subkey}' 未在 {block_name}[{index}] 中找到 / Warning: subkey '{subkey}' not found in {block_name}[{index}]")
            return None

        # 替換回去
        return conf_text[:match.start()] + new_block + conf_text[match.end():]

    # case: key[index]
    elif "[" in modified_key and "]" in modified_key:
        key = modified_key.split(".")[-1].split("[")[0].strip()
        index = int(modified_key.split("[")[-1].split("]")[0])

        pattern = rf"({key}\s*=\s*\()(.*?)(\);)"
        def replacer(match):
            items = [v.strip() for v in match.group(2).split(",")]
            if 0 <= index < len(items):
                old_val = items[index].strip().strip("\"")
                new_val = f"\"{error_value}\"" if not str(error_value).startswith("0x") else str(error_value)
                items[index] = new_val
                comment = f"  # 修改: 原始值 {old_val} → 錯誤值 {error_value} / Modified: original {old_val} → error {error_value}"
                return f"{match.group(1)}{', '.join(items)}{match.group(3)}{comment}"
            return match.group(0)
        
        result, count = re.subn(pattern, replacer, conf_text, flags=re.DOTALL)
        if count == 0:
            print(f"⚠️ 警告: 陣列參數 '{key}[{index}]' 未找到 / Warning: array parameter '{key}[{index}]' not found")
            return None
        return result

    else:
        # 普通 key = value; or block structures
        key = modified_key.split(".")[-1]
        
        # Special handling for None values on block structures
        if error_value is None:
            # Check if this is a block structure like fhi_72 = { ... }; or log_config : { ... };
            block_start_pattern = rf"({key}\s*[=:]\s*\{{)"
            start_match = re.search(block_start_pattern, conf_text)
            if start_match:
                # Find the matching closing brace
                start_pos = start_match.end() - 1  # Position of the opening brace
                brace_count = 1
                pos = start_pos + 1
                
                while pos < len(conf_text) and brace_count > 0:
                    if conf_text[pos] == '{':
                        brace_count += 1
                    elif conf_text[pos] == '}':
                        brace_count -= 1
                    pos += 1
                
                if brace_count == 0:  # Found matching closing brace
                    end_pos = pos
                    # Replace the entire block
                    replacement = f"{key} = NULL;  // 修改: 原始值 {original_value} → 錯誤值 NULL / Modified: original {original_value} → error NULL"
                    return conf_text[:start_match.start()] + replacement + conf_text[end_pos:]
        
        # Regular key-value replacement
        pattern = rf"({key}\s*=\s*)([^;]+)(;)"

        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        elif error_value is None:
            formatted_value = "NULL"
        else:
            formatted_value = str(error_value)

        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"

        result, count = re.subn(pattern, replacer, conf_text)
        if count == 0:
            print(f"⚠️ 警告: 參數 '{key}' 未找到 / Warning: parameter '{key}' not found")
            return None
        return result


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
    
    # 尋找 DU 相關的錯誤描述
    du_case = None
    for case in cases_delta:
        if "du" in case and isinstance(case["du"], dict):
            du_case = case["du"]
            break
    
    if du_case is None:
        print(f"⚠️ 跳過 {case_name}: 找不到 DU 錯誤描述 / Skip {case_name}: DU error description not found")
        return False
    
    # 提取必要資訊
    modified_key = du_case.get("modified_key")
    error_value = du_case.get("error_value")
    original_value = du_case.get("original_value")
    
    if modified_key is None or error_value is None:
        print(f"⚠️ 跳過 {case_name}: DU 錯誤描述不完整 / Skip {case_name}: Incomplete DU error description")
        return False
    
    # 生成修改後的 conf
    new_conf = replace_key_value(baseline_text, modified_key, error_value, original_value)
    
    if new_conf is None:
        print(f"❌ 失敗: {case_name} DU conf 生成失敗 / Failed: {case_name} DU conf generation failed")
        return False
    
    # 找出對應的 du_case_XX.json 檔案名稱
    du_json_files = glob.glob(os.path.join(case_folder_path, "du_case_*.json"))
    if du_json_files:
        json_filename = os.path.basename(du_json_files[0])
        conf_filename = json_filename.replace(".json", ".conf")
    else:
        # 如果找不到 du_case_XX.json，使用 case folder 名稱
        conf_filename = f"{case_name}_du.conf"
    
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