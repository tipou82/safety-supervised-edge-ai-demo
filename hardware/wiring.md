# Hardware Wiring Specification

## Overview

This document describes the physical wiring between Raspberry Pi 5 (Linux/ROS2 domain) and Raspberry Pi 400 (QNX supervisor domain), as well as connections to sensors and actuators.

## Safety Note

⚠️ **Single Point of Failure**: All GPIO connections are single-wire (no redundancy). This is acceptable for a demonstrator but would not meet production safety standards.

## Bill of Materials

| Component | Quantity | Purpose | Notes |
|-----------|----------|---------|-------|
| Raspberry Pi 5 (8GB) | 1 | Linux/ROS2 domain | Main perception processor |
| Raspberry Pi 400 | 1 | QNX supervisor domain | Safety monitor |
| HC-SR04 Ultrasonic Sensors | 3 | Obstacle detection | 2cm-400cm range |
| USB Camera (or Pi Camera) | 1 | AI perception | 1080p, 30fps recommended |
| Motor Driver (L298N or similar) | 1 | Motor control | PWM input, bidirectional |
| DC Motors | 2 | Actuators | 12V or 6V depending on robot |
| Jumper wires | 20+ | GPIO connections | Dupont female-female |
| Breadboard | 1 | Prototyping | Optional for sensor power |
| Power supply (5V, 3A+) | 2 | Power each Pi | USB-C for Pi5, USB-C for Pi400 |
| Power supply (motor voltage) | 1 | Motor power | Separate from logic power |

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

### Notes on Inter-Processor Wiring

- **Ground Reference**: Ensure common ground between both Pi boards
- **No Level Shifters**: Both Pi5 and Pi400 use 3.3V GPIO, direct connection OK
- **Cable Length**: Keep <30 cm to minimize noise and signal integrity issues
- **Strain Relief**: Use cable management to prevent accidental disconnection

## Sensor Wiring

### Ultrasonic Sensors (HC-SR04) x3

Each sensor requires 4 connections:

**Sensor 1 (Front Center)**
```
HC-SR04 Pin      → Pi5 GPIO
VCC              → 5V (Pin 2)
GND              → GND (Pin 6)
TRIG             → GPIO 23 (Pin 16)
ECHO             → GPIO 24 (Pin 18) via voltage divider
```

**Sensor 2 (Front Left)**
```
HC-SR04 Pin      → Pi5 GPIO
VCC              → 5V (Pin 4)
GND              → GND (Pin 9)
TRIG             → GPIO 5 (Pin 29)
ECHO             → GPIO 6 (Pin 31) via voltage divider
```

**Sensor 3 (Front Right)**
```
HC-SR04 Pin      → Pi5 GPIO
VCC              → 5V (Pin 4)
GND              → GND (Pin 14)
TRIG             → GPIO 13 (Pin 33)
ECHO             → GPIO 19 (Pin 35) via voltage divider
```

**Voltage Divider for ECHO Pin**:
HC-SR04 ECHO output is 5V, but Pi GPIO is 3.3V tolerant. Use voltage divider:
```
ECHO pin ──── R1 (1kΩ) ──┬──── Pi GPIO
                          │
                         R2 (2kΩ)
                          │
                         GND

Vout = 5V * (2kΩ / (1kΩ + 2kΩ)) = 3.33V
```

### Camera

**USB Camera**: Connect to Pi5 USB 3.0 port (blue connector).

**Pi Camera Module**: Connect to Pi5 camera connector (CSI).

No GPIO wiring required for camera.

## Actuator Wiring

### Motor Driver (L298N)

**Control Signals from Pi5**
```
L298N Pin        → Pi5 GPIO
IN1 (Motor A Dir) → GPIO 22 (Pin 15)
IN2 (Motor A Dir) → GPIO 10 (Pin 19)
IN3 (Motor B Dir) → GPIO 9 (Pin 21)
IN4 (Motor B Dir) → GPIO 11 (Pin 23)
ENA (Motor A PWM) → GPIO 18 (Pin 12, PWM0)
ENB (Motor B PWM) → GPIO 12 (Pin 32, PWM0)
```

**Emergency Stop from QNX (via Pi5)**
```
Pi5 GPIO 27 (Pin 13) ──→ Motor driver ENABLE (active-high)
```
Logic: When GPIO 27 is LOW (emergency stop asserted), motor driver is disabled.

