#!/usr/bin/env python3
"""
批次處理多個 cases_XX 資料夾，根據 cases_delta.json 中的 CU 配置
修改 cu_gnb.conf 並輸出 cu_case.conf，每個修改處會自動加上中英雙語註解
"""

import os
import json
import re
import argparse

# 預設路徑
DEFAULT_CASES_ROOT = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/one_parameter/output/du"
DEFAULT_CU_BASELINE = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/du_gnb.conf"


def _find_block_span(conf_text: str, block_name: str, index: int):
    """Return (start, end) span in conf_text for block `block_name = ( ... );` at given occurrence index."""
    pattern = rf"{re.escape(block_name)}\s*=\s*\("
    matches = list(re.finditer(pattern, conf_text))
    if index >= len(matches):
        return None
    open_paren_pos = matches[index].end() - 1

    depth = 0
    pos = open_paren_pos
    end_pos = None
    while pos < len(conf_text):
        ch = conf_text[pos]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                end_pos = pos
                break
        pos += 1

    if end_pos is None:
        return None

    tail_pos = end_pos + 1
    while tail_pos < len(conf_text) and conf_text[tail_pos].isspace():
        tail_pos += 1
    if tail_pos < len(conf_text) and conf_text[tail_pos] == ';':
        tail_pos += 1

    start_of_block = matches[index].start()
    end_of_block = tail_pos
    return (start_of_block, end_of_block)


def replace_key_value(conf_text: str, modified_key: str, error_value, original_value=None) -> str:
    """根據 modified_key 在 conf_text 裡替換值，並加上中英對照註解"""

    # 特殊處理: gNBs[0].servingCellConfigCommon[0].subkey
    if "gNBs[0].servingCellConfigCommon[0]." in modified_key:
        subkey = modified_key.split("gNBs[0].servingCellConfigCommon[0].")[-1]
        pattern = rf"({subkey}\s*=\s*)([^;]+)(;)"

        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)

        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"

        new_text, count = re.subn(pattern, replacer, conf_text)
        if count == 0:
            key = subkey.split(".")[-1]
            global_pattern = rf"({re.escape(key)}\s*=\s*)([^;]+)(;)"

            def global_replacer(m):
                return f"{m.group(1)}{formatted_value}{m.group(3)}  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"

            conf_text_after, global_count = re.subn(global_pattern, global_replacer, conf_text)
            if global_count == 0:
                print(f"[WARN] 子參數 '{subkey}' 未在 gNBs[0] 中找到，且無全域鍵可用 / Warning: subkey '{subkey}' not found")
                return conf_text
            return conf_text_after
        return new_text

    # 特殊處理: fhi_72.fh_config[0].subkey
    if "fhi_72.fh_config[0]." in modified_key:
        subkey = modified_key.split("fhi_72.fh_config[0].")[-1]
        pattern = rf"({subkey}\s*=\s*)([^;]+)(;)"
        
        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)
        
        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"
        
        new_text, count = re.subn(pattern, replacer, conf_text)
        if count == 0:
            print(f"[WARN] 區塊 'fhi_72.fh_config' 未找到 / Warning: block 'fhi_72.fh_config' not found")
            return conf_text
        return new_text

    # case: plmn_list[0].mnc_length
    if "[" in modified_key and "]" in modified_key and "." in modified_key.split("]")[-1]:
        block_name = modified_key.split("[")[0]
        index = int(modified_key.split("[")[-1].split("]")[0])
        subkey = modified_key.split("].")[-1]

        span = _find_block_span(conf_text, block_name, index)
        if span is None:
            exists_first = _find_block_span(conf_text, block_name, 0) is not None
            if not exists_first:
                print(f"[WARN] 區塊 '{block_name}' 未找到 / Warning: block '{block_name}' not found")
            else:
                print(f"[WARN] 區塊 '{block_name}[{index}]' 超出索引 / Warning: block '{block_name}[{index}]' out of range")
            return conf_text
        start_idx, end_idx = span
        block_text = conf_text[start_idx:end_idx]

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
            key = subkey.split(".")[-1]
            global_pattern = rf"({re.escape(key)}\s*=\s*)([^;]+)(;)"

            if isinstance(error_value, str) and not str(error_value).startswith("0x"):
                global_new_val = f'"{error_value}"'
            else:
                global_new_val = str(error_value)

            def global_replacer(m):
                return f"{m.group(1)}{global_new_val}{m.group(3)}  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"

            conf_text_after, global_count = re.subn(global_pattern, global_replacer, conf_text)
            if global_count == 0:
                print(f"[WARN] 子參數 '{subkey}' 未在 {block_name}[{index}] 或全域中找到 / Warning: subkey '{subkey}' not found")
                return conf_text
            return conf_text_after

        return conf_text[:start_idx] + new_block + conf_text[end_idx:]

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
        return re.sub(pattern, replacer, conf_text, flags=re.DOTALL)

    else:
        # 普通 key = value;
        key = modified_key.split(".")[-1]
        pattern = rf"({key}\s*=\s*)([^;]+)(;)"

        if isinstance(error_value, str) and not error_value.startswith("0x"):
            formatted_value = f"\"{error_value}\""
        else:
            formatted_value = str(error_value)

        def replacer(match):
            comment = f"  # 修改: 原始值 {original_value} → 錯誤值 {error_value} / Modified: original {original_value} → error {error_value}"
            return f"{match.group(1)}{formatted_value}{match.group(3)}{comment}"

        return re.sub(pattern, replacer, conf_text)


