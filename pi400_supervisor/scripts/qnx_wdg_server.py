#!/usr/bin/env python3
# qnx_wdg_server.py — Pi400 Q&A watchdog server and safe-state controller.
# M5/M7: DD-002 Option B — UDP transport over dedicated Ethernet (192.168.50.x).
#
# Watchdog window (50ms total):
#   t=0        Seed sent to Pi5
#   t=0–15ms   Closed window  — response too early → failure_counter++
#   t=15–50ms  Open window    — valid response window
#   t=50ms     Timeout        — no response → failure_counter++
#   New cycle starts immediately after response or timeout.
#
# Failure counter: +1 on early/late/wrong; −1 after 2 consecutive correct; ≥3 → SAFE_STATE
# SAFE_STATE latency: 3 × 50ms + GPIO + poll = ~200ms (SYS-SAFE-006 updated).
#
# Protocol (UDP port 9001):
#   Pi400 → Pi5: {"type": "seed",     "seed": <uint32>, "seq": <uint8>, "crc": <uint16>}
#   Pi5   → Pi400: {"type": "response", "seed": <uint32>, "response": <uint32>,
#                                        "seq": <uint8>,  "crc": <uint16>}
#   Pi400 → Pi5: {"type": "status",   "failure_counter": <int>, "state": <str>}
#
# Pi400 GPIO (BCM2711, gpiochip0):
#   GPIO 25 (Pin 22): e-stop output, active-low → Pi5 GPIO 25
#   GPIO 22 (Pin 15): red LED output → diode-OR with Pi5 GPIO 22
#
# Educational demonstrator — not ISO 26262 certified.

import json
import random
import socket
import struct
import time
import lgpio

# ── Network ───────────────────────────────────────────────────────────────────
PI5_IP   = '192.168.50.10'
WDG_PORT = 9001

# ── Protocol ──────────────────────────────────────────────────────────────────
RESP_MASK       = 0xA5A5A5A5
WINDOW_OPEN_MS  = 15.0    # closed window end  — response before this → too early
WINDOW_CLOSE_MS = 50.0    # window timeout     — response after this → missed
FAIL_THRESHOLD  = 3

# ── GPIO (Pi400 BCM2711, gpiochip0) ──────────────────────────────────────────
GPIO_CHIP  = 0
GPIO_ESTOP = 25
GPIO_LED   = 22


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE over data bytes."""
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
    return crc & 0xFFFF


def make_seed_packet(seed: int, seq: int) -> bytes:
    payload = struct.pack('>IB', seed, seq)  # seed(4) + seq(1)
    crc = crc16(payload)
    return json.dumps({
        'type': 'seed', 'seed': seed, 'seq': seq, 'crc': crc
    }).encode()


def main() -> None:
    print("======================================================")
    print(" Pi400 Q&A Watchdog Server — M7")
    print(" Window: 50ms (15ms closed + 35ms open)")
    print(" Educational demonstrator — not ISO 26262 certified")
    print("======================================================")
    print()

    gpio = lgpio.gpiochip_open(GPIO_CHIP)
    lgpio.gpio_claim_output(gpio, GPIO_ESTOP, 0)  # LOW = e-stop asserted
    lgpio.gpio_claim_output(gpio, GPIO_LED,   1)  # HIGH = red LED ON
    print(f"[BOOT] GPIO {GPIO_ESTOP} LOW (e-stop), GPIO {GPIO_LED} HIGH (red LED)")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', WDG_PORT))
    sock.settimeout((WINDOW_CLOSE_MS + 5.0) / 1000.0)  # 55ms receive timeout

    failure_counter  = 0
    consecutive_ok   = 0
    released         = False
    seq              = 0
    cycle            = 0

    print(f"[INIT] Listening on UDP {WDG_PORT}, Pi5: {PI5_IP}")
    print()

    try:
        while True:
            cycle += 1
            seq = (seq + 1) & 0xFF
            cycle_start = time.monotonic()

            seed     = random.getrandbits(32)
            expected = (seed ^ RESP_MASK) & 0xFFFFFFFF
            expected_crc_payload = struct.pack('>IBI', seed, seq, expected)

            sock.sendto(make_seed_packet(seed, seq), (PI5_IP, WDG_PORT))

            # ── Wait for response ─────────────────────────────────────────────
            response_ok = False
            fail_reason = 'timeout'

            try:
                data, _ = sock.recvfrom(512)
                elapsed_ms = (time.monotonic() - cycle_start) * 1000.0
                msg = json.loads(data.decode())

                if msg.get('type') == 'response' and msg.get('seed') == seed:
                    answer   = msg.get('response', -1)
                    resp_seq = msg.get('seq', -1)
                    resp_crc = msg.get('crc', -1)

                    # Validate CRC over response payload
                    resp_payload = struct.pack('>IBI', seed, resp_seq & 0xFF, answer & 0xFFFFFFFF)
                    crc_ok    = (resp_crc == crc16(resp_payload))
                    seq_ok    = (resp_seq == seq)
                    timing_ok = WINDOW_OPEN_MS <= elapsed_ms <= WINDOW_CLOSE_MS
                    answer_ok = (answer == expected)

                    if timing_ok and answer_ok and seq_ok and crc_ok:
                        response_ok = True
                    elif elapsed_ms < WINDOW_OPEN_MS:
                        fail_reason = 'too_early'
                    elif not answer_ok:
                        fail_reason = 'wrong_answer'
                    elif not seq_ok:
                        fail_reason = f'seq_mismatch(got {resp_seq} want {seq})'
                    elif not crc_ok:
                        fail_reason = 'crc_error'
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
                    print(f"[#{cycle:04d}] OK×2 → counter={failure_counter}")
                elif cycle % 20 == 0:
                    print(f"[#{cycle:04d}] OK  counter={failure_counter} seq={seq}")
            else:
                failure_counter = min(failure_counter + 1, FAIL_THRESHOLD)
                consecutive_ok  = 0
                print(f"[#{cycle:04d}] FAIL ({fail_reason}) → counter={failure_counter}")

            # ── Safe state / release ──────────────────────────────────────────
            in_safe = failure_counter >= FAIL_THRESHOLD

            if in_safe:
                lgpio.gpio_write(gpio, GPIO_ESTOP, 0)
                lgpio.gpio_write(gpio, GPIO_LED,   1)
                if released:
                    print(f"[SAFE] counter={failure_counter} → e-stop asserted")
                    released = False
            elif not released and response_ok:
                lgpio.gpio_write(gpio, GPIO_ESTOP, 1)
                lgpio.gpio_write(gpio, GPIO_LED,   0)
                released = True
                print("[RELEASE] First valid Q&A → GPIO 25 HIGH, red LED OFF")

            # ── Status to Pi5 ─────────────────────────────────────────────────
            status = json.dumps({
                'type':            'status',
                'failure_counter': failure_counter,
                'state':           'SAFE_STATE' if in_safe else 'NORMAL',
                'released':        released,
                'cycle':           cycle,
            }).encode()
            sock.sendto(status, (PI5_IP, WDG_PORT))

            # No fixed cycle sleep — next cycle starts immediately

    except KeyboardInterrupt:
        print("\n[STOP] Asserting e-stop.")
    finally:
        lgpio.gpio_write(gpio, GPIO_ESTOP, 0)
        lgpio.gpio_write(gpio, GPIO_LED,   1)
        lgpio.gpio_free(gpio, GPIO_ESTOP)
        lgpio.gpio_free(gpio, GPIO_LED)
        lgpio.gpiochip_close(gpio)
        sock.close()


if __name__ == '__main__':
    main()
