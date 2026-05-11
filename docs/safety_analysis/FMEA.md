# Failure Mode and Effects Analysis (FMEA)

**Document**: FMEA-001
**Project**: Safety-Supervised Edge AI Demonstrator
**Standard reference**: ISO 26262-9:2018 Clause 8 (Analysis of dependent failures),
ISO 26262-4:2018 Clause 8 (FMEA at system level)
**Date**: 2026-05-11
**Author**: Yunpeng Yang
**Status**: COMPLETE — educational demonstrator scope

> **Disclaimer**: This FMEA is performed using ISO 26262-inspired methodology for an
> educational demonstrator. It is NOT a certified FMEA and does NOT constitute ISO 26262
> compliance. No quantitative FIT (Failures In Time) rates are available for the hardware
> platform. Diagnostic coverage (DC) estimates are qualitative. A production system
> would require a quantitative FMEA/FMEDA with certified failure rate data.

---

## 1. Scope and Method

This FMEA analyses failure modes of each safety-relevant component in the system,
their effects at subsystem and system level, existing detection mechanisms, and
residual risk.

**Severity classification**:
- **Critical**: leads to SAFE_STATE not being reached when required (safety goal violation)
- **Significant**: leads to delayed or incomplete safe state transition
- **Minor**: degraded functionality, no safety goal violation
- **None**: no safety impact

**Diagnostic coverage (DC)** — qualitative estimate:
- **High**: >99% of failure instances detected
- **Medium**: 90–99%
- **Low**: 60–90%
- **None**: <60%

---

## 2. FMEA Table

### 2.1 SM-1: UDP Q&A Watchdog

| ID | Component | Failure Mode | Local Effect | System Effect | Detection Mechanism | DC | Residual Risk | Mitigation |
|---|---|---|---|---|---|---|---|---|
| F-001 | health_node UDP thread | Thread hangs (no response sent) | No Q&A response | Pi400 failure_counter++ → SAFE_STATE after 3 cycles (90ms) | Pi400 timeout | High | Low | Flow check monitors health_node liveness indirectly via /system_state |
| F-002 | health_node UDP thread | Wrong response computed (XOR error) | Wrong answer sent | Pi400 failure_counter++ | Pi400 value check + CRC | High | Low | E2E: CRC-16 detects corruption |
| F-003 | health_node | Process crash (SIGKILL/SIGSEGV) | No UDP response | SAFE_STATE within 90ms | Pi400 timeout | High | Low | OS process isolation; systemd could auto-restart |
| F-004 | qnx_wdg_server | Seed not generated (Python exception) | No seed sent to Pi5 | Pi5 has no seed to respond to; Pi400 own timer fires → failure_counter++ | Pi400 internal timeout | Medium | Low | Exception handler restarts loop; fail-safe: GPIO 25 remains LOW |
| F-005 | UDP channel | Packet loss (single packet) | One missed response | failure_counter++ (1 of 3 needed for SAFE_STATE) | Pi400 timeout | High | Low | Three consecutive failures required; single loss tolerated |
| F-006 | UDP channel | Sustained packet loss (>3 cycles) | No response received | SAFE_STATE after 3 × 30ms = 90ms | Pi400 timeout | High | Low | Dedicated Ethernet link reduces congestion risk |
| F-007 | UDP channel | Packet replay (old response) | Wrong seq counter | Pi400 seq mismatch → failure_counter++ | Seq counter E2E | High | Low | Sequence counter detects replay/reorder |
| F-008 | UDP channel | Bit flip in payload | Wrong CRC or value | Pi400 CRC check fails → failure_counter++ | CRC-16 | High | Low | CRC-16 detects all 1-bit and 2-bit errors |
| F-009 | Ethernet link | Physical disconnection | No UDP packets | SAFE_STATE after 90ms | Pi400 timeout | High | Low | Fail-safe: GPIO 25 asserted at boot; link loss = safe |
| F-010 | Flow check | /system_state deadline missed (decision_node crash) | flow_ok = false | WDG response withheld → Pi400 counts failure → SAFE_STATE | 60ms deadline check | High | Low | Bundles pipeline liveness with watchdog servicing |
| F-011 | Flow check | /obstacles deadline missed (ultrasonic_node crash) | flow_ok = false | WDG response withheld → SAFE_STATE | 150ms deadline check | High | Low | Ultrasonic crash detected within 150ms |

