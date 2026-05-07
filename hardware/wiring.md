# Hardware Wiring Specification

## Overview

This document describes the physical wiring between Raspberry Pi 5 (Linux/ROS2 domain) and Raspberry Pi 400 (QNX supervisor domain), as well as connections to sensors and actuators.

## Safety Note

⚠️ **Single Point of Failure**: All GPIO connections are single-wire (no redundancy). This is acceptable for a demonstrator but would not meet production safety standards.

## Bill of Materials

**Actual hardware as of M1.1 (2026-05-07) — pending M2 hardware changes**

| Component | Quantity | Purpose | Notes |
|-----------|----------|---------|-------|
| Raspberry Pi 5 (8GB) | 1 | Linux/ROS2 domain | Main perception processor |
| Raspberry Pi 400 | 1 | QNX-inspired supervisor domain | Safety monitor |
| Raspberry Pi Camera Module 3 | 1 | AI perception | IMX708, 4608×2592, CSI ribbon cable |
| Grove Ultrasonic Ranger | 1 | Obstacle detection | 2–350 cm, single-wire SIG, 3.3 V |
| Traffic-light LED module | 1 | System state indicators | Green/Yellow/Red, GPIO-driven |
| Active 3.3 V buzzer | 1 | Audible alert | Sounds when GPIO driven HIGH |
| 1N4148 diode | 2 | Red LED wired-OR isolation | Prevents back-current between Pi5 and Pi400 drivers |
| 150 Ω resistor | 2 | Red LED current limiting (replaces 330 Ω) | One per driver leg; compensates for diode Vf drop |
| 4.7 kΩ resistor | 2 | I2C SDA and SCL pull-ups to 3.3V | Required for I2C bus on both wires |
| Jumper wires | 30+ | GPIO connections | Dupont female-female |
| Breadboard | 1 | Prototyping | Sensor, LED, and I2C pull-up wiring |
| Power supply (5V, 3A+) | 2 | Power each Pi | USB-C for Pi5, USB-C for Pi400 |

**⚠️ Hardware changes required from M1.1 baseline — see `hardware/TODO_hardware_changes.md`**

**Not present in current hardware build** (deferred to future milestone):
- Motor driver (L298N or similar)
- DC motors

## GPIO Pin Mapping

See [gpio_mapping.md](gpio_mapping.md) for detailed pin assignments.

---

## Inter-Processor Wiring

### I2C Q&A Watchdog (Primary Safety Channel)

The Q&A watchdog replaces the simple GPIO heartbeat. Pi5 acts as I2C master; Pi400 acts as I2C slave at address `0x40`.

```
Pi5  GPIO 2 / Pin 3  (SDA) ──────────────── Pi400 GPIO 2 / Pin 3  (SDA)
Pi5  GPIO 3 / Pin 5  (SCL) ──────────────── Pi400 GPIO 3 / Pin 5  (SCL)
Pi5  GND    / Pin 6        ──────────────── Pi400 GND    / Pin 6

Pull-up resistors (on breadboard or Pi5 side):
  3.3V ──[ 4.7 kΩ ]── SDA line
  3.3V ──[ 4.7 kΩ ]── SCL line
```

| Parameter | Value |
|---|---|
| Bus speed | 100 kHz standard mode |
| Pi400 slave address | 0x40 |
| Seed register | 0x00 (Pi400 generates, Pi5 reads) |
| Response register | 0x01 (Pi5 writes, Pi400 validates) |
| Response algorithm | `response = seed XOR 0xA5A5A5A5` |
| Valid window | 50–100 ms after last correct response |
| Failure counter threshold | 3 → SAFE_STATE |

**Protocol flow (one watchdog cycle):**
```
Pi400 generates new seed → stores in register 0x00
Pi5   reads register 0x00 (I2C read transaction)
Pi5   computes response = seed XOR 0xA5A5A5A5
Pi5   waits until ~70 ms after last acknowledged response
Pi5   writes response to register 0x01 (I2C write transaction)
Pi400 validates: timing ∈ [50ms, 100ms] AND response correct
      → success: decrement failure_counter after 2 consecutive successes
      → failure: failure_counter++; if ≥ 3 → assert SAFE_STATE
```

### Emergency Stop: Pi400 → Pi5

Direct GPIO wire, active-low, fail-safe.

```
Pi400 GPIO 25 (Pin 22) ──────────────── Pi5 GPIO 25 (Pin 22)
Pi400 GND     (Pin 6)  ──────────────── Pi5 GND     (Pin 6)   (shared)
```

