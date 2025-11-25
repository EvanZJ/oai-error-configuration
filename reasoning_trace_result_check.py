import os
import json
import re

def extract_parameter_from_fix_section(content):
    """Extract the parameters from the Configuration Fix section."""
    # Find the Configuration Fix section
    fix_match = re.search(r'\*\*Configuration Fix\*\*:\s*```json\s*(.*?)\s*```', content, re.DOTALL)
    if fix_match:
        try:
            fix_json = json.loads(fix_match.group(1).strip())
            # The fix is a dict with parameter keys
            if isinstance(fix_json, dict) and len(fix_json) > 0:
                params = []
                for param_key in fix_json.keys():
                    # Remove the prefix "du_conf." or "cu_conf." if present
                    if param_key.startswith('du_conf.'):
                        param_key = param_key[8:]  # Remove 'du_conf.'
                    elif param_key.startswith('cu_conf.'):
                        param_key = param_key[8:]  # Remove 'cu_conf.'
                    params.append(param_key)
                return params
        except json.JSONDecodeError:
            pass
    return []

def main():
    # Path to the merged training file
    training_file = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/merged_training.jsonl"
    reasoning_outputs_dir = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/reasoning_outputs"

    # Read all correct parameters from the training file
    correct_params = []
    with open(training_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                correct_param = data.get('correct_param', '')
                # Extract just the parameter name (before the =)
                param_name = correct_param.split('=')[0] if '=' in correct_param else correct_param
                correct_params.append((line_num, param_name))
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue

    print(f"Found {len(correct_params)} entries in training file")

    # Check each trace folder
    mismatches = []
    matches = []

    for i, (line_num, expected_param) in enumerate(correct_params, 0):
        trace_folder = f"trace_{i:04d}"
        trace_path = os.path.join(reasoning_outputs_dir, trace_folder)
        response_file = os.path.join(trace_path, "copilot_response.md")

        if not os.path.exists(response_file):
            print(f"Missing response file: {response_file}")
            continue

        try:
            with open(response_file, 'r') as f:
                content = f.read()

            actual_params = extract_parameter_from_fix_section(content)

            if not actual_params:
                print(f"Could not extract parameters from {response_file}")
                continue

            # Check if the expected parameter is in the list of suggested parameters
            if expected_param in actual_params:
                matches.append((i, expected_param, actual_params))
            else:
                mismatches.append((i, expected_param, actual_params))

        except Exception as e:
            print(f"Error processing {response_file}: {e}")
            continue

    # Print results
    print(f"\nMatches: {len(matches)}")
    print(f"Mismatches: {len(mismatches)}")

    if mismatches:
        print("\nMismatches found:")
        for line_num, expected, actual in mismatches:
            print(f"Line {line_num}: Expected '{expected}', Got '{actual}'")

    if matches:
        print(f"\nAll matches:")
        for line_num, expected, actual in matches:
            print(f"Line {line_num}: '{expected}'")

if __name__ == "__main__":
    main()