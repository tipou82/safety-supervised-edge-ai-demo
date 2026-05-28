# DD-002 — Q&A Watchdog Transport: I2C vs UDP

**Status**: OPEN — awaiting engineer decision
**Date**: 2026-05-09
**Author**: Yunpeng
**Milestone**: M5 — FFI / External Supervisor
**Related issue**: #6

> Educational demonstrator — not ISO 26262 certified.
> All safety wording is ASIL-B-inspired. No production safety claims.

---

## 1. Problem Statement

The Q&A watchdog protocol requires a bidirectional channel between Pi5
(watchdog client) and Pi400 (watchdog server):

- Pi5 reads a 32-bit seed from Pi400
- Pi5 computes `response = seed XOR 0xA5A5A5A5`
- Pi5 writes the response back to Pi400 within the open window (50–100 ms)
- Pi400 validates timing and correctness; asserts GPIO 25 e-stop on failure

The original architecture specified I2C (GPIO 2/3, Pi400 as slave at `0x40`).
A hardware constraint has been identified: implementing true I2C slave mode on
Pi400's GPIO 2/3 in Linux userspace is not straightforward — the BCM2711's
primary I2C master controller (i2c-1) cannot be reconfigured as slave in
software without kernel driver work or a different GPIO pin pair.

Three transport options are evaluated:

| Option | Transport | Pi400 role |
|---|---|---|
| A | I2C via BCM2711 BSC slave (GPIO 18/19) | I2C slave (hardware-assisted, re-wiring) |
| B | UDP over dedicated Ethernet (192.168.50.x) | UDP server |
| C | UART/serial (GPIO TX/RX) | UART peer (full-duplex, no slave concept) |

---

## 2. Industry Practice: Watchdog Transport in Safety Systems

### How external watchdog ICs communicate

Commercial external watchdog ICs (e.g., MAX6369, TPS3813, SBC UJA1169)
universally use **hardware-level serial protocols**:

| Protocol | Examples | Why chosen |
|---|---|---|
| SPI | Infineon TLE9261, NXP UJA1169 | Deterministic, high speed, full-duplex |
| I2C | MAX6369 family, TI TPS382x | Simple wiring, short distance |
| PWM / GPIO toggle | Many discrete watchdog ICs | Simplest, most deterministic |

**Automotive-grade watchdogs** (AUTOSAR, MCAL) use SPI or dedicated GPIO lines
because they sit on the same PCB/ECU, operate at hardware interrupt level, and
require bounded latency unaffected by OS scheduling.

**Distributed watchdogs** (server/cloud, IEC 61508 safety PLCs) use:
- Dedicated CAN bus (automotive)
- Ethernet/TCP keepalive (industrial Ethernet, EtherCAT)
- Safety-rated Ethernet (PROFIsafe, CIP Safety) — always on isolated network

**Key principle from practice**: the watchdog transport must be:
1. Deterministic (bounded latency)
2. Independent of the application processor's OS/network stack where possible
3. Detectable when failed (wire-break → safe state)

---

## 3. Option A — I2C via BCM2711 BSC Slave (GPIO 18/19)

### Description

The BCM2711 on Pi400 has a dedicated **BSC (Broadcom Serial Controller)**
that can operate as an I2C slave. This is separate from the I2C master
controller (i2c-1, GPIO 2/3). Accessible via `pigpio`'s `bsc_i2c()` function.
Requires re-wiring I2C connection from GPIO 2/3 to GPIO 18/19 on both boards.

### Pros

- **Closest to industry practice** — I2C external watchdog is standard in
  embedded safety systems; demonstrates production-relevant architecture
- **Hardware-assisted slave** — BSC slave is implemented in BCM2711 silicon,
  not pure software bit-banging
- **Deterministic at hardware level** — I2C transactions are handled at
  interrupt level, no OS network stack involvement
- **Strongest FFI argument** — hardware-level channel, independent of Linux
  scheduler on both sides
