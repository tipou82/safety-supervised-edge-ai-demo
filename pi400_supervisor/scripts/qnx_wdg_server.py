#!/usr/bin/env python3
# qnx_wdg_server.py — Pi400 Q&A watchdog server and safe-state controller.
# M5: DD-002 Option B — UDP transport over dedicated Ethernet (192.168.50.x).
#
# Responsibilities:
#   - Assert GPIO 25 LOW (e-stop to Pi5) and GPIO 22 HIGH (red LED) at boot
#   - Send 32-bit random seeds to Pi5 every watchdog cycle (~100ms)
#   - Validate Pi5 responses: timing (50–100ms) AND value (seed XOR 0xA5A5A5A5)
#   - Manage failure counter: +1 on miss/wrong/early, -1 after 2 consecutive correct
#   - Release GPIO 25 HIGH after first valid Q&A cycle
#   - Assert SAFE_STATE (GPIO 25 LOW + GPIO 22 HIGH) when failure_counter >= 3
#   - Broadcast status to Pi5 each cycle
#
# Protocol (UDP port 9001, both boards):
#   Pi400 → Pi5: {"type": "seed",   "seed": <uint32>, "ts": <float>}
#   Pi5   → Pi400: {"type": "response", "seed": <uint32>, "response": <uint32>}
#   Pi400 → Pi5: {"type": "status", "failure_counter": <int>, "state": <str>}
#
# Pi400 GPIO (BCM2711, gpiochip0):
#   GPIO 25 (Pin 22): e-stop output, active-low → Pi5 GPIO 25
#   GPIO 22 (Pin 15): red LED output → diode-OR with Pi5 GPIO 22
#
# Educational demonstrator — not ISO 26262 certified.

import json
import random
import socket
import time
import lgpio

# ── Network ───────────────────────────────────────────────────────────────────
PI5_IP   = '192.168.50.10'
WDG_PORT = 9001

# ── Protocol ──────────────────────────────────────────────────────────────────
RESP_MASK       = 0xA5A5A5A5
WINDOW_OPEN_MS  = 50.0
WINDOW_CLOSE_MS = 100.0
FAIL_THRESHOLD  = 3
CYCLE_MS        = 110.0   # cycle slightly longer than window to avoid overlap

# ── GPIO (Pi400 BCM2711, gpiochip0) ──────────────────────────────────────────
GPIO_CHIP  = 0
GPIO_ESTOP = 25   # active-low output → Pi5 GPIO 25
GPIO_LED   = 22   # red LED (wired-OR via 1N4148 to red LED anode)


