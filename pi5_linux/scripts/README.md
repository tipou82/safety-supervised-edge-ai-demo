# Pi5 Bring-up Scripts

**Milestone**: M1.1 – Pi5 Hardware Component Bring-up
**Scope**: Manual hardware bring-up and verification only.
**Not in scope**: ROS2 integration, AI inference, safety decision logic, watchdog/heartbeat protocol.
ROS2 integration begins in a later milestone.

This is an educational demonstrator. No ISO 26262 certification or ASIL-B compliance is claimed.

---

## Prerequisites

Install required packages on Pi5 before running GPIO or camera scripts:

```bash
# GPIO library (required for led_test.py, buzzer_test.py, ultrasonic_test.py)
sudo apt install python3-lgpio

# Camera tools (required for camera_test.sh)
sudo apt install rpicam-apps v4l-utils
```

No packages are installed automatically by any script.

---

## Scripts

### `camera_test.sh` — Camera Detection

**Purpose**: Check whether the camera module is detected by the Pi5.

**Run**:
```bash
bash pi5_linux/scripts/camera_test.sh
```

**Expected output**: `[PASS]` lines for camera tool availability, `/dev/video*` devices,
device tree entries, and camera list.

**Manual evidence to record**:
- Which camera tool was found (`rpicam-hello` or `libcamera-hello`)
- Whether `--list-cameras` listed the camera module
- Any error messages

**No wiring required.** Safe to run at any time.

---

### `led_test.py` — Traffic-light LED Toggle

**Purpose**: Toggle green, yellow, and red LEDs individually and confirm visual response.

**Wiring (confirm before running)**:
| LED    | GPIO | Physical Pin | Resistor | GND Pin |
|--------|------|-------------|----------|---------|
| Green  | 16   | Pin 36      | 330 Ω    | Pin 39  |
| Yellow | 20   | Pin 38      | 330 Ω    | Pin 39  |
| Red    | 21   | Pin 40      | 330 Ω    | Pin 39  |

**Run**:
```bash
python3 pi5_linux/scripts/led_test.py
```

The script will ask you to confirm wiring before proceeding, then test each LED individually,
prompting for visual confirmation (ON / OFF) at each step.

**Manual evidence to record**:
- Each LED turns ON and OFF as expected (yes/no per LED)
- Any wiring deviations

---

### `buzzer_test.py` — Active Buzzer Toggle

**Purpose**: Activate the 3.3 V active buzzer for 0.5 s and confirm audible response.

**Wiring (confirm before running)**:
| Signal | GPIO | Physical Pin |
|--------|------|-------------|
| Buzzer + | 26 | Pin 37      |
| Buzzer − | —  | Pin 39 (GND)|

Use an **active** buzzer (sounds when GPIO is driven HIGH with DC). A passive buzzer requires
PWM and will not work with this script.

**WARNING: The buzzer may be loud.**

**Run**:
```bash
python3 pi5_linux/scripts/buzzer_test.py
```

The script asks for wiring confirmation, then activates the buzzer once for 0.5 s.

**Manual evidence to record**:
- Audible tone heard (yes/no)
- Any wiring deviations

---

### `ultrasonic_test.py` — HC-SR04 Distance Readings

**Purpose**: Read distance from HC-SR04 Sensor 1 (front-centre) and print timestamped readings.

**Wiring (confirm before running)**:
| HC-SR04 Pin | Connection |
|-------------|-----------|
| VCC         | Pin 2 (5 V) |
| GND         | Pin 6 (GND) |
| TRIG        | GPIO 23, Pin 16 |
| ECHO        | Voltage divider → GPIO 24, Pin 18 |

**ECHO voltage divider is mandatory** (HC-SR04 ECHO = 5 V; Pi5 GPIO max = 3.3 V):
```
HC-SR04 ECHO ── R1 (1 kΩ) ─┬── GPIO 24 (Pin 18)
                             R2 (2 kΩ)
                             GND
```
Skipping the voltage divider risks permanent GPIO damage.

**Run**:
```bash
python3 pi5_linux/scripts/ultrasonic_test.py
```

The script asks for wiring confirmation, then prints 20 distance readings at ~5 Hz.
Place an object at a known distance (e.g. 20 cm, 50 cm) to verify accuracy.

**Manual evidence to record**:
- Sample readings at two known distances (expected ±10%)
- Number of timeouts (should be 0 on a healthy sensor)

---

## Suggested Execution Order

1. `camera_test.sh` — no wiring required, safe to run first
2. `led_test.py` — after wiring LEDs and confirming resistors
3. `buzzer_test.py` — after wiring buzzer, be prepared for noise
4. `ultrasonic_test.py` — after wiring sensor AND building voltage divider on ECHO line

---

## What These Scripts Do NOT Do

- No ROS2 nodes or topics
- No AI inference or object detection
- No heartbeat or watchdog logic
- No safety state machine
- No motor control
- No data logging to files
- No ISO 26262 compliance