- **Portfolio credibility** — reviewers familiar with embedded safety will
  recognise I2C as the appropriate protocol
- **Wire-break detection** — I2C NACK on missing slave is immediate; health_node
  can detect Pi400 failure within one transaction

### Cons

- **Re-wiring required** — current I2C wires on GPIO 2/3 must be moved to
  GPIO 18/19 on both Pi5 and Pi400 (hardware change)
- **`pigpio` dependency** — Pi400 needs `pigpio` daemon running (`sudo pigpiod`)
- **BSC register complexity** — `pigpio`'s `bsc_i2c()` is not widely documented;
  register-level access requires careful implementation
- **GPIO 18/19 conflict check** — GPIO 18 is currently used for buzzer (Pin 12).
  Pi5 GPIO 18 must be freed before re-using for I2C SCL; buzzer must move to
  another pin or be removed from M5 scope

### Performance estimate

| Metric | Value |
|---|---|
| Latency (I2C at 100 kHz) | ~0.4 ms per transaction |
| Jitter | <0.1 ms (hardware interrupt driven) |
| Wire-break detection | Immediate (NACK within 1 transaction) |
| 50–100 ms window achievable | Yes — with significant margin |

---

## 4. Option B — UDP over Dedicated Ethernet

### Description

Pi5 health_node sends watchdog responses via UDP to Pi400
(`192.168.50.20:9001`). Pi400 `watchdog_server.py` acts as UDP server,
generates seeds, validates responses and timing. No I2C slave needed.

### Pros

- **No hardware changes** — dedicated Ethernet already wired and verified (M1);
  no re-wiring, no GPIO conflicts
- **Simplest implementation** — Python `socket` library, no hardware drivers
- **Extensible** — Pi400 can publish detailed status back to Pi5 over same UDP
  channel (failure_counter, state, timestamps)
- **Already tested transport** — UDP Ethernet verified in M1 smoke test;
  known-good end-to-end path
- **No pigpio dependency** — fewer system dependencies on Pi400

### Cons

- **Non-standard for safety watchdog** — UDP/Ethernet watchdog is not the
  industry norm for hardware-level supervision; a safety auditor would flag
  this as a weaker FFI measure
- **OS network stack dependency** — Linux kernel, network driver, and socket
  layer are involved; any of these failing silently would break the watchdog
  without detection
- **Shared network medium** — even on a dedicated link, Ethernet involves
  switches, ARP, MAC layer — more complex than I2C
- **Latency variability** — UDP jitter on LAN is typically <1 ms but not
  hardware-deterministic; unlikely to affect the 50–100 ms window but weaker
  timing argument
- **Wire-break not immediately detectable** — UDP is connectionless; Pi400
  would only detect Pi5 failure after the 100 ms window expires, same as I2C
- **Weakens FFI argument** — "independence" is harder to argue when both
  processors share a network stack (even on separate hardware)

### Performance estimate

| Metric | Value |
|---|---|
| Latency (UDP LAN) | 0.2–2 ms typical |
| Jitter | <2 ms (OS-dependent) |
| Wire-break detection | After 100 ms window timeout |
| 50–100 ms window achievable | Yes — with good margin |

---

## 5. Option C — UART/Serial (GPIO TX/RX)

### Description

Full-duplex serial link between Pi5 GPIO 14/15 (UART0) and Pi400 GPIO 14/15.
Simple framed protocol (seed frame, response frame). No master/slave concept —
either side can transmit at any time.

### Pros

- **No slave mode needed** — UART is inherently symmetric, no master/slave
- **Hardware-level** — UART is handled by dedicated UART hardware on BCM2711
- **Simple framing** — fixed-length seed/response frames, easy to implement
- **Common in safety systems** — UART/RS-232 used in industrial safety devices

### Cons

- **Requires new wiring** — current GPIO 14/15 on Pi5 may conflict with UART
  console; must verify and possibly disable console UART
