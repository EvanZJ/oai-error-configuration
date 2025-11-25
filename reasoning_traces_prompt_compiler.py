import json
import os
import time
import sys
import subprocess
import pyautogui
import pyperclip
from pathlib import Path
import argparse

# Paths - UPDATE THESE TO YOUR ACTUAL PATHS
input_jsonl_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/merged_training.jsonl"
prompt_template_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/reasoning_prompt.md"
output_base_path = "/home/sionna/evan/CursorAutomation/cursor_gen_conf/reasoning_outputs/"

failed_traces = []

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

def read_jsonl(file_path):
    """Read JSONL file and return list of JSON objects"""
    data = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        print(f"✅ Loaded {len(data)} traces from {file_path}")
        return data
    except Exception as e:
        print(f"❌ Error reading JSONL: {e}")
        return None

def read_prompt_template(file_path):
    """Read prompt template markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Loaded prompt template from {file_path}")
        return content
    except Exception as e:
        print(f"❌ Error reading prompt template: {e}")
        return None

def fill_prompt_template(template, trace, specific_keys):
    """Fill template with trace data"""
    prompt = template
    for key in specific_keys:
        if key in trace:
            placeholder = f"{{{key}}}"
            value = json.dumps(trace[key], indent=2) if isinstance(trace[key], (dict, list)) else str(trace[key])
            prompt = prompt.replace(placeholder, value)
    return prompt

def cleanup_copilot_chat():
    """Clean up Copilot chat state after a failure"""
    print("🧹 Cleaning up Copilot chat state...")
    try:
        if not ensure_vscode_active():
            print("⚠️  Could not activate VS Code for cleanup")
            return
        
        time.sleep(0.5)
        
        pyautogui.hotkey('ctrl', 'shift', 'alt', 'i')
        time.sleep(1)
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.press('backspace')
        time.sleep(0.5)
        
        print("🆕 Creating new chat window (Ctrl+N)...")
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(1)
        
        print("✅ Copilot chat cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup failed: {e}")

def send_prompt_to_copilot(prompt):
    """Send a prompt to Copilot chat"""
    try:
        if not ensure_vscode_active():
            print("❌ Could not activate VS Code")
            return False

        time.sleep(1)
        
        print("💬 Opening Copilot chat...")
        pyautogui.hotkey('ctrl', 'shift', 'alt', 'i')
        time.sleep(2)

        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.press('backspace')
        time.sleep(0.5)

        print("📋 Pasting prompt...")
        pyperclip.copy(prompt)
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        
        print("📤 Sending prompt to Copilot...")
        pyautogui.press('enter')
        
        return True
    except Exception as e:
        print(f"❌ Error sending prompt to Copilot: {e}")
        return False

def wait_for_response_file(output_file, max_timeout=300, check_interval=10, stabilization_wait=20):
    """Wait for response file to be created and populated"""
    print(f"👀 Waiting for: {os.path.basename(output_file)}")
    print(f"⏱️  Checking every {check_interval} seconds, max timeout: {max_timeout} seconds")
    
    start_time = time.time()
    checks_done = 0
    
    while time.time() - start_time < max_timeout:
        elapsed = int(time.time() - start_time)
        checks_done += 1
        
        print(f"🔍 Check #{checks_done} ({elapsed}s elapsed)...")
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            if file_size > 50:
                print(f"  ✓ File found ({file_size} bytes)")
                
                print(f"⏳ File detected, waiting {stabilization_wait}s for Copilot to finish...")
                time.sleep(stabilization_wait)
                
                new_file_size = os.path.getsize(output_file)
                if new_file_size != file_size:
                    print(f"  ⚠ File still being written ({file_size} -> {new_file_size} bytes), waiting...")
                    time.sleep(check_interval)
                    continue
                
                print(f"✅ Response file successfully generated!")
                print(f"⚡ Completed in {elapsed + stabilization_wait}s")
                
                print("🔧 Performing post-detection actions...")
                
                print("💬 Activating Copilot window...")
                pyautogui.hotkey('ctrl', 'shift', 'alt', 'i')
                time.sleep(1)
                
                print("💾 Saving all generated files (Ctrl+Enter)...")
                pyautogui.hotkey('ctrl', 'enter')
                time.sleep(1.5)
                
                print("🆕 Creating new chat window (Ctrl+N)...")
                pyautogui.hotkey('ctrl', 'n')
                time.sleep(1)
                
                print("✅ Post-detection actions completed!")
                
                return True
            else:
                print(f"  ⚠ File exists but too small: {file_size} bytes")
        
        if time.time() - start_time < max_timeout:
            time.sleep(check_interval)
    
    print(f"⏰ Timeout after {max_timeout} seconds")
    return False

def create_output_folder(base_path, trace_index):
    """Create output folder for a trace"""
    folder_name = f"trace_{trace_index:04d}"
    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def process_single_trace(trace, trace_index, template, specific_keys, max_wait_time, check_interval, stabilization_wait):
    """Process a single trace through the automation pipeline"""
    print("\n" + "=" * 80)
    print(f"🔄 Processing Trace #{trace_index}")
    print("=" * 80)
    
    output_folder = create_output_folder(output_base_path, trace_index)
    print(f"📂 Created folder: {os.path.basename(output_folder)}")
    
    output_response_file = os.path.join(output_folder, "copilot_response.md")
    if os.path.exists(output_response_file):
        file_size = os.path.getsize(output_response_file)
        if file_size > 50:
            print(f"⏭️  SKIPPING - copilot_response.md already exists ({file_size} bytes)")
            print(f"✅ Trace #{trace_index} already completed")
            return True
        else:
            print(f"⚠️  Found existing copilot_response.md but it's too small ({file_size} bytes), will regenerate")
    
    trace_file = os.path.join(output_folder, "input_trace.json")
    with open(trace_file, 'w') as f:
        json.dump(trace, f, indent=2)
    print(f"💾 Saved input trace")
    
    filled_prompt = fill_prompt_template(template, trace, specific_keys)
    
    prompt_file = os.path.join(output_folder, "filled_prompt.md")
    with open(prompt_file, 'w') as f:
        f.write(filled_prompt)
    print(f"📝 Saved filled prompt ({len(filled_prompt)} chars)")
    
    filled_prompt += f"\n\n" + "="*80 + "\n"
    filled_prompt += "CRITICAL INSTRUCTIONS FOR SAVING OUTPUT:\n"
    filled_prompt += "="*80 + "\n"
    filled_prompt += f"1. After generating your complete response, you MUST save it to this exact file path:\n"
    filled_prompt += f"   {output_response_file}\n\n"
    filled_prompt += f"2. Create a new file at that path and write your ENTIRE response to it.\n\n"
    filled_prompt += f"3. The file must be named: copilot_response.md\n\n"
    filled_prompt += f"4. Save the file in markdown format with your complete analysis.\n\n"
    filled_prompt += f"5. Do NOT just acknowledge - actually CREATE and SAVE the file with your response.\n"
    filled_prompt += "="*80
    
    if not send_prompt_to_copilot(filled_prompt):
        record_failure(trace_index, "send_prompt")
        print(f"❌ Failed to send prompt")
        cleanup_copilot_chat()
        return False
    
    print(f"🔍 Starting verification checks (every {check_interval}s, max {max_wait_time}s)...")
    
    if wait_for_response_file(output_response_file, max_wait_time, check_interval, stabilization_wait):
        print(f"✅ Trace #{trace_index} processing successful")
        return True
    else:
        record_failure(trace_index, "response_not_generated")
        print(f"❌ Trace #{trace_index} processing failed")
        cleanup_copilot_chat()
        return False

def process_traces_loop(traces, template, specific_keys, start_index, end_index, max_wait_time, check_interval, stabilization_wait):
    """Loop through processing multiple traces"""
    print("\n" + "=" * 80)
    print(f"🚀 Starting Reasoning Prompt Automation Loop")
    print(f"📝 Processing traces {start_index} to {end_index-1} ({end_index - start_index} total)")
    print(f"⚡ Check interval: {check_interval}s, stabilization wait: {stabilization_wait}s")
    print("=" * 80)
    
    success_count = 0
    failed_count = 0
    
    for i in range(start_index, end_index):
        if i >= len(traces):
            print(f"⚠️  Trace index {i} out of range, stopping")
            break
        
        try:
            trace = traces[i]
            
            if process_single_trace(trace, i, template, specific_keys, max_wait_time, check_interval, stabilization_wait):
                success_count += 1
                print(f"✅ Progress: {success_count}/{end_index - start_index} traces completed")
            else:
                failed_count += 1
                print(f"❌ Progress: {success_count}/{end_index - start_index} traces completed, {failed_count} failed")
                print(f"⚠️  Trace processing failed. Continue to next trace? (waiting 5s...)")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n⚠️  User interrupted the loop")
            break
        except Exception as e:
            print(f"❌ Error processing trace {i}: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
            cleanup_copilot_chat()
    
    return success_count, failed_count

def record_failure(trace_index, reason=""):
    """Record a failed trace"""
    global failed_traces
    entry = {"trace_index": trace_index, "reason": reason or "unknown"}
    failed_traces.append(entry)
    print(f"❌ Failed trace {trace_index} — {reason}")

def main():
    """Main automation function"""
    parser = argparse.ArgumentParser(
        description='Reasoning Prompt Automation - Send traces to Copilot for analysis'
    )
    parser.add_argument('--start', type=int, default=1, help='Starting trace index (default: 1)')
    parser.add_argument('--end', type=int, default=None, help='Ending trace index (exclusive, default: all traces)')
    parser.add_argument('--max-wait', type=int, default=300, help='Maximum wait time in seconds for each trace (default: 300)')
    parser.add_argument('--check-interval', type=int, default=10, help='Check interval in seconds for file verification (default: 10)')
    parser.add_argument('--stabilization-wait', type=int, default=20, help='Wait time in seconds after file detection for Copilot to finish (default: 20)')
    parser.add_argument('--keys', type=str, default='misconfigured_param,logs,network_config', help='Comma-separated list of keys to extract from trace')
    
    args = parser.parse_args()
    
    print("🚀 Starting Reasoning Prompt Automation")
    print("=" * 80)
    
    traces = read_jsonl(input_jsonl_path)
    if traces is None:
        print("❌ Failed to load traces. Exiting.")
        return
    
    template = read_prompt_template(prompt_template_path)
    if template is None:
        print("❌ Failed to load prompt template. Exiting.")
        return
    
    specific_keys = [k.strip() for k in args.keys.split(',')]
    
    end_index = args.end if args.end is not None else len(traces)
    if end_index > len(traces):
        end_index = len(traces)
    
    print(f"Configuration:")
    print(f"  Total traces available: {len(traces)}")
    print(f"  Processing range: {args.start} to {end_index-1}")
    print(f"  Total to process: {end_index - args.start}")
    print(f"  Keys to extract: {', '.join(specific_keys)}")
    print(f"  Max wait per trace: {args.max_wait} seconds")
    print(f"  Check interval: {args.check_interval} seconds")
    print(f"  Stabilization wait: {args.stabilization_wait} seconds")
    print(f"  Output directory: {output_base_path}")
    print("=" * 80)
    
    if not find_vscode_window():
        print("❌ Could not find VS Code window. Please open VS Code.")
        return
    
    os.makedirs(output_base_path, exist_ok=True)
    
    success_count = 0
    failed_count = 0
    
    try:
        success_count, failed_count = process_traces_loop(
            traces, template, specific_keys, args.start, end_index,
            args.max_wait, args.check_interval, args.stabilization_wait
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Automation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 80)
        print("📊 AUTOMATION SUMMARY")
        print("=" * 80)
        
        total_attempted = end_index - args.start
        print(f"Traces processed:")
        print(f"  ✅ Success: {success_count}/{total_attempted}")
        print(f"  ❌ Failed: {failed_count}/{total_attempted}")
        
        print(f"\n📁 Output location: {output_base_path}")
        print(f"\nEach trace folder contains:")
        print(f"  - input_trace.json (original trace data)")
        print(f"  - filled_prompt.md (prompt sent to Copilot)")
        print(f"  - copilot_response.md (Copilot's reasoning output)")
        print("\n🏁 Automation completed")
        
        if failed_traces:
            print("\n" + "!" * 80)
            print("FAILURE REPORT")
            print("!" * 80)
            for f in failed_traces:
                print(f" • Trace {f['trace_index']:04d} — {f['reason']}")
            
            report_path = os.path.join(output_base_path, "FAILED_TRACES_REPORT.json")
            with open(report_path, "w") as rf:
                json.dump(failed_traces, rf, indent=2)
            print(f"\nReport written to: {report_path}")
        else:
            print("\n✨ No failures recorded!")

if __name__ == "__main__":
    main()