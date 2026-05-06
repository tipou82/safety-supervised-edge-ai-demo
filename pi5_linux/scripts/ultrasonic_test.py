#!/usr/bin/env python3
# M1.1 – Pi5 Hardware Component Bring-up: HC-SR04 ultrasonic distance test.
# Reads distance from Sensor 1 (front-center) via GPIO 23 (TRIG) / GPIO 24 (ECHO).
# This is a bring-up script only. It does NOT implement filtering, plausibility
# checking, sensor fusion, or any safety decision logic.
# ROS2 integration is deferred to a later milestone.

# --- Wiring assumptions (confirm before running) ---
# HC-SR04 Sensor 1 (front-centre):
#   VCC  → Pi5 Pin 2 (5 V)
#   GND  → Pi5 Pin 6 (GND)
#   TRIG → GPIO 23 (Pin 16)   — 3.3 V output is sufficient to trigger HC-SR04
#   ECHO → voltage divider → GPIO 24 (Pin 18)
#
# ECHO voltage divider (REQUIRED — HC-SR04 ECHO is 5 V, Pi5 GPIO is 3.3 V max):
#   HC-SR04 ECHO → R1 (1 kΩ) ─┬─ GPIO 24 (Pin 18)
#                               R2 (2 kΩ)
#                               GND
#   Vout = 5 V × 2/(1+2) ≈ 3.33 V  ✓
#
# Do NOT connect HC-SR04 ECHO directly to Pi5 GPIO without the voltage divider.
# 5 V on a Pi5 GPIO pin will damage the RP1 southbridge.

import sys
import time
import datetime

GPIO_TRIG  = 23   # Pin 16 — output
GPIO_ECHO  = 24   # Pin 18 — input (via voltage divider)
GPIO_CHIP  = 4    # Pi5 RP1 southbridge

SPEED_OF_SOUND_M_S = 343.0   # m/s at ~20 °C
TRIG_PULSE_S       = 0.00001  # 10 µs
ECHO_TIMEOUT_S     = 0.03     # 30 ms → ~5 m max; HC-SR04 max range is 4 m
SAMPLE_INTERVAL_S  = 0.2      # 5 Hz — well within HC-SR04 spec (max 10 Hz cycle)
N_SAMPLES          = 20       # number of readings before stopping


def check_wiring() -> bool:
    print("====================================================")
    print(" M1.1 Ultrasonic Sensor Bring-up Test (HC-SR04 #1)")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("====================================================")
    print()
    print("Wiring assumptions (Sensor 1 — front-centre):")
    print("  HC-SR04 VCC  → Pin 2  (5 V)")
    print("  HC-SR04 GND  → Pin 6  (GND)")
    print("  HC-SR04 TRIG → GPIO 23 (Pin 16)")
    print("  HC-SR04 ECHO → voltage divider (1 kΩ / 2 kΩ) → GPIO 24 (Pin 18)")
    print()
    print("WARNING: Do NOT skip the voltage divider on the ECHO line.")
    print("         5 V on a Pi5 GPIO pin WILL damage the hardware.")
    print()
    answer = input("Have you confirmed wiring AND voltage divider on ECHO? (yes/no): ").strip().lower()
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


def measure_distance(lgpio, handle: int) -> float | None:
    """Return distance in cm, or None on timeout."""
    # Ensure TRIG is LOW before pulse
    lgpio.gpio_write(handle, GPIO_TRIG, 0)
    time.sleep(0.000002)  # 2 µs settling

    # Send 10 µs TRIG pulse
    lgpio.gpio_write(handle, GPIO_TRIG, 1)
    time.sleep(TRIG_PULSE_S)
    lgpio.gpio_write(handle, GPIO_TRIG, 0)

    # Wait for ECHO to go HIGH (with timeout)
    t_start = time.perf_counter()
    while lgpio.gpio_read(handle, GPIO_ECHO) == 0:
        if time.perf_counter() - t_start > ECHO_TIMEOUT_S:
            return None  # timeout waiting for echo start

    echo_start = time.perf_counter()

    # Wait for ECHO to go LOW (with timeout)
    while lgpio.gpio_read(handle, GPIO_ECHO) == 1:
        if time.perf_counter() - echo_start > ECHO_TIMEOUT_S:
            return None  # timeout waiting for echo end

    echo_end = time.perf_counter()

    pulse_s = echo_end - echo_start
    distance_cm = (pulse_s * SPEED_OF_SOUND_M_S * 100) / 2
    return distance_cm


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
        lgpio.gpio_claim_output(handle, GPIO_TRIG, 0)
        lgpio.gpio_claim_input(handle, GPIO_ECHO)
    except Exception as e:
        print(f"[FAIL] GPIO claim failed: {e}")
        lgpio.gpiochip_close(handle)
        sys.exit(1)

    print(f"\nReading {N_SAMPLES} samples at {1/SAMPLE_INTERVAL_S:.0f} Hz. Press Ctrl+C to stop early.\n")
    print(f"{'Timestamp':<30} {'Distance (cm)':>14} {'Status':>10}")
    print("-" * 60)

    timeouts = 0
    readings = []
    try:
        for i in range(N_SAMPLES):
            ts = datetime.datetime.now().isoformat(timespec="milliseconds")
            dist = measure_distance(lgpio, handle)
            if dist is None:
                timeouts += 1
                print(f"{ts:<30} {'---':>14} {'TIMEOUT':>10}")
            elif dist < 2.0 or dist > 400.0:
                print(f"{ts:<30} {dist:>13.1f} {'OUT-OF-RANGE':>10}")
            else:
                readings.append(dist)
                print(f"{ts:<30} {dist:>13.1f} {'OK':>10}")
            time.sleep(SAMPLE_INTERVAL_S)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        lgpio.gpio_free(handle, GPIO_TRIG)
        lgpio.gpio_free(handle, GPIO_ECHO)
        lgpio.gpiochip_close(handle)

    print()
    print("====================================================")
    print(" Ultrasonic Test Summary")
    print("====================================================")
    total = len(readings) + timeouts
    if readings:
        avg = sum(readings) / len(readings)
        print(f"  Valid readings : {len(readings)}/{total}")
        print(f"  Timeouts       : {timeouts}/{total}")
        print(f"  Average dist   : {avg:.1f} cm")
        print(f"  Min / Max      : {min(readings):.1f} / {max(readings):.1f} cm")
        if timeouts == 0:
            print("  [PASS] Sensor responding with valid readings.")
        else:
            print("  [PARTIAL] Some timeouts. Check wiring and sensor alignment.")
    else:
        print(f"  [FAIL] No valid readings. {timeouts} timeouts.")
        print("  Check: VCC 5 V present, ECHO voltage divider, TRIG connected.")


if __name__ == "__main__":
    main()
