#!/usr/bin/env python3
# M1.1 – Pi5 Hardware Component Bring-up: Grove Ultrasonic Ranger distance test.
# Single-wire protocol: one SIG pin handles both trigger and echo.
# This is a bring-up script only. It does NOT implement filtering, plausibility
# checking, sensor fusion, or any safety decision logic.
# ROS2 integration is deferred to a later milestone.

# --- Wiring (confirmed) ---
# Grove Ultrasonic Ranger:
#   Yellow (SIG) → GPIO 23 (Pin 16)
#   White  (NC)  → not connected
#   Red    (VCC) → 3.3 V (Pin 1 or 17)
#   Black  (GND) → GND
#
# Powered at 3.3 V → SIG output is 3.3 V logic → safe for Pi5 GPIO directly.
# No voltage divider required.

import sys
import time
import datetime

GPIO_SIG   = 23   # Pin 16 — SIG (trigger + echo, single wire)
GPIO_CHIP  = 4    # Pi5 RP1 southbridge (gpiochip4)

SPEED_OF_SOUND_M_S = 343.0   # m/s at ~20 °C
TRIG_PULSE_S       = 0.00001  # 10 µs trigger pulse
ECHO_TIMEOUT_S     = 0.025    # 25 ms → ~430 cm max; beyond Grove sensor range
SAMPLE_INTERVAL_S  = 0.2      # 5 Hz
N_SAMPLES          = 20


def check_wiring() -> bool:
    print("====================================================")
    print(" M1.1 Grove Ultrasonic Ranger Bring-up Test")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("====================================================")
    print()
    print("Wiring (confirmed):")
    print("  Yellow (SIG) → GPIO 23 (Pin 16)")
    print("  White  (NC)  → not connected")
    print("  Red    (VCC) → 3.3 V")
    print("  Black  (GND) → GND")
    print()
    print("Single-wire protocol — no voltage divider required at 3.3 V.")
    print()
    answer = input("Confirm wiring is correct? (yes/no): ").strip().lower()
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
    """
    Grove Ultrasonic Ranger single-wire protocol:
    1. Drive SIG LOW for 2 µs (ensure clean start)
    2. Drive SIG HIGH for 10 µs (trigger)
    3. Drive SIG LOW, then release as input
    4. Wait for SIG HIGH (echo start)
    5. Measure HIGH duration (echo end)
    6. Distance = pulse_width × speed_of_sound / 2
    """
    # --- Trigger ---
    lgpio.gpio_claim_output(handle, GPIO_SIG, 0)
    time.sleep(0.000002)  # 2 µs LOW
    lgpio.gpio_write(handle, GPIO_SIG, 1)
    time.sleep(TRIG_PULSE_S)  # 10 µs HIGH
    lgpio.gpio_write(handle, GPIO_SIG, 0)
    lgpio.gpio_free(handle, GPIO_SIG)

    # --- Echo ---
    lgpio.gpio_claim_input(handle, GPIO_SIG)

    # Wait for echo HIGH
    t_start = time.perf_counter()
    while lgpio.gpio_read(handle, GPIO_SIG) == 0:
        if time.perf_counter() - t_start > ECHO_TIMEOUT_S:
            lgpio.gpio_free(handle, GPIO_SIG)
            return None

    echo_start = time.perf_counter()

    # Wait for echo LOW
    while lgpio.gpio_read(handle, GPIO_SIG) == 1:
        if time.perf_counter() - echo_start > ECHO_TIMEOUT_S:
            lgpio.gpio_free(handle, GPIO_SIG)
            return None

    echo_end = time.perf_counter()
    lgpio.gpio_free(handle, GPIO_SIG)

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

    print(f"\nReading {N_SAMPLES} samples at {1/SAMPLE_INTERVAL_S:.0f} Hz.")
    print("Place an object at a known distance (e.g. 20 cm, 50 cm).")
    print("Press Ctrl+C to stop early.\n")
    print(f"{'Timestamp':<30} {'Distance (cm)':>14} {'Status':>12}")
    print("-" * 60)

    timeouts = 0
    readings = []
    try:
        for _ in range(N_SAMPLES):
            ts = datetime.datetime.now().isoformat(timespec="milliseconds")
            dist = measure_distance(lgpio, handle)
            if dist is None:
                timeouts += 1
                print(f"{ts:<30} {'---':>14} {'TIMEOUT':>12}")
            elif dist < 2.0 or dist > 350.0:
                print(f"{ts:<30} {dist:>13.1f} {'OUT-OF-RANGE':>12}")
            else:
                readings.append(dist)
                print(f"{ts:<30} {dist:>13.1f} {'OK':>12}")
            time.sleep(SAMPLE_INTERVAL_S)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
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
            print("  [PARTIAL] Some timeouts — check SIG connection and VCC.")
    else:
        print(f"  [FAIL] No valid readings. {timeouts} timeouts.")
        print("  Check: VCC 3.3 V present, SIG (yellow) connected to GPIO 23.")


if __name__ == "__main__":
    main()
