#!/usr/bin/env bash
set -euo pipefail

### ====== 使用者可調整區 / User-tunable Settings ======
# 放一堆 cases_XX 資料夾的根目錄（會依字母序逐一處理）
# Root directory containing cases_XX folders (processed in lexicographic order)
CASES_ROOT="/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/output"

# UE conf（固定） / Fixed UE conf
UE_CONF="/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/ue_oai.conf"

# 可執行檔位置（相對或絕對都可） / Binaries (absolute or relative)
NR_GNB_BIN="/home/sionna/evan/openairinterface5g/cmake_targets/ran_build/build/nr-softmodem"
NR_UE_BIN="/home/sionna/evan/openairinterface5g/cmake_targets/ran_build/build/nr-uesoftmodem"

# RFSIM 伺服器環境變數 / RFSIM server env var
RFSIMULATOR_TARGET="server"

# 每輪測試持續秒數 / Per-run active duration (seconds)
RUNTIME_SECS=30

# 進度點點的間隔秒數（每 N 秒印一個 .）
# Interval in seconds for printing progress dots
PROGRESS_INTERVAL=5

# 啟動間的緩衝秒數（讓前一個元件先起來）
# Staggered start delays (give time for previous component to come up)
DELAY_AFTER_CU=4
DELAY_AFTER_DU=4

# 輸出 log 根目錄 / Logs root directory
LOG_ROOT="/home/sionna/evan/CursorAutomation/cursor_gen_conf/multiple_parameter/logs_batch_run"

# Docker 容器 IDs（每輪測試前重啟）
# Docker container IDs to restart before each test case
DOCKER_CONTAINERS="78d03d6ed583 a86f24977b1b a752fa1f5a13 fd3aca606db3 f4e16e89b2ee f612b909f593 766a65ecce01 3f2a91613157 24c88761f8ef"
### ====== 使用者可調整區 / End of User-tunable Settings ======


timestamp() { date +"%Y%m%d_%H%M%S"; }

ensure_bins() {
  for b in "$NR_GNB_BIN" "$NR_UE_BIN"; do
    if [[ ! -x "$b" ]]; then
      echo "❌ 找不到或不可執行：$b  / Not found or not executable"
      exit 1
    fi
  done
}

cleanup_procs() {
  # 殺掉所有可能殘留的進程（容忍找不到） / Kill any lingering processes (ignore if none)
  sudo pkill -9 -f "[n]r-softmodem" 2>/dev/null || true
  sudo pkill -9 -f "[n]r-uesoftmodem" 2>/dev/null || true
}

restart_containers() {
  echo "🔄 重啟 Docker 容器 / Restarting Docker containers..."
  for cid in $DOCKER_CONTAINERS; do
    sudo docker restart "$cid" 2>/dev/null || echo "⚠️ 無法重啟容器 $cid / Failed to restart container $cid"
  done
  sleep 5  # 給容器重啟時間 / Give containers time to restart
}

sleep_with_dots() {
  # 每 PROGRESS_INTERVAL 秒印出一個 .，直到 RUNTIME_SECS 結束
  # Print a dot every PROGRESS_INTERVAL seconds until RUNTIME_SECS elapses
  local total="$RUNTIME_SECS"
  local step="$PROGRESS_INTERVAL"
  local elapsed=0

  echo -n "⏱️  測試進行中（${total}s）/ Running (${total}s): "
  while (( elapsed + step <= total )); do
    sleep "$step"
    elapsed=$(( elapsed + step ))
    echo -n "."
  done
  # 若有餘數，補最後一段 / Sleep the remainder if any
  if (( elapsed < total )); then
    sleep $(( total - elapsed ))
  fi
  echo ""  # 換行 / newline
}