**Power Connections**
```
L298N Pin        → Connection
12V              → Motor power supply +
GND              → Motor power supply - AND Pi5 GND (Pin 6)
OUT1, OUT2       → Motor A
OUT3, OUT4       → Motor B
```

**Important**: Common ground between motor power supply and Pi5 logic ground.

## Power Distribution

### Isolated Power Supplies

**Pi5 Power**:
- 5V, 3A minimum (5A recommended for peripherals)
- USB-C power delivery
- Powers: Pi5 board, USB camera, ultrasonic sensors (5V)

**Pi400 Power**:
- 5V, 3A minimum
- USB-C power delivery
- Powers: Pi400 board only

**Motor Power**:
- Voltage per motor specification (6V or 12V typical)
- Current: Calculate based on motor stall current (e.g., 2A per motor)
- Separate supply from logic power (prevents voltage drops on Pi)

### Ground Connections

All grounds must be connected:
```
Pi5 GND ──┬── Pi400 GND
          ├── Motor power supply GND
          └── Motor driver GND
```

## Wiring Diagram (ASCII Art)

```
┌─────────────────────────┐                  ┌─────────────────────────┐
│   Raspberry Pi 5        │                  │   Raspberry Pi 400      │
│   (Linux/ROS2)          │                  │   (QNX Supervisor)      │
│                         │                  │                         │
│  GPIO 17 (Heartbeat) ───┼──────────────────┼───> GPIO In (WDG)       │
│  GPIO 27 (E-Stop In) <──┼──────────────────┼──── GPIO Out (E-Stop)   │
│  GND ────────────────────┼────────┬─────────┼──── GND                 │
│                         │        │         │                         │
└────┬─────────┬──────────┘        │         └─────────────────────────┘
     │         │                   │
     │ USB     │ GPIO              │
     │         │                   │
  ┌──▼──┐   ┌──▼─────────────┐    │
  │ USB │   │  HC-SR04 x3     │    │
  │Camera   │  Ultrasonic     │    │
  └─────┘   │  Sensors        │    │
            └─────────────────┘    │
                                   │
            ┌──────────────────────▼──────┐
            │   Motor Driver (L298N)       │
            │   - IN1-4 from Pi5           │
            │   - ENA/ENB PWM from Pi5     │
            │   - ENABLE from GPIO27       │
            └──────┬───────────┬───────────┘
                   │           │
               ┌───▼──┐    ┌───▼──┐
               │Motor │    │Motor │
               │  A   │    │  B   │
               └──────┘    └──────┘
```

## Wiring Checklist

Before powering on, verify:

- [ ] All ground connections established (Pi5, Pi400, motor driver)
- [ ] No direct 5V to 3.3V GPIO connections (ECHO pins have voltage dividers)
- [ ] Heartbeat GPIO output (Pi5) connected to input (Pi400)
- [ ] Emergency stop GPIO output (Pi400) connected to input (Pi5)
- [ ] Motor power supply isolated from logic power supplies
- [ ] USB camera connected to Pi5
- [ ] All ultrasonic sensors powered and connected with correct TRIG/ECHO pins
- [ ] Motor driver ENABLE line connected to GPIO27 (emergency stop control)
- [ ] No loose wires or shorts visible

## Testing Procedure

1. **Power Sequence**:
   - Power Pi400 first (supervisor should assert emergency stop)
   - Power Pi5 second
   - Power motor supply last

2. **Signal Verification**:
   - Measure heartbeat GPIO with oscilloscope (should see 10 Hz after ROS2 startup)
   - Measure emergency stop GPIO (should be LOW until supervisor releases)

3. **Emergency Stop Test**:
   - With system running in NORMAL state
   - Manually stop heartbeat (kill health monitor process)
   - Verify emergency stop asserted within 500 ms
   - Verify motors disabled

4. **Sensor Test**:
   - Move obstacle in front of each ultrasonic sensor
   - Verify distance readings published on ROS2 topic
   - Check for consistent measurements

## Maintenance Notes

**GPIO Connection Reliability**:
- Dupont jumper wires can become loose over time
- Consider soldering or using screw terminals for permanent installation
- Use cable ties to prevent strain on GPIO connections

**Ultrasonic Sensor Placement**:
- Mount sensors rigidly to prevent vibration affecting measurements
- Angle sensors slightly downward to detect ground obstacles
- Avoid mounting near acoustic noise sources (motors, speakers)

**Motor Driver Heat Dissipation**:
- L298N can get hot under continuous load
- Ensure adequate ventilation
- Consider heatsink if motors draw >1A continuous

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
