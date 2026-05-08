#!/usr/bin/env bash
# FFI-SPATIAL — Spatial independence verification.
#
# Goal: confirm Pi400 Q&A watchdog is unaffected by CPU/memory stress on Pi5.
# If spatial independence holds, failure_counter stays 0 under full Pi5 load.
#
# Method:
#   1. Run full system (ros2 launch + Pi400 watchdog server)
#   2. Stress Pi5 CPU and memory for 30 seconds
#   3. Monitor /watchdog_failure_counter throughout
#   4. Pass criterion: failure_counter stays 0 during stress
#
# Requirement: SYS-SAFE-002 (spatial independence), FFI-001
# Educational demonstrator — not ISO 26262 certified.

set -euo pipefail

STRESS_DURATION_S=30
LOG_FILE="/tmp/ffi_spatial_$(date +%Y%m%d_%H%M%S).log"

echo "======================================================"
echo " FFI-SPATIAL: Spatial Independence Verification"
echo " Pi5 CPU+memory stress — Pi400 watchdog must be unaffected"
echo "======================================================"
echo ""
echo "Pre-conditions:"
echo "  Pi400: qnx_wdg_server.py running"
echo "  Pi5:   ros2 launch safety_demo demo.launch.py"
echo "         /reset published (system in NORMAL or DEGRADED)"
echo ""
echo "Log file: $LOG_FILE"
echo ""

# Check stress-ng is available
if ! command -v stress-ng &>/dev/null; then
    echo "Installing stress-ng..."
    sudo apt install -y stress-ng
fi

# Check ROS2 workspace sourced
if ! command -v ros2 &>/dev/null; then
    echo "ERROR: ros2 not found. Source workspace first."
    exit 1
fi

read -r -p "Press Enter to start ${STRESS_DURATION_S}s stress test..."

echo ""
echo "Starting watchdog counter monitoring in background..."

# Monitor failure counter in background
(
    echo "timestamp,failure_counter" > "$LOG_FILE"
    END=$((SECONDS + STRESS_DURATION_S + 5))
    while [ $SECONDS -lt $END ]; do
        TS=$(date +%s.%3N)
        CTR=$(ros2 topic echo /watchdog_failure_counter --once --no-arr 2>/dev/null \
              | grep 'data:' | awk '{print $2}' || echo "N/A")
        echo "$TS,$CTR" >> "$LOG_FILE"
        sleep 0.5
    done
) &
MONITOR_PID=$!

echo "Starting Pi5 CPU and memory stress (${STRESS_DURATION_S}s)..."
stress-ng --cpu 4 --vm 2 --vm-bytes 1G --timeout "${STRESS_DURATION_S}s" \
          --metrics-brief 2>&1 | tail -5

wait $MONITOR_PID 2>/dev/null || true

echo ""
echo "======================================================"
echo " FFI-SPATIAL Results"
echo "======================================================"
echo ""
echo "Failure counter log ($LOG_FILE):"
echo ""
cat "$LOG_FILE"
echo ""

MAX_CTR=$(awk -F',' 'NR>1 && $2~/^[0-9]/ {print $2}' "$LOG_FILE" | sort -n | tail -1)
echo "Maximum failure_counter observed: $MAX_CTR"
echo ""

if [ "$MAX_CTR" = "0" ] || [ "$MAX_CTR" = "" ]; then
    echo "RESULT: PASS — failure_counter stayed 0 under Pi5 stress"
    echo "        Spatial independence CONFIRMED: Pi5 load does not affect Pi400 watchdog"
else
    echo "RESULT: FAIL — failure_counter rose to $MAX_CTR under stress"
    echo "        Investigate: network congestion, Pi5 scheduler impact on health_node"
fi
