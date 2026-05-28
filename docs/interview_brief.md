# Project Interview Brief

## Safety-Supervised Edge AI Demo — Raspberry Pi 5 + Pi 400

**Role target**: Functional safety engineer, autonomous systems engineer, robotics
software engineer, ADAS safety architect.

> Educational demonstrator — ASIL-B-inspired patterns. Not ISO 26262 certified.

---

## One-Sentence Summary

A dual-processor embedded system implementing ASIL-B-inspired safety supervision of
AI-based perception on a Raspberry Pi platform, with verified FFI-inspired architectural
measures, full requirements traceability, and a complete safety analysis portfolio.

---

## What Was Built

An indoor mobile robot safety supervisor demonstrating the architectural patterns used
in automotive and robotics safety systems. The system uses two physically separate
processors — one for AI perception, one for deterministic safety monitoring — with a
verified hardware safety path that operates independently of all software.

### Hardware

- **Raspberry Pi 5**: runs 7 ROS2 nodes for AI perception and decision making
- **Raspberry Pi 400**: runs a deterministic safety supervisor (Ubuntu 22.04, Python)
- **IMX708 camera**: hand and object detection via MediaPipe Hands + YOLOv8n
- **Grove Ultrasonic Ranger**: precise proximity measurement (2–350cm) at 20 Hz
- **Traffic-light LEDs + buzzer**: system state indicators (green/yellow/red/buzzer)
- **Direct GPIO wire**: hardware e-stop — Pi400 GPIO 25 → Pi5 GPIO 25, active-low

### Software architecture (7 ROS2 nodes on Pi5)

```
hand_detection_node  ─── MediaPipe Hands ──── separate process (MMU-isolated)
object_detection_node ── YOLOv8n on ROI ─── separate process (MMU-isolated)
ultrasonic_node      ─── Grove Ranger, 20 Hz
decision_node        ─── StateEvaluator C++20, 50 Hz
actuator_node        ─── GPIO 25 poll 100 Hz, motor inhibit
health_node          ─── UDP Q&A client, flow check, LEDs/buzzer
                            │
                     [dedicated Ethernet]
                            │
Pi400 watchdog_server ── UDP Q&A server, GPIO 25 + GPIO 22 control
```

---

## Key Technical Decisions (with rationale)

| Decision | Choice | Why |
|---|---|---|
| Camera AI model | MediaPipe + YOLOv8n (DD-001 Option C) | MediaPipe: fast, accurate for hands. YOLOv8n gated on ROI: identifies held objects. MMU isolation separates the two algorithms. |
| Watchdog transport | UDP over Ethernet (DD-002 Option B) | I2C BSC slave not feasible on BCM2711 (Pi400). UDP over dedicated point-to-point link achieves equivalent communication independence. |
| Watchdog protocol | Q&A challenge-response, 30ms window | Stronger than simple GPIO heartbeat: frozen process cannot compute correct response. Maps to automotive external watchdog IC patterns. |
| StateEvaluator language | C++20 pure function | Deterministic, no side effects, stack-only — testable in isolation. 33 gtest cases cover all transitions and boundary conditions. |
| Camera-to-safety boundary | Liveness boolean only | AI output (bounding boxes) never reaches safety path. Only camera_valid (alive/dead) enters StateEvaluator — verified by fault injection FI-02. |

---

## Safety Engineering Depth

### Architecture measures

| Measure | Implementation | Verification |
|---|---|---|
| Spatial independence | Separate processors (Pi5 / Pi400) | FFI-SPATIAL: 30s Pi5 stress, failure_counter stayed 0 |
| Temporal independence | Pi400 monotonic clock, independent of Pi5 timing | FFI-TEMPORAL: 60s AI load, Q&A window maintained |
| Communication independence | UDP on dedicated Ethernet, separate from ROS2/DDS | FFI-COMM: 200 Hz ROS2 flood, UDP watchdog unaffected |
| MMU process isolation | hand_detection + object_detection as separate Linux processes | Architecture: YOLOv8n fault cannot corrupt MediaPipe state |
| Program flow check | health_node monitors decision_node + ultrasonic_node deadlines | Any pipeline crash withholds watchdog → Pi400 triggers SAFE_STATE |
| Hardware e-stop | GPIO 25 direct wire, active-low, fail-safe at boot | FI-05: health_node killed → SAFE_STATE via GPIO 25 in <300ms |

