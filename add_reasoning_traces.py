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
    output_file = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/merged_training_with_traces.jsonl"

    # Read all entries from the training file
    entries = []
    with open(training_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                correct_param = data.get('correct_param', '')
                # Extract just the parameter name (before the =)
                param_name = correct_param.split('=')[0] if '=' in correct_param else correct_param
                entries.append((line_num, param_name, data))
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue

    print(f"Found {len(entries)} entries in training file")

    # Process each entry and add reasoning traces if matched
    with open(output_file, 'w') as out_f:
        for i, (line_num, expected_param, data) in enumerate(entries):
            trace_folder = f"trace_{i:04d}"
            trace_path = os.path.join(reasoning_outputs_dir, trace_folder)
            response_file = os.path.join(trace_path, "copilot_response.md")

            if os.path.exists(response_file):
                try:
                    with open(response_file, 'r') as f:
                        content = f.read()

                    actual_params = extract_parameter_from_fix_section(content)

                    if actual_params and expected_param in actual_params:
                        # Add the reasoning trace
                        data['reasoning_traces'] = content
                        print(f"Added reasoning trace for line {line_num} (index {i})")
                    else:
                        print(f"No match for line {line_num} (index {i}), expected '{expected_param}', got '{actual_params}'")
                except Exception as e:
                    print(f"Error processing {response_file}: {e}")
            else:
                print(f"Missing response file: {response_file}")

            # Write the updated data to the output file only if reasoning_traces was added
            if 'reasoning_traces' in data:
                out_f.write(json.dumps(data) + '\n')

    print(f"Output written to {output_file}")

if __name__ == "__main__":
    main()