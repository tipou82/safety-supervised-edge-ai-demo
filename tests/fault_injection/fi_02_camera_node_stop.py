#!/usr/bin/env python3
"""
FI-02 — Camera AI node process stop.

Kills camera_ai_node and observes state machine response.
camera_valid times out after 2s → camera_valid=false, ultrasonic_valid=true
→ DEGRADED (one sensor path — confirms AI failure is handled safely).

Expected:
  - Within 2s: camera_valid times out in decision_node
  - /system_state: DEGRADED (if was NORMAL/WARNING before)
  - /diagnostics trigger: degraded_one_sensor
  - Yellow LED ON (if was NORMAL → DEGRADED), green LED ON, red LED OFF
  - vel_scale: 0.2
  - System does NOT enter SAFE_STATE (single sensor failure = DEGRADED, not SAFE)

Requirement: SYS-SAFE-001 (AI not in safety path), SYS-SAFE-008 (degradation)
Educational demonstrator — not ISO 26262 certified.
"""

import subprocess
import time

OBSERVE_S = 5


def main():
    print("=" * 60)
    print(" FI-02: Camera AI Node Process Stop")
    print(" Kill camera_ai_node, observe DEGRADED (not SAFE_STATE)")
    print("=" * 60)
    print()
    print("Pre-condition: system running, camera active, in NORMAL state")
    print("               (camera detecting hand or just running)")
    print()
    input("Press Enter to inject fault...")

    result = subprocess.run(['pkill', '-f', 'camera_ai_node'], capture_output=True)
    print(f"\n[{time.strftime('%H:%M:%S')}] camera_ai_node killed (return code {result.returncode})")
    print(f"Waiting 3s for camera_valid timeout (2s threshold)...")
    time.sleep(3)
    print(f"Observing for {OBSERVE_S - 3}s...")
    time.sleep(OBSERVE_S - 3)

    print()
    print("=" * 60)
    print(" FI-02 — Expected Results")
    print("=" * 60)
    print("  State:   DEGRADED  (NOT SAFE_STATE)")
    print("  Trigger: degraded_one_sensor")
    print("  LEDs:    Green ON, Yellow ON, Red OFF")
    print("  Key:     AI failure → DEGRADED only, not SAFE_STATE")
    print("           This confirms SYS-SAFE-001 (AI not in safety path)")
    print()
    print("Verify with:")
    print("  ros2 topic echo /system_state --once")
    print()

    passed = input("Did system enter DEGRADED (not SAFE_STATE)? (yes/no): ").strip().lower()
    print()
    print(f"FI-02 RESULT: {'PASS' if passed == 'yes' else 'FAIL'}")


if __name__ == '__main__':
    main()
