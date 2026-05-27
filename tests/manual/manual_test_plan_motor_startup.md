# Manual Test Plan — Motor Actuator, Startup, and Safe-State Behaviour

> **Educational demonstrator only — NOT ISO 26262 certified — NOT production-ready.**
> These are manual acceptance tests for the DRV8833 motor actuator and startup concept.

---

## Prerequisites

- Hardware wired as described in `hardware/wiring.md` (DRV8833 + 4×AA battery + AEDIKO TT motor)
- Pi5 and Pi400 connected to shared power strip (Main Switch)
- 4×AA batteries inserted; battery box switch = Motor Switch
- ROS2 workspace built on Pi5 (`colcon build` complete)
- Pi400 supervisor script available (`pi400_supervisor/scripts/qnx_wdg_server.py`)

---

## MT-001 — Main Switch Startup: Both Processors Boot

**Objective**: Verify Pi5 and Pi400 boot simultaneously when Main Switch is turned ON.

**Preconditions**:
- Main Switch OFF
- Motor Switch OFF

**Steps**:
1. Connect Pi5 and Pi400 USB-C PSUs to the shared power strip.
2. Turn **Main Switch ON**.
3. Observe Pi5 and Pi400 status LEDs / boot output.

**Expected results**:
- Pi5 begins booting (green activity LED on board).
- Pi400 begins booting.
- Both boards are reachable via SSH within ~30 seconds of Main Switch ON.

**Pass/Fail**: ____

---

## MT-002 — Boot Default: Motor Off During Startup

**Objective**: Verify motor does not rotate during system boot even if Motor Switch is ON.

**Preconditions**:
- Main Switch OFF
- Motor Switch ON (to confirm motor is inhibited by software, not by power)
- DRV8833 and TT motor wired and ready

**Steps**:
1. Turn **Main Switch ON** (Pi5 and Pi400 boot).
2. Observe TT motor during entire boot sequence (do not run ROS2 nodes yet).

**Expected results**:
- Motor does NOT rotate at any point during boot.
- DRV8833 IN1 and IN2 are both LOW (can verify with multimeter on GPIO 12, 16).
- Red LED may be ON (e-stop asserted by Pi400).

**Pass/Fail**: ____

---

## MT-003 — Software Not Initialised: Motor Remains Off

**Objective**: Verify motor remains off if ROS2 nodes are not started (software not initialised).

**Preconditions**:
- Main Switch ON (Pi5 and Pi400 booted)
- Motor Switch ON
- ROS2 nodes NOT launched

**Steps**:
1. Do not run any ROS2 launch commands on Pi5.
2. Observe motor for at least 30 seconds.

**Expected results**:
- Motor does NOT rotate.
- System remains in INIT / SAFE_STATE (watchdog not healthy — no response from Pi5 application nodes).
- Red LED ON.

**Pass/Fail**: ____

---

## MT-004 — Normal Motor Rotation in NORMAL State

**Objective**: Verify motor rotates at velocity_scale = 1.0 in NORMAL state with Motor Switch ON.

**Preconditions**:
- Main Switch ON
- Motor Switch ON
- ROS2 nodes launched on Pi5 (all alive)
- Pi400 supervisor running
- No obstacle in sensor detection range
- System in NORMAL state (green LED ON)

**Steps**:
1. Launch Pi400 supervisor: `python3 ~/safety-supervised-edge-ai-demo/pi400_supervisor/scripts/qnx_wdg_server.py`
2. Launch Pi5 ROS2 stack: `ros2 launch safety_demo demo.launch.py`
3. Send reset: `ros2 topic pub --once /reset std_msgs/msg/Bool "data: true"`
4. Confirm system state: `ros2 topic echo /system_state` — expect NORMAL.
5. Check velocity_scale: `ros2 topic echo /velocity_scale` — expect 1.0.
6. Observe TT motor.