---

### 2.2 SM-2: Hardware E-Stop (GPIO 25)

| ID | Component | Failure Mode | Local Effect | System Effect | Detection Mechanism | DC | Residual Risk | Mitigation |
|---|---|---|---|---|---|---|---|---|
| F-020 | GPIO 25 wire | Wire break (open circuit) | Pi5 GPIO 25 floats HIGH (pull-up) | E-stop NOT asserted on Pi400 command — **SPOF** | None — actuator_node reads HIGH = inactive | **None** | **High** | Documented SPOF; production would need redundant wire or active monitoring |
| F-021 | GPIO 25 wire | Short to ground | GPIO 25 permanently LOW | Permanent e-stop — system cannot release | Pi400 cannot release GPIO 25 | High (detected immediately) | Low (fail-safe) | Fail-safe direction; system halted but safe |
| F-022 | Pi400 GPIO 25 driver | GPIO stuck HIGH (cannot assert) | E-stop cannot be asserted | Watchdog failure → no hardware safety action | No detection in current design | **None** | **Critical** | Known SPOF documented in HARA; production requires driver health monitoring |
| F-023 | Pi400 GPIO 25 driver | GPIO stuck LOW (permanent assert) | Permanent e-stop | System cannot operate | Pi400 sees stuck LOW | High | Low (fail-safe) | Fail-safe direction |
| F-024 | actuator_node | Process crash | GPIO 25 no longer polled | Hardware e-stop functional; software path lost | health_node flow check detects via /system_state timeout | Medium | Low | Pi400 e-stop independent of actuator_node |
| F-025 | actuator_node | GPIO poll rate degraded (<100Hz) | Delayed e-stop detection | Detection latency > 10ms — still within budget | Not detected unless timeout | Low | Low | 100Hz poll has 30ms budget; minor degradation tolerated |

---

### 2.3 SM-3: StateEvaluator (Software State Machine)

| ID | Component | Failure Mode | Local Effect | System Effect | Detection Mechanism | DC | Residual Risk | Mitigation |
|---|---|---|---|---|---|---|---|---|
| F-030 | StateEvaluator | Wrong state returned (logic error) | Incorrect velocity scale or missed SAFE_STATE | Safety goal violation if SAFE_STATE missed | 33 gtest unit tests; code review | Medium | Medium | Pure C++ function, no side effects; 33 tests cover all transitions; hardware path (GPIO 25) independent |
| F-031 | StateEvaluator | SAFE_STATE not triggered on critical distance | Robot continues at speed | Safety goal violation (SG-001) | Gtest boundary tests; fault injection FI-03 | Medium | Medium | Hardware GPIO 25 path independent of StateEvaluator |
| F-032 | decision_node | Process crash | No StateEvaluator evaluation | /system_state stops publishing → flow check fails → WDG withheld → SAFE_STATE | health_node flow check (60ms deadline) | High | Low | Pipeline crash detected via flow check |
| F-033 | decision_node timer | Timer drift (>20ms cycle time) | Late StateEvaluator evaluation | FTTI budget affected | Not detected | Low | Low | 50Hz evaluation has margin vs. 100ms FTTI target |
| F-034 | camera_distance_m parsing | JSON parse error | camera_distance_m = FLT_MAX | camera_hand_critical not triggered | Exception handler → FLT_MAX | High | Low | FLT_MAX = no hand → safe default (conservative) |
| F-035 | watchdog_failure_counter | Counter not updated (UDP status loss) | Counter stuck at stale value | Late or missed SAFE_STATE on watchdog failure | health_node timeout on status messages | Low | Medium | Status published each Q&A cycle; loss detected within 3 cycles |

