#!/usr/bin/env python3
# M2 hardware bring-up: emergency stop output test (Pi400 side).
# Drives GPIO 25 (Pin 22) LOW then HIGH to simulate e-stop assert/release.
# Run simultaneously with estop_input_test.py on Pi5 to verify the wire.
# Pi400 uses gpiochip0 (BCM2711).
# Educational demonstrator — not ISO 26262 certified.

import sys
import time

GPIO_ESTOP = 25   # Pin 22 — active-low e-stop output
GPIO_CHIP  = 0    # Pi400 BCM2711

ASSERT_DURATION_S  = 3.0   # hold LOW for 3 seconds
RELEASE_DURATION_S = 3.0   # hold HIGH for 3 seconds


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
    print(" M2 E-Stop Output Test — Pi400 GPIO 25 (Pin 22)")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("======================================================")
    print()
    print("Wiring expected:")
    print("  Pi400 GPIO 25 (Pin 22) → Pi5 GPIO 25 (Pin 22)")
    print("  Active-low: LOW = e-stop asserted, HIGH = released")
    print()
    print("Sequence:")
    print(f"  1. Assert e-stop (GPIO 25 → LOW) for {ASSERT_DURATION_S:.0f}s")
    print(f"  2. Release e-stop (GPIO 25 → HIGH) for {RELEASE_DURATION_S:.0f}s")
    print(f"  3. Re-assert e-stop (GPIO 25 → LOW) — fail-safe default")
    print()
    print("Run estop_input_test.py on Pi5 simultaneously to verify.")
    print()
    input("Press Enter to start...")
    print()

    lgpio = import_lgpio()

    try:
        handle = lgpio.gpiochip_open(GPIO_CHIP)
    except Exception as e:
        print(f"[FAIL] Cannot open gpiochip{GPIO_CHIP}: {e}")
        print("       Ensure lgpio is installed and you have GPIO access.")
        sys.exit(1)

    try:
        lgpio.gpio_claim_output(handle, GPIO_ESTOP, 1)   # start HIGH (released)

        # Phase 1: Assert (LOW)
        print(f"[{time.strftime('%H:%M:%S')}] Asserting e-stop: GPIO 25 → LOW ...")
        lgpio.gpio_write(handle, GPIO_ESTOP, 0)
        time.sleep(ASSERT_DURATION_S)

        # Phase 2: Release (HIGH)
        print(f"[{time.strftime('%H:%M:%S')}] Releasing e-stop: GPIO 25 → HIGH ...")
        lgpio.gpio_write(handle, GPIO_ESTOP, 1)
        time.sleep(RELEASE_DURATION_S)

        # Phase 3: Re-assert (fail-safe default)
        print(f"[{time.strftime('%H:%M:%S')}] Re-asserting e-stop (fail-safe default): GPIO 25 → LOW")
        lgpio.gpio_write(handle, GPIO_ESTOP, 0)

    except KeyboardInterrupt:
        print("\nStopped by user — leaving GPIO 25 LOW (fail-safe).")
        lgpio.gpio_write(handle, GPIO_ESTOP, 0)
    finally:
        lgpio.gpiochip_close(handle)

    print()
    print("======================================================")
    print(" E-Stop Output Test Complete")
    print("======================================================")
    print("  GPIO 25 left LOW (e-stop asserted — fail-safe default).")
    print("  Check Pi5 estop_input_test.py output for HIGH↔LOW transitions.")
    print()
    print("  [PASS] if Pi5 observed: HIGH → LOW → HIGH → LOW")
    print("  [FAIL] if Pi5 stayed HIGH throughout (check wiring: Pi400 Pin 22 → Pi5 Pin 22)")


if __name__ == "__main__":
    main()
