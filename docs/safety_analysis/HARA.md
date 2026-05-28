# Hazard Analysis and Risk Assessment (HARA)

**Document**: HARA-001
**Project**: Safety-Supervised Edge AI Demonstrator
**Standard reference**: ISO 26262-3:2018 Clause 6 (Hazard analysis and risk assessment)
**Date**: 2026-05-11
**Author**: Yunpeng Yang
**Status**: COMPLETE — educational demonstrator scope

> **Disclaimer**: This HARA is performed for an **educational demonstrator** using
> ASIL-B-inspired methodology. It is NOT a certified ASIL determination and does NOT
> constitute ISO 26262 compliance. It demonstrates the methodology and its application
> to the system architecture. Production deployment would require a fully qualified HARA
> process under an ISO 26262-compliant development process.

---

## 1. Item Definition

### 1.1 Item under analysis

**Item**: Safety-Supervised Edge AI Mobile Robot System

An indoor mobile robot platform using camera-based AI perception (hand/object detection)
and ultrasonic proximity sensing, supervised by a deterministic safety monitor on an
independent processor. The system controls robot motion velocity and enforces safe stop.

### 1.2 System boundary

| In scope | Out of scope |
|---|---|
| Camera AI perception (Pi5) | Motor hardware (not present in current demonstrator) |
| Ultrasonic proximity sensing | Motor driver electronics |
| Q&A watchdog supervisor (Pi400) | Battery management |
| Velocity scaling and safe state | Navigation/path planning |
| Hardware e-stop (GPIO 25) | Communication with external infrastructure |

### 1.3 Operating parameters (assumed for HARA)

| Parameter | Value | Basis |
|---|---|---|
| Maximum robot velocity | 0.5 m/s | Typical Pi-based educational robot |
| Robot mass | ~2 kg | Raspberry Pi + chassis + battery |
| Kinetic energy at max speed | 0.25 J | Below pain threshold for adult |
| Operating environment | Indoor, controlled laboratory/demo | Assumed |
| Typical operator proximity | 0.5–3 m | Demonstration context |

---

## 2. Situation Analysis

### 2.1 Operational situations

| ID | Situation | Description |
|---|---|---|
| OS-01 | Normal operation | Robot moving in open space, no obstacles |
| OS-02 | Human approach | Person walks toward or reaches toward robot |
| OS-03 | Obstacle in path | Static or dynamic object in robot path |
| OS-04 | Sensor degradation | One sensor path unavailable |
| OS-05 | Supervisor failure | Safety monitor (Pi400) unresponsive |
| OS-06 | AI perception failure | Camera AI node crashes or produces wrong output |
| OS-07 | Startup | System initialising, states not yet established |
| OS-08 | Recovery | Returning from safe state after fault |

### 2.2 Operating modes

| Mode | Description | Velocity |
|---|---|---|
| NORMAL | All sensors valid, path clear | 100% |
| WARNING | Obstacle within 50cm or hand within 20cm camera | 50% |
| DEGRADED | One sensor path lost | 20% |
| SAFE_STATE | Critical fault — motors disabled | 0% |
| INIT | Startup — awaiting first sensor data | 0% |

---

## 3. Hazard Identification

Hazards are identified per operational situation. A hazard is an unsafe condition that,
combined with a trigger event, can lead to an accident.

| HAZ-ID | Hazard | Operational situation | Trigger |
|---|---|---|---|
| HAZ-001 | Robot continues at full speed with human in proximity | OS-02 | Sensor failure to detect |
| HAZ-002 | Robot fails to stop when obstacle contact imminent | OS-03 | Distance sensor invalid |
| HAZ-003 | Robot operates at full speed with only one sensor valid | OS-04 | Degraded mode not enforced |
| HAZ-004 | Safety supervisor fails silently; no safe state triggered | OS-05 | Watchdog failure undetected |
| HAZ-005 | AI false negative — hand not detected when within threshold | OS-02 | Camera AI model error |
| HAZ-006 | Incorrect state after reset — robot moves in unsafe state | OS-08 | Reset logic error |
| HAZ-007 | Robot accelerates unexpectedly due to wrong velocity command | OS-01 | State machine incorrect transition |
| HAZ-008 | Robot moves during startup before sensors validated | OS-07 | Missing INIT guard |