### Safety analysis portfolio

| Document | Technique | Key finding |
|---|---|---|
| HARA | ISO 26262-3 Clause 6 | 8 hazards; max ASIL B; 3 safety goals |
| FMEA | ISO 26262-4/9 | 63 failure modes; 4 SPOFs; DC per mechanism |
| FTA | ISO 26262-9 Clause 7 | GPIO 25 dominant MCS; dual-path architecture proven |
| ISO 26262 gap analysis | Parts 1–11 | 18 major gaps; 4-phase production path |
| AUTOSAR E2E comparison | AUTOSAR SWS E2ELibrary | UDP Q&A maps to E2EProfile01 + WdgM |

### Testing evidence

| Test | Result | Evidence |
|---|---|---|
| StateEvaluator unit tests | 33 / 33 PASS | test_state_evaluator.cpp (gtest) |
| Fault injection (5 scenarios) | 5 / 5 PASS | docs/fault_injection_report.md |
| FFI interference tests (3 scenarios) | 3 / 3 PASS | docs/ffi_verification_report.md |
| Hardware state transitions | All verified | Engineering logbook 2026-05-09 |
| Camera 20cm trigger | PASS | SYS-SAFE-012, logbook 2026-05-11 |

---

## Interview Talking Points

### "Walk me through the safety architecture."

*"The system separates AI perception from safety decisions at the hardware level.
Pi5 runs ROS2 nodes for camera AI and sensor fusion, but its output only reaches
the safety path as a liveness boolean — not as raw detections. Pi400 runs a
deterministic watchdog that independently monitors Pi5 health via a UDP
challenge-response protocol. If Pi5 fails in any way — crash, hang, timing violation,
or pipeline node failure — Pi400 asserts GPIO 25 LOW within 90ms, cutting motor power
independently of Pi5 software. The camera cannot accidentally trigger or prevent an
e-stop."*

### "How is this relevant to automotive?"

*"The architecture implements the same separation pattern used in functional safety
systems: development domain (AI) + safety domain (supervisor), with verified
Freedom from Interference. The Q&A watchdog maps directly to AUTOSAR E2EProfile01
and WdgM alive supervision. The HARA and FMEA follow ISO 26262-3/9 methodology.
The gap analysis shows I understand exactly what's missing for full ASIL-B
certification — tool qualification, independent assessment, quantitative FMEDA,
MISRA compliance — and documents an 18–24 month production path."*

### "What would you change for production?"

*"Three things immediately: First, replace the GPIO 25 single wire with a redundant
channel and periodic self-test — the FMEA and FTA both identified this as the dominant
single point of failure. Second, replace the Raspberry Pi with an ASIL-rated
microcontroller and run a qualified RTOS on the supervisor. Third, port the StateEvaluator
from C++20 to MISRA C with MC/DC coverage measurement. Everything else — the Q&A
protocol, the FFI architecture, the E2E protection, the flow check — can migrate
directly to a production platform."*

### "Why Python on the supervisor?"

*"Pragmatic choice for a demonstrator. The supervisor logic is in Python for
development speed, but the safety-relevant StateEvaluator is in pure C++20 with
no ROS2 dependencies and no dynamic memory allocation in the evaluation path.
In production, the supervisor would move to C on a qualified RTOS. The architectural
pattern — independent processor, Q&A watchdog, hardware e-stop — is what matters
for portfolio demonstration, and that transfers directly."*

---

## Repository

**`https://github.com/tipou82/safety-supervised-edge-ai-demo`**

| Metric | Value |
|---|---|
| Milestones completed | M0–M8 (all 9) |
| GitHub issues | 0 open |
| Requirements | 60+ with full traceability (0 TODO) |
| Unit tests | 33 gtest (all pass) |
| Fault injection | 5 scenarios (all pass) |
| FFI tests | 3 scenarios (all pass) |
| Safety analysis | HARA + FMEA + FTA + gap analysis + AUTOSAR E2E |
| Architecture diagrams | 11 Mermaid diagrams (GitHub-rendered) |
| Engineering logbook | Daily entries, M0–M8 |

---

*Educational demonstrator — ASIL-B-inspired patterns. Not ISO 26262 certified.*
*Not production-ready. All safety claims are explicitly scoped to demonstrator level.*
