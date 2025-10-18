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
cu_output_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/cu_output/json/"
du_output_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/du_output/json/"
baseline_conf_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/"
baseline_conf_json_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf_json/"
cu_prompt_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/cu_gen_prompt.md"
du_prompt_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/du_gen_prompt.md"

# Wait time for Copilot to generate ONE case
COPILOT_WAIT_TIME = 120  # 2 minutes default per case

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

def get_existing_case_count(output_path, prefix):
    """Count existing case files to determine starting number"""
    try:
        files = [f for f in os.listdir(output_path) if f.startswith(f"{prefix}_case_") and f.endswith(".json")]
        if not files:
            return 0
        
        # Extract numbers from filenames
        numbers = []
        for f in files:
            try:
                num_str = f.replace(f"{prefix}_case_", "").replace(".json", "")
                numbers.append(int(num_str))
            except ValueError:
                continue
        
        return max(numbers) if numbers else 0
    except Exception as e:
        print(f"Error counting existing cases: {e}")
        return 0

def get_cases_delta_count(output_path):
    """Get the count of cases in cases_delta.json"""
    try:
        delta_file = os.path.join(output_path, "cases_delta.json")
        if not os.path.exists(delta_file):
            return 0
        
        with open(delta_file, 'r') as f:
            cases_delta = json.load(f)
        
        return len(cases_delta)
    except Exception as e:
        print(f"Error reading cases_delta.json: {e}")
        return 0

