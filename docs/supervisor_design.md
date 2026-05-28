# Pi400 Supervisor Design

> **Educational demonstrator — ASIL-B-inspired patterns only. Not ISO 26262 certified.**
> Implementation details (watchdog protocol, timing, failure counter, FTTI) are in
> `docs/safety_mechanisms.md` SM-1 and SM-2.

## Role and Rationale

The Pi400 supervisor is **physically separate** from the Pi5 AI perception domain.
It implements a single responsibility: monitor the Pi5 application via UDP Q&A watchdog
and assert a hardware e-stop (GPIO 25) if the Pi5 fails to respond correctly.

**Why a second processor?**
- FFI-inspired spatial isolation: a kernel panic or AI inference fault on Pi5 cannot
  corrupt the supervisor process on Pi400
- E-stop is a direct GPIO wire — no software stack involved on the enforcement path
- Supervisor uses only deterministic rule-based logic; no AI or probabilistic reasoning

---

## Process Architecture

```
watchdog_server.py (Pi400)
    │
    ├─ UDP socket (port 9001, 192.168.50.20)
    │   ├─ Send seed packet to Pi5 (seed, seq, CRC-16)
    │   └─ Receive response from Pi5 (response, seq, CRC-16)
    │
    ├─ Failure counter logic
    │   ├─ +1 on timeout / wrong answer / CRC error / seq mismatch / too-early
    │   └─ −1 after 2 consecutive correct responses
    │
    └─ GPIO output (gpiochip0 / BCM2711)
        ├─ GPIO 25 (e-stop): LOW at boot (fail-safe), HIGH after first valid Q&A
        └─ GPIO 22 (red LED): HIGH at boot, LOW after release
```

---

## Watchdog Protocol

See **`docs/safety_mechanisms.md` SM-1** for the full protocol specification.
Implementation: `pi400_supervisor/scripts/watchdog_server.py`

| Parameter | Value |
|---|---|
| Cycle | Continuous — next cycle starts immediately after response or timeout |
| Closed window | 0–15 ms (response before this → too early → failure) |
| Open window | 15–30 ms (valid response window) |
| Timeout | 30 ms (no response → failure) |
| Failure threshold | ≥ 3 → SAFE_STATE |
| Recovery | −1 after 2 consecutive correct; e-stop released when counter < threshold |
| Transport | UDP, port 9001, dedicated Ethernet 192.168.50.x |
| E2E protection | CRC-16/CCITT-FALSE, sequence counter (uint8, wraps at 255) |

---

## GPIO Behaviour

| GPIO | Direction | At boot | Released | Re-asserted (fault) |
|---|---|---|---|---|
| 25 | Output, active-low e-stop | LOW | HIGH | LOW |
| 22 | Output, red LED | HIGH (on) | LOW (off) | HIGH (on) |

Re-asserted when `failure_counter ≥ 3`.

---

## Startup Sequence

1. `lgpio.gpiochip_open(0)` — open BCM2711 GPIO chip
2. GPIO 25 claimed as output, driven **LOW immediately** (fail-safe before any watchdog exchange)
3. GPIO 22 claimed as output, driven **HIGH** (red LED on)
4. UDP socket bound to `0.0.0.0:9001`
5. First watchdog cycle begins — seed sent to Pi5
6. After first valid Q&A response: GPIO 25 → HIGH, GPIO 22 → LOW (released)

---

## Timing and Latency

| Event | Latency |
|---|---|
| Boot → e-stop asserted | < 1 s (Python startup + lgpio init, after `network.target`) |
| Fault detection | ≤ 3 × 30 ms = 90 ms (3 consecutive timeouts) |
| GPIO assertion after fault | + kernel scheduling jitter (~1–5 ms) |
| Total fault → e-stop active | ≤ ~100 ms |

---

## Monitoring

```bash
# Live log (most useful during debugging)
journalctl -fu safety-supervisor

# Current GPIO state
raspi-gpio get 25   # HIGH = released (normal), LOW = e-stop asserted
raspi-gpio get 22   # HIGH = red LED on, LOW = off

# Raw UDP packets (seed/response/status)
sudo tcpdump -i eth0 udp port 9001 -A -l

# Service health (PID, restarts, uptime)
systemctl status safety-supervisor
```

---

## Testing

| Test | Method |
|---|---|
| Watchdog E2E | Pi5 ↔ Pi400 full cycle — verified M5 |
| Fault injection (timeout) | Kill health_node → counter → SAFE_STATE (FI-05, M6 PASS) |
| FFI temporal | Pi5 CPU stress → watchdog timing stays within window (M7 FFI-TEMPORAL PASS) |
| FFI comm | ROS2 topic flood → UDP watchdog unaffected (M7 FFI-COMM PASS) |

---

## Limitations vs. Production Automotive

| Aspect | This demonstrator | Production pattern |
|---|---|---|
| OS | Linux (Raspberry Pi OS) | Dedicated MCU (STM32, Infineon TC3xx) or certified RTOS |
| Startup time | ~5–10 s (Linux boot + network.target) | < 100 ms (bare-metal MCU) |
| Scheduling | Linux CFS | FIFO real-time or hardware timer ISR |
| WCET | Not formally analysed | Mandatory for ASIL-B |
| Certification | None | ISO 26262 tool qualification + safety case required |

The architecture pattern (independent supervisor, hardware e-stop, deterministic rules)
is aligned with ASIL-B-inspired approaches. A production system would use a certified MCU
or RTOS for sub-100 ms startup and formally bounded scheduling.

---

## References

- `docs/safety_mechanisms.md` — authoritative watchdog protocol and FTTI analysis
- `pi400_supervisor/scripts/watchdog_server.py` — implementation
- `pi400_supervisor/systemd/safety-supervisor.service` — systemd auto-start