---

### 2.4 SM-4: Sensor Path Monitoring

| ID | Component | Failure Mode | Local Effect | System Effect | Detection Mechanism | DC | Residual Risk | Mitigation |
|---|---|---|---|---|---|---|---|---|
| F-040 | ultrasonic_node | Process crash | No /obstacles messages | ultrasonic_valid=false after 100ms → DEGRADED | 100ms timeout in decision_node | High | Low | DEGRADED → 20% velocity; camera provides backup |
| F-041 | Grove Ultrasonic Ranger | Hardware failure (no echo) | /obstacles publishes inf | ultrasonic_valid not set (invalid readings ignored) → 100ms timeout → DEGRADED | 100ms timeout | High | Low | Single missed readings debounced |
| F-042 | ultrasonic_node | Spurious reading (acoustic noise) | Single out-of-range reading | Ignored by debounce filter | Debounce: invalid readings not propagated | High | Low | Only valid readings reset the liveness timer |
| F-043 | hand_detection_node | Process crash | No /hand_detections, /hand_roi | camera_valid=false after 2s → DEGRADED | 2s timeout in decision_node | High | Low | 2s timeout provides graceful degradation |
| F-044 | object_detection_node | Process crash | No /detections | camera_valid=false after 2s → DEGRADED | 2s timeout | High | Low | Same as F-043 |
| F-045 | MediaPipe Hands | Model inference error (wrong bounding box) | Incorrect hand_distance_m | camera_hand_critical may not trigger at correct distance | None in current design | Low | Medium | 20cm threshold provides margin for ±30% accuracy |
| F-046 | IMX708 camera | Hardware failure | No frames captured | picamera2 exception → INACTIVE status published → camera_valid=false after 2s | 2s timeout | High | Low | Camera failure → DEGRADED (ultrasonic still valid) |

---

### 2.5 SM-5: MMU Process Isolation

| ID | Component | Failure Mode | Local Effect | System Effect | Detection Mechanism | DC | Residual Risk | Mitigation |
|---|---|---|---|---|---|---|---|---|
| F-050 | hand_detection_node | Memory corruption (bug in MediaPipe) | Process crash or segfault | Contained to process; other nodes unaffected | OS kills process; camera_valid timeout | High | Low | MMU prevents propagation to object_detection_node |
| F-051 | object_detection_node | Memory corruption (bug in YOLOv8n) | Process crash or segfault | /detections stops → camera_valid timeout → DEGRADED | OS kills process; 2s timeout | High | Low | MMU prevents propagation to hand_detection_node |
| F-052 | Linux kernel | Kernel panic (Pi5) | All Pi5 processes killed | No UDP response → Pi400 triggers SAFE_STATE via GPIO 25 | Pi400 watchdog timeout (90ms) | High | Low | Pi400 independent of Pi5 kernel |

---

### 2.6 SM-6: LED and Buzzer Indicators

| ID | Component | Failure Mode | Local Effect | System Effect | Detection Mechanism | DC | Residual Risk | Mitigation |
|---|---|---|---|---|---|---|---|---|
| F-060 | Green LED (GPIO 17) | LED open circuit (burnt out) | No green indication | Operator loses NORMAL state visual — not safety-critical | None | None | Low | Operator must use /system_state topic for reliable status |
| F-061 | Red LED diode-OR circuit | D1 or D2 diode failure | One driver leg lost | Red LED still illuminated by other side | None | Low | Low | Wired-OR redundancy; both sides drive independently |
| F-062 | Buzzer (GPIO 18) | Buzzer hardware failure | No audible WARNING/DEGRADED alert | Operator must rely on visual LED only | None | None | Low | LED provides visual backup; not safety-critical output |
| F-063 | health_node | GPIO claim failure at startup | No LED or buzzer control | State indication lost; safety path unaffected | lgpio error → node crash → flow check | High | Low | Safety path (GPIO 25, StateEvaluator) independent of LEDs |

