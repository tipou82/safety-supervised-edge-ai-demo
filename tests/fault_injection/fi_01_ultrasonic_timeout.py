#!/usr/bin/env python3
"""
FI-01 — Ultrasonic node timeout.

Kills ultrasonic_node and observes state machine response.
With camera active (M4): camera_valid=true, ultrasonic_valid=false
→ DEGRADED (one sensor path — graceful degradation).

Expected:
  - Within 1s: decision_node logs "Ultrasonic timeout — marking invalid"
  - /system_state: DEGRADED
  - /diagnostics trigger: degraded_one_sensor
  - Yellow LED ON, green LED ON, red LED OFF
  - vel_scale: 0.2

Requirement: SYS-SAFE-008 (graceful degradation)
Educational demonstrator — not ISO 26262 certified.
"""

import subprocess
import time
import sys

OBSERVE_S = 5


def main():
    print("=" * 60)
    print(" FI-01: Ultrasonic Node Timeout")
    print(" Kill ultrasonic_node, observe DEGRADED state")
    print("=" * 60)
    print()
    print("Pre-condition: system running via 'ros2 launch safety_demo demo.launch.py'")
    print("               /reset published (system in NORMAL or DEGRADED)")
    print()
    input("Press Enter to inject fault...")

    # Kill ultrasonic_node
    result = subprocess.run(['pkill', '-f', 'ultrasonic_node'], capture_output=True)
    t_fault = time.monotonic()
    print(f"\n[{time.strftime('%H:%M:%S')}] ultrasonic_node killed (return code {result.returncode})")
    print(f"Observing for {OBSERVE_S}s — watch /system_state and /diagnostics")
    print()

    time.sleep(OBSERVE_S)

    print()
    print("=" * 60)
    print(" FI-01 — Expected Results")
    print("=" * 60)
    print("  State:   DEGRADED")
    print("  Trigger: degraded_one_sensor")
    print("  LEDs:    Green ON, Yellow ON, Red OFF")
    print("  Source:  decision_node logs 'Ultrasonic timeout'")
    print()
    print("Verify with:")
    print("  ros2 topic echo /system_state --once")
    print("  ros2 topic echo /diagnostics --once")
    print()

    passed = input("Did system enter DEGRADED state? (yes/no): ").strip().lower()
    print()
    print(f"FI-01 RESULT: {'PASS' if passed == 'yes' else 'FAIL'}")


if __name__ == '__main__':
    main()
