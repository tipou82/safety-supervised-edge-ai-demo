#!/usr/bin/env python3
# M2 hardware bring-up: emergency stop input test (Pi5 side).
# Tests GPIO 25 (Pin 22) as active-low e-stop input from Pi400 GPIO 25.
# Reads GPIO 25 at 10 Hz for 10 seconds and reports observed states.
# Requires the operator to manually toggle Pi400 GPIO 25 during the test.
# Educational demonstrator — not ISO 26262 certified.

import sys
import time

GPIO_ESTOP = 25   # Pin 22 — active-low e-stop input
GPIO_CHIP   = 4   # Pi5 RP1 southbridge

SAMPLE_HZ   = 10
DURATION_S  = 10


def import_lgpio():
    try:
        import lgpio
        return lgpio
    except ImportError:
        print("[FAIL] lgpio not installed.")
        print("       Install with: sudo apt install python3-lgpio")
        sys.exit(1)


def main() -> None:
    print("======================================================")
    print(" M2 E-Stop Input Test — Pi5 GPIO 25 (Pin 22)")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("======================================================")
    print()
    print("Wiring expected:")
    print("  Pi400 GPIO 25 (Pin 22) → Pi5 GPIO 25 (Pin 22)")
    print("  Pi5 GPIO 25 has internal pull-up — reads HIGH when undriven")
    print("  Pi400 drives LOW to assert e-stop (active-low)")
    print()
    print("Test procedure:")
    print("  1. Script reads GPIO 25 for 10 seconds at 10 Hz")
    print("  2. Run estop_output_test.py on Pi400 simultaneously (or toggle manually)")
    print("  3. Observe HIGH → LOW → HIGH transitions in output below")
    print()
    input("Press Enter to start the 10-second capture...")
    print()

    lgpio = import_lgpio()

    try:
        handle = lgpio.gpiochip_open(GPIO_CHIP)
    except Exception as e:
        print(f"[FAIL] Cannot open gpiochip{GPIO_CHIP}: {e}")
        sys.exit(1)

    lgpio.gpio_claim_input(handle, GPIO_ESTOP, lgpio.SET_PULL_UP)

    interval = 1.0 / SAMPLE_HZ
    samples = SAMPLE_HZ * DURATION_S
    readings = []

    print(f"Reading GPIO {GPIO_ESTOP} for {DURATION_S}s ({samples} samples)...")
    print()

    try:
        for i in range(samples):
            val = lgpio.gpio_read(handle, GPIO_ESTOP)
            state = "HIGH (inactive)" if val else "LOW  (E-STOP ASSERTED)"
            ts = time.strftime("%H:%M:%S")
            print(f"  [{ts}] GPIO 25 = {val}  {state}")
            readings.append(val)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        lgpio.gpio_free(handle, GPIO_ESTOP)
        lgpio.gpiochip_close(handle)

    print()
    highs = readings.count(1)
    lows  = readings.count(0)
    total = len(readings)

    print("======================================================")
    print(" E-Stop Input Test Summary")
    print("======================================================")
    print(f"  Total samples : {total}")
    print(f"  HIGH (inactive): {highs}")
    print(f"  LOW  (asserted): {lows}")
    print()

    if lows == 0 and highs == total:
        print("  [INFO] GPIO 25 stayed HIGH throughout.")
        print("         If Pi400 was not driving LOW, this is expected.")
        print("         Re-run with estop_output_test.py active on Pi400.")
    elif lows > 0 and highs > 0:
        print("  [PASS] GPIO 25 transitioned HIGH↔LOW — e-stop wire confirmed functional.")
    elif lows == total:
        print("  [INFO] GPIO 25 stayed LOW throughout — Pi400 holding e-stop asserted.")
        print("         Expected at boot (fail-safe default). Release from Pi400 to verify HIGH.")
    else:
        print("  [INFO] Review readings above.")


if __name__ == "__main__":
    main()
