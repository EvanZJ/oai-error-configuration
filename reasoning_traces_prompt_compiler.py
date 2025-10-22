import json
import os
import time
import sys
import threading
import subprocess
import pyautogui
import pyperclip
from pathlib import Path

# Paths
cu_output_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/cu_output/json/"
du_output_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/du_output/json/"
baseline_conf_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf_json/"
logs_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/logs_batch_run/"
prompt_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/reasoning_prompt.md"
output_trace_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/reasoning_trace/"

# Create output directory if it doesn't exist
os.makedirs(output_trace_path, exist_ok=True)

# Wait time for Copilot to generate response (adjust based on analysis complexity)
COPILOT_WAIT_TIME = 600  # 10 minutes for analysis + file creation

# Mouse mover to prevent screen sleep
stop_mouse_mover = False

def mouse_mover():
    global stop_mouse_mover
    x, y = pyautogui.position()
    while not stop_mouse_mover:
        try:
            pyautogui.moveTo(x + 100, y)
            time.sleep(0.4)
            pyautogui.moveTo(x, y)
            time.sleep(5)
        except Exception as e:
            print(f"Mouse mover error: {e}")
            time.sleep(5)

def start_mouse_mover():
    global stop_mouse_mover
    stop_mouse_mover = False
    mouse_thread = threading.Thread(target=mouse_mover, daemon=True)
    mouse_thread.start()
    print("🖱️  Mouse mover started")
    return mouse_thread

def stop_mouse_mover_thread():
    global stop_mouse_mover
    stop_mouse_mover = True
    print("🖱️  Mouse mover stopped")

# Window Management Functions
def is_vscode_window_active():
    try:
        if sys.platform.startswith("linux"):
            active_window = subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'], text=True)
            win_id = active_window.split()[-1]
            window_info = subprocess.check_output(['xprop', '-id', win_id, 'WM_NAME'], text=True)
            window_title = window_info.split('"')[1].lower() if '"' in window_info else ""
            return any(k in window_title for k in ["visual studio code", "code -", "vscode"])
        else:
            import pygetwindow as gw
            active_window = gw.getActiveWindow()
            if active_window:
                return any(k in active_window.title.lower() for k in ["visual studio code", "code -", "vscode"])
            return False
    except Exception as e:
        print(f"is_vscode_window_active failed: {e}")
        return False

def find_vscode_window():
    try:
        if sys.platform.startswith("linux"):
            output = subprocess.check_output(['wmctrl', '-l'], text=True)
            for line in output.splitlines():
                if any(k in line.lower() for k in ["visual studio code", "code -", "vscode"]):
                    win_id = line.split()[0]
                    subprocess.run(['wmctrl', '-ia', win_id])
                    time.sleep(0.5)
                    return True
        else:
            import pygetwindow as gw
            for window in gw.getAllWindows():
                if any(k in window.title.lower() for k in ["visual studio code", "code -", "vscode"]) and window.visible:
                    if window.isMinimized:
                        window.restore()
                    window.activate()
                    time.sleep(0.5)
                    return True
    except Exception as e:
        print(f"find_vscode_window failed: {e}")
        return False
    return False

def ensure_vscode_active():
    for _ in range(3):
        if is_vscode_window_active():
            return True
        if find_vscode_window():
            time.sleep(1)
    return False

# Copilot Integration Functions
def send_prompt_to_copilot(prompt):
    """Send a prompt to Copilot and wait for it to create the file"""
    try:
        # Ensure VS Code is active
        if not ensure_vscode_active():
            print("❌ Could not activate VS Code")
            return False

        time.sleep(1)
        
        # Open Copilot chat with Ctrl+Shift+Alt+I
        print("💬 Opening Copilot chat...")
        pyautogui.hotkey('ctrl', 'shift', 'alt', 'i')
        time.sleep(2)

        # Paste prompt
        print("📋 Pasting prompt...")
        pyperclip.copy(prompt)
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        pyautogui.press('enter')

        # Wait for Copilot to generate and create the file
        print(f"⏳ Waiting {COPILOT_WAIT_TIME} seconds for Copilot to analyze and create file...")
        time.sleep(COPILOT_WAIT_TIME)
        
        return True
    except Exception as e:
        print(f"❌ Error sending prompt to Copilot: {e}")
        return False