---

## 4. Hazard Assessment

### 4.1 Rating scales (ISO 26262-3:2018 Table 1, 4, 6)

**Severity (S)**

| Level | Description | Example |
|---|---|---|
| S0 | No injuries | Cosmetic damage only |
| S1 | Light and moderate injuries | Bruise, minor cuts |
| S2 | Severe and life-threatening injuries (survival probable) | Fracture, concussion |
| S3 | Life-threatening injuries (survival uncertain), fatal | Head trauma, crush injury |

**Exposure (E)**

| Level | Description |
|---|---|
| E0 | Incredibly unlikely |
| E1 | Very low probability |
| E2 | Low probability |
| E3 | Medium probability |
| E4 | High probability (occurs in most operating cycles) |

**Controllability (C)**

| Level | Description |
|---|---|
| C0 | Controllable in general |
| C1 | Simply controllable (>99% of drivers/operators) |
| C2 | Normally controllable (>90%) |
| C3 | Difficult to control or uncontrollable (<90%) |

**ASIL determination** (ISO 26262-3 Annex B):

|  | C1 | C2 | C3 |
|---|---|---|---|
| **S1, E2** | QM | QM | QM |
| **S1, E3** | QM | QM | A |
| **S1, E4** | QM | A | B |
| **S2, E2** | QM | QM | A |
| **S2, E3** | QM | A | B |
| **S2, E4** | A | B | C |
| **S3, E2** | QM | A | B |
| **S3, E3** | A | B | C |
| **S3, E4** | B | C | D |

### 4.2 Hazard ratings

| HAZ-ID | Hazard (brief) | S | E | C | ASIL | Rationale |
|---|---|---|---|---|---|---|
| HAZ-001 | Full speed with human in proximity | S2 | E3 | C2 | **B** | Low-speed robot (0.5 m/s, 0.25J); moderate exposure in demo; operator can step back |
| HAZ-002 | Fail to stop before contact | S2 | E2 | C2 | **QM→A** | Low speed limits severity; low probability with dual sensors; operator present |
| HAZ-003 | Full speed in single-sensor mode | S1 | E3 | C2 | **QM** | Degraded mode limits speed to 20%; severity reduced |
| HAZ-004 | Silent supervisor failure | S2 | E2 | C3 | **A** | Operator may not notice supervisor failure; hard to control if undetected |
| HAZ-005 | AI false negative (hand not detected) | S1 | E3 | C2 | **QM** | Ultrasonic provides backup detection; AI failure → DEGRADED (lower speed) |
| HAZ-006 | Unsafe state after reset | S1 | E2 | C2 | **QM** | Reset requires all_clear condition; low probability |
| HAZ-007 | Unexpected acceleration | S2 | E1 | C2 | **QM** | Deterministic state machine; low probability; operator present |
| HAZ-008 | Motion during startup | S1 | E2 | C1 | **QM** | INIT state enforces 0% velocity; operator present at startup |

**Maximum ASIL: B** (HAZ-001, consistent with existing ASIL-B-inspired design)

---

## 5. Safety Goals

Derived from hazards with ASIL ≥ A.

| SG-ID | Safety Goal | ASIL | Source hazard | FTTI |
|---|---|---|---|---|
| SG-001 | The system shall prevent unintended robot motion at full speed when a human is within the safety zone | B | HAZ-001 | 200ms |
| SG-002 | The system shall detect loss of safety supervision capability and transition to safe state | A | HAZ-004 | 300ms (3 watchdog cycles) |
| SG-003 | The system shall limit robot velocity to ≤20% when operating with a single sensor path | B (inherited) | HAZ-003 | 100ms |

### 5.1 Safety goal decomposition

