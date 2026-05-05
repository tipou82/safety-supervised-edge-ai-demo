# Safety-Supervised Edge AI Demo on Raspberry Pi with QNX/Linux Concepts

## Project Goal

This demonstrator showcases a dual-processor architecture for safety-supervised edge AI applications, implementing FFI-inspired architectural measures across heterogeneous compute platforms. The system demonstrates deterministic safety monitoring of AI-based perception functions using a rule-based supervisor.

## Scope

**What this project demonstrates:**
- Dual-processor architecture (Pi 5 Linux + Pi 400 QNX concepts)
- ASIL-B-inspired monitoring path with deterministic safety decisions
- FFI-inspired architectural measures (independence, interference management)
- ROS2-based AI perception with rule-based safety supervision
- Watchdog communication and safe state transitions
- Requirements traceability and engineering discipline

**What this project is NOT:**
- This is NOT an ISO 26262 certified system
- This is NOT production-ready automotive software
- This is a learning demonstrator and portfolio piece

## Safety Disclaimer

⚠️ **IMPORTANT**: Runtime safety decisions are deterministic and rule-based. LLMs and AI agents are NOT part of the safety decision path. AI perception outputs are monitored by independent, deterministic logic on the QNX-inspired supervisor.

## Architecture Overview

```
┌─────────────────────────────────────┐
│   Raspberry Pi 5 (Linux/ROS2)      │
│  - Camera AI Node                   │
│  - Ultrasonic Node                  │
│  - Decision Node                    │
│  - Actuator Node                    │
│  - Health Monitor                   │
└──────────────┬──────────────────────┘
               │ Watchdog Messages
               │ (GPIO + Shared State)
┌──────────────┴──────────────────────┐
│   Raspberry Pi 400 (QNX-inspired)   │
│  - Watchdog Server                  │
│  - Safe State Controller            │
│  - Deterministic Safety Logic       │
└─────────────────────────────────────┘
```

## Planned Milestones

- [x] M0: Repository baseline — documentation, requirements, architecture
- [ ] M1: Platform access and hardware bring-up — SSH, direct Ethernet, camera, sensors, LEDs
- [ ] M2: ROS2 sensor pipeline — workspace, placeholder nodes, topic definitions
- [ ] M3: Deterministic decision logic — C++20 state evaluator, unit tests
- [ ] M4: Fault injection — five scenarios, safe-state latency measured
- [ ] M5: External supervisor — QNX watchdog prototype or Linux fallback (optional)
- [ ] M6: Portfolio-ready demo — README finalized, demo script, test report

## Quick Start

```bash
# Repository structure setup
git clone <repository-url>
cd safety-supervised-edge-ai-demo

# Review architecture and requirements
cat docs/architecture.md
cat docs/safety_concept.md
cat requirements/system_requirements.md

# ROS2 workspace setup (TBD)
# cd pi5_linux/ros2_ws
# colcon build

# QNX supervisor setup (TBD)
# cd pi400_qnx/qnx_wdg_server
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Safety Concept](docs/safety_concept.md)
- [QNX Supervisor Design](docs/qnx_supervisor.md)
- [FFI-Inspired Measures](docs/ffi_argument.md)
- [Hardware Wiring](hardware/wiring.md)
- [GPIO Mapping](hardware/gpio_mapping.md)

## Requirements

- [System Requirements](requirements/system_requirements.md)
- [Safety Requirements](requirements/safety_requirements.md)
- [Interface Specifications](requirements/interfaces.yaml)
- [Traceability Matrix](requirements/traceability.csv)

## Engineering Logbook

Development decisions and progress are documented in `engineering_logbook/` with daily entries.

## License

Educational demonstrator - See LICENSE file for details.

## Contact

This is a portfolio project demonstrating safety-critical systems engineering concepts.