def wait_for_file_creation(case_filename, timeout=600, check_interval=1):
    """Wait for Copilot to create the output file - checks every second"""
    output_file = os.path.join(output_trace_path, f"{case_filename}.txt")
    start_time = time.time()
    last_size = 0
    stable_count = 0
    last_print_time = start_time
    
    print(f"👀 Watching for file: {output_file}")
    print(f"⏱️  Will check every {check_interval} second(s), timeout after {timeout} seconds")
    
    while time.time() - start_time < timeout:
        elapsed = int(time.time() - start_time)
        
        # Print progress every 10 seconds
        if time.time() - last_print_time >= 10:
            print(f"⏳ Still waiting... ({elapsed}s elapsed)")
            last_print_time = time.time()
        
        if os.path.exists(output_file):
            current_size = os.path.getsize(output_file)
            if current_size > 0:
                # File detected for the first time
                if last_size == 0:
                    print(f"📄 File detected! Size: {current_size} bytes")
                
                # Check if file size is stable (file writing completed)
                if current_size == last_size:
                    stable_count += 1
                    if stable_count >= 3:  # Stable for 3 consecutive checks
                        print(f"✅ File creation completed: {current_size} bytes (took {elapsed}s)")
                        return True
                else:
                    # File still growing
                    if last_size > 0:  # Only print if we've seen it before
                        print(f"📝 File growing: {last_size} -> {current_size} bytes")
                    stable_count = 0
                    last_size = current_size
        
        time.sleep(check_interval)
    
    print(f"⏰ Timeout waiting for file after {timeout} seconds")
    return False

def build_temp_json2(case):
    """Build the temp_json structure for a case"""
    temp_json = {}
    temp_json["misconfigured_param"] = f"{case['modified_key']}={case['error_value']}"
    temp_json["original_param"] = f"{case['modified_key']}={case['original_value']}"
    temp_json["logs"] = {}
    
    # Find log folder
    dirs = [d for d in os.listdir(logs_path)]
    cur_folder = ""
    for dir in dirs:
        if case["filename"].split(".")[0] in dir:
            cur_folder = dir
            break
    
    if cur_folder == "":
        print(f"⚠️  No logs found for case: {case['filename']}")
        return None
    
    # Load logs
    temp_json["logs"]["CU"] = []
    temp_json["logs"]["DU"] = []
    temp_json["logs"]["UE"] = []
    
    summary_file = os.path.join(logs_path, cur_folder, "tail100_summary.json")
    if os.path.exists(summary_file):
        with open(summary_file, "r") as f:
            summary = json.load(f)
            temp_json["logs"]["CU"] = summary.get("CU", [])
            temp_json["logs"]["DU"] = summary.get("DU", [])
            temp_json["logs"]["UE"] = summary.get("UE", [])
    
    # Load network config
    temp_json["network_config"] = {}
    with open(os.path.join(baseline_conf_path, "cu_gnb.json"), "r") as f:
        temp_json["network_config"]["cu_conf"] = json.load(f)
    with open(os.path.join(du_output_path, case["filename"]), "r") as f:
        temp_json["network_config"]["du_conf"] = json.load(f)
    with open(os.path.join(baseline_conf_path, "ue.json"), "r") as f:
        temp_json["network_config"]["ue_conf"] = json.load(f)
    
    # Save to compiled folder
    compiled_folder = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/compiled_du_cases/"
    os.makedirs(compiled_folder, exist_ok=True)
    case_filename = case["filename"].split(".")[0]
    compiled_file_path = os.path.join(compiled_folder, f"du_case_{case_filename}_new_format.json")
    with open(compiled_file_path, "w") as f:
        json.dump(temp_json, f, indent=2)
    
    return temp_json

