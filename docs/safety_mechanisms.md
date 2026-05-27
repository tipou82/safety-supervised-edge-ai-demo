# Safety Mechanisms

> **Disclaimer**: Educational demonstrator — ASIL-B-inspired patterns only.
> NOT ISO 26262 certified. NOT suitable for production use.
> See `docs/safety_concept.md` for the safety philosophy and hazard context.

This is the **single authoritative reference** for all safety mechanisms implemented in the
Safety-Supervised Edge AI Demonstrator. All other documents that previously described
implementation details link here.

---

## Architecture Safety Boundaries

Two physically separate processors demonstrate **FFI-inspired architectural measures**
(Freedom from Interference — not certified, ASIL-B-inspired patterns only):

```
Pi5 (Linux / ROS2)          ← AI perception domain (development)
  hand_detection_node  ─┐
  object_detection_node ┘  ← MMU-isolated processes (spatial FFI within Pi5)
  decision_node
  actuator_node
  health_node
        │
        │  UDP Q&A watchdog (Ethernet 192.168.50.x)   SM-1
        │  GPIO 25 e-stop (direct wire)                SM-2
        │
Pi400 (Ubuntu / QNX-inspired)  ← Safety supervisor domain (deterministic)
  qnx_wdg_server
```

AI outputs **never enter the safety path**. The supervisor makes decisions based solely on
watchdog liveness and deterministic rules.

For the full FFI argument, effectiveness ratings, and gap analysis, see `docs/ffi_argument.md`.

---

## SM-1 — Q&A Watchdog (UDP)

### Transport
UDP over dedicated Ethernet, port 9001. Pi400 IP: `192.168.50.20`. Pi5 IP: `192.168.50.10`.
Transport chosen over I2C because BCM2711 BSC slave is not supported by pigpio (DD-002).

### Protocol

```
Pi400 → Pi5:  {"type": "seed",     "seed": <uint32>, "seq": <uint8>,  "crc": <uint16>}
Pi5   → Pi400: {"type": "response", "seed": <uint32>, "response": <uint32>,
                                     "seq": <uint8>,  "crc": <uint16>}
Pi400 → Pi5:  {"type": "status",   "failure_counter": <int>, "state": <str>,
                                    "released": <bool>}
```

### Response algorithm

```
response = seed XOR 0xA5A5A5A5
```

### E2E protection

| Field | Purpose |
|---|---|
| `seq` | uint8 counter incremented by Pi400 each cycle; Pi5 echoes — detects lost/replayed packets |
| `crc` | CRC-16/CCITT-FALSE over `{seed, seq}` — detects bit flips in transit |

### Timing window (30ms total)

| Zone | Elapsed from seed send | Pi400 action |
|---|---|---|
| Closed | 0–15ms | Response too early → `failure_counter++` |
| Open | 15–30ms | Validate response |
| Timeout | >30ms | No response → `failure_counter++` |

**health_node cycle: 20ms** — response targets ~20ms, centre of open window.
UDP thread socket timeout: **5ms** — ensures pending seed checked within open window.

### Failure counter

| Event | Effect |
|---|---|
| Wrong answer, too early, or timeout | `failure_counter++` |
| 2 consecutive correct responses | `failure_counter--` (minimum 0) |
| `failure_counter ≥ 3` | **SAFE_STATE**: GPIO 25 LOW + GPIO 22 HIGH |

### Flow check gate (SM-7 integration)

health_node **withholds the Q&A response** if any monitored node misses its deadline:

| Topic | Publisher | Nominal period | Deadline |
|---|---|---|---|
| `/system_state` | decision_node | 20ms | 60ms |
| `/obstacles` | ultrasonic_node | 50ms | 150ms |

If either misses its deadline → response withheld → Pi400 counts failures → SAFE_STATE.
Pipeline failure directly triggers safe state via the hardware path.

### Implementation files

- `pi400_supervisor/scripts/qnx_wdg_server.py` — Pi400 server
- `pi5_linux/ros2_ws/src/health_node/health_node/health_node.py` — Pi5 client + flow check

---

## SM-2 — Hardware E-Stop (GPIO 25)

Direct wire: Pi400 GPIO 25 (Pin 22) → Pi5 GPIO 25 (Pin 22), active-low.

