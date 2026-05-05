# M1 Handoff – Hardware Bring-up

## Current Repository Status

The M0 repository baseline is complete. The repository contains a full documentation skeleton including architecture, safety concept, QNX supervisor design, FFI argument, system and safety requirements, interface specification, traceability matrix, hardware wiring and GPIO mapping, SysML model, milestone plan, AI-agent engineering rules, milestone issue descriptions, and an engineering logbook. No implementation code is present.

## Completed M0 Items

- [x] Repository folder structure created
- [x] README with project overview and limitations
- [x] `docs/architecture.md` — component descriptions and FFI measures
- [x] `docs/safety_concept.md` — state machine and safety mechanisms
- [x] `docs/qnx_supervisor.md` — watchdog design and timing analysis
- [x] `docs/ffi_argument.md` — FFI effectiveness analysis and production gaps
- [x] `docs/milestones.md` — milestone plan
- [x] `docs/sysml/architecture.sysml` — SysML v2 model
- [x] `requirements/system_requirements.md` — 30+ functional and safety requirements
- [x] `requirements/safety_requirements.md` — hazard analysis, FSRs, ASIL decomposition
- [x] `requirements/interfaces.yaml` — authoritative timing constraints and GPIO specs
- [x] `requirements/traceability.csv` — requirement to design to test mapping
- [x] `hardware/wiring.md` — BOM, inter-processor wiring, power distribution
- [x] `hardware/gpio_mapping.md` — GPIO pin assignments with code snippets
- [x] `AGENTS.md` — AI-agent engineering rules and boundaries
- [x] `docs/project_management/issues/M0–M6` — GitHub Issue descriptions for all milestones

## Important Safety Wording Rules

These rules apply to all contributions in this milestone and must not be weakened:

- **Never** claim ISO 26262 certification. This project is not certified.
- **Never** claim real ASIL-B implementation. Use **"ASIL-B-inspired"** instead.
- Use **"ASIL-B-inspired monitoring path"**, not "ASIL-B path".
- Use **"FFI-inspired architectural measures"**, not "certified FFI".
- Use **"demonstrator"** or **"educational demonstrator"**, not "safety-certified system".
- Runtime safety decisions shall be **deterministic and rule-based**.
- LLMs and AI agents shall not be part of the runtime safety decision path.
- The QNX supervisor is **planned or optional** until proven on hardware.
- A Linux PREEMPT_RT fallback for the supervisor is acceptable and shall be documented honestly.

## M1 Goal

Verify that each individual hardware component connected to the Raspberry Pi 5 operates correctly in isolation, before any ROS2 or software integration begins. Produce documented test evidence for each component.

## M1 Hardware Scope

| Component | Purpose |
|---|---|
| Raspberry Pi Camera Module 3 | Visual perception input |
| Grove Ultrasonic Ranger (×3 planned, ×1 for initial bring-up) | Distance measurement |
| Traffic-light LED module (green / yellow / red) | Visual status indicator |
| Active 3.3 V buzzer | Audible alert output |
| Breadboard, jumper wires, resistors | Prototyping and voltage division |

## M1 Out of Scope

- ROS2 workspace setup or node integration
- Object detection model (YOLOv8n / MobileNet)
- QNX supervisor or Raspberry Pi 400 bring-up
- Ethernet watchdog or heartbeat protocol
- Deterministic decision node implementation
- Fault injection campaign

## Relevant Files for M1

| File | Purpose |
|---|---|
| `hardware/wiring.md` | BOM and wiring plan |
| `hardware/gpio_mapping.md` | GPIO pin assignments |
| `docs/safety_concept.md` | State machine reference |
| `requirements/system_requirements.md` | Hardware and sensor requirements |
| `requirements/safety_requirements.md` | Safety-relevant hardware requirements |
| `engineering_logbook/` | Test result records |
| `docs/project_management/issues/M1_hardware_bringup.md` | Full M1 issue description and acceptance criteria |

## Suggested First M1 Tasks

- [ ] Confirm Raspberry Pi 5 OS version (`cat /etc/os-release`)
- [ ] Confirm camera cable seating and camera detection (`libcamera-hello` or equivalent)
- [ ] Review `hardware/gpio_mapping.md` before any wiring
- [ ] Test green, yellow, and red LEDs individually via GPIO toggle
- [ ] Test active buzzer via GPIO assert
- [ ] Test ultrasonic sensor distance measurement and record sample readings
- [ ] Document all results in `engineering_logbook/` with date and outcome
- [ ] Update `hardware/wiring.md` if actual wiring differs from the documented plan

## Test Evidence Expected

- Command output confirming camera detection (e.g. `libcamera-hello` device list)
- Sample distance readings from the ultrasonic sensor (expected range: 2–400 cm)
- Visual confirmation of LED toggling (photo of wiring if available)
- Audio confirmation of buzzer response
- Logbook entry per component: date, procedure, actual result, pass/fail
- Updated wiring notes if any deviation from `hardware/wiring.md`
- Known limitations or open items noted explicitly

## Suggested Git Branch

```
feature/m1-hardware-bringup
```

## Suggested First Commit Message

```
docs: add M1 hardware bring-up handoff
```
