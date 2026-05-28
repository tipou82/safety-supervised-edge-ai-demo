# Documentation Review Notes

**Date**: 2026-05-05
**Reviewer**: Yunpeng
**Scope**: All Markdown, YAML, CSV and SysML files in repository

---

## Review Summary

All documentation files were reviewed for wording consistency, safety claim accuracy, and portfolio readiness.

| File | Status | Notes |
|------|--------|-------|
| README.md | Pass | Correct disclaimers, demonstrator scope clearly stated |
| docs/architecture.md | Pass | FFI-inspired wording consistent; QNX domain described as "QNX-inspired or Linux Fallback" |
| docs/safety_concept.md | Pass | ASIL-B-inspired framing consistent throughout; clear "what is NOT claimed" section |
| docs/supervisor_design.md | Fixed | QNX product certification bullet clarified to prevent misreading as project claim |
| docs/ffi_argument.md | Pass | Honest effectiveness ratings; clear gap analysis; good interview talking points |
| requirements/system_requirements.md | Pass | All ASIL tags use "B-inspired"; explicit non-certification assumption documented |
| requirements/safety_requirements.md | Pass | Compliance statement is accurate; ASIL decomposition correctly hedged |
| requirements/interfaces.yaml | Pass | Technical content only; no certification language |
| requirements/traceability.csv | Pass | Status column correctly shows all items TODO; no false completion claims |
| hardware/wiring.md | Pass | SPOF acknowledged; demonstrator scope explicit |
| hardware/gpio_mapping.md | Pass | Code snippets labelled as pseudocode/reference; TBD pins not claimed |
| engineering_logbook/2026-05-04.md | Pass | Honest reflection; safety wording strategy section validates approach |

---

## Safety Wording Review Result

**Overall assessment: PASS with one minor fix applied.**

### Issue Found and Corrected

**File**: `docs/supervisor_design.md`
**Issue**: Bullet "Certified to IEC 61508 SIL 3, ISO 26262 ASIL D (when properly qualified)" could be read as a project-level certification claim, even though the surrounding context clarified it was a product-level capability.
**Fix applied**: Reworded to "Certifiable to IEC 61508 SIL 3, ISO 26262 ASIL D as a product (requires qualified BSP and tool chain — NOT applicable to this Raspberry Pi demonstrator)".

### Confirmed Correct Patterns

The following wording conventions are applied consistently across all documents:

| Correct Wording Used | Incorrect Wording Avoided |
|---------------------|--------------------------|
| "ASIL-B-inspired monitoring path" | "ASIL-B path" / "ASIL-B certified" |
| "FFI-inspired architectural measures" | "certified FFI" / "FFI compliant" |
| "demonstrator" | "safety-certified system" / "production system" |
| "QNX-inspired supervisor" or "QNX supervisor (or Linux fallback)" | Unqualified "QNX system" implying certification |
| "rule-based deterministic logic" in safety path | Any reference to AI/ML in safety decision path |

---

## Known Limitations

### Documentation Limitations

1. **Pi 400 GPIO assignments are TBD** — `gpio_mapping.md` and `wiring.md` note these as "TBD pending hardware integration". This is intentional and correct; they should be filled in during hardware bring-up (M1).

2. **SysML model not validated by tooling** — `docs/sysml/architecture.sysml` is a text artifact; no SysML v2 tooling execution has been performed. The model should be considered illustrative.

3. **Timing values are estimates** — All WCET figures and latency budgets in `docs/supervisor_design.md` are design targets, not measured values. This is clearly noted ("TBD" in the measurement columns).

4. **Traceability CSV has all items as TODO** — Correct for the current phase (documentation only). Implementation and test completion will update these.

### Architectural Limitations (as documented in ffi_argument.md)

- Common power supply is an unmitigated single point of failure
- GPIO communication has no redundancy
- Design independence is partial (single-person project)
- No quantitative PMHF / FIT rate analysis
- No third-party safety assessment

---

## Next Recommended Engineering Steps

### M1 — Hardware Bring-up (Recommended Next)

1. Assemble hardware per `hardware/wiring.md`
2. Confirm Pi 400 GPIO pin availability and fill in TBD entries in `gpio_mapping.md`
3. Verify 3.3V GPIO compatibility and voltage dividers for HC-SR04 ECHO pins
4. Validate heartbeat square wave with oscilloscope (should be 10 Hz, 50% duty cycle)
5. Validate emergency stop GPIO default state (active-low, asserted at boot)

### M2 — ROS2 Sensor Pipeline

1. Set up Ubuntu 22.04 + ROS2 Humble on Pi5
2. Scaffold ROS2 packages with `colcon` build structure
3. Implement `health_node` first (heartbeat generation) — enables supervisor testing early
4. Implement `ultrasonic_node` for obstacle detection
5. Implement `camera_ai_node` (YOLOv8n or MobileNet via TFLite)

### M3 — Deterministic Decision Logic

1. Implement `decision_node` with rule-based obstacle avoidance
2. Implement `actuator_node` with emergency stop GPIO polling (100 Hz)
3. Implement Linux-fallback supervisor (POSIX SCHED_FIFO, `libgpiod`)
4. Validate state machine transitions manually

### M4 — Fault Injection

1. Implement fault injection test scripts from `requirements/safety_requirements.md`
2. Measure end-to-end safe state latency (target: <150 ms)
3. Run CPU stress interference test; verify supervisor timing stability
4. Update `requirements/traceability.csv` with measured results

### M5 — External Supervisor (Optional)

1. Evaluate QNX 7.1 BSP availability for Raspberry Pi 400
2. If available: port Linux fallback supervisor to QNX
3. Re-run fault injection tests on QNX implementation
4. Compare latency and timing jitter between Linux fallback and QNX

### M6 — Portfolio-Ready Demo

1. Record demonstration video (NORMAL → fault injection → SAFE_STATE → manual reset)
2. Finalize all documentation with measured values
3. Tag release `v1.0-demo`
4. Prepare interview presentation deck
