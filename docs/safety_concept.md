# Safety Concept

## Disclaimer

This is an educational demonstrator showcasing ASIL-B-inspired monitoring patterns.
This system is **NOT** ISO 26262 certified and is **NOT** suitable for production use.

> **Safety mechanism details are in `docs/safety_mechanisms.md`** (single source of truth).
> This document covers the safety philosophy, hazard context, and system state definitions.

---

## Safety Philosophy

**Core Principle**: AI-based perception operates in the development domain. Runtime safety
decisions are made by deterministic, rule-based logic on an independent supervisor.

**Key Insight**: We do not claim the AI is safe. We demonstrate architectural measures to
detect and mitigate AI failures through independent monitoring.

**AI Safety Boundary**: AI inference (MediaPipe, YOLOv8n) outputs reach the state machine
only as a liveness boolean (`camera_valid`). Raw detections never enter the safety path.

---

## Hazard Analysis Summary

### HAZ-001 — Unintended Vehicle Motion
- **Severity**: S2 (Moderate — property damage, minor injury possible)
- **Controllability**: C2 (Normally controllable by operator)
- **Exposure**: E3 (Medium frequency in demonstration scenarios)
- **ASIL**: B-inspired

### HAZ-002 — Collision with Obstacle
- **Severity**: S1 (Light — minor property damage)
- **Controllability**: C1 (Simple to control in demo environment)
- **Exposure**: E3 (Medium frequency)
- **ASIL**: A (covered by ASIL-B supervision)

### Safety Goals

**SG-001**: Prevent unintended motion — SAFE_STATE on detected faults. Fault Tolerance
Time: 150ms.

**SG-002**: Detect supervision failure — Q&A watchdog on independent supervisor.

---

## System States

Managed by the StateEvaluator (Pi5) with safe-state enforcement by the Pi400 supervisor.
Full state machine rules in `docs/safety_mechanisms.md` SM-3.

| State | Description | velocity_scale | Green LED | Yellow LED | Red LED |
|---|---|---|---|---|---|
| BOOTING / INIT | Starting up, watchdog not yet healthy | 0.0 | ON (init) | OFF | OFF |
| NORMAL | Watchdog healthy, sensors valid, clear path | 1.0 | ON | OFF | OFF |
| WARNING | Obstacle in warning range (ultrasonic) | 0.5 | OFF | ON | OFF |
| DEGRADED | One sensor path invalid | 0.2 | OFF | ON | OFF |
| SAFE_STATE | Critical fault — halted | 0.0 | OFF | OFF | ON |

**SAFE_STATE** latches — requires manual `/reset` with all fault conditions cleared.
No auto-recovery.

### Startup Release Criterion

The system shall NOT enter NORMAL automatically at boot. Release to NORMAL requires all of:
1. Pi400 Q&A watchdog: `failure_counter < 3` (watchdog communication healthy).
2. All required ROS2 nodes on Pi5 alive (health_node flow check passes).
3. Sensor validity checks pass (ultrasonic valid within timeout).

If any criterion fails at startup, the system shall enter SAFE_STATE directly.
Manual `/reset` is required after all conditions are cleared.

### velocity_scale and Motor Actuator Behaviour

Motor speed is controlled by `velocity_scale` (0.0 = stop, 1.0 = full speed):

- **NORMAL**: `velocity_scale = 1.0` — motor runs at full speed if Motor Switch is ON.
- **WARNING** (obstacle in warning range): `velocity_scale = 0.5` — speed reduced.
- **SAFE_STATE**: `velocity_scale = 0.0` — motor stopped, red LED ON.
- **BOOTING / INIT**: `velocity_scale = 0.0` — motor off until release criterion met.

**Safe State has priority over any velocity command.**
If SAFE_STATE is requested due to near-range detection, watchdog fault, invalid startup
release or critical monitoring fault, the actuator command shall force `velocity_scale` to
`0.0` and the red LED shall be activated.

The Motor Switch (4×AA battery box) is independent of software state. If the Motor Switch is
OFF, the motor cannot rotate regardless of `velocity_scale`. If the Motor Switch is ON, the
motor rotates only if the software state allows it.

### State Transition Summary

| Trigger | From | To | velocity_scale | LED |
|---|---|---|---|---|
| Boot (default) | — | BOOTING/INIT | 0.0 | Green (init) |
| All startup criteria met | INIT | NORMAL | 1.0 | Green ON |
| Obstacle in warning range | NORMAL | WARNING | 0.5 | Yellow ON |
| Warning condition cleared | WARNING | NORMAL | 1.0 | Green ON |
| Obstacle in near range (<0.15 m ultrasonic) | ANY | SAFE_STATE | 0.0 | Red ON |
| Pi400 watchdog fault (failure_counter ≥ 3) | ANY | SAFE_STATE | 0.0 | Red ON |
| One sensor path invalid | NORMAL | DEGRADED | 0.2 | Yellow ON |
| Both sensors invalid | ANY | SAFE_STATE | 0.0 | Red ON |
| Manual `/reset` (all conditions clear) | SAFE_STATE | INIT | 0.0 | Green (init) |

### AI Safety Boundary (unchanged)

AI inference (MediaPipe, YOLOv8n) outputs reach the state machine **only** as a liveness
boolean (`camera_valid`). Raw AI detections do **not** enter the safety path.
The ultrasonic path, watchdog status, timeout status, and deterministic StateEvaluator rules
define the runtime safety reaction. AI perception provides diagnostic/perception context only.

---

## Fault Handling Summary

| Fault type | Example | Response | Recovery |
|---|---|---|---|
| Transient | Camera occlusion | WARNING, continue | Automatic on fault clear |
| Persistent | Camera AI node crash | DEGRADED or SAFE_STATE | Manual reset |
| Watchdog failure | health_node stops | SAFE_STATE via GPIO 25 | Manual reset after counter drops |
| Both sensors invalid | Both nodes killed | SAFE_STATE | Restart nodes, then reset |

---

## ASIL-B-Inspired Measures

- **Independence**: Separate safety monitor on independent processor (Pi400)
- **Determinism**: Safety decisions are rule-based — no AI in safety path
- **Timing**: Bounded latency for safety-critical transitions (150ms FTTI)
- **Testing**: Fault injection test suite (M6), FFI verification (M7)

### What is NOT Claimed

- ISO 26262 certification
- Quantified safety metrics (probabilistic failure rates)
- Production-ready software
- Tool qualification

---

## References

- `docs/safety_mechanisms.md` — all safety mechanism details
- `docs/ffi_argument.md` — FFI argument and effectiveness analysis
- `requirements/safety_requirements.md` — FSRs and ASIL decomposition
- ISO 26262:2018 Part 3 (Concept Phase), Part 6 Clause 7
