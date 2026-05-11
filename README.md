# Safety-Supervised Edge AI Demo — Raspberry Pi 5 + Pi 400

A dual-processor **ASIL-B-inspired** edge AI safety demonstrator implementing Freedom from
Interference (FFI) architectural measures, deterministic safety supervision, and sensor
fusion across heterogeneous compute platforms.

> **Educational demonstrator only — NOT ISO 26262 certified — NOT production-ready.**
> ASIL-B-inspired patterns. No LLM or cloud AI in the runtime safety path.

---

## What This Demonstrates

| Capability | Implementation |
|---|---|
| Dual-processor FFI architecture | Pi5 (Linux/ROS2) + Pi400 (QNX-inspired supervisor) |
| AI perception with safety supervision | MediaPipe Hands + YOLOv8n, monitored by deterministic rule-based logic |
| Q&A external watchdog | UDP challenge/response, 30ms window, CRC-16 + sequence counter (E2E) |
| Hardware e-stop | GPIO 25 direct wire Pi400→Pi5, active-low, fail-safe at boot |
| Deterministic state machine | C++20 StateEvaluator, 5 states, 27 gtest unit tests |
| Sensor fusion | Ultrasonic + camera distance estimation (pinhole model) |
| MMU spatial isolation | MediaPipe and YOLOv8n in separate Linux processes |
| Program flow check | health_node monitors pipeline liveness, gates watchdog servicing |
| Fault injection verified | 5 scenarios tested (M6) |
| FFI verification | 3 interference tests under stress (M7) |

---

## Hardware

| Component | Role |
|---|---|
| Raspberry Pi 5 (8 GB) | Linux/ROS2 domain — AI perception, state machine |
| Raspberry Pi 400 | QNX-inspired supervisor — watchdog server, hardware e-stop |
| Raspberry Pi Camera Module 3 (IMX708) | Hand and object detection |
| Grove Ultrasonic Ranger (GPIO 23) | Precise proximity measurement (2–350 cm) |
| Traffic-light LED module (GPIO 17/27/22) | System state indicators |
| Active buzzer (GPIO 18) | Audible alerts |

**Inter-processor wiring:**
- UDP Q&A watchdog over dedicated Ethernet `192.168.50.10 ↔ 192.168.50.20`
- E-stop: Pi400 GPIO 25 → Pi5 GPIO 25 (active-low direct wire)
- Red LED: wired-OR via 1N4148 diodes (both sides can assert independently)

---

## Architecture

```mermaid
graph TB
    subgraph Pi5["Raspberry Pi 5 — Linux / ROS2"]
        HN["health_node\nUDP Q&A client + flow check"]
        HDN["hand_detection_node\nMediaPipe Hands"]
        ODN["object_detection_node\nYOLOv8n"]
        UN["ultrasonic_node\nGrove Ranger 20Hz"]
        DN["decision_node\nStateEvaluator C++20 50Hz"]
        AN["actuator_node\nGPIO 25 poll 100Hz"]
    end

    subgraph Pi400["Raspberry Pi 400 — QNX-Inspired Supervisor"]
        WDG["qnx_wdg_server\nUDP Q&A 30ms window"]
    end

    HN  -->|"UDP Q&A watchdog\n192.168.50.x"| WDG
    WDG -->|"GPIO 25 e-stop\nactive-low"| AN
    HDN -->|"/hand_detections\n/hand_roi"| ODN
    ODN -->|"/detections"| DN
    UN  -->|"/obstacles 20Hz"| DN
    DN  -->|"/system_state 50Hz"| HN
    HN  -->|"/watchdog_failure_counter"| DN
```

### State Machine

```
INIT → NORMAL → WARNING (obstacle <0.50m)
                       ↓
             DEGRADED (one sensor lost)
                       ↓
             SAFE_STATE ← watchdog failure OR
                          ultrasonic <0.15m OR
                          camera hand <0.20m OR
                          both sensors invalid
                       ↓
                  manual /reset
```

| State | vel_scale | Green LED | Yellow LED | Red LED |
|---|---|---|---|---|
| INIT | 0% | ON | OFF | OFF |
| NORMAL | 100% | ON | OFF | OFF |
| WARNING | 50% | ON | OFF | OFF |
| DEGRADED | 20% | ON | ON | OFF |
| SAFE_STATE | 0% | OFF | OFF | ON |

---

## Getting Started

### Prerequisites (Pi5)

```bash
# ROS2 Humble (built from source on RPi OS Bookworm)
source ~/ros2_humble/install/setup.bash

# Python dependencies
sudo apt install python3-picamera2 python3-smbus2
pip3 install mediapipe ultralytics opencv-python-headless simplejpeg
```

