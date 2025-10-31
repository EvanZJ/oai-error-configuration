#!/usr/bin/env python3
"""
Filter merged_paired_test_results.jsonl to only include cases with 7, 8, or 9 files in logs folder
"""

import json
import os
from pathlib import Path

def main():
    # Paths
    counts_file = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/file_counts_logs.txt"
    jsonl_file = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/merged_paired_test_results.jsonl"
    backup_file = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/merged_paired_test_results_backup.jsonl"

    # Load file counts
    folder_counts = {}
    with open(counts_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ': ' in line:
                folder, count_str = line.split(': ', 1)
                try:
                    count = int(count_str)
                    folder_counts[folder.rstrip('/')] = count
                except ValueError:
                    continue

    print(f"Loaded {len(folder_counts)} folder counts")

    # Filter records
    filtered_records = []
    total_records = 0

    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            total_records += 1
            record = json.loads(line.strip())
            log_folder = record['metadata']['log_folder']
            count = folder_counts.get(log_folder, 0)
            if count in [7, 8, 9]:
                filtered_records.append(record)

    print(f"Total records: {total_records}")
    print(f"Filtered records: {len(filtered_records)}")

    # Backup original
    if os.path.exists(jsonl_file):
        os.rename(jsonl_file, backup_file)
        print(f"Original file backed up to {backup_file}")

    # Write filtered records
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for record in filtered_records:
            json_line = json.dumps(record, ensure_ascii=False)
            f.write(json_line + '\n')

    print(f"Filtered JSONL written to {jsonl_file}")

if __name__ == "__main__":
    main()
