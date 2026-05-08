# Fault Injection Test Report

**Project**: Safety-Supervised Edge AI Demonstrator
**Milestone**: M6 — Fault Injection Tests
**Date**: 2026-05-09
**Engineer**: Yunpeng

> **Disclaimer**: This is a demonstrator-level fault injection exercise.
> No certified fault coverage metrics are claimed. This report does NOT
> constitute ISO 26262 fault injection evidence. The system is
> ASIL-B-inspired and educational only.

---

## Scope

Five fault-injection scenarios are defined and executed against the full
M4+M5 system (camera AI active, Pi400 Q&A watchdog active). Each scenario
has a defined expected outcome derived from `docs/safety_concept.md` and
the `StateEvaluator` priority rules in `src/decision_node/src/state_evaluator.cpp`.

**Pass/fail determination is made by the engineer**, not by an automated tool.

---

## System Under Test

| Component | Version / State |
|---|---|
| Pi5 OS | Raspberry Pi OS Bookworm |
| ROS2 | Humble (built from source) |
| camera_ai_node | M4 — MediaPipe Hands + YOLOv8n |
| decision_node | M3/M5 — StateEvaluator C++20, watchdog_failure_counter wired |
| health_node | M5 — UDP Q&A watchdog client |
| Pi400 supervisor | M5 — qnx_wdg_server.py, GPIO 25 + GPIO 22 |

---

## Scenario Results

### FI-01 — Ultrasonic Node Timeout

| Field | Value |
|---|---|
| Script | `tests/fault_injection/fi_01_ultrasonic_timeout.py` |
| Fault | `pkill -f ultrasonic_node` |
| Requirement | SYS-SAFE-008 (graceful degradation) |
| Expected state | DEGRADED (`degraded_one_sensor` — camera valid, ultrasonic invalid) |
| Expected LEDs | Green ON, Yellow ON, Red OFF |
| Expected vel_scale | 0.2 |

| Check | Expected | Actual | Result |
|---|---|---|---|
| /system_state | DEGRADED | DEGRADED | ✅ |
| /diagnostics trigger | degraded_one_sensor | degraded_one_sensor | ✅ |
| Yellow LED ON | Yes | Yes | ✅ |
| decision_node still running | Yes | Yes | ✅ |

**Overall**: ✅ PASS
**Notes**: System degraded gracefully to 20% velocity. Camera path remained valid.

---

### FI-02 — Camera AI Node Process Stop

| Field | Value |
|---|---|
| Script | `tests/fault_injection/fi_02_camera_node_stop.py` |
| Fault | `pkill -f camera_ai_node` |
| Requirement | SYS-SAFE-001 (AI not in safety path), SYS-SAFE-008 |
| Expected state | DEGRADED (`degraded_one_sensor` — camera invalid, ultrasonic valid) |
| Expected LEDs | Green ON, Yellow ON, Red OFF |
| Key assertion | SAFE_STATE must NOT be entered (AI failure = DEGRADED only) |

| Check | Expected | Actual | Result |
|---|---|---|---|
| /system_state | DEGRADED | DEGRADED | ✅ |
| /system_state NOT SAFE_STATE | Confirmed | Confirmed | ✅ |
| /diagnostics trigger | degraded_one_sensor | degraded_one_sensor | ✅ |
| decision_node still running | Yes | Yes | ✅ |

**Overall**: ✅ PASS
**Notes**: AI node failure correctly yields DEGRADED, not SAFE_STATE. Confirms SYS-SAFE-001 — AI output not in safety path.

---

### FI-03 — Both Sensor Paths Simultaneously Invalid

| Field | Value |
|---|---|
| Script | `tests/fault_injection/fi_03_both_sensors_invalid.py` |
| Fault | `pkill -f camera_ai_node` + `pkill -f ultrasonic_node` |
| Requirement | SYS-SAFE-006, SYS-SAFE-011 |
| Expected state | SAFE_STATE (`both_sensors_invalid`) |
| Expected LEDs | Green OFF, Red ON |
| Expected latency | < 3s (camera 2s timeout + ultrasonic 1s timeout) |
| Latches | Yes — requires /reset |