### Build

```bash
cd ~/safety-supervised-edge-ai-demo
git pull

cd pi5_linux/ros2_ws
source ~/ros2_humble/install/setup.bash
colcon build --merge-install
source install/setup.bash
```

### Run

**Terminal 1 — Pi400 supervisor:**
```bash
python3 ~/safety-supervised-edge-ai-demo/pi400_supervisor/scripts/qnx_wdg_server.py
```

**Terminal 2 — Pi5 system:**
```bash
source ~/ros2_humble/install/setup.bash
source ~/safety-supervised-edge-ai-demo/pi5_linux/ros2_ws/install/setup.bash
ros2 launch safety_demo demo.launch.py
```

**Terminal 3 — Reset and monitor:**
```bash
ros2 topic pub --once /reset std_msgs/msg/Bool "data: true"
ros2 topic echo /system_state
ros2 topic echo /diagnostics
```

**MJPEG live view** (annotated camera feed): `http://<pi5-ip>:8080`

---

## Demo Sequence

1. **Launch** → system boots into SAFE_STATE (sensors not yet valid)
2. **Reset** → INIT → NORMAL (both sensors valid, hand not detected close)
3. **Approach hand to 50cm** → WARNING (ultrasonic)
4. **Approach hand to ~20cm from camera** → SAFE_STATE (`camera_hand_critical`)
5. **Remove hand, reset** → NORMAL
6. **Stop `health_node`** → watchdog failures → SAFE_STATE via Pi400 GPIO 25 (hardware path)

---

## Key Safety Mechanisms

See **[`docs/safety_mechanisms.md`](docs/safety_mechanisms.md)** for full details.

| Mechanism | Description |
|---|---|
| SM-1 Q&A Watchdog | UDP challenge/response, 30ms window, flow check gate, E2E CRC-16 |
| SM-2 Hardware E-Stop | GPIO 25 direct wire, active-low, independent of software stack |
| SM-3 StateEvaluator | C++20 pure function, deterministic priority rules, 27 gtest tests |
| SM-4 Sensor Monitoring | camera_valid 2s timeout, ultrasonic_valid 1s timeout |
| SM-5 MMU Isolation | MediaPipe and YOLOv8n in separate Linux processes |
| SM-6 LED Indicators | Green/Yellow/Red, wired-OR for red (Pi5 + Pi400 independent) |
| SM-7 Flow Check | health_node monitors decision_node and ultrasonic_node deadlines |

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/safety_mechanisms.md`](docs/safety_mechanisms.md) | All safety mechanisms — authoritative reference |
| [`docs/safety_concept.md`](docs/safety_concept.md) | Safety philosophy, hazard analysis, system states |
| [`docs/architecture.md`](docs/architecture.md) | Component descriptions, inter-domain connections |
| [`docs/ffi_argument.md`](docs/ffi_argument.md) | FFI argument narrative and effectiveness ratings |
| [`docs/ffi_verification_report.md`](docs/ffi_verification_report.md) | FFI test results (M7) |
| [`docs/fault_injection_report.md`](docs/fault_injection_report.md) | Fault injection results (M6) |
| [`docs/sysml/architecture_diagrams.md`](docs/sysml/architecture_diagrams.md) | All architecture diagrams (Mermaid) |
| [`docs/design_decisions/`](docs/design_decisions/) | DD-001 camera model, DD-002 watchdog transport |
| [`requirements/system_requirements.md`](requirements/system_requirements.md) | 30+ requirements |
| [`requirements/traceability.csv`](requirements/traceability.csv) | Requirements → design → test |
| [`engineering_logbook/`](engineering_logbook/) | Daily engineering decisions and test evidence |

---

## Milestones Completed

| # | Milestone | Key deliverable |
|---|---|---|
| M0 | Repository Baseline | Architecture, requirements, traceability |
| M1 | Hardware Bring-up | Pi5/Pi400 sensors, LEDs, Ethernet — all PASS |
| M2 | ROS2 Sensor Pipeline | 6 packages, 5 nodes, e-stop verified |
| M3 | Deterministic Decision Logic | StateEvaluator C++20, 27 gtest |
| M4 | Camera AI Sensor Path | MediaPipe + YOLOv8n, MJPEG stream |
| M5 | FFI / External Supervisor | Pi400 Q&A watchdog, GPIO 25 hardware path |
| M6 | Fault Injection Tests | 5 scenarios PASS |
| M7 | FFI Verification | 3 interference tests PASS; safety mechanisms centralised |

---

## Licence

Educational demonstrator — see [LICENSE](LICENSE) file.

## Contact

Portfolio project — Yunpeng Yang
