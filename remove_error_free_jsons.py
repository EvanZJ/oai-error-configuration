import csv
import os

def remove_json_files(csv_file, json_dir, prefix):
    """
    Remove .json files where is_error == '0' in the CSV.
    
    Args:
        csv_file (str): Path to the CSV file
        json_dir (str): Path to the directory with .json files
        prefix (str): Prefix for the filename, e.g., 'cu_case' or 'du_case'
    """
    if not os.path.exists(csv_file):
        print(f"CSV file {csv_file} does not exist.")
        return
    
    with open(csv_file, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get('is_error') == '0':
                case = row.get('case')
                if case:
                    # Construct filename: e.g., cu_case_cu_case_01_new_format.json
                    filename = f"{prefix}_{case}_new_format.json"
                    filepath = os.path.join(json_dir, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        print(f"Removed: {filepath}")
                    else:
                        print(f"File not found: {filepath}")

if __name__ == "__main__":
    # Paths
    base_dir = "/home/sionna/evan/CursorAutomation/cursor_gen_conf"
    
    # For CU
    cu_csv = os.path.join(base_dir, "is_error_cu.csv")
    cu_json_dir = os.path.join(base_dir, "compiled_cu_cases")
    remove_json_files(cu_csv, cu_json_dir, "cu_case")
    
    # For DU
    du_csv = os.path.join(base_dir, "is_error_du.csv")
    du_json_dir = os.path.join(base_dir, "compiled_du_cases")
    remove_json_files(du_csv, du_json_dir, "du_case")
