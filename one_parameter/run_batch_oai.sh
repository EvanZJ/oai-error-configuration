#!/usr/bin/env bash
set -euo pipefail

### ====== User-tunable Settings ======
# Root path containing cu/ and du/ folders with case subdirs
BASE_OUTPUT_PATH="/home/sionna/evan/CursorAutomation/cursor_gen_conf/one_parameter/output"

# Baseline confs (used for the unmodified side)
BASELINE_CU="/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/cu_gnb.conf"
BASELINE_DU="/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/du_gnb.conf"

# Fixed UE config
UE_CONF="/home/sionna/evan/CursorAutomation/cursor_gen_conf/baseline_conf/ue_oai.conf"

# Binary paths
NR_GNB_BIN="/home/sionna/evan/openairinterface5g/cmake_targets/ran_build/build/nr-softmodem"
NR_UE_BIN="/home/sionna/evan/openairinterface5g/cmake_targets/ran_build/build/nr-uesoftmodem"

RFSIMULATOR_TARGET="server"
RUNTIME_SECS=30
PROGRESS_INTERVAL=5
DELAY_AFTER_CU=4
DELAY_AFTER_DU=4
LOG_ROOT="./logs_batch_run"

DOCKER_CONTAINERS="78d03d6ed583 a86f24977b1b a752fa1f5a13 fd3aca606db3 f4e16e89b2ee f612b909f593 766a65ecce01 3f2a91613157 24c88761f8ef"
### ====== End of User-tunable Settings ======


timestamp() {
  date +"%Y%m%d_%H%M%S"
}

ensure_bins() {
  for b in "$NR_GNB_BIN" "$NR_UE_BIN"; do
    if [[ ! -x "$b" ]]; then
      echo "ERROR: Not found or not executable: $b"
      exit 1
    fi
  done
}

cleanup_procs() {
  sudo pkill -9 -f "[n]r-softmodem" 2>/dev/null || true
  sudo pkill -9 -f "[n]r-uesoftmodem" 2>/dev/null || true
}

restart_containers() {
  echo "Restarting Docker containers..."
  for cid in $DOCKER_CONTAINERS; do
    sudo docker restart "$cid" 2>/dev/null || echo "WARNING: Failed to restart container $cid"
  done
  sleep 5
}

sleep_with_dots() {
  local total="$RUNTIME_SECS"
  local step="$PROGRESS_INTERVAL"
  local elapsed=0

  echo -n "Running test (${total}s): "
  while (( elapsed + step <= total )); do
    sleep "$step"
    elapsed=$(( elapsed + step ))
    echo -n "."
  done
  if (( elapsed < total )); then
    sleep $(( total - elapsed ))
  fi
  echo ""
}

