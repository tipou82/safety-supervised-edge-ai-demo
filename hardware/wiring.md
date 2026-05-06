# Hardware Wiring Specification

## Overview

This document describes the physical wiring between Raspberry Pi 5 (Linux/ROS2 domain) and Raspberry Pi 400 (QNX supervisor domain), as well as connections to sensors and actuators.

## Safety Note

⚠️ **Single Point of Failure**: All GPIO connections are single-wire (no redundancy). This is acceptable for a demonstrator but would not meet production safety standards.

## Bill of Materials

**Actual hardware as of M1.1 (2026-05-07)**

| Component | Quantity | Purpose | Notes |
|-----------|----------|---------|-------|
| Raspberry Pi 5 (8GB) | 1 | Linux/ROS2 domain | Main perception processor |
| Raspberry Pi 400 | 1 | QNX-inspired supervisor domain | Safety monitor (Linux fallback) |
| Raspberry Pi Camera Module 3 | 1 | AI perception | IMX708, 4608×2592, CSI ribbon cable |
| Grove Ultrasonic Ranger | 1 | Obstacle detection | 2–350 cm, single-wire SIG, 3.3 V |
| Traffic-light LED module | 1 | System state indicators | Green/Yellow/Red, GPIO-driven |
| Active 3.3 V buzzer | 1 | Audible alert | Sounds when GPIO driven HIGH |
| Jumper wires | 20+ | GPIO connections | Dupont female-female |
| Breadboard | 1 | Prototyping | Sensor and LED wiring |
| Power supply (5V, 3A+) | 2 | Power each Pi | USB-C for Pi5, USB-C for Pi400 |

**Not present in current hardware build** (deferred to future milestone):
- Motor driver (L298N or similar)
- DC motors

## GPIO Pin Mapping

See [gpio_mapping.md](gpio_mapping.md) for detailed pin assignments.

## Inter-Processor Wiring

### Critical Safety Signals

**Heartbeat Signal: Pi5 → Pi400**
```
Pi5 GPIO 17 (Pin 11) ──────→ Pi400 GPIO TBD (Pin TBD)
Pi5 GND (Pin 6)      ──────→ Pi400 GND (Pin 6)
```
- **Signal**: 10 Hz square wave, 3.3V logic
- **Function**: Aliveness indication from Linux to QNX
- **Safety-critical**: Yes (watchdog input)

**Emergency Stop: Pi400 → Pi5**
```
Pi400 GPIO TBD (Pin TBD) ───→ Pi5 GPIO 27 (Pin 13)
Pi400 GND (Pin 14)       ───→ Pi5 GND (Pin 9)
```
- **Signal**: Active-low, 3.3V logic (0V = stop)
- **Function**: Safe state command from QNX to actuator node
- **Safety-critical**: Yes (emergency brake)

### Direct Ethernet Link (Pi 5 ↔ Pi 400)

A dedicated Ethernet cable connects Pi 5 and Pi 400 directly for future supervisor/watchdog communication. In M1 this link is verified by ping only. The heartbeat/watchdog protocol is not implemented in M1.

```
Pi 5 Ethernet port ─────────────────────── Pi 400 Ethernet port
  Static IP: 192.168.50.10/24               Static IP: 192.168.50.20/24
```

| Parameter | Value |
|---|---|
| Cable type | Standard Cat5e/Cat6 Ethernet (direct or crossover — modern adapters auto-negotiate) |
| Pi 5 address | 192.168.50.10/24 |
| Pi 400 address | 192.168.50.20/24 |
| Purpose (M1) | Connectivity verification — ping only |
| Purpose (future) | Heartbeat/watchdog protocol (deferred to later milestone) |
| Development access | Separate — via Wi-Fi or home LAN, independent of this link |

### Notes on Inter-Processor Wiring

- **Ground Reference**: Ensure common ground between both Pi boards
- **No Level Shifters**: Both Pi5 and Pi400 use 3.3V GPIO, direct connection OK
- **Cable Length**: Keep <30 cm to minimize noise and signal integrity issues
- **Strain Relief**: Use cable management to prevent accidental disconnection

## Sensor Wiring

### Grove Ultrasonic Ranger (×1, front)

Single-wire SIG protocol — one GPIO pin handles both trigger and echo.

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

- Sensor: IMX708, 4608×2592 (10-bit RGGB), up to 120 fps at 1536×864.
- No GPIO wiring required.
- Detected automatically at boot via `camera_auto_detect=1` in `/boot/firmware/config.txt`.

### Status LEDs (Traffic-light module)

```
GPIO 17 (Pin 11) → Green LED  anode  → GND  (NORMAL state indicator)
GPIO 27 (Pin 13) → Yellow LED anode  → GND  (DEGRADED state indicator)
GPIO 22 (Pin 15) → Red LED    anode  → GND  (SAFE STATE indicator)
```

Include current-limiting resistors (330 Ω recommended) on each LED.

### Active Buzzer

```
GPIO 18 (Pin 12) → Buzzer (+)
GND              → Buzzer (−)
```

Active 3.3 V buzzer — sounds when GPIO driven HIGH.

## Actuator Wiring

