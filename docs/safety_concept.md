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

Managed by the QNX-inspired supervisor (Pi400). Full state machine rules in
`docs/safety_mechanisms.md` SM-3.

| State | Description | vel_scale | LEDs |
|---|---|---|---|
| INIT | Starting up | 0% | Green ON |
| NORMAL | Both sensors valid, clear | 100% | Green ON |
| WARNING | Obstacle < 0.50m | 50% | Green ON |
| DEGRADED | One sensor path invalid | 20% | Green ON, Yellow ON |
| SAFE_STATE | Critical fault — halted | 0% | Green OFF, Red ON |

**SAFE_STATE** latches — requires manual `/reset` with all fault conditions cleared.
No auto-recovery.

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