**Expected results**:
- Motor rotates clearly and visibly.
- Green LED ON.
- `velocity_scale = 1.0` published.
- `/system_state` = NORMAL.

**Pass/Fail**: ____

---

## MT-005 — Motor Switch OFF: Motor Stops Regardless of Software State

**Objective**: Verify Motor Switch OFF stops the motor even if system is in NORMAL (software allows motion).

**Preconditions**:
- System in NORMAL state (from MT-004)
- Motor rotating at velocity_scale = 1.0
- Motor Switch ON

**Steps**:
1. With motor rotating in NORMAL, turn **Motor Switch OFF**.
2. Observe motor.
3. Check ROS2 topics — system state should remain NORMAL.

**Expected results**:
- Motor stops immediately (motor supply removed).
- System state remains NORMAL (software does not detect Motor Switch position).
- Green LED remains ON.
- `velocity_scale` remains 1.0 (software still commands motion).

**Pass/Fail**: ____

**Steps (restore)**:
4. Turn **Motor Switch ON** again.

**Expected results (restore)**:
- Motor resumes rotation at velocity_scale = 1.0.
- No state change in software.

**Pass/Fail (restore)**: ____

---

## MT-006 — WARNING State: Velocity Reduction

**Objective**: Verify motor speed is reduced to velocity_scale = 0.5 when obstacle is in warning range.

**Preconditions**:
- System in NORMAL state
- Motor rotating at velocity_scale = 1.0
- Motor Switch ON

**Steps**:
1. Place an obstacle at the configured warning range distance (default ~0.50 m) in front of the ultrasonic sensor.
2. Observe motor speed and LED state.
3. Check: `ros2 topic echo /system_state` — expect WARNING.
4. Check: `ros2 topic echo /velocity_scale` — expect 0.5.

**Expected results**:
- Motor speed visibly reduces.
- Yellow LED ON; Green LED OFF.
- `/system_state` = WARNING.
- `velocity_scale = 0.5`.

**Pass/Fail**: ____

**Steps (clear warning)**:
5. Remove obstacle from warning range.

**Expected results (clear warning)**:
- System returns to NORMAL automatically.
- Green LED ON; Yellow LED OFF.
- Motor speed returns to velocity_scale = 1.0.

**Pass/Fail (clear)**: ____

---

## MT-007 — Near Range: SAFE_STATE Triggered

**Objective**: Verify SAFE_STATE is entered and motor stops when ultrasonic detects obstacle in near range (<0.15 m).

**Preconditions**:
- System in NORMAL state
- Motor rotating
- Motor Switch ON

**Steps**:
1. Slowly bring an obstacle to within 0.15 m of the ultrasonic sensor.
2. Observe motor and LEDs.
3. Check: `ros2 topic echo /system_state` — expect SAFE_STATE.
4. Measure latency from threshold breach to motor stop (target: <100 ms).

**Expected results**:
- Motor stops (velocity_scale = 0.0).
- Red LED ON.
- `/system_state` = SAFE_STATE.
- SAFE_STATE latches — motor does not restart when obstacle is removed without `/reset`.

**Pass/Fail**: ____

**Steps (reset)**:
5. Remove obstacle.
6. Send reset: `ros2 topic pub --once /reset std_msgs/msg/Bool "data: true"`

**Expected results (reset)**:
- System returns to NORMAL (if all conditions clear).
- Green LED ON; Red LED OFF.
- Motor resumes at velocity_scale = 1.0.

**Pass/Fail (reset)**: ____

---

## MT-008 — Pi400 Watchdog Fault: SAFE_STATE and Motor Stop

**Objective**: Verify Pi400 watchdog fault causes SAFE_STATE and motor stop via hardware GPIO 25 path.

**Preconditions**:
- System in NORMAL state
- Motor rotating
- Motor Switch ON

**Steps**:
1. Identify and stop the `health_node` process on Pi5:
   ```bash
   ros2 node kill /health_node
   # or: kill <health_node PID>
   ```