run_one_case() {
  local CASE_DIR="$1"
  local CASE_TYPE="$2"  # "cu" or "du"
  local CASE_NAME="$3"  # e.g., cu_cases_01

  local OUT_DIR="${LOG_ROOT}/$(timestamp)_${CASE_NAME}"
  mkdir -p "$OUT_DIR"

  echo "Starting test: $CASE_NAME --> log: $OUT_DIR"

  # The .conf file is named exactly like the case folder (e.g., cu_cases_01.conf)
  local EXPECTED_CONF_FILE="${CASE_NAME}.conf"
  local MOD_CONF_PATH="$CASE_DIR/$EXPECTED_CONF_FILE"

  if [[ ! -f "$MOD_CONF_PATH" ]]; then
    echo "ERROR: Missing expected config file: $MOD_CONF_PATH"
    echo "       Each case folder must contain: $EXPECTED_CONF_FILE"
    return 1
  fi

  local CU_CONF_TO_USE DU_CONF_TO_USE
  if [[ "$CASE_TYPE" == "cu" ]]; then
    CU_CONF_TO_USE="$MOD_CONF_PATH"
    DU_CONF_TO_USE="$BASELINE_DU"
  else
    CU_CONF_TO_USE="$BASELINE_CU"
    DU_CONF_TO_USE="$MOD_CONF_PATH"
  fi

  # Resolve to absolute paths
  CU_CONF_TO_USE="$(readlink -f "$CU_CONF_TO_USE")"
  DU_CONF_TO_USE="$(readlink -f "$DU_CONF_TO_USE")"
  local UE_CONF_ABS="$(readlink -f "$UE_CONF")"

  echo "Cleaning up lingering processes..."
  cleanup_procs

  pushd "$OUT_DIR" >/dev/null

  # Start CU
  echo "[CU] Launching: $CU_CONF_TO_USE"
  sudo -E env RFSIMULATOR="$RFSIMULATOR_TARGET" \
    "$NR_GNB_BIN" --rfsim --sa -O "$CU_CONF_TO_USE" \
    > "cu.stdout.log" 2>&1 &
  local CU_PID=$!
  echo "    PID = $CU_PID"
  sleep "${DELAY_AFTER_CU}"

  # Start DU
  echo "[DU] Launching: $DU_CONF_TO_USE"
  sudo -E env RFSIMULATOR="$RFSIMULATOR_TARGET" \
    "$NR_GNB_BIN" --rfsim --sa -O "$DU_CONF_TO_USE" \
    > "du.stdout.log" 2>&1 &
  local DU_PID=$!
  echo "    PID = $DU_PID"
  sleep "${DELAY_AFTER_DU}"

  # Start UE
  echo "[UE] Launching: $UE_CONF_ABS"
  sudo "$NR_UE_BIN" -r 106 --numerology 1 --band 78 -C 3619200000 \
    --rfsim -O "$UE_CONF_ABS" \
    > "ue.stdout.log" 2>&1 &
  local UE_PID=$!
  echo "    PID = $UE_PID"

  echo "Entering test window..."
  sleep_with_dots

  echo "Time's up, cleaning up processes..."
  cleanup_procs

  # Generate plain-text tail summary
  {
    echo "===== CU stdout (tail -n 100) ====="; tail -n 100 "cu.stdout.log" 2>/dev/null || true; echo
    echo "===== DU stdout (tail -n 100) ====="; tail -n 100 "du.stdout.log" 2>/dev/null || true; echo
    echo "===== UE stdout (tail -n 100) ====="; tail -n 100 "ue.stdout.log" 2>/dev/null || true; echo
  } > "tail100_summary.log"

  # Generate JSON version
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

  # Record manifest
  {
    echo "CASE_NAME=${CASE_NAME}"
    echo "CASE_DIR=${CASE_DIR}"
    echo "CASE_TYPE=${CASE_TYPE}"
    echo "CU_CONF=${CU_CONF_TO_USE}"
    echo "DU_CONF=${DU_CONF_TO_USE}"
    echo "UE_CONF=${UE_CONF_ABS}"
    echo "START_TIME=$(date -Iseconds)"
    echo "DURATION=${RUNTIME_SECS}s"
  } > "run_manifest.txt"

  popd >/dev/null

  echo "Done: $CASE_NAME"
}

main() {
  echo "Checking binaries..."
  ensure_bins

  mkdir -p "$LOG_ROOT"

  trap 'echo "Interrupt caught, cleaning up..."; cleanup_procs; exit 130' INT TERM

  # Collect all valid case folders
  local case_dirs=()
  for type_dir in "$BASE_OUTPUT_PATH"/{cu,du}; do
    if [[ ! -d "$type_dir" ]]; then
      echo "Skipping missing type directory: $type_dir"
      continue
    fi
    local type_name
    type_name="$(basename "$type_dir")"
    for case_subdir in "$type_dir"/*/; do
      if [[ -d "$case_subdir" ]]; then
        case_subdir="${case_subdir%/}"
        local case_name="$(basename "$case_subdir")"
        if [[ -f "$case_subdir/cases_delta.json" ]]; then
          case_dirs+=("$type_name|$case_subdir|$case_name")
        else
          echo "Skipping (missing cases_delta.json): $case_subdir"
        fi
      fi
    done
  done

  if (( ${#case_dirs[@]} == 0 )); then
    echo "ERROR: No valid case folders found in $BASE_OUTPUT_PATH"
    exit 1
  fi

  echo "Number of test cases to process: ${#case_dirs[@]}"

  local counter=0
  restart_containers

  for entry in "${case_dirs[@]}"; do
    IFS='|' read -r case_type case_dir case_name <<< "$entry"
    if run_one_case "$case_dir" "$case_type" "$case_name"; then
      counter=$((counter + 1))
      if (( counter % 100 == 0 )); then
        restart_containers
      fi
    fi
    echo
    sleep 2
  done

  echo "All tests finished. Logs root: $LOG_ROOT"
}

main "$@"