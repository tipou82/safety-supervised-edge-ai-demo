# M0 Session Summary – Repository Baseline

## Project

**Safety-Supervised Edge AI Demo on Raspberry Pi with QNX/Linux Concepts** — an educational portfolio demonstrator of a dual-processor safety-supervised edge AI system implementing ASIL-B-inspired architectural patterns on Raspberry Pi hardware.

## Session Purpose

This session established the initial repository baseline, documentation structure, and AI-assisted engineering rules before any hardware implementation or ROS2 integration begins. The goal was to create a consistent, reviewable starting point that any future session or contributor can continue from without losing context.

## Completed M0 Work

- [x] Repository folder skeleton
- [x] `README.md` — project overview, architecture summary, limitations, and portfolio context
- [x] `docs/architecture.md` — component descriptions and FFI-inspired measures
- [x] `docs/safety_concept.md` — state machine, system states, and safety mechanisms
- [x] `docs/qnx_supervisor.md` — watchdog design and timing analysis
- [x] `docs/ffi_argument.md` — FFI-inspired argument, effectiveness ratings, and production gaps
- [x] `docs/sysml/architecture.sysml` — SysML v2 textual architecture placeholder
- [x] `docs/milestones.md` — milestone plan
- [x] `requirements/system_requirements.md` — 30+ functional and safety-inspired requirements
- [x] `requirements/safety_requirements.md` — hazard analysis, FSRs, ASIL decomposition
- [x] `requirements/interfaces.yaml` — authoritative timing constraints and GPIO specifications
- [x] `requirements/traceability.csv` — requirement to design to test mapping (60+ entries)
- [x] `hardware/wiring.md` — BOM, inter-processor wiring, power distribution
- [x] `hardware/gpio_mapping.md` — GPIO pin assignments with code snippets
- [x] `engineering_logbook/` — logbook structure and initial entry
- [x] `AGENTS.md` — AI-agent engineering rules and boundaries
- [x] `docs/project_management/issues/M0–M6` — GitHub Issue descriptions for all milestones
- [x] `docs/project_management/M1_handoff.md` — M1 handoff document

## Repository Status

The repository is prepared for M1 Hardware Bring-up. No ROS2 runtime code, hardware scripts, or implementation code has been written. The repository contains documentation and requirements only.

## Key Engineering Decisions

- **MVP-first strategy** — demonstrate a working Pi 5 Linux system before adding QNX complexity.
- **Pi 5 / Linux demo before QNX dependency** — the Raspberry Pi 5 (Ubuntu 22.04 + ROS2 Humble) is the critical path; the Pi 400 supervisor is additive.
- **QNX supervisor is important but not the critical path** — it is planned and optional until proven on hardware; a Linux PREEMPT_RT fallback is acceptable.
- **Python** for fast camera and AI perception prototyping.
- **C++20** for deterministic decision logic, heartbeat protocol, and supervisor logic.
- **Markdown / doc-as-code** for all documentation — version-controlled alongside code.
- **GitHub Issues or prepared issue descriptions** for milestone and task tracking.
- **AI tools used only as development support** — not as runtime safety logic or decision-makers.

## Safety and AI Boundaries

- This project is **not ISO 26262 certified** and must never be described as such.
- Use **"ASIL-B-inspired"**, not "ASIL-B" or "ASIL-B certified".
- Use **"FFI-inspired architectural measures"**, not "certified FFI".
- Use **"demonstrator"** or **"educational demonstrator"**, not "safety-certified system".
- Runtime safety decisions shall be **deterministic and rule-based only**.
- LLMs and AI agents shall **not** be part of the runtime safety decision path.
- The QNX supervisor shall be described as **planned, attempted, prototyped, or optional** until confirmed on hardware.
- All rules are defined in `AGENTS.md` and shall be respected in every session.

## Milestone Plan

| Milestone | Title | Status |
|---|---|---|
| M0 | Repository Baseline | **Complete** |
| M1 | Hardware Bring-up | **Complete** |
| M2 | ROS2 Sensor Pipeline | **Complete** |
| M3 | Deterministic Decision Logic | **Complete** |
| M4 | Camera AI Sensor Path | **Complete** |
| M5 | FFI / External Supervisor (Pi400 Q&A Watchdog) | **Complete** |
| M6 | Fault Injection Tests | **Complete** |
| M7 | Freedom From Interference (FFI) Verification | Planned |
| M8 | Portfolio-Ready Demo | Planned |

## Next Milestone: M1 Hardware Bring-up

**Goal:** Verify that the camera, ultrasonic sensors, LEDs, and buzzer each operate correctly in isolation on the Raspberry Pi 5, before any ROS2 integration begins.

**M1 Out of Scope:**

- ROS2 workspace setup or node integration
- Object detection model (YOLOv8n / MobileNet)
- QNX supervisor or Raspberry Pi 400 bring-up
- Ethernet watchdog or heartbeat protocol
- Deterministic decision node implementation
- Fault injection campaign

See `docs/project_management/M1_handoff.md` for the full task list and acceptance criteria.

## Relevant Files for Continuation

| File | Purpose |
|---|---|
| `README.md` | Project overview and limitations |
| `AGENTS.md` | AI-agent rules and safety boundaries |
| `docs/architecture.md` | System architecture and FFI measures |
| `docs/safety_concept.md` | State machine and safety mechanisms |
| `docs/ffi_argument.md` | FFI effectiveness analysis |
| `docs/qnx_supervisor.md` | Watchdog and supervisor design |
| `docs/project_management/issues/` | GitHub Issue descriptions for M0–M6 |
| `docs/project_management/M1_handoff.md` | M1 task list, scope, and acceptance criteria |
| `requirements/system_requirements.md` | Functional and safety-inspired requirements |
| `requirements/safety_requirements.md` | Hazard analysis and FSRs |
| `requirements/interfaces.yaml` | Authoritative timing and GPIO specifications |
| `requirements/traceability.csv` | Requirement to design to test mapping |
| `hardware/wiring.md` | BOM and wiring plan |
| `hardware/gpio_mapping.md` | GPIO pin assignments |
| `engineering_logbook/` | Test results and session records |

## Recommended Next Chat Opening

Copy and paste the following to continue in a new ChatGPT or Claude session:

> "We are continuing the Safety-Supervised Edge AI Demo project. M0 repository baseline is complete. Please help me start M1 Hardware Bring-up based on `docs/project_management/M0_session_summary.md` and `docs/project_management/M1_handoff.md`. First, help me confirm Raspberry Pi 5 OS, connectivity and GPIO mapping before any ROS2 integration."

## Suggested Git Commit

```
docs: add M0 session summary
```
