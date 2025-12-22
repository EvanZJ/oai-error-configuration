import json
import os

# Path to the original cases_delta.json
original_file = '/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output/cases_01/cases_delta.json'

# Output directory
output_dir = '/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output'

# Load the JSON data
with open(original_file, 'r') as f:
    cases = json.load(f)

# For each case, create a folder and save the case
for case in cases:
    case_num = case['filename'].replace('case_', '').replace('.json', '').zfill(3)
    case_folder = os.path.join(output_dir, f'case_{case_num}')
    os.makedirs(case_folder, exist_ok=True)
    
    case_file = os.path.join(case_folder, 'cases_delta.json')
    with open(case_file, 'w') as f:
        json.dump([case], f, indent=2)

print("Individual case folders created.")