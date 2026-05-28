# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Educational/portfolio demonstrator of a **dual-processor safety-supervised edge AI system** on Raspberry Pi hardware, implementing ASIL-B-*inspired* (not certified) architectural patterns. The system shows systems engineering discipline — separation of AI perception from deterministic safety monitoring.

**This is NOT ISO 26262 certified and NOT production-ready.** Always use phrasing like "ASIL-B-inspired" and "demonstrator", never imply certification.

## Build & Test Commands

The repository is in early implementation phase. Once code is written, expected commands are:

```bash
# ROS2 workspace (Pi5 Linux domain)
cd pi5_linux/ros2_ws && colcon build
ros2 launch safety_demo demo.launch.py

# Pi400 supervisor (run on Pi400)
python3 pi400_supervisor/scripts/watchdog_server.py

# Tests
pytest tests/unit/
pytest tests/integration/
pytest tests/fault_injection/
python tests/integration/test_e2e_latency.py
```

No CI configuration or Makefile exists yet.

## Architecture

### Dual-Processor Design

Two physically separate processors enforce **Freedom From Interference (FFI)**:

```
Raspberry Pi 5 (RPi OS Bookworm + ROS2 Humble) — perception & planning
  ├── hand_detection_node   MediaPipe Hands, owns camera, 10 Hz
  ├── object_detection_node YOLOv8n on hand ROI, 10 Hz
  ├── ultrasonic_node       Grove Ultrasonic Ranger GPIO 23, 20 Hz
  ├── decision_node         StateEvaluator C++20, 50 Hz
  ├── actuator_node         DRV8833 GPIO 12/16, polls e-stop GPIO 25 @ 100 Hz
  └── health_node           UDP Q&A client, LED control, flow check
          │
          │  UDP Q&A watchdog (Ethernet 192.168.50.x, port 9001)
          │  GPIO 25 e-stop (direct wire, active-low)
          │
Raspberry Pi 400 (RPi OS Bookworm) — deterministic Linux supervisor
  └── watchdog_server.py    UDP server, 30ms window, CRC-16, failure counter
                            GPIO 25 e-stop output, GPIO 22 red LED output
```

### Safety-Critical Communication

- **UDP Q&A Watchdog:** Pi400 → Pi5 seed, Pi5 → Pi400 response within 15–30 ms window
- **Emergency stop:** GPIO 25 (Pi400 out, active-low) → GPIO 25 (Pi5 in), asserted at boot (fail-safe)
- **Status feedback:** Pi400 → Pi5 UDP status packet after each cycle (failure_counter, state)

### System States

`INIT → NORMAL ↔ WARNING ↔ DEGRADED → SAFE_STATE`

- **SAFE_STATE** requires manual reset; no auto-recovery
- **DEGRADED**: AI failed, ultrasonic-only, 20% nominal velocity
- **WARNING**: sensor degraded, 50% nominal velocity

### Key Timing Constraints (from `requirements/interfaces.yaml`)

| Constraint | Value |
|---|---|
| Heartbeat generation | 100 ms ±20 ms |
| Watchdog cycle | 10 ms ±1 ms |
| Safe state latency | <150 ms total |
| Perception-to-actuation (NORMAL) | <200 ms |

## Key Conventions

**Safety wording:** Always "ASIL-B-inspired", "demonstrator", "educational". Never "certified" or "production".

**FFI measures** are categorized by independence type: spatial (separate processors), temporal (local supervisor clock), communication (CRC32 + GPIO), design (no AI in safety path). When discussing their effectiveness, use honest ratings (Strong/Moderate/Weak) as established in `docs/ffi_argument.md`.

**Requirements tagging:** All requirements use Priority (Critical/High/Medium), ASIL level, and traceability IDs. See `requirements/traceability.csv` for the full mapping.

**Safety path rule:** The Pi400 supervisor uses **only rule-based deterministic logic** — AI model outputs must never reach the safety path.

**GPIO assignments** (safety-critical pins are marked):
- GPIO 25 Pi5 in: e-stop input from Pi400 (**safety-critical**, active-low)
- GPIO 25 Pi400 out: e-stop output to Pi5 (**safety-critical**, active-low)
- GPIO 17 Pi5: green LED (NORMAL indicator)
- GPIO 27 Pi5: yellow LED (WARNING/DEGRADED indicator)
- GPIO 22 Pi5/Pi400: red LED wired-OR via 1N4148 (SAFE_STATE indicator)
- GPIO 18 Pi5: buzzer (WARNING/DEGRADED)
- GPIO 12 Pi5: DRV8833 IN1 (motor PWM)
- GPIO 16 Pi5: DRV8833 IN2 (motor direction)
- GPIO 23 Pi5: Grove Ultrasonic Ranger SIG

## Documentation Map

| File | Contents |
|---|---|
| `docs/safety_analysis/HARA.md` | Hazard Analysis and Risk Assessment — S/E/C ratings, ASIL determination, safety goals, gap analysis |
| `docs/safety_analysis/FMEA.md` | Failure Mode and Effects Analysis — 63 failure modes across 6 safety mechanisms, SPOF register, DC summary |
| `docs/safety_analysis/ISO26262_gap_analysis.md` | ISO 26262 gap analysis — part-by-part assessment, 18 major gaps, 4-phase production path |
| `docs/safety_analysis/AUTOSAR_E2E_comparison.md` | AUTOSAR E2E profile mapping — UDP Q&A vs E2EProfile01/WdgM, CRC analysis, upgrade path |
| `docs/safety_analysis/FTA.md` | Fault Tree Analysis — FTA-1 (unsafe speed), FTA-2 (silent supervisor failure), MCS, CCF |
| `docs/interview_brief.md` | 3-page portfolio brief — architecture, safety depth, interview talking points |
| `docs/safety_mechanisms.md` | **All safety mechanisms** — Q&A watchdog, e-stop, StateEvaluator, sensor monitoring, MMU isolation, LEDs, FTTI (single source of truth) |
| `docs/architecture.md` | Component descriptions, inter-domain connections |
| `docs/safety_concept.md` | Safety philosophy, hazard analysis, system states (brief) |
| `docs/supervisor_design.md` | Pi400 supervisor design — watchdog protocol, GPIO logic, timing |
| `docs/ffi_argument.md` | FFI argument narrative, effectiveness ratings, gap analysis |
| `requirements/system_requirements.md` | 30+ functional/safety/performance requirements |
| `requirements/safety_requirements.md` | Hazard analysis, FSRs, ASIL decomposition |
| `requirements/interfaces.yaml` | ROS2 topics, GPIO specs, timing constraints (authoritative) |
| `requirements/traceability.csv` | 60+ requirements → design → implementation → test |
| `hardware/wiring.md` | BOM, inter-processor wiring, power distribution |
| `hardware/gpio_mapping.md` | GPIO pin assignments with code snippets |
| `docs/sysml/architecture_diagrams.md` | All architecture diagrams — BDD, IBD, package, requirements, state machine, sequence, activity (Mermaid, single source of truth) |