def build_temp_json(case):
    """Build the temp_json structure for a case"""
    temp_json = {}
    temp_json["misconfigured_param"] = f"{case['modified_key']}={case['error_value']}"
    temp_json["original_param"] = f"{case['modified_key']}={case['original_value']}"
    temp_json["logs"] = {}
    
    # Find log folder
    dirs = [d for d in os.listdir(logs_path)]
    cur_folder = ""
    for dir in dirs:
        if case["filename"].split(".")[0] in dir:
            cur_folder = dir
            break
    
    if cur_folder == "":
        print(f"⚠️  No logs found for case: {case['filename']}")
        return None
    
    # Load logs
    temp_json["logs"]["CU"] = []
    temp_json["logs"]["DU"] = []
    temp_json["logs"]["UE"] = []
    
    summary_file = os.path.join(logs_path, cur_folder, "tail100_summary.json")
    if os.path.exists(summary_file):
        with open(summary_file, "r") as f:
            summary = json.load(f)
            temp_json["logs"]["CU"] = summary.get("CU", [])
            temp_json["logs"]["DU"] = summary.get("DU", [])
            temp_json["logs"]["UE"] = summary.get("UE", [])
    
    # Load network config
    temp_json["network_config"] = {}
    with open(os.path.join(cu_output_path, case["filename"]), "r") as f:
        temp_json["network_config"]["cu_conf"] = json.load(f)
    with open(os.path.join(baseline_conf_path, "du_gnb.json"), "r") as f:
        temp_json["network_config"]["du_conf"] = json.load(f)
    with open(os.path.join(baseline_conf_path, "ue.json"), "r") as f:
        temp_json["network_config"]["ue_conf"] = json.load(f)
        
    # Save to compiled folder
    compiled_folder = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/compiled_cu_cases/"
    os.makedirs(compiled_folder, exist_ok=True)
    case_filename = case["filename"].split(".")[0]
    compiled_file_path = os.path.join(compiled_folder, f"cu_case_{case_filename}_new_format.json")
    with open(compiled_file_path, "w") as f:
        json.dump(temp_json, f, indent=2)
    
    return temp_json

def create_prompt_for_case(case, temp_json):
    """Create the full prompt for a case"""
    case_filename = case["filename"].split(".")[0]
    
    # Load prompt template
    with open(prompt_path, "r") as f:
        prompt_template = f.read()
    
    # Replace placeholders
    prompt = prompt_template.replace("{temp_json}", json.dumps(temp_json, indent=2))
    prompt = prompt.replace("{case_filename}", case_filename)
    
    # Add instruction to save to file
    prompt += f"\n\nPlease create the file at: {output_trace_path}{case_filename}.txt"
    
    return prompt, case_filename

def check_if_output_exists(case_filename):
    """Check if output file already exists and has content"""
    output_file = os.path.join(output_trace_path, f"{case_filename}.txt")
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        return size > 100  # Consider valid if > 100 bytes
    return False

def save_response_to_output(case_filename, response_content):
    """Verify the output file was created by Copilot"""
    output_file = os.path.join(output_trace_path, f"{case_filename}.txt")
    try:
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content) > 100:
                print(f"✅ Verified file created by Copilot: {output_file} ({len(content)} characters)")
                return True
            else:
                print(f"⚠️  File exists but is too small: {len(content)} characters")
                return False
        else:
            print(f"❌ File not created: {output_file}")
            return False
    except Exception as e:
        print(f"❌ Error verifying {output_file}: {e}")
        return False

def main2():
    """Main automation function"""
    print("🚀 Starting 5G Analysis Copilot Automation...")
    print("=" * 80)
    
    # Load cases
    try:
        with open(os.path.join(du_output_path, "cases_delta.json"), "r") as f:
            cases_delta = json.load(f)
    except Exception as e:
        print(f"❌ Error loading cases_delta.json: {e}")
        return
    
    print(f"📊 Found {len(cases_delta)} cases to process\n")
    
    # Check VS Code availability
    if not find_vscode_window():
        print("❌ Could not find VS Code window. Please open VS Code.")
        return
    
    # Start mouse mover
    mouse_thread = start_mouse_mover()
    
    processed_cases = []
    skipped_cases = []
    failed_cases = []
    
    try:
        for i, case in enumerate(cases_delta, 1):
            print("\n" + "=" * 80)
            print(f"📝 Processing case {i}/{len(cases_delta)}: {case['filename']}")
            print(f"   Modified: {case['modified_key']}={case['error_value']}")
            print("=" * 80)
            
            case_filename = case["filename"].split(".")[0]
            
            # Check if already processed
            # if check_if_output_exists(case_filename):
            #     print(f"⏭️  Skipping (already exists): {case_filename}.txt")
            #     skipped_cases.append(case['filename'])
            #     continue
            
            # Build temp_json
            temp_json = build_temp_json2(case)
            # if temp_json is None:
            #     print(f"⚠️  Skipping case (no logs): {case['filename']}")
            #     skipped_cases.append(case['filename'])
            #     continue
            
            # # Create prompt
            # prompt, case_filename = create_prompt_for_case(case, temp_json)
            
            # print(f"📏 Prompt length: {len(prompt)} characters")
            
            # # Send to Copilot
            # if send_prompt_to_copilot(prompt):
            #     # Wait for Copilot to create the file
            #     if wait_for_file_creation(case_filename, timeout=COPILOT_WAIT_TIME + 60):
            #         # Verify the file was created successfully
            #         if save_response_to_output(case_filename, None):
            #             processed_cases.append(case['filename'])
            #             print(f"✅ Case processed successfully")
            #         else:
            #             failed_cases.append(case['filename'])
            #             print(f"❌ File verification failed")
            #     else:
            #         failed_cases.append(case['filename'])
            #         print(f"❌ Timeout: File not created by Copilot")
            # else:
            #     failed_cases.append(case['filename'])
            #     print(f"❌ Failed to send prompt to Copilot")
            
            # Brief pause between cases
            # time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Automation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_mouse_mover_thread()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 AUTOMATION SUMMARY")
        print("=" * 80)
        print(f"Total cases: {len(cases_delta)}")
        print(f"✅ Processed: {len(processed_cases)}")
        print(f"⏭️  Skipped (already exists): {len(skipped_cases)}")
        print(f"❌ Failed: {len(failed_cases)}")
        
        if failed_cases:
            print(f"\n❌ Failed cases:")
            for case in failed_cases:
                print(f"   - {case}")
        
        print("\n🏁 Automation completed")
        
