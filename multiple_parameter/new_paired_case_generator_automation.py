import json
import os
import time
import sys
import threading
import subprocess
import pyautogui
import pyperclip
from pathlib import Path
import argparse

# Paths
base_output_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output/"
baseline_conf_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/"
baseline_conf_json_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf_json/"
delta_maker_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/cases_delta_maker.md"

failed_cases = []   

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

def get_existing_case_folders():
    """Get list of existing case folders"""
    try:
        if not os.path.exists(base_output_path):
            return []
        folders = [f for f in os.listdir(base_output_path) if f.startswith("cases_") and os.path.isdir(os.path.join(base_output_path, f))]
        return sorted(folders)
    except Exception as e:
        print(f"Error getting existing folders: {e}")
        return []

def get_next_case_number():
    """Determine the next case number based on existing folders"""
    folders = get_existing_case_folders()
    if not folders:
        return 1
    
    numbers = []
    for folder in folders:
        try:
            num_str = folder.replace("cases_", "")
            numbers.append(int(num_str))
        except ValueError:
            continue
    
    return max(numbers) + 1 if numbers else 1

def create_case_folder(case_num):
    """Create a new case folder"""
    folder_name = f"cases_{case_num:02d}"
    folder_path = os.path.join(base_output_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def load_baseline_files():
    """Load all baseline configuration files"""
    try:
        cu_conf_path = os.path.join(baseline_conf_path, "cu_gnb.conf")
        du_conf_path = os.path.join(baseline_conf_path, "du_gnb.conf")
        cu_json_path = os.path.join(baseline_conf_json_path, "cu_gnb.json")
        du_json_path = os.path.join(baseline_conf_json_path, "du_gnb.json")
        
        with open(cu_conf_path, 'r') as f:
            cu_conf = f.read()
        with open(du_conf_path, 'r') as f:
            du_conf = f.read()
        with open(cu_json_path, 'r') as f:
            cu_json = f.read()
        with open(du_json_path, 'r') as f:
            du_json = f.read()
        
        return {
            'cu_gnb_conf': cu_conf,
            'du_gnb_conf': du_conf,
            'cu_gnb_json': cu_json,
            'du_gnb_json': du_json
        }
    except Exception as e:
        print(f"❌ Error loading baseline files: {e}")
        return None

def load_prompt_template():
    """Load the delta maker prompt template"""
    try:
        with open(delta_maker_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error loading prompt template: {e}")
        return None

def send_prompt_to_copilot(prompt):
    """Send a prompt to Copilot chat"""
    try:
        if not ensure_vscode_active():
            print("❌ Could not activate VS Code")
            return False

        time.sleep(1)
        
        # Open Copilot chat with Ctrl+Shift+Alt+I
        print("💬 Opening Copilot chat...")
        pyautogui.hotkey('ctrl', 'shift', 'alt', 'i')
        time.sleep(2)

        # Clear any existing content
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.press('backspace')
        time.sleep(0.5)

        # Paste prompt
        print("📋 Pasting prompt...")
        pyperclip.copy(prompt)
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        
        # Send the prompt
        print("📤 Sending prompt to Copilot...")
        pyautogui.press('enter')
        
        return True
    except Exception as e:
        print(f"❌ Error sending prompt to Copilot: {e}")
        return False

def wait_for_cases_delta(folder_path, max_timeout=300, check_interval=10, stabilization_wait=5):
    """Wait for cases_delta.json to be created and populated"""
    delta_filepath = os.path.join(folder_path, "cases_delta.json")
    
    print(f"👀 Waiting for: cases_delta.json")
    print(f"⏱️  Checking every {check_interval} seconds, max timeout: {max_timeout} seconds")
    
    start_time = time.time()
    checks_done = 0
    
    while time.time() - start_time < max_timeout:
        elapsed = int(time.time() - start_time)
        checks_done += 1
        
        print(f"🔍 Check #{checks_done} ({elapsed}s elapsed)...")
        
        if os.path.exists(delta_filepath):
            file_size = os.path.getsize(delta_filepath)
            if file_size > 50:  # Valid file
                try:
                    with open(delta_filepath, 'r') as f:
                        delta_data = json.load(f)
                    
                    if isinstance(delta_data, list) and len(delta_data) > 0:
                        print(f"  ✓ cases_delta.json found with {len(delta_data)} entries ({file_size} bytes)")
                        
                        # Verify it has both cu and du entries
                        has_cu = any('cu' in case for case in delta_data)
                        has_du = any('du' in case for case in delta_data)
                        
                        if has_cu and has_du:
                            # Wait for stabilization
                            print(f"⏳ File detected, waiting {stabilization_wait}s for Copilot to finish...")
                            time.sleep(stabilization_wait)
                            
                            # Verify file size hasn't changed
                            new_file_size = os.path.getsize(delta_filepath)
                            if new_file_size != file_size:
                                print(f"  ⚠ File still being written ({file_size} -> {new_file_size} bytes), waiting...")
                                time.sleep(check_interval)
                                continue
                            
                            print(f"✅ cases_delta.json successfully generated with CU and DU entries!")
                            print(f"⚡ Completed in {elapsed + stabilization_wait}s")
                            return True
                        else:
                            print(f"  ⚠ cases_delta.json exists but missing entries (CU: {has_cu}, DU: {has_du})")
                    else:
                        print(f"  ⚠ cases_delta.json exists but empty or invalid")
                except json.JSONDecodeError:
                    print(f"  ⚠ File exists but not valid JSON yet")
            else:
                print(f"  ⚠ File exists but too small: {file_size} bytes")
        
        # Wait for next check interval
        if time.time() - start_time < max_timeout:
            time.sleep(check_interval)
    
    # Timeout
    print(f"⏰ Timeout after {max_timeout} seconds")
    return False

def generate_delta_case(case_num, max_wait_time, check_interval, stabilization_wait, baseline_files):
    """Generate only cases_delta.json directly from baseline configs"""
    print("\n" + "=" * 80)
    print(f"📝 Generating Delta Case Set #{case_num}")
    print("=" * 80)
    
    # Create case folder
    folder_path = create_case_folder(case_num)
    folder_name = os.path.basename(folder_path)
    print(f"📂 Created folder: {folder_name}")
    
    # Generate cases_delta.json directly
    print(f"\n{'─' * 80}")
    print(f"🔧 Generating cases_delta.json")
    print(f"{'─' * 80}")
    
    delta_prompt_template = load_prompt_template()
    if delta_prompt_template is None:
        return False
    
    # Build comprehensive prompt with all baseline configs embedded
    delta_prompt = f"""I want you to create a cases_delta.json file based on the baseline configurations provided below.

The file should contain test cases with single-key errors for both CU and DU configurations.

## Baseline CU Configuration (.conf)
```
{baseline_files['cu_gnb_conf']}
```

## Baseline CU Configuration (.json)
```json
{baseline_files['cu_gnb_json']}
```

## Baseline DU Configuration (.conf)
```
{baseline_files['du_gnb_conf']}
```

## Baseline DU Configuration (.json)
```json
{baseline_files['du_gnb_json']}
```

## Task
{delta_prompt_template}

IMPORTANT: Save the file as 'cases_delta.json' in the folder '{folder_path}'

Generate exactly 1 test case, each with both CU and DU modifications as shown in the example format.
"""
    
    if not send_prompt_to_copilot(delta_prompt):
        record_failure(case_num, "DELTA", "send_prompt_to_copilot")
        print(f"❌ Failed to send delta prompt")
        return False
    
    if not wait_for_cases_delta(folder_path, max_wait_time, check_interval, stabilization_wait):
        record_failure(case_num, "DELTA", "file_not_generated")
        print(f"❌ cases_delta.json generation failed")
        return False
    
    print(f"\n{'═' * 80}")
    print(f"✅ Delta Case Set #{case_num} COMPLETED!")
    print(f"📁 Location: {folder_path}")
    print(f"📄 File: cases_delta.json")
    print(f"{'═' * 80}")
    
    return True

def generate_cases_loop(num_cases, max_wait_time, check_interval, stabilization_wait, baseline_files):
    """Loop through generating multiple delta case sets"""
    print("\n" + "=" * 80)
    print(f"🚀 Starting DELTA-ONLY Case Generation Loop")
    print(f"📦 Will generate {num_cases} case sets (each with cases_delta.json only)")
    print(f"⚡ Check interval: {check_interval}s, stabilization wait: {stabilization_wait}s")
    print("=" * 80)
    
    # Create base output directory if it doesn't exist
    os.makedirs(base_output_path, exist_ok=True)
    
    start_case_num = get_next_case_number()
    print(f"📊 Starting from case number: {start_case_num}")
    
    success_count = 0
    failed_count = 0
    
    for i in range(num_cases):
        case_num = start_case_num + i
        
        try:
            if generate_delta_case(case_num, max_wait_time, check_interval, stabilization_wait, baseline_files):
                success_count += 1
                print(f"✅ Progress: {success_count}/{num_cases} case sets completed")
            else:
                failed_count += 1
                print(f"❌ Progress: {success_count}/{num_cases} case sets completed, {failed_count} failed")
                
                print(f"⚠️  Case set generation failed. Continue to next case? (waiting 5s...)")
                time.sleep(5)
            
            # Pause between case sets
            if i < num_cases - 1:
                print(f"\n⏸️  Pausing 10 seconds before next case set...")
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n⚠️  User interrupted the loop")
            break
        except Exception as e:
            print(f"❌ Error in case set {case_num}: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    return success_count, failed_count

def record_failure(case_num, step, reason=""):
    """Append a structured entry to the global failed_cases list."""
    global failed_cases
    entry = {
        "case": case_num,
        "step": step,
        "reason": reason or "unknown"
    }
    failed_cases.append(entry)
    print(f"Failed case {case_num} — {step}: {reason}")

def main():
    """Main automation function"""
    parser = argparse.ArgumentParser(
        description='5G gNodeB Delta-Only Test Case Generator (generates cases_delta.json only)'
    )
    parser.add_argument('--num-cases', type=int, required=True,
                        help='Number of case sets to generate (each contains cases_delta.json)')
    parser.add_argument('--max-wait', type=int, default=300,
                        help='Maximum wait time in seconds for each file (default: 300)')
    parser.add_argument('--check-interval', type=int, default=10,
                        help='Check interval in seconds for file verification (default: 10)')
    parser.add_argument('--stabilization-wait', type=int, default=5,
                        help='Wait time in seconds after file detection for Copilot to finish (default: 5)')
    
    args = parser.parse_args()
    
    if args.num_cases <= 0:
        print("❌ Please specify a positive number of cases with --num-cases")
        return
    
    print("🚀 Starting 5G Delta-Only Test Case Generator Automation")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  Case sets to generate: {args.num_cases}")
    print(f"  Files per set: cases_delta.json (only)")
    print(f"  Max wait per file: {args.max_wait} seconds")
    print(f"  Check interval: {args.check_interval} seconds")
    print(f"  Stabilization wait: {args.stabilization_wait} seconds (after file detected)")
    print(f"  Output directory: {base_output_path}")
    print(f"  ⚡ Mode: Check every {args.check_interval}s, wait {args.stabilization_wait}s after detection!")
    print("=" * 80)
    
    # Load baseline files once at the start
    print("\n📖 Loading baseline configuration files...")
    baseline_files = load_baseline_files()
    if not baseline_files:
        print("❌ Failed to load baseline files. Exiting.")
        return
    print("✅ Baseline files loaded successfully")
    
    # Check VS Code availability
    if not find_vscode_window():
        print("❌ Could not find VS Code window. Please open VS Code.")
        return
    
    # Start mouse mover
    mouse_thread = start_mouse_mover()
    
    success_count = 0
    failed_count = 0
    
    try:
        success_count, failed_count = generate_cases_loop(
            args.num_cases, 
            args.max_wait, 
            args.check_interval,
            args.stabilization_wait,
            baseline_files
        )
        
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
        print(f"Case Sets Generated:")
        print(f"  ✅ Success: {success_count}/{args.num_cases}")
        print(f"  ❌ Failed: {failed_count}/{args.num_cases}")
        print(f"\n📁 Output location: {base_output_path}")
        print(f"\nEach case set contains:")
        print(f"  - cases_delta.json (delta summary with CU and DU modifications)")
        print("\n🏁 Automation completed")
        
        if failed_cases:
            print("\n" + "!" * 80)
            print("FAILURE REPORT")
            print("!" * 80)
            for f in failed_cases:
                print(f" • Case {f['case']:02d} — {f['step']} — {f['reason']}")

            # Save a JSON file next to the output folder for later inspection
            report_path = os.path.join(base_output_path, "FAILED_CASES_REPORT.json")
            with open(report_path, "w") as rf:
                json.dump(failed_cases, rf, indent=2)
            print(f"\nReport written to: {report_path}")
        else:
            print("\nNo failures recorded.")

if __name__ == "__main__":
    main()