run_one_case() {
  local CASE_DIR="$1"
  local CASE_NAME="$2"
  
  # Check if this case has already been run by looking for existing log folders
  shopt -s nullglob
  local existing_logs=("${LOG_ROOT}"/*_"${CASE_NAME}")
  shopt -u nullglob
  
  if (( ${#existing_logs[@]} > 0 )); then
    echo "⏭️  跳過 ${CASE_NAME}：已執行過 / Skip ${CASE_NAME}: Already run"
    echo "   現有 log: $(basename "${existing_logs[0]}")"
    return 2  # Return code 2 = skipped
  fi
  
  local OUT_DIR="${LOG_ROOT}/$(timestamp)_${CASE_NAME}"
  mkdir -p "$OUT_DIR"

  echo "🚀 ==== 開始測試 / Start Test：$CASE_NAME → log：$OUT_DIR ===="

  # 尋找 CU 和 DU conf 檔案
  local CU_CONF_TO_USE DU_CONF_TO_USE
  
  # First, try to find .conf files (already converted)
  shopt -s nullglob
  local cu_conf_files=("$CASE_DIR"/cu_case_*.conf)
  local du_conf_files=("$CASE_DIR"/du_case_*.conf)
  shopt -u nullglob
  
  # Check CU config - MUST be .conf file
  if (( ${#cu_conf_files[@]} > 0 )); then
    CU_CONF_TO_USE="${cu_conf_files[0]}"
    echo "✅ 找到 CU .conf 檔案 / Found CU .conf file: $(basename "$CU_CONF_TO_USE")"
  else
    echo "❌ 找不到 CU .conf 檔案在：$CASE_DIR  / CU .conf file not found in: $CASE_DIR"
    echo "   請先執行 json_to_conf_cu_paired.py 轉換 / Please run json_to_conf_cu_paired.py first"
    return 1  # Return code 1 = failed
  fi
  
  # Check DU config - MUST be .conf file
  if (( ${#du_conf_files[@]} > 0 )); then
    DU_CONF_TO_USE="${du_conf_files[0]}"
    echo "✅ 找到 DU .conf 檔案 / Found DU .conf file: $(basename "$DU_CONF_TO_USE")"
  else
    echo "❌ 找不到 DU .conf 檔案在：$CASE_DIR  / DU .conf file not found in: $CASE_DIR"
    echo "   請先執行 json_to_conf_du_paired.py 轉換 / Please run json_to_conf_du_paired.py first"
    return 1  # Return code 1 = failed
  fi

  # 將 conf 轉為絕對路徑，避免 cd OUT_DIR 後相對路徑失效
  CU_CONF_TO_USE="$(readlink -f "$CU_CONF_TO_USE")"
  DU_CONF_TO_USE="$(readlink -f "$DU_CONF_TO_USE")"
  local UE_CONF_ABS
  UE_CONF_ABS="$(readlink -f "$UE_CONF")"

  echo "🧹 清理殘留進程 / Cleaning up lingering processes..."
  cleanup_procs

  # 在 case 目錄內啟動（stats 檔會落在這裡）
  pushd "$OUT_DIR" >/dev/null

  # 啟動 CU
  echo "🟦 [CU] 啟動 / Launch: $CU_CONF_TO_USE"
  sudo -E env RFSIMULATOR="$RFSIMULATOR_TARGET" \
    "$NR_GNB_BIN" --rfsim --sa \
    -O "$CU_CONF_TO_USE" \
    > "cu.stdout.log" 2>&1 &
  local CU_PID=$!
  echo "    PID = $CU_PID"
  sleep "${DELAY_AFTER_CU}"

  # 啟動 DU
  echo "🟩 [DU] 啟動 / Launch: $DU_CONF_TO_USE"
  sudo -E env RFSIMULATOR="$RFSIMULATOR_TARGET" \
    "$NR_GNB_BIN" --rfsim --sa \
    -O "$DU_CONF_TO_USE" \
    > "du.stdout.log" 2>&1 &
  local DU_PID=$!
  echo "    PID = $DU_PID"
  sleep "${DELAY_AFTER_DU}"

  # 啟動 UE
  echo "🟨 [UE] 啟動 / Launch: $UE_CONF_ABS"
  sudo "$NR_UE_BIN" -r 106 --numerology 1 --band 78 -C 3619200000 \
    --rfsim -O "$UE_CONF_ABS" \
    > "ue.stdout.log" 2>&1 &
  local UE_PID=$!
  echo "    PID = $UE_PID"

  # 跑固定秒數 + 進度點點
  echo "📡  進入測試窗口 / Entering test window..."
  sleep_with_dots

  # 收尾
  echo "🛑 時間到，清理進程 / Time's up, cleaning up processes..."
  cleanup_procs

  # 各自最後 100 行摘要（在 OUT_DIR 內直接讀）
  {
    echo "===== CU stdout (tail -n 100) ====="; tail -n 100 "cu.stdout.log" 2>/dev/null || true; echo
    echo "===== DU stdout (tail -n 100) ====="; tail -n 100 "du.stdout.log" 2>/dev/null || true; echo
    echo "===== UE stdout (tail -n 100) ====="; tail -n 100 "ue.stdout.log" 2>/dev/null || true; echo
  } > "tail100_summary.log"

  # 產出 JSON 版的 tail100.summary（你要求的格式）
  # 仍保留上面的 tail100.summary.log 純文字摘要
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY' > "tail100_summary.json"
import json
def last_lines(path, n=100):
    try:
        with open(path, 'r', errors='ignore') as f:
            return [line.rstrip("\r\n") for line in f.readlines()[-n:]]
    except FileNotFoundError:
        return []
obj = {
    "CU": last_lines("cu.stdout.log", 100),
    "DU": last_lines("du.stdout.log", 100),
    "UE": last_lines("ue.stdout.log", 100),
}
print(json.dumps(obj, ensure_ascii=False, indent=2))
PY
  else
    # 沒有 python3 就用 awk 組 JSON（簡單轉義）
    {
      echo '{'
      echo '  "CU": ['
      tail -n 100 "cu.stdout.log" 2>/dev/null | awk '{
        gsub(/\\/,"\\\\"); gsub(/"/,"\\\"");
        printf("    \"%s\",\n",$0)
      }' | sed '$ s/,$//'
      echo '  ],'
      echo '  "DU": ['
      tail -n 100 "du.stdout.log" 2>/dev/null | awk '{
        gsub(/\\/,"\\\\"); gsub(/"/,"\\\"");
        printf("    \"%s\",\n",$0)
      }' | sed '$ s/,$//'
      echo '  ],'
      echo '  "UE": ['
      tail -n 100 "ue.stdout.log" 2>/dev/null | awk '{
        gsub(/\\/,"\\\\"); gsub(/"/,"\\\"");
        printf("    \"%s\",\n",$0)
      }' | sed '$ s/,$//'
      echo '  ]'
      echo '}'
    } > "tail100_summary.json"
  fi

  # 紀錄本輪使用的 conf
  {
    echo "CASE_NAME=${CASE_NAME}"
    echo "CU_CONF=${CU_CONF_TO_USE}"
    echo "DU_CONF=${DU_CONF_TO_USE}"
    echo "UE_CONF=${UE_CONF_ABS}"
    echo "START_TIME=$(date -Iseconds)"
    echo "DURATION=${RUNTIME_SECS}s"
    echo "SOURCE_CASE_DIR=${CASE_DIR}"
  } > "run_manifest.txt"

  popd >/dev/null

  echo "✅ ==== 完成 / Done：$CASE_NAME ===="
  return 0  # Return code 0 = success
}


main() {
  echo "🔎 檢查執行檔 / Checking binaries..."
  ensure_bins

  mkdir -p "$LOG_ROOT"

  # Ctrl-C 時也清掉殘留 / Clean up on interrupt
  trap 'echo "⚠️ 捕捉到中斷，清理進程 / Caught interrupt, cleaning up..."; cleanup_procs; exit 130' INT TERM

  # 找出所有 cases_XX 資料夾 / Find all cases_XX directories
  shopt -s nullglob
  mapfile -t cases_dirs < <(find "$CASES_ROOT" -maxdepth 1 -type d -name "cases_*" | sort)
  shopt -u nullglob

  if (( ${#cases_dirs[@]} == 0 )); then
    echo "📭 在 ${CASES_ROOT} 找不到任何 cases_* 資料夾 / No cases_* folders found in ${CASES_ROOT}"
    exit 1
  fi

  echo "🗂️  待處理數量 / Cases to process: ${#cases_dirs[@]}"

  local completed_count=0
  local skipped_count=0
  local failed_count=0
  
  restart_containers  # 初始重啟容器 / Initial restart of containers

  for case_dir in "${cases_dirs[@]}"; do
    case_name="$(basename "$case_dir")"
    
    # Run the case and capture return code
    set +e  # Temporarily disable exit on error
    run_one_case "$case_dir" "$case_name"
    local result=$?
    set -e  # Re-enable exit on error
    
    # Handle different return codes
    if [[ $result -eq 0 ]]; then
      # Successfully completed
      completed_count=$((completed_count + 1))
      echo "   ✅ 進度 / Progress: 完成 ${completed_count}, 跳過 ${skipped_count}, 失敗 ${failed_count}"
      
      # Restart containers every 100 completed tests
      if (( completed_count % 100 == 0 )); then
        restart_containers
      fi
    elif [[ $result -eq 2 ]]; then
      # Skipped (already run)
      skipped_count=$((skipped_count + 1))
      echo "   ⏭️  進度 / Progress: 完成 ${completed_count}, 跳過 ${skipped_count}, 失敗 ${failed_count}"
    else
      # Failed (result -eq 1 or other error)
      failed_count=$((failed_count + 1))
      echo "   ❌ 進度 / Progress: 完成 ${completed_count}, 跳過 ${skipped_count}, 失敗 ${failed_count}"
    fi
    
    echo
    # 小休息，避免下一輪太快黏在一起 / short pause between cases
    sleep 2
  done

  echo "🎉 全部測試完成 / All tests finished"
  echo "=" * 80
  echo "📊 最終統計 / Final Statistics:"
  echo "   ✅ 成功完成 / Completed: ${completed_count}"
  echo "   ⏭️  已跳過 / Skipped: ${skipped_count}"
  echo "   ❌ 失敗 / Failed: ${failed_count}"
  echo "   📁 總計 / Total: ${#cases_dirs[@]}"
  echo "   📂 Log 目錄 / Logs root: $LOG_ROOT"
}

main "$@"