| State | Pi400 GPIO 25 | Pi5 reads | Effect |
|---|---|---|---|
| Boot / SAFE_STATE | LOW (asserted) | 0 | Motors disabled |
| NORMAL (released) | HIGH | 1 | Motors enabled |

- Pi5 `actuator_node` polls at **100 Hz** — detects assertion within 10ms
- Motor disable within **30ms** of assertion
- **Fail-safe**: asserted at Pi400 boot, released only after first valid Q&A cycle
- **FFI boundary**: independent of decision_node, StateEvaluator, and ROS2

**Implementation**: `pi5_linux/ros2_ws/src/actuator_node/actuator_node/actuator_node.py`

---

## SM-3 — Software State Machine (StateEvaluator C++20)

Evaluated at **50 Hz** (20ms) in `decision_node`. Pure function — no side effects.

### States and velocity scaling

| State | Description | vel_scale |
|---|---|---|
| INIT | Starting up, awaiting first sensor data | 0.0 |
| NORMAL | Both sensors valid, no obstacle close | 1.0 |
| WARNING | Obstacle within 0.50m | 0.2 |
| DEGRADED | Exactly one sensor path valid | 0.2 |
| SAFE_STATE | Critical fault — motors disabled | 0.0 |

### Priority rules (evaluated top-down)

```
1. SAFE_STATE latch:
   if previous == SAFE_STATE:
     if manual_reset_pending AND all_clear → INIT
     else → SAFE_STATE (latch)

2. SAFE_STATE conditions (any one triggers):
   - watchdog_failure_counter >= 3
   - ultrasonic_valid AND distance_m < 0.15m
   - !camera_valid AND !ultrasonic_valid

3. INIT: if !system_ready → INIT

4. DEGRADED: exactly one sensor path valid

5. WARNING: ultrasonic_valid AND distance_m < 0.50m

6. NORMAL: fallback (all clear)
```

### Thresholds

| Threshold | Value | Notes |
|---|---|---|
| WARNING distance | 0.50m | Bench-test assumption — not safety-validated |
| SAFE_STATE distance | 0.15m | Bench-test assumption — not safety-validated |

### SAFE_STATE reset conditions (`all_clear`)

Reset is held pending until ALL are true:
- `watchdog_failure_counter < 3`
- NOT (`ultrasonic_valid AND distance < 0.15m`)
- `camera_valid OR ultrasonic_valid`

Reset **does not expire** — it is held until `all_clear` becomes true.

### `watchdog_failure_counter` wiring

Published by `health_node` (`/watchdog_failure_counter`, 10 Hz) from Pi400 status UDP.
Subscribed by `decision_node` and fed into StateEvaluator input each tick.

### Implementation files

- `pi5_linux/ros2_ws/src/decision_node/include/decision_node/state_evaluator.hpp`
- `pi5_linux/ros2_ws/src/decision_node/src/state_evaluator.cpp`
- `pi5_linux/ros2_ws/src/decision_node/src/decision_node.cpp`
- Unit tests (27 gtest): `pi5_linux/ros2_ws/src/decision_node/test/test_state_evaluator.cpp`

---

## SM-4 — Sensor Path Monitoring

### camera_valid

- Set `true` when `/detections` message received (from `object_detection_node`)
- Times out to `false` after **2 seconds** without a message
- Source: `decision_node.cpp` — `last_detection_time_` tracking

### ultrasonic_valid

- Set `true` when `/obstacles` message has finite range within `[min_range, max_range]`
- Times out to `false` after **1 second** without a valid message
- Source: `decision_node.cpp` — `last_obstacle_time_` tracking

### Sensor path failure effects

| camera_valid | ultrasonic_valid | State |
|---|---|---|
| true | true | NORMAL or WARNING (distance-dependent) |
| true | false | DEGRADED |
| false | true | DEGRADED |
| false | false | SAFE_STATE (`both_sensors_invalid`) |

---

## SM-5 — MMU Process Isolation (Spatial FFI within Pi5)

Linux MMU enforces separate virtual address spaces per process. Each ROS2 node is a
separate process.

**Isolation boundary for AI algorithms**:

| Process | Algorithm | Address space |
|---|---|---|
| `hand_detection_node` | MediaPipe Hands | Isolated |
| `object_detection_node` | YOLOv8n | Isolated |