def main():
    """Main automation function"""
    print("🚀 Starting 5G Analysis Copilot Automation...")
    print("=" * 80)
    
    # Load cases
    try:
        with open(os.path.join(cu_output_path, "cases_delta.json"), "r") as f:
            cases_delta = json.load(f)
    except Exception as e:
        print(f"❌ Error loading cases_delta.json: {e}")
        return
    
    print(f"📊 Found {len(cases_delta)} cases to process\n")
    
    # Check VS Code availability
    if not find_vscode_window():
        print("❌ Could not find VS Code window. Please open VS Code.")
        return
    
    # Start mouse mover
    mouse_thread = start_mouse_mover()
    
    processed_cases = []
    skipped_cases = []
    failed_cases = []
    
    try:
        for i, case in enumerate(cases_delta, 1):
            print("\n" + "=" * 80)
            print(f"📝 Processing case {i}/{len(cases_delta)}: {case['filename']}")
            print(f"   Modified: {case['modified_key']}={case['error_value']}")
            print("=" * 80)
            
            case_filename = case["filename"].split(".")[0]
            
            # Check if already processed
            # if check_if_output_exists(case_filename):
            #     print(f"⏭️  Skipping (already exists): {case_filename}.txt")
            #     skipped_cases.append(case['filename'])
            #     continue
            
            # Build temp_json
            temp_json = build_temp_json(case)
            # if temp_json is None:
            #     print(f"⚠️  Skipping case (no logs): {case['filename']}")
            #     skipped_cases.append(case['filename'])
            #     continue
            
            # # Create prompt
            # prompt, case_filename = create_prompt_for_case(case, temp_json)
            
            # print(f"📏 Prompt length: {len(prompt)} characters")
            
            # # Send to Copilot
            # if send_prompt_to_copilot(prompt):
            #     # Wait for Copilot to create the file
            #     if wait_for_file_creation(case_filename, timeout=COPILOT_WAIT_TIME + 60):
            #         # Verify the file was created successfully
            #         if save_response_to_output(case_filename, None):
            #             processed_cases.append(case['filename'])
            #             print(f"✅ Case processed successfully")
            #         else:
            #             failed_cases.append(case['filename'])
            #             print(f"❌ File verification failed")
            #     else:
            #         failed_cases.append(case['filename'])
            #         print(f"❌ Timeout: File not created by Copilot")
            # else:
            #     failed_cases.append(case['filename'])
            #     print(f"❌ Failed to send prompt to Copilot")
            
            # Brief pause between cases
            # time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Automation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_mouse_mover_thread()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 AUTOMATION SUMMARY")
        print("=" * 80)
        print(f"Total cases: {len(cases_delta)}")
        print(f"✅ Processed: {len(processed_cases)}")
        print(f"⏭️  Skipped (already exists): {len(skipped_cases)}")
        print(f"❌ Failed: {len(failed_cases)}")
        
        if failed_cases:
            print(f"\n❌ Failed cases:")
            for case in failed_cases:
                print(f"   - {case}")
        
        print("\n🏁 Automation completed")
        

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='5G Analysis Copilot Automation')
    parser.add_argument('--wait-time', type=int, default=120,
                        help='Wait time in seconds for Copilot to generate response (default: 120)')
    parser.add_argument('--skip-existing', action='store_true', default=True,
                        help='Skip cases that already have output files (default: True)')
    
    args = parser.parse_args()
    
    COPILOT_WAIT_TIME = args.wait_time
    
    main2()
    main()