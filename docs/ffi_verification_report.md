# FFI Verification Report

**Project**: Safety-Supervised Edge AI Demonstrator
**Milestone**: M7 — Freedom From Interference Verification
**Status**: PENDING — tests not yet executed
**Engineer**: Yunpeng

> **Disclaimer**: ASIL-B-inspired demonstrator only. No certified FFI metrics claimed.
> These tests demonstrate the architectural independence measures, not production ASIL-B compliance.

---

## Scope

Three FFI verification tests confirm that the three independence measures
hold under stress conditions. Pass/fail is determined by the engineer.

| Test | Script | Independence measure |
|---|---|---|
| FFI-SPATIAL | `tests/ffi/ffi_spatial_stress.sh` | Pi5 load does not affect Pi400 watchdog |
| FFI-TEMPORAL | `tests/ffi/ffi_temporal_timing.py` | AI inference does not push Q&A outside window |
| FFI-COMM | `tests/ffi/ffi_comm_ros_flood.py` | ROS2 flood does not affect UDP watchdog |

---

## Pre-conditions (all tests)

- Pi400: `qnx_wdg_server.py` running (M7 version — 30ms window, CRC/seq)
- Pi5: `ros2 launch safety_demo demo.launch.py` (all 7 nodes running)
- `/reset` published — system in NORMAL or DEGRADED
- `/watchdog_failure_counter` echoing 0

---

## FFI-SPATIAL — Spatial Independence

**Fault injected**: Pi5 CPU (4 cores) + memory (1 GB) stressed with `stress-ng` for 30s.

**Expected**: `failure_counter` stays 0 — Pi5 load cannot corrupt Pi400's independent
watchdog cycle.

**Requirement**: SYS-SAFE-002 (spatial independence via separate processors), FFI-001

| Check | Expected | Actual | Result |
|---|---|---|---|
| failure_counter max during stress | 0 | | |
| Pi400 logs any FAIL entries during stress | None | | |
| System state during stress | NORMAL/DEGRADED | | |

**Notes**:

**Overall**: ☐ PASS  ☐ FAIL
**Date executed**: ___________

---

## FFI-TEMPORAL — Temporal Independence

**Fault injected**: Full AI pipeline active (MediaPipe + YOLOv8n on live camera) for 60s.

**Expected**: `failure_counter` stays 0 — AI inference delays do not push health_node's
Q&A responses outside the 15–30ms window.

**Requirement**: SYS-SAFE-003 (temporal independence), FFI-002

| Check | Expected | Actual | Result |
|---|---|---|---|
| failure_counter during AI load | 0 | | |
| "too_early" events in Pi400 log | 0 | | |
| "timeout" events in Pi400 log | 0 | | |
| health_node 20ms cycle maintained under load | Yes | | |

**Notes**:

**Overall**: ☐ PASS  ☐ FAIL
**Date executed**: ___________

---

## FFI-COMM — Communication Independence

**Fault injected**: `/obstacles` topic flooded at 200 Hz (10× nominal) for 30s.

**Expected**: `failure_counter` stays 0 — DDS/ROS2 congestion does not affect the
UDP watchdog socket (separate network path).

**Requirement**: FFI-003 (communication independence), SYS-IF-001

| Check | Expected | Actual | Result |
|---|---|---|---|
| failure_counter during ROS2 flood | 0 | | |
| Pi400 logs any FAIL entries during flood | None | | |
| UDP watchdog continues at normal rate | Yes | | |

**Note**: `/obstacles` flood may trigger state changes (WARNING/SAFE_STATE via
StateEvaluator) — this is expected and acceptable. Only the UDP watchdog
failure_counter must stay 0.

**Overall**: ☐ PASS  ☐ FAIL
**Date executed**: ___________

---

## Summary

| Test | Result | Date |
|---|---|---|
| FFI-SPATIAL | ☐ PASS  ☐ FAIL | |
| FFI-TEMPORAL | ☐ PASS  ☐ FAIL | |
| FFI-COMM | ☐ PASS  ☐ FAIL | |

---

## Observations and Limitations

*(To be filled in after execution)*

Known architectural limitations regardless of test results:
- UDP watchdog relies on Linux network stack — weaker than hardware I2C (DD-002)
- Linux kernel is shared between Pi5 processes — not hardware-level partitioning
- No quantitative interference probability metrics claimed

---

*Report completed: ___________*
*Engineer sign-off: Yunpeng*
