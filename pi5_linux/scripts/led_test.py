#!/usr/bin/env python3
# M1.1 – Pi5 Hardware Component Bring-up: LED toggle test.
# Tests green, yellow, and red LEDs individually via GPIO.
# This is a manual bring-up script only. It does NOT implement
# system state logic, safety decisions, or ROS2 node behaviour.

# --- Wiring assumptions (confirm before running) ---
# GPIO 17 (Pin 11) → Green LED  (NORMAL state indicator)
# GPIO 27 (Pin 13) → Yellow LED (DEGRADED state indicator)
# GPIO 22 (Pin 15) → Red LED    (SAFE STATE indicator)
# Low side: all LEDs connected to GND.
# Ensure current-limiting resistors (330 Ω recommended) are present on each LED.
#
# NOTE: GPIO 17 and GPIO 27 are reserved for heartbeat output and emergency stop
# input in the target architecture (hardware/gpio_mapping.md). Their assignment
# to LEDs is confirmed for M1.1 bring-up. The heartbeat and e-stop signals will
# be assigned to different pins before M2 integration.
# GPIO 22 was previously Motor A IN1 — also reassigned to Red LED here.

import sys
import time

# GPIO numbers — confirmed wiring for M1.1 bring-up
GPIO_GREEN  = 17  # Pin 11 — NORMAL state indicator
GPIO_YELLOW = 27  # Pin 13 — DEGRADED state indicator
GPIO_RED    = 22  # Pin 15 — SAFE STATE indicator

# Pi5 GPIO chip (RP1 southbridge)
GPIO_CHIP = 4

LEDS = [
    (GPIO_GREEN,  "GREEN  / NORMAL    (GPIO 17, Pin 11)"),
    (GPIO_YELLOW, "YELLOW / DEGRADED  (GPIO 27, Pin 13)"),
    (GPIO_RED,    "RED    / SAFE STATE (GPIO 22, Pin 15)"),
]


def check_wiring() -> bool:
    print("====================================================")
    print(" M1.1 LED Bring-up Test")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("====================================================")
    print()
    print("Wiring (confirmed M1.1 assignment):")
    print("  GPIO 17 (Pin 11) → Green LED  (NORMAL state indicator)")
    print("  GPIO 27 (Pin 13) → Yellow LED (DEGRADED state indicator)")
    print("  GPIO 22 (Pin 15) → Red LED    (SAFE STATE indicator)")
    print("  Low side: all LEDs to GND")
    print()
    print("WARNING: Do NOT run this script if wiring is not confirmed.")
    print("         Incorrect wiring may damage GPIO pins.")
    print()
    answer = input("Have you verified the wiring above? (yes/no): ").strip().lower()
    if answer != "yes":
        print("Aborted. Verify wiring and re-run.")
        return False
    return True


def import_lgpio():
    try:
        import lgpio
        return lgpio
    except ImportError:
        print("[FAIL] lgpio not installed.")
        print("       Install with: sudo apt install python3-lgpio")
        sys.exit(1)


def test_led(lgpio, handle: int, gpio: int, label: str) -> bool:
    print(f"--- Testing {label} ---")
    lgpio.gpio_claim_output(handle, gpio, 0)

    print(f"  Turning ON  {label}...")
    lgpio.gpio_write(handle, gpio, 1)
    time.sleep(1.5)

    answer = input(f"  Is the {label.split()[0]} LED ON? (yes/no): ").strip().lower()
    on_ok = answer == "yes"

    print(f"  Turning OFF {label}...")
    lgpio.gpio_write(handle, gpio, 0)
    time.sleep(0.5)

    answer = input(f"  Is the {label.split()[0]} LED OFF? (yes/no): ").strip().lower()
    off_ok = answer == "yes"

    lgpio.gpio_free(handle, gpio)

    result = on_ok and off_ok
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {label}")
    print()
    return result


def main() -> None:
    if not check_wiring():
        sys.exit(0)

    lgpio = import_lgpio()

    try:
        handle = lgpio.gpiochip_open(GPIO_CHIP)
    except Exception as e:
        print(f"[FAIL] Cannot open gpiochip{GPIO_CHIP}: {e}")
        print("       Try: sudo apt install python3-lgpio")
        print("       Ensure you have GPIO access (may need sudo or gpio group).")
        sys.exit(1)

    results = {}
    try:
        for gpio, label in LEDS:
            results[label] = test_led(lgpio, handle, gpio, label)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        lgpio.gpiochip_close(handle)

    print("====================================================")
    print(" LED Test Summary")
    print("====================================================")
    for label, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {label}")
    print()
    all_pass = all(results.values())
    if all_pass:
        print("All LEDs: PASS")
    else:
        print("One or more LEDs: FAIL — check wiring and re-run.")


if __name__ == "__main__":
    main()