def get_case_folders(root_path):
    """Get all cases_XX folders sorted by number"""
    case_folders = []
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path) and item.startswith("du_cases_"):
            case_folders.append(item_path)
    return sorted(case_folders)


def process_case_folder(case_folder, cu_baseline_text):
    """Process a single case folder and generate cu_case.conf"""
    delta_file = os.path.join(case_folder, "cases_delta.json")
    
    if not os.path.exists(delta_file):
        print(f"[SKIP] {os.path.basename(case_folder)}: No cases_delta.json found")
        return False
    
    with open(delta_file, "r", encoding="utf-8") as f:
        case_data = json.load(f)
    
    # Handle both single object and array format
    if isinstance(case_data, list):
        if len(case_data) == 0:
            print(f"[SKIP] {os.path.basename(case_folder)}: Empty cases_delta.json")
            return False
        case = case_data[0]  # Take first element if it's an array
    else:
        case = case_data  # Single object
    
    case_folder_name = os.path.basename(case_folder)
    
    # Extract case number from folder name (e.g., "cases_01" -> "01")
    case_number = case_folder_name.split("_")[-1]
    
    cu_case = case
    if not isinstance(cu_case, dict):
        print(f"[SKIP] {case_folder_name}: Missing CU keys")
        return False
    
    modified_key = cu_case.get("modified_key", None)
    error_value = cu_case.get("error_value", None) 
    original_value = cu_case.get("original_value", None)
    
    if not modified_key or error_value is None:
        print(f"[SKIP] {case_folder_name}: Missing CU keys")
        return False
    
    # Replace in baseline
    new_cu_conf = replace_key_value(cu_baseline_text, modified_key, error_value, original_value)
    
    # Write cu_case_XX.conf directly in the case folder with numbering
    cu_output_filename = f"du_cases_{case_number}.conf"
    cu_output_path = os.path.join(case_folder, cu_output_filename)
    with open(cu_output_path, "w", encoding="utf-8") as f:
        f.write(new_cu_conf)
    
    print(f"  ✅ {case_folder_name}/{cu_output_filename}")
    print(f"     {modified_key} → {error_value}")
    
    return True


def parse_args():
    parser = argparse.ArgumentParser(description="Batch generate cu_case.conf files from cases_delta.json")
    parser.add_argument("--cases-root", default=DEFAULT_CASES_ROOT, 
                        help="Root directory containing cases_XX folders")
    parser.add_argument("--cu-baseline", default=DEFAULT_CU_BASELINE, 
                        help="Path to baseline cu_gnb.conf")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.cases_root):
        print(f"❌ Cases root directory not found: {args.cases_root}")
        return

    if not os.path.exists(args.cu_baseline):
        print(f"❌ CU baseline not found: {args.cu_baseline}")
        return

    # Load CU baseline
    print(f"📖 Loading CU baseline: {args.cu_baseline}")
    with open(args.cu_baseline, "r", encoding="utf-8") as f:
        cu_baseline_text = f.read()

    # Get all case folders
    case_folders = get_case_folders(args.cases_root)
    
    if not case_folders:
        print(f"❌ No cases_XX folders found in {args.cases_root}")
        return

    print(f"\n🚀 Found {len(case_folders)} case folders to process")
    print("="*80)

    success_count = 0
    skip_count = 0

    # Process each case folder
    for case_folder in case_folders:
        if process_case_folder(case_folder, cu_baseline_text):
            success_count += 1
        else:
            skip_count += 1

    # Summary
    print("\n" + "="*80)
    print("📊 BATCH PROCESSING SUMMARY (CU)")
    print("="*80)
    print(f"Total case folders: {len(case_folders)}")
    print(f"✅ Successfully generated: {success_count}")
    print(f"⏭️  Skipped: {skip_count}")
    print(f"Output: {args.cases_root}/cases_XX/cu_case_XX.conf")
    print("="*80)


if __name__ == "__main__":
    main()