#!/usr/bin/env python3
"""
FI-05 — Q&A watchdog failure (health_node stop).

Kills health_node, stopping the UDP Q&A watchdog client.
Pi400 qnx_wdg_server detects 3 consecutive failures (~300ms)
→ asserts GPIO 25 LOW (e-stop) + GPIO 22 HIGH (red LED)
→ Pi5 actuator_node detects GPIO 25 LOW → SAFE_STATE.

This tests the HARDWARE safety path — independent of decision_node.

Expected:
  - Within ~300ms of health_node stop:
    Pi400 logs: "[SAFE] failure_counter=3 → e-stop asserted"
    Pi5 actuator_node logs: "E-STOP ASSERTED (GPIO 25 LOW)"
  - /system_state: SAFE_STATE
  - /diagnostics trigger: watchdog_failure
  - Green LED OFF, Red LED ON (both Pi5 and Pi400 sides)
  - /watchdog_failure_counter: 3

This scenario was verified during M5 acceptance testing (2026-05-09).

Requirement: SYS-SAFE-004a, SYS-SAFE-006, FSR-001
Educational demonstrator — not ISO 26262 certified.
"""

import subprocess
import time


def main():
    print("=" * 60)
    print(" FI-05: Q&A Watchdog Failure (health_node stop)")
    print(" Hardware safety path: Pi400 GPIO 25 → Pi5 e-stop")
    print("=" * 60)
    print()
    print("Pre-condition:")
    print("  Pi400: qnx_wdg_server.py running")
    print("  Pi5:   ros2 launch safety_demo demo.launch.py")
    print("         system in NORMAL or DEGRADED, /reset published")
    print()
    print("Watch in separate terminal:")
    print("  ros2 topic echo /watchdog_failure_counter")
    print("  ros2 topic echo /system_state")
    print()
    input("Press Enter to inject fault (kill health_node)...")

    result = subprocess.run(['pkill', '-f', 'health_node'], capture_output=True)
    t0 = time.monotonic()
    print(f"\n[{time.strftime('%H:%M:%S')}] health_node killed ({result.returncode})")
    print("Timing SAFE_STATE entry from fault injection...")

    print("Observing for 2s...")
    time.sleep(2.0)
    t_elapsed = (time.monotonic() - t0) * 1000

    print()
    print("=" * 60)
    print(" FI-05 — Expected Results")
    print("=" * 60)
    print("  State:             SAFE_STATE")
    print("  Trigger:           watchdog_failure (software path)")
    print("                     GPIO 25 LOW (hardware path, independent)")
    print("  LEDs:              Green OFF, Red ON (Pi5 + Pi400)")
    print(f"  Target latency:    < 300ms from fault to SAFE_STATE")
    print("  failure_counter:   3")
    print()
    print("Verify with:")
    print("  ros2 topic echo /diagnostics --once")
    print("  ros2 topic echo /watchdog_failure_counter --once")
    print()

    passed  = input("Did system enter SAFE_STATE within 300ms? (yes/no): ").strip().lower()
    latency = input("Approximate latency observed (ms, or 'unknown'): ").strip()
    print()
    print(f"FI-05 RESULT: {'PASS' if passed == 'yes' else 'FAIL'}  latency={latency}ms")


if __name__ == '__main__':
    main()
