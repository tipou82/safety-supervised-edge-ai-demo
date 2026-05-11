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

# QNX supervisor (Pi400)
cd pi400_qnx && qcc -o qnx_supervisor *.c

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
Raspberry Pi 5 (Ubuntu 22.04 + ROS2 Humble) — perception & planning
  ├── camera_ai_node     YOLOv8n/MobileNet inference @ 10 Hz
  ├── ultrasonic_node    HC-SR04 x3 @ 10 Hz (2–400 cm)
  ├── decision_node      obstacle avoidance, sensor fusion
  ├── actuator_node      motor PWM via L298N, monitors e-stop GPIO @ 100 Hz
  └── health_node        heartbeat output on GPIO 17 @ 10 Hz
          │
          │  GPIO (heartbeat + emergency stop)
          │  Shared memory /dev/shm/safety_state (CRC32-validated, 4 KB)
          │
Raspberry Pi 400 (QNX 7.1 or PREEMPT_RT Linux fallback) — safety supervision
  ├── qnx_wdg_server     watchdog cycle 10 ms, FIFO priority 250
  └── safe_state_ctrl    e-stop assertion, FIFO priority 255 (highest)
```

### Safety-Critical Communication

- **Heartbeat:** GPIO 17 (Pi5 out) → GPIO (Pi400 in), 10 Hz ±20%, 500 ms timeout
- **Emergency stop:** GPIO 27 (Pi5 in, active-low) ← GPIO (Pi400 out), asserted at boot (fail-safe)
- **Shared memory:** Magic `0xCAFEBABE` + CRC32 (polynomial `0xEDB88320`); Linux writes, QNX reads-only

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

**Safety path rule:** The QNX supervisor uses **only rule-based deterministic logic** — AI model outputs must never reach the safety path.

**GPIO assignments** (safety-critical pins are marked):
- GPIO 17: heartbeat out (**safety-critical**)
- GPIO 27: e-stop in (**safety-critical**, active-low)
- GPIO 22/10/9/11: motor direction (L298N IN1–4)
- GPIO 18/12: motor speed PWM (1 kHz)
- GPIO 23/5/13: ultrasonic TRIG; GPIO 24/6/19: ECHO (voltage-divided 5V→3.3V)

## Documentation Map

| File | Contents |
|---|---|
| `docs/safety_analysis/HARA.md` | Hazard Analysis and Risk Assessment — S/E/C ratings, ASIL determination, safety goals, gap analysis |
| `docs/safety_analysis/FMEA.md` | Failure Mode and Effects Analysis — 63 failure modes across 6 safety mechanisms, SPOF register, DC summary |
| `docs/safety_mechanisms.md` | **All safety mechanisms** — Q&A watchdog, e-stop, StateEvaluator, sensor monitoring, MMU isolation, LEDs, FTTI (single source of truth) |
| `docs/architecture.md` | Component descriptions, inter-domain connections |
| `docs/safety_concept.md` | Safety philosophy, hazard analysis, system states (brief) |
| `docs/qnx_supervisor.md` | QNX RTOS rationale, process architecture, Linux fallback |
| `docs/ffi_argument.md` | FFI argument narrative, effectiveness ratings, gap analysis |
| `requirements/system_requirements.md` | 30+ functional/safety/performance requirements |
| `requirements/safety_requirements.md` | Hazard analysis, FSRs, ASIL decomposition |
| `requirements/interfaces.yaml` | ROS2 topics, GPIO specs, timing constraints (authoritative) |
| `requirements/traceability.csv` | 60+ requirements → design → implementation → test |
| `hardware/wiring.md` | BOM, inter-processor wiring, power distribution |
| `hardware/gpio_mapping.md` | GPIO pin assignments with code snippets |
| `docs/sysml/architecture_diagrams.md` | All architecture diagrams — BDD, IBD, package, requirements, state machine, sequence, activity (Mermaid, single source of truth) |
