#!/usr/bin/env python3
# M1.1 – Pi5 Hardware Component Bring-up: LED toggle test.
# Tests green, yellow, and red LEDs individually via GPIO.
# This is a manual bring-up script only. It does NOT implement
# system state logic, safety decisions, or ROS2 node behaviour.

# --- Wiring assumptions (confirm before running) ---
# GPIO 16 (Pin 36) → Green LED anode → 330 Ω resistor → GND (Pin 39)
# GPIO 20 (Pin 38) → Yellow LED anode → 330 Ω resistor → GND (Pin 39)
# GPIO 21 (Pin 40) → Red LED anode → 330 Ω resistor → GND (Pin 39)
# All LEDs: common cathode side to Pi5 GND.
# 3.3 V GPIO output — use 330 Ω current-limiting resistor on each LED.
# Do NOT connect LED anode directly to GPIO without a resistor.

import sys
import time

# GPIO numbers — update if wiring differs from the plan above
GPIO_GREEN  = 16  # Pin 36
GPIO_YELLOW = 20  # Pin 38
GPIO_RED    = 21  # Pin 40

# Pi5 GPIO chip (RP1 southbridge)
GPIO_CHIP = 4

LEDS = [
    (GPIO_GREEN,  "GREEN  (GPIO 16, Pin 36)"),
    (GPIO_YELLOW, "YELLOW (GPIO 20, Pin 38)"),
    (GPIO_RED,    "RED    (GPIO 21, Pin 40)"),
]


def check_wiring() -> bool:
    print("====================================================")
    print(" M1.1 LED Bring-up Test")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("====================================================")
    print()
    print("Wiring assumptions:")
    print("  GPIO 16 (Pin 36) → Green LED  → 330 Ω → GND (Pin 39)")
    print("  GPIO 20 (Pin 38) → Yellow LED → 330 Ω → GND (Pin 39)")
    print("  GPIO 21 (Pin 40) → Red LED    → 330 Ω → GND (Pin 39)")
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