2. Observe motor, LEDs, and GPIO 25 state.
3. Wait for Pi400 failure_counter to reach ≥ 3 (approximately 3 × 30 ms = ~90 ms + processing).
4. Measure time from health_node stop to motor stop.

**Expected results**:
- Motor stops within 150 ms of health_node stop.
- Red LED ON (asserted by Pi400 via GPIO 22).
- Pi400 GPIO 25 driven LOW (e-stop asserted) — measurable with multimeter on Pi5 Pin 22.
- `/system_state` = SAFE_STATE (if Pi5 can still publish).
- `velocity_scale = 0.0`.

**Pass/Fail**: ____

**Steps (recover)**:
5. Restart health_node.
6. Wait for failure_counter to drop below threshold.
7. Send `/reset`.

**Expected results (recover)**:
- System returns to NORMAL.
- Green LED ON; Red LED OFF.
- Motor resumes.

**Pass/Fail (recover)**: ____

---

## MT-009 — SAFE_STATE Motor Override: velocity_scale Command Ignored

**Objective**: Verify that publishing velocity_scale > 0.0 in SAFE_STATE does NOT cause motor to rotate.

**Preconditions**:
- System in SAFE_STATE (e.g., triggered by near-range detection in MT-007)
- Motor stopped

**Steps**:
1. While in SAFE_STATE, manually publish velocity_scale = 1.0:
   ```bash
   ros2 topic pub --once /velocity_scale std_msgs/msg/Float32 "data: 1.0"
   ```
2. Observe motor.

**Expected results**:
- Motor does NOT rotate.
- actuator_node overrides command to velocity_scale = 0.0 in SAFE_STATE.
- Red LED remains ON.

**Pass/Fail**: ____

---

## MT-010 — Incomplete Startup: System Does Not Release to NORMAL

**Objective**: Verify the system does not reach NORMAL if startup criteria are not satisfied (e.g., watchdog not yet healthy).

**Preconditions**:
- Main Switch OFF
- Pi400 supervisor NOT running

**Steps**:
1. Turn **Main Switch ON** — Pi5 and Pi400 boot.
2. Launch Pi5 ROS2 nodes but do NOT start Pi400 supervisor.
3. Send reset: `ros2 topic pub --once /reset std_msgs/msg/Bool "data: true"`
4. Observe `/system_state` for 30 seconds.

**Expected results**:
- System stays in INIT or SAFE_STATE.
- Does NOT transition to NORMAL (Q&A watchdog is not healthy — Pi400 supervisor not running).
- Motor does NOT rotate (Motor Switch ON or OFF).
- Red LED ON (or init pattern).

**Pass/Fail**: ____

---

## Test Summary

| Test ID | Description | Result |
|---------|-------------|--------|
| MT-001 | Main Switch: both processors boot | |
| MT-002 | Boot default: motor off during startup | |
| MT-003 | Software not initialised: motor remains off | |
| MT-004 | NORMAL state: motor rotates at velocity_scale = 1.0 | |
| MT-005 | Motor Switch OFF: motor stops, software state unchanged | |
| MT-006 | WARNING state: velocity reduced to 0.5 | |
| MT-007 | Near range: SAFE_STATE, motor stops | |
| MT-008 | Watchdog fault: SAFE_STATE via GPIO 25, motor stops | |
| MT-009 | SAFE_STATE override: velocity command ignored | |
| MT-010 | Incomplete startup: system stays in INIT/SAFE_STATE | |

---

## References

- `hardware/wiring.md` — DRV8833 wiring specification
- `hardware/gpio_mapping.md` — GPIO 12, 16 motor driver pin mapping
- `docs/safety_concept.md` — state transitions and velocity_scale behaviour
- `requirements/safety_requirements.md` — FSR-009 through FSR-013
- `requirements/system_requirements.md` — SYS-FUNC-009 through SYS-SAFE-014