| Parameter | Value |
|---|---|
| Pi5 pin | GPIO 25 (Pin 22) — input, internal pull-up |
| Pi400 pin | GPIO 25 (Pin 22) — output, active-low |
| Default state | LOW (asserted) at Pi400 boot |
| Released | After Q&A watchdog establishes NORMAL state |
| Pi5 poll rate | 100 Hz (actuator_node) |
| Response time | <30 ms from assertion to motor disable |

### Red LED — Wired-OR (Both Domains Can Assert SAFE STATE)

Both Pi5 and Pi400 can independently illuminate the red LED. Diode isolation prevents back-current.

```
Pi5   GPIO 22 (Pin 15) ──[ 150 Ω ]──[D1: 1N4148]──┐
                                                     ├── Red LED (+) ──── Red LED (−) ── GND
Pi400 GPIO 22 (Pin 15) ──[ 150 Ω ]──[D2: 1N4148]──┘
```

| Parameter | Value |
|---|---|
| Current limiting | 150 Ω per leg (not shared — one per driver) |
| Diodes | 1N4148, Vf ≈ 0.7V |
| LED forward voltage | ~2.0V (red) |
| Drive current | (3.3V − 0.7V − 2.0V) / 150 Ω ≈ 4 mA per active driver |
| Asserted by Pi5 | On SAFE_STATE entry in actuator_node |
| Asserted by Pi400 | On failure_counter ≥ 3 in safe_state_ctrl |

**Note**: Replace the 330 Ω resistor used in M1.1 bring-up with 150 Ω per leg, and add both 1N4148 diodes.

### Direct Ethernet Link (Pi5 ↔ Pi400)

A dedicated Ethernet cable for future ROS2 diagnostics and non-safety communication.

```
Pi5 Ethernet port ─────────────────────────────── Pi400 Ethernet port
  Static IP: 192.168.50.10/24                       Static IP: 192.168.50.20/24
```

| Parameter | Value |
|---|---|
| Cable type | Cat5e/Cat6, direct or crossover (auto-negotiate) |
| Pi5 address | 192.168.50.10/24 |
| Pi400 address | 192.168.50.20/24 |
| Purpose (M1/M2) | Connectivity verification and diagnostics |
| Safety-critical | No — I2C + GPIO are the safety channels |

---

## Sensor Wiring

### Grove Ultrasonic Ranger (×1, front)

```
Grove Pin        → Pi5
Yellow (SIG)     → GPIO 23 (Pin 16)
White  (NC)      → not connected
Red    (VCC)     → 3.3 V (Pin 1 or 17)
Black  (GND)     → GND (Pin 6)
```

- No voltage divider required — powered at 3.3 V, SIG output is 3.3 V logic.
- Range: 2–350 cm.

### Camera — Raspberry Pi Camera Module 3

```
Camera Module 3 → Pi5 CSI connector (ribbon cable)
```

- Sensor: IMX708, 4608×2592 (10-bit RGGB).
- No GPIO wiring required.

### Status LEDs (Traffic-light module)

```
Pi5 GPIO 17 (Pin 11) → Green LED  anode → [ 330 Ω ] → GND  (NORMAL indicator)
Pi5 GPIO 27 (Pin 13) → Yellow LED anode → [ 330 Ω ] → GND  (DEGRADED indicator)

Red LED (wired-OR — see diode circuit above):
Pi5   GPIO 22 (Pin 15) → [ 150 Ω ] → [ D1: 1N4148 ] → Red LED anode → GND
Pi400 GPIO 22 (Pin 15) → [ 150 Ω ] → [ D2: 1N4148 ] → Red LED anode → GND
```

### Active Buzzer

```
GPIO 18 (Pin 12) → Buzzer (+)
GND              → Buzzer (−)
```

Active 3.3 V buzzer — sounds when GPIO driven HIGH.

---

## Power Distribution

### Isolated Power Supplies

**Pi5 Power**: 5V, 3A minimum — USB-C. Powers Pi5, Camera, Grove sensor, LEDs, buzzer.

**Pi400 Power**: 5V, 3A minimum — USB-C. Powers Pi400 only.

### Ground Reference

```
Pi5 GND (Pin 6) ──── Pi400 GND (Pin 6)   (common ground for I2C and e-stop GPIO)
```

A common ground is mandatory for correct I2C operation and GPIO signal reference.

---

## Wiring Diagram