A memory fault in YOLOv8n cannot corrupt MediaPipe state and vice versa.

**Inter-process communication**: ROS2 topics `/hand_detections` (std_msgs/String JSON)
and `/hand_roi` (sensor_msgs/CompressedImage JPEG).

**Limitation**: Linux kernel is shared between all processes. This is process isolation,
not hardware-level partitioning. A kernel fault would affect all processes. True ASIL-B
partitioning requires a qualified hypervisor or separate processors.

---

## SM-6 — LED Indicators

| LED | GPIO (Pi5) | Driver | Condition |
|---|---|---|---|
| Green | GPIO 17 (Pin 11) | health_node | ON in INIT and NORMAL; OFF in WARNING/DEGRADED/SAFE_STATE |
| Yellow | GPIO 27 (Pin 13) | health_node | ON in WARNING and DEGRADED; OFF otherwise |
| Red | GPIO 22 (Pin 15) | actuator_node OR Pi400 safe_state_ctrl | ON in SAFE_STATE |

**Red LED wired-OR circuit**: Pi5 GPIO 22 and Pi400 GPIO 22 each drive through a
1N4148 diode (150Ω per leg) to the shared LED anode. Either side can independently
assert the SAFE_STATE indicator.

See `hardware/wiring.md` for circuit details.

---

## SM-7 — Program Flow Check

Implemented in `health_node` as a WDG gate (see SM-1 flow check gate section above).

**Monitored tasks and deadlines**:

| Safety-critical task | Node | Nominal period | Deadline |
|---|---|---|---|
| StateEvaluator evaluation | decision_node | 20ms | 60ms |
| Sensor obstacle publish | ultrasonic_node | 50ms | 150ms |
| E-stop GPIO poll | actuator_node | 10ms | — (hardware, not monitored via topic) |

`actuator_node` is not monitored via topic (it publishes nothing observable). Its
liveness is implicitly verified by the hardware e-stop path: if actuator_node dies,
GPIO 25 is no longer polled, but Pi400 can still assert SAFE_STATE independently.

---

## FTTI Analysis

### Proximity FTTI (SYS-SAFE-011)

Hand detected by camera (camera_valid=true) AND ultrasonic < 0.15m → SAFE_STATE.

| Step | Latency |
|---|---|
| Ultrasonic period (20 Hz) | 50ms |
| decision_node period (50 Hz) | 20ms |
| Overhead | 10ms |
| **Worst case** | **80ms < 100ms ✓** |

### Watchdog FTTI (SYS-SAFE-006)

health_node stops servicing Q&A → Pi400 failure_counter reaches 3 → GPIO 25 LOW.

| Step | Latency |
|---|---|
| 3 × 30ms window | 90ms |
| GPIO assertion + poll | 20ms |
| Motor disable | 30ms |
| **Worst case** | **140ms < 150ms ✓** |

---

## Known Limitations

| Limitation | Detail |
|---|---|
| UDP network stack dependency | Watchdog channel relies on Linux kernel; hardware I2C slave not feasible on BCM2711 (DD-002) |
| Linux kernel shared by all processes | MMU isolation is process-level, not hardware-level partitioning |
| No ECC RAM | Cosmic ray bit flips in safety data undetected |
| Single e-stop wire | GPIO 25 is a single point of failure — no redundant channel |
| Common power supply | No isolated power domains |
| Distance thresholds unvalidated | 0.50m and 0.15m are bench-test assumptions, not from a formal hazard analysis |
| Single-person project | Design independence not fully achieved |

---

## AI Safety Boundary

Per `AGENTS.md`:
- AI inference (MediaPipe, YOLOv8n) runs in the **development domain** (Pi5) only
- AI outputs reach `decision_node` only as a **liveness boolean** (`camera_valid`)
- Raw detection results **never enter** the StateEvaluator or any safety path
- The supervisor (Pi400) makes decisions based solely on watchdog timing — no AI output

---

*Last updated: 2026-05-09*
*For the FFI argument narrative: `docs/ffi_argument.md`*
*For hazard analysis and safety goals: `docs/safety_concept.md`*
*For requirements: `requirements/system_requirements.md`, `requirements/safety_requirements.md`*
