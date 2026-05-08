# M7: Freedom From Interference (FFI) Verification

## Goal

Verify and document the three FFI-inspired measures through targeted tests.
Produce a quantified effectiveness assessment. Update `docs/ffi_argument.md`
with measured evidence.

## Scope

### FFI-SPATIAL: Spatial Independence
- Stress Pi5 CPU/memory while Pi400 watchdog measures its own cycle timing
- Confirm failure_counter stays 0 under Pi5 load
- Script: `tests/ffi/ffi_spatial_stress.sh`

### FFI-TEMPORAL: Temporal Independence
- Run full AI pipeline (camera + YOLOv8n) under CPU load
- Measure UDP Q&A response times under load vs. idle
- Confirm all responses within 50–100ms window
- Script: `tests/ffi/ffi_temporal_timing.py`

### FFI-COMM: Communication Independence
- Flood ROS2 topics at high rate
- Confirm UDP watchdog timing unaffected
- Script: `tests/ffi/ffi_comm_ros_flood.py`

## Deliverables

- `tests/ffi/` — test scripts
- `docs/ffi_verification_report.md` — results with measured data
- Updated `docs/ffi_argument.md` — effectiveness ratings with evidence
- `requirements/traceability.csv` — FFI test links

## Acceptance Criteria

- [ ] Pi5 CPU stress does not increment Pi400 failure_counter
- [ ] Watchdog response times within window under AI load
- [ ] ROS2 topic flood does not affect UDP watchdog
- [ ] `docs/ffi_verification_report.md` complete and signed off

## GitHub issue: #10