```
┌─────────────────────────────────────────────┐       ┌───────────────────────────────────┐
│   Raspberry Pi 5 (Linux/ROS2)               │       │   Raspberry Pi 400 (Supervisor)   │
│                                             │       │                                   │
│  GPIO 2  (Pin  3) ── SDA ───────────────────┼───────┼── SDA (Pin 3) GPIO 2              │
│  GPIO 3  (Pin  5) ── SCL ───────────────────┼───────┼── SCL (Pin 5) GPIO 3              │
│  GND     (Pin  6) ─────────────────────────┼───────┼── GND (Pin 6)     [4.7kΩ pull-ups  │
│                                             │       │                    on SDA and SCL] │
│  GPIO 25 (Pin 22) ←── E-Stop (active-low) ─┼───────┼── GPIO 25 (Pin 22)                │
│                                             │       │                                   │
│  GPIO 17 (Pin 11) ── Green  LED → GND      │       │  GPIO 22 (Pin 15) ──[150Ω]─[D2]──┐│
│  GPIO 27 (Pin 13) ── Yellow LED → GND      │       └───────────────────────────────────┘│
│  GPIO 22 (Pin 15) ──[150Ω]──[D1]───────────┼─────────────────────────────────────────→ Red LED → GND
│  GPIO 18 (Pin 12) ── Buzzer (+) → GND      │
│  GPIO 23 (Pin 16) ── Ultrasonic SIG        │
│                                             │
└──────────────────┬──────────────────────────┘
                   │ CSI ribbon cable
            ┌──────▼──────────┐    ┌──────────────────────┐
            │  Camera Module 3 │    │  Grove Ultrasonic     │
            │  IMX708          │    │  Ranger (SIG Pin 16)  │
            └─────────────────┘    └──────────────────────┘

D1, D2 = 1N4148 (cathode toward LED anode)
```

---

## Wiring Checklist

Before powering on, verify (M2 target state):

- [ ] Common ground established between Pi5 and Pi400 (Pin 6 ↔ Pin 6)
- [ ] I2C SDA: Pi5 GPIO 2 (Pin 3) ↔ Pi400 GPIO 2 (Pin 3)
- [ ] I2C SCL: Pi5 GPIO 3 (Pin 5) ↔ Pi400 GPIO 3 (Pin 5)
- [ ] 4.7 kΩ pull-up resistors: SDA to 3.3V and SCL to 3.3V
- [ ] E-stop: Pi400 GPIO 25 (Pin 22) → Pi5 GPIO 25 (Pin 22)
- [ ] Red LED: diode-OR circuit with D1, D2 (1N4148) and 150 Ω resistors in place
- [ ] Green LED: Pi5 GPIO 17 (Pin 11) → 330 Ω → GND
- [ ] Yellow LED: Pi5 GPIO 27 (Pin 13) → 330 Ω → GND
- [ ] Buzzer: Pi5 GPIO 18 (Pin 12) → Buzzer (+), GND → (−)
- [ ] Camera Module 3 CSI ribbon cable fully seated, correct orientation
- [ ] Grove Ultrasonic Ranger: SIG → GPIO 23 (Pin 16), VCC → 3.3V, GND connected
- [ ] No loose wires or shorts visible

**Hardware changes from M1.1 baseline still pending** — see `hardware/TODO_hardware_changes.md`.

---

## Testing Procedure

1. **Power Sequence**: Power Pi400 first (e-stop asserted). Then power Pi5.
2. **I2C Connectivity**: `i2cdetect -y 1` on Pi5 — should show device at `0x40`.
3. **Q&A Watchdog Smoke Test**: Run `pi400_supervisor/scripts/i2c_wdg_test.py` (TBD M2).
4. **E-stop Test**: Confirm Pi5 GPIO 25 reads LOW after Pi400 boots, 3.3V after supervisor releases.
5. **Camera Test**: `bash pi5_linux/scripts/camera_test.sh`
6. **Ultrasonic Test**: `python3 pi5_linux/scripts/ultrasonic_test.py`
7. **LED Test**: `python3 pi5_linux/scripts/led_test.py` — note: red LED now requires diode circuit to be in place.
8. **Buzzer Test**: `python3 pi5_linux/scripts/buzzer_test.py`

---

## References

- Raspberry Pi 5 GPIO Pinout: https://pinout.xyz
- Raspberry Pi 400 GPIO Pinout: https://pinout.xyz/pinout/pi400
- 1N4148 Datasheet: small-signal fast-switching diode, Vf ≈ 0.7V at 10 mA
- Linux I2C tools: `sudo apt install i2c-tools`