Motor driver and DC motors are **not present in the current hardware build**.
Motor control GPIO assignments (GPIO 9, 10, 11, 12) are reserved but unconnected.
Motor integration is deferred to a future milestone.

## Power Distribution

### Isolated Power Supplies

**Pi5 Power**:
- 5V, 3A minimum (5A recommended for peripherals)
- USB-C power delivery
- Powers: Pi5 board, Camera Module 3, Grove Ultrasonic Ranger (via 3.3 V pin), LEDs, buzzer

**Pi400 Power**:
- 5V, 3A minimum
- USB-C power delivery
- Powers: Pi400 board only

### Ground Connections

```
Pi5 GND ───── Pi400 GND (common ground for inter-processor GPIO signals)
```

## Wiring Diagram (ASCII Art)

```
┌─────────────────────────────────────┐       ┌─────────────────────────┐
│   Raspberry Pi 5 (Linux/ROS2)       │       │   Raspberry Pi 400      │
│                                     │       │   (QNX-inspired)        │
│  GPIO 17 (Pin 11) ─ Green LED       │       │                         │
│  GPIO 27 (Pin 13) ─ Yellow LED      │       │                         │
│  GPIO 22 (Pin 15) ─ Red LED         │       │                         │
│  GPIO 18 (Pin 12) ─ Buzzer          │       │                         │
│  GPIO 23 (Pin 16) ─ Ultrasonic SIG  │       │                         │
│                                     │       │                         │
│  GPIO TBD ── Heartbeat ─────────────┼───────┼──> GPIO In (WDG)        │
│  GPIO TBD <── E-Stop ───────────────┼───────┼─── GPIO Out (E-Stop)    │
│  GND ───────────────────────────────┼───────┼─── GND                  │
│                                     │       │                         │
└──────────────────┬──────────────────┘       └─────────────────────────┘
                   │ CSI ribbon cable
            ┌──────▼──────────┐    ┌──────────────────────┐
            │  Camera Module 3 │    │  Grove Ultrasonic     │
            │  IMX708          │    │  Ranger (SIG Pin 16)  │
            └─────────────────┘    └──────────────────────┘
```

**Note**: Heartbeat and e-stop GPIO numbers on Pi5 are TBD — GPIO 17/27 are currently
used for LEDs and will be reassigned to unallocated pins before M2 integration.

## Wiring Checklist

Before powering on, verify:

- [ ] Common ground established between Pi5 and Pi400
- [ ] Camera Module 3 CSI ribbon cable fully seated, correct orientation
- [ ] Grove Ultrasonic Ranger: SIG (yellow) → GPIO 23 (Pin 16), VCC → 3.3 V, GND connected
- [ ] LEDs: GPIO 17/27/22 → Green/Yellow/Red anodes, cathodes to GND
- [ ] Buzzer: GPIO 18 → (+), GND → (−)
- [ ] Heartbeat GPIO (TBD) connected to Pi400 input (deferred to M2)
- [ ] Emergency stop GPIO (TBD) connected from Pi400 output (deferred to M2)
- [ ] No loose wires or shorts visible

## Testing Procedure

1. **Power Sequence**:
   - Power Pi400 first (supervisor should assert emergency stop when implemented)
   - Power Pi5 second

2. **Camera Test**:
   - Run `bash pi5_linux/scripts/camera_test.sh`
   - Confirm IMX708 detected

3. **Sensor Test**:
   - Run `python3 pi5_linux/scripts/ultrasonic_test.py`
   - Move obstacle in front of sensor at known distances, verify readings

4. **LED and Buzzer Test**:
   - Run `python3 pi5_linux/scripts/led_test.py`
   - Run `python3 pi5_linux/scripts/buzzer_test.py`

5. **Signal Verification** (deferred to M2):
   - Heartbeat GPIO: measure 10 Hz square wave after ROS2 startup
   - Emergency stop GPIO: measure LOW until supervisor releases

## Maintenance Notes

**GPIO Connection Reliability**:
- Dupont jumper wires can become loose over time
- Consider soldering or using screw terminals for permanent installation
- Use cable ties to prevent strain on GPIO connections

**Ultrasonic Sensor Placement**:
- Mount sensor rigidly to prevent vibration affecting measurements
- Angle slightly downward to detect ground obstacles
- Avoid mounting near acoustic noise sources (speakers, fans)

## Future Enhancements

**Redundancy** (not implemented in this demo):
- Dual heartbeat GPIOs on separate pins
- Dual emergency stop signals (2oo2 voting)
- Watchdog feedback GPIO (Pi400 → Pi5 acknowledge)

**Diagnostics**:
- LED indicators for heartbeat and emergency stop state
- Buzzer for audible warnings on state transitions

**Robust Connectors**:
- Replace jumper wires with locking connectors
- PCB shield with screw terminals for sensors and motors

## References

- Raspberry Pi 5 GPIO Pinout: https://pinout.xyz
- Raspberry Pi 400 GPIO Pinout: https://pinout.xyz/pinout/pi400
- HC-SR04 Datasheet: https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf
- L298N Motor Driver Datasheet: https://www.st.com/resource/en/datasheet/l298.pdf
