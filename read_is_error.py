import csv
import os

def read_is_error_csv(file_path):
    """
    Reads the is_error.csv file and extracts the 'case' and 'is_error' columns.
    
    Args:
        file_path (str): Path to the is_error.csv file
    
    Returns:
        list: List of dictionaries with 'case' and 'is_error' keys
    """
    data = []
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return data
    
    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'case' in row and 'is_error' in row:
                data.append({
                    'case': row['case'],
                    'is_error': row['is_error']
                })
            else:
                print("Warning: 'case' or 'is_error' column not found in row.")
    
    return data

def find_case_folder(logs_path, case_name):
    """
    Finds the folder in logs_path that corresponds to the case_name.
    
    Args:
        logs_path (str): Path to the logs_batch_run directory
        case_name (str): The case name, e.g., 'cu_case_1'
    
    Returns:
        str: Path to the matching folder, or None if not found
    """
    if not os.path.exists(logs_path):
        return None
    
    parts = case_name.split('_')
    if len(parts) != 3 or parts[1] != 'case' or parts[0] not in ['cu', 'du']:
        return None
    
    try:
        number = int(parts[2])
    except ValueError:
        return None
    
    padded = str(number).zfill(2)
    target_suffix = f"_{parts[0]}_case_{padded}"
    
    for folder in os.listdir(logs_path):
        folder_path = os.path.join(logs_path, folder)
        if os.path.isdir(folder_path) and folder.endswith(target_suffix):
            return folder_path
    return None

def count_files_in_folder(folder_path):
    """
    Counts the number of files in the given folder.
    
    Args:
        folder_path (str): Path to the folder
    
    Returns:
        int: Number of files
    """
    if not os.path.exists(folder_path):
        return 0
    
    return len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])

if __name__ == "__main__":
    # Path to the logs_batch_run directory
    logs_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/logs_batch_run"
    
    # Process both cu and du
    for case_type in ['cu', 'du']:
        file_path = f"/home/sionna/evan/CursorAutomation/cursor_gen_conf/is_error_{case_type}.csv"
        
        # Read the data
        data = read_is_error_csv(file_path)
        
        # Update is_error based on file count
        for item in data:
            case = item['case']
            folder_path = find_case_folder(logs_path, case)
            if folder_path:
                file_count = count_files_in_folder(folder_path)
                item['is_error'] = '0' if file_count == 10 else '1'
        
        # Write back to CSV
        if data:
            with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        
        # Print the results
        print(f"\nProcessing {case_type.upper()} cases:")
        for item in data:
            case = item['case']
            is_error = item['is_error']
            folder_path = find_case_folder(logs_path, case)
            file_count = count_files_in_folder(folder_path) if folder_path else 0
            print(f"Case: {case}, Is Error: {is_error}, Folder: {folder_path}, File Count: {file_count}")