---

## 3. Critical Failure Mode Summary

| ID | Failure Mode | Residual Risk | Root cause |
|---|---|---|---|
| F-020 | GPIO 25 wire break | **High** | No detection mechanism; e-stop silently lost |
| F-022 | Pi400 GPIO 25 driver stuck HIGH | **Critical** | Cannot assert e-stop; no self-test |
| F-030 | StateEvaluator wrong state | **Medium** | Depends on test coverage for all scenarios |
| F-035 | watchdog_failure_counter staleness | **Medium** | UDP status loss undetected |
| F-045 | Camera distance accuracy | **Medium** | ±30% accuracy; no calibration verification |

---

## 4. Single Point of Failure (SPOF) Register

| SPOF | Component | Effect | Justification for acceptance |
|---|---|---|---|
| SPOF-001 | GPIO 25 wire | E-stop cannot be asserted by Pi400 | Single wire; no redundancy. Accepted for demonstrator; production requires dual channel |
| SPOF-002 | Pi400 GPIO 25 output driver | E-stop stuck-at-HIGH cannot self-test | No driver health monitoring. Accepted; production requires periodic self-test pulse |
| SPOF-003 | Pi5 Linux kernel | Pi400 can trigger GPIO 25 but Pi5 must still read it | Shared kernel risk mitigated by Pi400 independence; kernel panic → watchdog fires |
| SPOF-004 | Dedicated Ethernet link | UDP watchdog channel lost | No redundant network path. Accepted; physical link break is fail-safe (watchdog timeout → SAFE_STATE) |

---

## 5. Diagnostic Coverage Summary

| Safety Mechanism | Faults covered | DC estimate | Evidence |
|---|---|---|---|
| Q&A watchdog (SM-1) | F-001 to F-011 | High | FI-05 PASS; FFI-COMM PASS |
| Hardware e-stop (SM-2) | F-020 to F-025 | Medium (SPOF F-020, F-022) | M5 e-stop verified; F-022 known gap |
| StateEvaluator (SM-3) | F-030 to F-035 | Medium–High | 33 gtest; FI-03 PASS; FI-04 PASS |
| Sensor monitoring (SM-4) | F-040 to F-046 | High (except F-045) | FI-01/02 PASS; debounce verified |
| MMU isolation (SM-5) | F-050 to F-052 | High | FFI-SPATIAL PASS |
| Indicators (SM-6) | F-060 to F-063 | Low (not safety-critical) | Manual verification |

---

## 6. Residual Risk Acceptance

| Risk level | Count | Decision |
|---|---|---|
| Critical | 1 (F-022) | Accepted for demonstrator; documented SPOF |
| High | 1 (F-020) | Accepted for demonstrator; single wire intentional |
| Medium | 3 (F-030, F-035, F-045) | Accepted; mitigated by independent hardware path |
| Low | All others | Accepted |

**Overall residual risk**: Acceptable for an educational demonstrator.
A production system must resolve F-020 and F-022 before deployment.

---

## 7. References

- ISO 26262-4:2018 — System-level design and FMEA
- ISO 26262-9:2018 — Dependent failure analysis
- `docs/safety_analysis/HARA.md` — hazard identification and ASIL
- `docs/safety_mechanisms.md` — mechanism implementation details
- `docs/fault_injection_report.md` — fault injection test evidence
- `docs/ffi_verification_report.md` — FFI test evidence

---

*A production system requires quantitative FMEDA with FIT rates per IEC 62380 or SN 29500.*
*This FMEA is qualitative and for educational/portfolio purposes only.*