**SG-001** → Functional Safety Requirements:
- FSR-001: Q&A watchdog shall detect Pi5 health_node failure within 3 cycles (150ms)
- FSR-002: StateEvaluator shall trigger SAFE_STATE (0% velocity) on: distance <0.15m (ultrasonic) OR camera distance <0.20m OR both sensors invalid
- FSR-003: Hardware e-stop (GPIO 25) shall enforce 0% velocity independently of software

**SG-002** → Functional Safety Requirements:
- FSR-004: Pi400 shall assert GPIO 25 LOW within 150ms of watchdog failure detection
- FSR-005: Flow check gate shall detect pipeline node failure and withhold WDG response

**SG-003** → Functional Safety Requirements:
- FSR-006: StateEvaluator shall enforce 20% velocity scale in DEGRADED state
- FSR-007: Sensor timeout (100ms) shall trigger DEGRADED within one period after sensor loss

---

## 6. Architecture Fit Assessment

How the current architecture addresses each safety goal:

| SG-ID | Mechanism | Implementation | Evidence |
|---|---|---|---|
| SG-001 | StateEvaluator (software) + GPIO 25 (hardware) | decision_node C++20; Pi400 GPIO 25 | 33 gtest; FI-05 PASS; e-stop wire verified |
| SG-001 | Camera distance fusion | hand_detection_node pinhole model | SYS-SAFE-012; 20cm trigger verified 2026-05-11 |
| SG-002 | Q&A watchdog + flow check gate | health_node UDP; watchdog_server | FI-05 PASS; FFI-TEMPORAL PASS |
| SG-003 | StateEvaluator DEGRADED velocity | state_evaluator.cpp vel_scale=0.2 | 27+ gtest; FI-01 PASS |

---

## 7. SOTIF Considerations (ISO 21448)

Safety of the Intended Function — hazards caused by correct system function in
unexpected scenarios.

| Scenario | SOTIF concern | Mitigation |
|---|---|---|
| AI detects hand but hand is far away | Camera distance triggers SAFE_STATE unnecessarily (availability) | 20cm threshold + camera_valid guard prevent spurious triggers |
| Ultrasonic detects wall, not human | Robot slows for non-human obstacle | Acceptable — conservative behaviour |
| MediaPipe misses a partially visible hand | camera_hand_critical not triggered | Ultrasonic provides backup path (SYS-SAFE-011) |
| Fast-moving object causes transient miss | DEGRADED flicker | 100ms debounce filter resolves this |

---

## 8. Gap Analysis vs. Full ASIL-B Certification

| ISO 26262 Requirement | This Demonstrator | Gap |
|---|---|---|
| Qualified HARA process (Part 3) | HARA-inspired methodology | No qualified assessor; single engineer |
| ASIL decomposition and allocation | ASIL-B-inspired, not allocated | Formal ASIL allocation to SW components missing |
| WCET analysis (Part 6, 6.4.4) | Timing estimates only | No formal WCET tool analysis |
| MISRA C:2012 compliance | C++20, no MISRA check | Static analysis tool not qualified |
| Safety case (Part 2) | docs/safety_mechanisms.md | No formal GSN/CAE safety case structure |
| Independent safety assessment | Single-person project | No independent review |
| Tool qualification (Part 8) | Standard tools | GCC, colcon not qualified |
| Quantitative FMEDA | FMEA in progress | No failure rate data (FIT rates) |

**Conclusion**: The architecture demonstrates all relevant ASIL-B safety patterns.
Full certification would require process compliance, tool qualification, and
independent assessment — not achievable in an educational demonstrator.

---

## 9. References

- ISO 26262-3:2018 — Road vehicles — Functional safety — Part 3: Concept phase
- ISO 26262-3:2018 Annex B — ASIL determination
- ISO 21448:2022 — Safety of the intended function (SOTIF)
- `docs/safety_mechanisms.md` — implementation details
- `docs/safety_concept.md` — safety philosophy and hazard summary
- `requirements/safety_requirements.md` — derived FSRs

---

*Document status: Complete for educational demonstrator scope.*
*A production system would require a qualified HARA process per ISO 26262-3.*