def main() -> None:
    print("======================================================")
    print(" Pi400 Q&A Watchdog Server — M5")
    print(" UDP transport, DD-002 Option B")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("======================================================")
    print()

    # ── GPIO — assert safe state at boot (fail-safe default) ─────────────────
    gpio = lgpio.gpiochip_open(GPIO_CHIP)
    lgpio.gpio_claim_output(gpio, GPIO_ESTOP, 0)  # LOW  = e-stop asserted
    lgpio.gpio_claim_output(gpio, GPIO_LED,   1)  # HIGH = red LED ON
    print(f"[BOOT] GPIO {GPIO_ESTOP} LOW (e-stop asserted)")
    print(f"[BOOT] GPIO {GPIO_LED} HIGH (red LED ON)")
    print()

    # ── UDP socket ────────────────────────────────────────────────────────────
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', WDG_PORT))
    # Receive timeout = close of window + margin to handle late packets
    sock.settimeout((WINDOW_CLOSE_MS + 20.0) / 1000.0)
    print(f"[INIT] UDP port {WDG_PORT}  Pi5 target: {PI5_IP}:{WDG_PORT}")
    print()

    failure_counter    = 0
    consecutive_ok     = 0
    released           = False   # has GPIO 25 been released yet?
    cycle              = 0

    try:
        while True:
            cycle += 1
            cycle_start = time.monotonic()

            # ── Generate and send seed ────────────────────────────────────────
            seed     = random.getrandbits(32)
            expected = (seed ^ RESP_MASK) & 0xFFFFFFFF
            seed_pkt = json.dumps({'type': 'seed', 'seed': seed,
                                   'ts': cycle_start}).encode()
            sock.sendto(seed_pkt, (PI5_IP, WDG_PORT))

            # ── Wait for response ─────────────────────────────────────────────
            response_ok = False
            fail_reason = 'timeout'

            try:
                data, _addr = sock.recvfrom(256)
                elapsed_ms  = (time.monotonic() - cycle_start) * 1000.0
                msg         = json.loads(data.decode())

                if msg.get('type') == 'response' and msg.get('seed') == seed:
                    answer    = msg.get('response', -1)
                    timing_ok = WINDOW_OPEN_MS <= elapsed_ms <= WINDOW_CLOSE_MS
                    answer_ok = (answer == expected)

                    if timing_ok and answer_ok:
                        response_ok = True
                    elif elapsed_ms < WINDOW_OPEN_MS:
                        fail_reason = 'too_early'
                    elif not answer_ok:
                        fail_reason = 'wrong_answer'
                    else:
                        fail_reason = 'timeout'

            except socket.timeout:
                fail_reason = 'timeout'
            except (json.JSONDecodeError, KeyError):
                fail_reason = 'malformed'

            # ── Failure counter ───────────────────────────────────────────────
            if response_ok:
                consecutive_ok += 1
                if consecutive_ok >= 2 and failure_counter > 0:
                    failure_counter -= 1
                    consecutive_ok  = 0
                    print(f"[#{cycle:04d}] OK ×2 → counter={failure_counter}")
                else:
                    if cycle % 10 == 0:   # log every 10 cycles to reduce noise
                        print(f"[#{cycle:04d}] OK  counter={failure_counter}  "
                              f"consec={consecutive_ok}")
            else:
                failure_counter = min(failure_counter + 1, FAIL_THRESHOLD)
                consecutive_ok  = 0
                print(f"[#{cycle:04d}] FAIL ({fail_reason}) → counter={failure_counter}")

            # ── Safe state / release logic ────────────────────────────────────
            in_safe = failure_counter >= FAIL_THRESHOLD

            if in_safe:
                lgpio.gpio_write(gpio, GPIO_ESTOP, 0)
                lgpio.gpio_write(gpio, GPIO_LED,   1)
                if released:
                    print(f"[SAFE] counter={failure_counter} → GPIO 25 LOW, red LED ON")
                    released = False

            elif not released and response_ok:
                lgpio.gpio_write(gpio, GPIO_ESTOP, 1)  # release e-stop
                lgpio.gpio_write(gpio, GPIO_LED,   0)  # red LED OFF
                released = True
                print("[RELEASE] First valid Q&A → GPIO 25 HIGH, red LED OFF → NORMAL")

            # ── Send status to Pi5 ────────────────────────────────────────────
            status_pkt = json.dumps({
                'type':            'status',
                'failure_counter': failure_counter,
                'state':           'SAFE_STATE' if in_safe else 'NORMAL',
                'released':        released,
                'cycle':           cycle,
            }).encode()
            sock.sendto(status_pkt, (PI5_IP, WDG_PORT))

            # ── Pace cycle ────────────────────────────────────────────────────
            elapsed = (time.monotonic() - cycle_start) * 1000.0
            sleep_ms = CYCLE_MS - elapsed
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)

    except KeyboardInterrupt:
        print("\n[STOP] KeyboardInterrupt — asserting e-stop (fail-safe).")

    finally:
        lgpio.gpio_write(gpio, GPIO_ESTOP, 0)
        lgpio.gpio_write(gpio, GPIO_LED,   1)
        lgpio.gpio_free(gpio, GPIO_ESTOP)
        lgpio.gpio_free(gpio, GPIO_LED)
        lgpio.gpiochip_close(gpio)
        sock.close()
        print("[STOP] GPIO 25 LOW, red LED ON. Exited cleanly.")


if __name__ == '__main__':
    main()