def load_prompt_template(config_type):
    """Load the prompt template for the config type"""
    try:
        prompt_path = cu_prompt_path if config_type == "cu" else du_prompt_path
        with open(prompt_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error loading prompt template: {e}")
        return None

def send_prompt_to_copilot(prompt):
    """Send a prompt to Copilot chat"""
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

def wait_and_verify_case_generation(config_type, expected_case_num, max_timeout=300, check_interval=10):
    """Wait for and verify that a new case was generated - checks every N seconds"""
    output_path = cu_output_path if config_type == "cu" else du_output_path
    prefix = config_type
    
    expected_filename = f"{prefix}_case_{expected_case_num:02d}.json"
    expected_filepath = os.path.join(output_path, expected_filename)
    delta_filepath = os.path.join(output_path, "cases_delta.json")
    
    print(f"👀 Waiting for: {expected_filename}")
    print(f"⏱️  Checking every {check_interval} seconds, max timeout: {max_timeout} seconds")
    
    start_time = time.time()
    initial_delta_count = get_cases_delta_count(output_path)
    checks_done = 0
    
    while time.time() - start_time < max_timeout:
        elapsed = int(time.time() - start_time)
        checks_done += 1
        
        print(f"🔍 Check #{checks_done} ({elapsed}s elapsed)...")
        
        case_file_found = False
        delta_updated = False
        
        # Check if case file exists
        if os.path.exists(expected_filepath):
            file_size = os.path.getsize(expected_filepath)
            if file_size > 100:  # Valid file
                print(f"  ✓ Case file found: {expected_filename} ({file_size} bytes)")
                case_file_found = True
            else:
                print(f"  ⚠ Case file exists but too small: {file_size} bytes")
        
        # Check if cases_delta.json was updated
        current_delta_count = get_cases_delta_count(output_path)
        if current_delta_count > initial_delta_count:
            print(f"  ✓ cases_delta.json updated: {initial_delta_count} -> {current_delta_count} entries")
            delta_updated = True
        
        # Both conditions met - verify thoroughly
        if case_file_found and delta_updated:
            try:
                with open(delta_filepath, 'r') as f:
                    cases_delta = json.load(f)
                
                # Check if the expected filename is in the delta
                found_in_delta = any(case['filename'] == expected_filename for case in cases_delta)
                if found_in_delta:
                    print(f"✅ Case {expected_case_num} successfully generated and verified!")
                    print(f"⚡ Completed in {elapsed}s (saved {max_timeout - elapsed}s)")
                    return True
                else:
                    print(f"  ⚠ Case file exists but not found in cases_delta.json yet")
            except Exception as e:
                print(f"  ⚠ Error verifying cases_delta.json: {e}")
        
        # Wait for next check interval
        if time.time() - start_time < max_timeout:
            time.sleep(check_interval)
    
    # Timeout
    print(f"⏰ Timeout after {max_timeout} seconds")
    print(f"   Case file found: {case_file_found}")
    print(f"   Delta updated: {delta_updated}")
    return False

def generate_single_case(config_type, iteration_num, total_iterations, max_wait_time, check_interval):
    """Generate a single test case"""
    print("\n" + "=" * 80)
    print(f"🔄 Iteration {iteration_num}/{total_iterations} - Generating {config_type.upper()} case")
    print("=" * 80)
    
    output_path = cu_output_path if config_type == "cu" else du_output_path
    prefix = config_type
    
    # Get current case count
    current_count = get_existing_case_count(output_path, prefix)
    expected_case_num = current_count + 1
    
    print(f"📊 Current case count: {current_count}")
    print(f"🎯 Expected new case: {prefix}_case_{expected_case_num:02d}.json")
    
    # Load prompt template
    prompt_template = load_prompt_template(config_type)
    if prompt_template is None:
        return False
    
    # The prompt template already contains all instructions
    # Just send it as-is - Copilot will generate ONE case and update cases_delta.json
    prompt = prompt_template
    
    print(f"📏 Prompt length: {len(prompt)} characters")
    
    # Send to Copilot
    if not send_prompt_to_copilot(prompt):
        print(f"❌ Failed to send prompt")
        return False
    
    # Start checking immediately - no fixed wait time
    print(f"🔍 Starting verification checks (every {check_interval}s, max {max_wait_time}s)...")
    
    # Verify the case was generated (checks every N seconds)
    if wait_and_verify_case_generation(config_type, expected_case_num, max_timeout=max_wait_time, check_interval=check_interval):
        print(f"✅ Case {expected_case_num} generation successful")
        return True
    else:
        print(f"❌ Case {expected_case_num} generation failed or not verified")
        return False

def generate_cases_loop(config_type, num_cases, max_wait_time, check_interval):
    """Loop through generating multiple cases one by one"""
    print("\n" + "=" * 80)
    print(f"🚀 Starting {config_type.upper()} case generation loop")
    print(f"📝 Will generate {num_cases} cases, one at a time")
    print(f"⚡ Check interval: {check_interval}s (moves to next when verified)")
    print("=" * 80)
    
    output_path = cu_output_path if config_type == "cu" else du_output_path
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    success_count = 0
    failed_count = 0
    
    for i in range(1, num_cases + 1):
        try:
            if generate_single_case(config_type, i, num_cases, max_wait_time, check_interval):
                success_count += 1
                print(f"✅ Progress: {success_count}/{num_cases} cases generated")
            else:
                failed_count += 1
                print(f"❌ Progress: {success_count}/{num_cases} cases generated, {failed_count} failed")
                
                # Ask user if they want to continue
                print(f"⚠️  Case generation failed. Continue to next case? (waiting 5s...)")
                time.sleep(5)
            
            # Short pause between iterations
            if i < num_cases:
                print(f"⏸️  Pausing 3 seconds before next iteration...")
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\n⚠️  User interrupted the loop")
            break
        except Exception as e:
            print(f"❌ Error in iteration {i}: {e}")
            failed_count += 1
    
    return success_count, failed_count

def main():
    """Main automation function"""
    parser = argparse.ArgumentParser(description='5G gNodeB Configuration Test Case Generator Automation (Loop Mode)')
    parser.add_argument('--cu-cases', type=int, default=0,
                        help='Number of CU test cases to generate (default: 0)')
    parser.add_argument('--du-cases', type=int, default=0,
                        help='Number of DU test cases to generate (default: 0)')
    parser.add_argument('--max-wait', type=int, default=300,
                        help='Maximum wait time in seconds for each case (default: 300)')
    parser.add_argument('--check-interval', type=int, default=10,
                        help='Check interval in seconds for file verification (default: 10)')
    
    args = parser.parse_args()
    
    if args.cu_cases == 0 and args.du_cases == 0:
        print("❌ Please specify at least --cu-cases or --du-cases")
        print("Example: python case_generator_automation.py --cu-cases 10 --du-cases 15")
        return
    
    print("🚀 Starting 5G Test Case Generator Automation (EFFICIENT LOOP MODE)")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  CU cases to generate: {args.cu_cases}")
    print(f"  DU cases to generate: {args.du_cases}")
    print(f"  Max wait per case: {args.max_wait} seconds")
    print(f"  Check interval: {args.check_interval} seconds")
    print(f"  ⚡ Mode: Check every {args.check_interval}s, move to next immediately when verified!")
    print("=" * 80)
    
    # Check VS Code availability
    if not find_vscode_window():
        print("❌ Could not find VS Code window. Please open VS Code.")
        return
    
    # Start mouse mover
    mouse_thread = start_mouse_mover()
    
    cu_success = 0
    cu_failed = 0
    du_success = 0
    du_failed = 0
    
    try:
        # Generate CU cases one by one
        if args.cu_cases > 0:
            cu_success, cu_failed = generate_cases_loop("cu", args.cu_cases, args.max_wait, args.check_interval)
            
            # Pause between CU and DU
            if args.du_cases > 0:
                print("\n⏸️  Pausing 10 seconds before DU generation...")
                time.sleep(10)
        
        # Generate DU cases one by one
        if args.du_cases > 0:
            du_success, du_failed = generate_cases_loop("du", args.du_cases, args.max_wait, args.check_interval)
        
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
        
        if args.cu_cases > 0:
            print(f"CU Cases:")
            print(f"  ✅ Success: {cu_success}/{args.cu_cases}")
            print(f"  ❌ Failed: {cu_failed}/{args.cu_cases}")
        
        if args.du_cases > 0:
            print(f"DU Cases:")
            print(f"  ✅ Success: {du_success}/{args.du_cases}")
            print(f"  ❌ Failed: {du_failed}/{args.du_cases}")
        
        print("\n🏁 Automation completed")
        print("\nPlease verify the generated files in:")
        if args.cu_cases > 0:
            print(f"  - {cu_output_path}")
            print(f"  - {cu_output_path}cases_delta.json")
        if args.du_cases > 0:
            print(f"  - {du_output_path}")
            print(f"  - {du_output_path}cases_delta.json")

if __name__ == "__main__":
    main()