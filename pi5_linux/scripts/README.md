# Pi5 Bring-up Scripts

**Milestones**: M1.1 (hardware bring-up) and M2 (inter-processor wiring verification)
**Scope**: Manual hardware bring-up and inter-processor wiring tests only.
**Not in scope**: ROS2 integration, AI inference, safety decision logic.

This is an educational demonstrator. No ISO 26262 certification or ASIL-B compliance is claimed.

---

## Prerequisites

Install required packages on Pi5 before running scripts:

```bash
# GPIO library (required for led_test.py, buzzer_test.py, ultrasonic_test.py, estop_input_test.py)
sudo apt install python3-lgpio

# Camera tools (required for camera_test.sh)
sudo apt install rpicam-apps v4l-utils

# I2C tools (required for i2c_bus_test.sh)
sudo apt install i2c-tools
```

Enable I2C if not already active:
```bash
sudo raspi-config   # → Interface Options → I2C → Enable
# or: add dtparam=i2c_arm=on to /boot/firmware/config.txt and reboot
```

---

## M1.1 Scripts (Hardware Component Bring-up)

### `camera_test.sh` — Camera Detection

**Purpose**: Check whether the camera module is detected.

```bash
bash pi5_linux/scripts/camera_test.sh
```

**No wiring required.** Expected: PASS on all 5 steps, IMX708 detected.

---

### `led_test.py` — Traffic-light LED Toggle (Pi5 side)

**Purpose**: Toggle green, yellow, and red LEDs individually and confirm visual response.

**Wiring (M2 confirmed)**:
| LED    | GPIO | Physical Pin | Circuit |
|--------|------|-------------|---------|
| Green  | 17   | Pin 11      | GPIO → 330 Ω → GND |
| Yellow | 27   | Pin 13      | GPIO → 330 Ω → GND |
| Red    | 22   | Pin 15      | GPIO → 150 Ω → 1N4148 → junction → LED → GND |

**Note**: Red LED uses diode-OR circuit from M2. Use 150 Ω (not 330 Ω) on the Pi5 leg.

```bash
python3 pi5_linux/scripts/led_test.py
```

---

### `buzzer_test.py` — Active Buzzer

**Purpose**: Confirm audible tone from active 3.3V buzzer on GPIO 18 (Pin 12).

```bash
python3 pi5_linux/scripts/buzzer_test.py
```

---

### `ultrasonic_test.py` — Grove Ultrasonic Ranger

**Purpose**: Read distances from Grove Ultrasonic Ranger on GPIO 23 (Pin 16).

**Wiring**: SIG (yellow) → GPIO 23 (Pin 16), VCC → 3.3V, GND → GND. No voltage divider needed.

```bash
python3 pi5_linux/scripts/ultrasonic_test.py
```

---

## M2 Scripts (Inter-Processor Wiring Verification)

### `i2c_bus_test.sh` — I2C Bus Health Check

**Purpose**: Verify I2C-1 bus is up on GPIO 2/3, pull-ups are fitted, and bus scan runs.

**Wiring required**:
- GPIO 2 (Pin 3) ↔ Pi400 GPIO 2 (Pin 3) — SDA
- GPIO 3 (Pin 5) ↔ Pi400 GPIO 3 (Pin 5) — SCL
- 4.7 kΩ pull-ups to 3.3V on both SDA and SCL
- Common GND: Pi5 Pin 6 ↔ Pi400 Pin 6

```bash
bash pi5_linux/scripts/i2c_bus_test.sh
```

**Expected**: `/dev/i2c-1` present, bus scan runs (no device at 0x40 until Pi400 slave software is running).

---

### `estop_input_test.py` — Emergency Stop Input

**Purpose**: Read GPIO 25 (Pin 22) for 10 seconds and observe HIGH/LOW transitions driven by Pi400.

**Wiring required**: Pi400 GPIO 25 (Pin 22) → Pi5 GPIO 25 (Pin 22)

**Run simultaneously with `estop_output_test.py` on Pi400**:

```bash
# Pi5 terminal:
python3 pi5_linux/scripts/estop_input_test.py

# Pi400 terminal (simultaneously):
python3 pi400_supervisor/scripts/estop_output_test.py
```

**Expected**: Pi5 observes HIGH → LOW → HIGH → LOW transitions.

---

## Suggested Execution Order (M2 hardware verification)

1. `i2c_bus_test.sh` — I2C bus and pull-ups
2. `estop_input_test.py` (Pi5) + `estop_output_test.py` (Pi400) — simultaneously
3. `led_test.py` (Pi5) — re-verify red LED with new 150 Ω + diode circuit
4. `pi400_supervisor/scripts/red_led_test.py` (Pi400) — confirm Pi400 can independently assert red LED

---

## What These Scripts Do NOT Do

- No ROS2 nodes or topics
- No AI inference or object detection
- No Q&A watchdog protocol (requires M2 node implementation)
- No safety state machine
- No motor control
- No ISO 26262 compliance
