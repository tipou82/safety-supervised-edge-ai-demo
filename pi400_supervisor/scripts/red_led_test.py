#!/usr/bin/env python3
# M2 hardware bring-up: red LED test from Pi400 side (diode-OR circuit).
# Tests that Pi400 GPIO 22 (Pin 15) can independently illuminate the red LED
# via the 1N4148 diode-OR circuit, without Pi5 GPIO 22 being driven.
# Pi400 uses gpiochip0 (BCM2711).
# Educational demonstrator — not ISO 26262 certified.

import sys
import time

GPIO_RED  = 22   # Pin 15 — red LED via 1N4148 diode-OR
GPIO_CHIP = 0    # Pi400 BCM2711


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
    print(" M2 Red LED Test — Pi400 GPIO 22 (Pin 15)")
    print(" Diode-OR circuit — Pi400 independent assertion")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("======================================================")
    print()
    print("Circuit:")
    print("  Pi400 GPIO 22 (Pin 15) → [150 Ω] → [D2: 1N4148] → Red LED (+) → GND")
    print("  Pi5   GPIO 22 (Pin 15) → [150 Ω] → [D1: 1N4148] → same junction")
    print()
    print("This test drives Pi400 GPIO 22 only.")
    print("Pi5 GPIO 22 should be LOW (or floating) during this test.")
    print("The red LED should illuminate from Pi400 drive alone.")
    print()

    answer = input("Confirm Pi5 GPIO 22 is LOW or not driven (yes/no): ").strip().lower()
    if answer != "yes":
        print("Aborted. Set Pi5 GPIO 22 LOW before running this test.")
        sys.exit(0)

    lgpio = import_lgpio()

    try:
        handle = lgpio.gpiochip_open(GPIO_CHIP)
    except Exception as e:
        print(f"[FAIL] Cannot open gpiochip{GPIO_CHIP}: {e}")
        sys.exit(1)

    result = False
    try:
        lgpio.gpio_claim_output(handle, GPIO_RED, 0)

        print()
        print(f"Turning ON  Red LED (Pi400 GPIO {GPIO_RED})...")
        lgpio.gpio_write(handle, GPIO_RED, 1)
        time.sleep(2.0)

        answer = input("Is the Red LED ON? (yes/no): ").strip().lower()
        on_ok = answer == "yes"

        print(f"Turning OFF Red LED (Pi400 GPIO {GPIO_RED})...")
        lgpio.gpio_write(handle, GPIO_RED, 0)
        time.sleep(1.0)

        answer = input("Is the Red LED OFF? (yes/no): ").strip().lower()
        off_ok = answer == "yes"

        result = on_ok and off_ok

    except KeyboardInterrupt:
        print("\nStopped by user.")
        lgpio.gpio_write(handle, GPIO_RED, 0)
    finally:
        lgpio.gpio_free(handle, GPIO_RED)
        lgpio.gpiochip_close(handle)

    print()
    print("======================================================")
    print(" Red LED Test Summary (Pi400 side)")
    print("======================================================")
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] Red LED independent assertion from Pi400 GPIO 22")
    print()
    if not result:
        print("  Troubleshooting:")
        print("  - Check D2 (1N4148) orientation: anode toward GPIO/resistor, cathode toward LED")
        print("  - Check 150 Ω resistor is in series (not 330 Ω)")
        print("  - Check wire from Pi400 GPIO 22 (Pin 15) to breadboard")
        print("  - Measure voltage at Pi400 Pin 15 with GPIO HIGH — expect ~3.3V")


if __name__ == "__main__":
    main()
