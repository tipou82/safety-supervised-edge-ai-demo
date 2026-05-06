#!/usr/bin/env python3
# M1.1 – Pi5 Hardware Component Bring-up: active buzzer toggle test.
# Verifies that the active 3.3 V buzzer responds to GPIO control.
# This is a manual bring-up script only. It does NOT implement
# warning patterns, safe-state alerts, or any runtime safety logic.

# --- Wiring assumptions (confirm before running) ---
# GPIO 26 (Pin 37) → Buzzer positive terminal
# GND    (Pin 39)  → Buzzer negative terminal
# Active 3.3 V buzzer — sounds when GPIO is driven HIGH.
# Do NOT use a passive buzzer (requires PWM frequency, different script).
# Current draw: typically 30–50 mA. Pi5 GPIO can source up to ~16 mA per pin.
# If buzzer draws more, use a NPN transistor (e.g. 2N2222) as a switch.

import sys
import time

GPIO_BUZZER = 26  # Pin 37
GPIO_CHIP   = 4   # Pi5 RP1 southbridge

BEEP_DURATION_S = 0.5   # Keep short — buzzer can be loud


def check_wiring() -> bool:
    print("====================================================")
    print(" M1.1 Buzzer Bring-up Test")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("====================================================")
    print()
    print("Wiring assumptions:")
    print("  GPIO 26 (Pin 37) → Buzzer (+)")
    print("  GND    (Pin 39)  → Buzzer (-)")
    print("  Active 3.3 V buzzer only (not passive).")
    print()
    print("WARNING: The buzzer may be LOUD. Be prepared.")
    print("WARNING: Do NOT run if wiring is not confirmed.")
    print()
    answer = input("Have you verified the wiring and are ready? (yes/no): ").strip().lower()
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


def main() -> None:
    if not check_wiring():
        sys.exit(0)

    lgpio = import_lgpio()

    try:
        handle = lgpio.gpiochip_open(GPIO_CHIP)
    except Exception as e:
        print(f"[FAIL] Cannot open gpiochip{GPIO_CHIP}: {e}")
        sys.exit(1)

    try:
        lgpio.gpio_claim_output(handle, GPIO_BUZZER, 0)

        print(f"\nActivating buzzer (GPIO {GPIO_BUZZER}) for {BEEP_DURATION_S} s...")
        lgpio.gpio_write(handle, GPIO_BUZZER, 1)
        time.sleep(BEEP_DURATION_S)
        lgpio.gpio_write(handle, GPIO_BUZZER, 0)
        print("Buzzer OFF.")

        answer = input("\nDid you hear the buzzer? (yes/no): ").strip().lower()
        if answer == "yes":
            print("[PASS] Buzzer test PASS.")
        else:
            print("[FAIL] Buzzer not heard. Check wiring, polarity, and buzzer type.")

    except KeyboardInterrupt:
        lgpio.gpio_write(handle, GPIO_BUZZER, 0)
        print("\nStopped by user.")
    finally:
        lgpio.gpio_free(handle, GPIO_BUZZER)
        lgpio.gpiochip_close(handle)


if __name__ == "__main__":
    main()