- **No existing wiring** — Ethernet and I2C are already wired; UART adds a
  new cable
- **Less standard than I2C for watchdog** — UART watchdog is less common than
  I2C; less portfolio value than Option A
- **Adds complexity** — framing, baud rate, parity must be configured

---

## 6. Safety / FFI Comparison

| Criterion | Option A (I2C BSC) | Option B (UDP) | Option C (UART) |
|---|---|---|---|
| Industry practice | ✅ Standard | ⚠️ Non-standard | ⚠️ Less common |
| Hardware determinism | ✅ Strong | ❌ OS-dependent | ✅ Moderate |
| FFI argument strength | ✅ Strong | ⚠️ Moderate | ✅ Moderate |
| Wire-break detection | ✅ NACK immediate | ⚠️ Timeout only | ✅ Framing error |
| Implementation effort | ⚠️ Medium (pigpio BSC) | ✅ Low | ⚠️ Medium |
| Re-wiring required | ⚠️ Yes (GPIO 18/19) | ✅ No | ❌ Yes (new wire) |
| GPIO 18 conflict (buzzer) | ⚠️ Needs resolution | ✅ None | ✅ None |
| Portfolio credibility | ✅ High | ⚠️ Moderate | ⚠️ Moderate |

---

## 7. Recommendation

**Option A — I2C via BCM2711 BSC Slave**, subject to resolving the GPIO 18
(buzzer) conflict.

*Rationale*:
1. I2C is the industry-standard transport for external watchdog communication
   in embedded safety systems. Using it demonstrates production-relevant
   architecture discipline.
2. The BSC slave interface provides hardware-level determinism, strengthening
   the FFI argument: the watchdog channel does not depend on the Linux network
   stack on either processor.
3. The re-wiring is minor (move two wires from GPIO 2/3 to GPIO 18/19) and
   the GPIO 18 buzzer conflict is resolvable (buzzer can be moved to GPIO 26
   or removed from the demo scope).

*If re-wiring or BSC pigpio complexity proves excessive*: fall back to
**Option B (UDP)** and document the FFI limitation explicitly — the watchdog
transport is over a dedicated Ethernet link but relies on the OS network stack,
which is a known gap from the production pattern.

---

## 8. Decision

**Decision**: ☐ Option A — I2C BSC slave (GPIO 18/19, re-wiring)
            ☑ **Option B — UDP over dedicated Ethernet**
            ☐ Option C — UART/serial

**Notes**:
Option A was attempted. `pigpio`'s `bsc_i2c()` does not support BCM2711
(Raspberry Pi 4/400) — the BSC slave peripheral exists on BCM2711 but at a
different register base address than BCM2835 (Pi 1–3). `i2cdetect` showed
no slave at 0x40 after BSC configuration. Option A is not achievable on
Pi400 without a custom kernel driver.

Option B (UDP over dedicated Ethernet 192.168.50.x) is adopted:
- Q&A protocol logic (seed/response/window/failure counter) unchanged
- GPIO 25 and GPIO 22 remain hardware outputs on Pi400
- I2C wires (GPIO 2/3) are no longer needed — disconnected
- FFI limitation documented: watchdog channel relies on Linux network stack;
  weaker than hardware I2C but acceptable for educational demonstrator

**Decided by**: Yunpeng
**Decision date**: 2026-05-09

---

## 9. References

- BCM2711 Datasheet — BSC (Broadcom Serial Controller) slave register description
- pigpio `bsc_i2c()` documentation: http://abyz.me.uk/rpi/pigpio/python.html#bsc_i2c
- MAX6369 External Watchdog Timer (I2C interface example)
- NXP UJA1169 System Basis Chip (SPI watchdog, automotive reference)
- `docs/ffi_argument.md` — FFI effectiveness analysis for this project
- `requirements/interfaces.yaml` — Q&A watchdog timing constraints
- `AGENTS.md` — AI boundary rules (no AI in safety path)
