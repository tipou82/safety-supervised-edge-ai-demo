#!/usr/bin/env python3
"""
FI-03 — Both sensor paths simultaneously invalid.

Kills camera_ai_node then ultrasonic_node sequentially.
Both camera_valid and ultrasonic_valid become false
→ SAFE_STATE (both_sensors_invalid rule, Rule 3).

Expected:
  - After both nodes killed and timeouts expire (~2s):
  - /system_state: SAFE_STATE
  - /diagnostics trigger: both_sensors_invalid
  - Green LED OFF, Red LED ON
  - vel_scale: 0.0
  - Latches — requires /reset to exit

Requirement: SYS-SAFE-006, SYS-SAFE-011
Educational demonstrator — not ISO 26262 certified.
"""

import subprocess
import time

OBSERVE_S = 5


def main():
    print("=" * 60)
    print(" FI-03: Both Sensor Paths Invalid")
    print(" Kill camera_ai_node + ultrasonic_node → SAFE_STATE")
    print("=" * 60)
    print()
    print("Pre-condition: system running, in NORMAL or DEGRADED state")
    print()
    input("Press Enter to inject fault...")

    # Kill camera first
    r1 = subprocess.run(['pkill', '-f', 'camera_ai_node'], capture_output=True)
    print(f"\n[{time.strftime('%H:%M:%S')}] camera_ai_node killed ({r1.returncode})")

    time.sleep(0.2)

    # Kill ultrasonic
    r2 = subprocess.run(['pkill', '-f', 'ultrasonic_node'], capture_output=True)
    print(f"[{time.strftime('%H:%M:%S')}] ultrasonic_node killed ({r2.returncode})")

    print(f"\nWaiting for timeouts (camera 2s, ultrasonic 1s)...")
    time.sleep(3)
    print(f"Observing for {OBSERVE_S - 3}s...")
    time.sleep(OBSERVE_S - 3)

    print()
    print("=" * 60)
    print(" FI-03 — Expected Results")
    print("=" * 60)
    print("  State:   SAFE_STATE")
    print("  Trigger: both_sensors_invalid")
    print("  LEDs:    Green OFF, Red ON")
    print("  Latches: yes — publish /reset to exit after restarting nodes")
    print()
    print("Verify with:")
    print("  ros2 topic echo /system_state --once")
    print("  ros2 topic echo /diagnostics --once")
    print()

    passed = input("Did system enter SAFE_STATE? (yes/no): ").strip().lower()
    print()
    print(f"FI-03 RESULT: {'PASS' if passed == 'yes' else 'FAIL'}")


if __name__ == '__main__':
    main()