| Check | Expected | Actual | Result |
|---|---|---|---|
| /system_state | SAFE_STATE | SAFE_STATE | ✅ |
| /diagnostics trigger | both_sensors_invalid | both_sensors_invalid | ✅ |
| Green LED OFF | Yes | Yes | ✅ |
| Red LED ON | Yes | Yes | ✅ |
| Latches without reset | Yes | Yes | ✅ |

**Overall**: ✅ PASS
**Notes**: SAFE_STATE entered after both timeouts expired (~2s). Latched until /reset published.

---

### FI-04 — Malformed Sensor Data

| Field | Value |
|---|---|
| Script | `tests/fault_injection/fi_04_malformed_sensor_data.py` |
| Fault | Publish NaN, negative, inf, zero range to /obstacles |
| Requirement | SYS-SAFE-005 (invalid input rejection) |
| Expected | No crash; ultrasonic_valid=false; DEGRADED (camera valid) |

| Input value | decision_node running | ultrasonic_valid=false | Result |
|---|---|---|---|
| NaN range | Yes | Yes | ✅ |
| Negative range (-1.0) | Yes | Yes | ✅ |
| Inf range | Yes | Yes | ✅ |
| Zero range (0.0) | Yes | Yes | ✅ |

**Overall**: ✅ PASS
**Notes**: decision_node C++ `std::isfinite()` check correctly rejected all invalid values. No crash. System degraded to DEGRADED state during injection, recovered when valid data resumed.

---

### FI-05 — Q&A Watchdog Failure (health_node stop)

| Field | Value |
|---|---|
| Script | `tests/fault_injection/fi_05_watchdog_failure.py` |
| Fault | `pkill -f health_node` (stops UDP Q&A client) |
| Requirement | SYS-SAFE-004a, SYS-SAFE-006, FSR-001 |
| Expected state | SAFE_STATE (`watchdog_failure`) |
| Expected hardware | Pi400 GPIO 25 LOW, Pi400 GPIO 22 HIGH |
| Target latency | < 300ms (3 × 100ms window) |

| Check | Expected | Actual | Result |
|---|---|---|---|
| /system_state | SAFE_STATE | SAFE_STATE | ✅ |
| /diagnostics trigger | watchdog_failure | watchdog_failure | ✅ |
| actuator_node logs E-STOP ASSERTED | Yes | Yes | ✅ |
| /watchdog_failure_counter | 3 | 3 | ✅ |
| Latency (fault → SAFE_STATE) | < 300ms | < 300ms | ✅ |
| Green LED OFF | Yes | Yes | ✅ |
| Red LED ON (Pi5 + Pi400) | Yes | Yes | ✅ |

**Overall**: ✅ PASS
**Notes**: Hardware e-stop path (Pi400 GPIO 25 → Pi5 GPIO 25) confirmed independent of decision_node. Also verified during M5 acceptance testing (2026-05-09).

---

## Summary

| ID | Scenario | Result | Requirement |
|---|---|---|---|
| FI-01 | Ultrasonic timeout → DEGRADED | ✅ PASS | SYS-SAFE-008 |
| FI-02 | Camera stop → DEGRADED (not SAFE_STATE) | ✅ PASS | SYS-SAFE-001 |
| FI-03 | Both sensors invalid → SAFE_STATE | ✅ PASS | SYS-SAFE-006 |
| FI-04 | Malformed sensor data → no crash | ✅ PASS | SYS-SAFE-005 |
| FI-05 | Watchdog failure → SAFE_STATE < 300ms | ✅ PASS | SYS-SAFE-004a |

**All 5 scenarios: PASS**

---

## Observations and Limitations

1. **Fault injection is software-only** — no hardware pin shorting or power interruption was performed.
2. **Camera_valid latency**: camera_valid timeout is 2s — slower than ultrasonic (1s). This means FI-03 takes ~2s to enter SAFE_STATE. Production systems would use faster detection.
3. **Watchdog transport**: Q&A watchdog uses UDP (DD-002 Option B). Hardware I2C slave not feasible on BCM2711. UDP relies on Linux network stack — weaker FFI argument than hardware I2C but acceptable for demonstrator.
4. **No quantitative fault coverage metrics** are claimed or implied by this report.

---

*Report completed: 2026-05-09*
*Engineer sign-off: Yunpeng*
