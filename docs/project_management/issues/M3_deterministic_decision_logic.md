# M3: Deterministic Decision Logic

## Goal

Implement and unit-test the deterministic rule-based state evaluator that governs transitions between NORMAL, WARNING, DEGRADED, and SAFE_STATE. All logic shall be explicit, traceable, and free of probabilistic or AI-driven branching.

## Scope

- C++20 implementation of the safety-inspired state machine in `decision_node`
- State transitions: `INIT → NORMAL ↔ WARNING ↔ DEGRADED → SAFE_STATE`
- Input rules based on ultrasonic distance thresholds, heartbeat validity, and sensor health flags
- Velocity scaling per state: NORMAL 100%, WARNING 50%, DEGRADED 20%, SAFE_STATE 0%
- SAFE_STATE requires manual reset (no auto-recovery)
- Unit tests covering all state transitions and boundary conditions
- Updated traceability matrix linking rules to requirements and tests

## Out of Scope

- LLM-based or AI-driven decision making of any kind
- Cloud AI calls or non-deterministic runtime behavior
- QNX supervisor integration (deferred to M5)
- Camera AI model integration (may run in parallel but must not influence safety state)
- Quantitative ASIL or fault-coverage metrics

## Engineering Tasks

- [ ] Define `SystemState` enum: `INIT`, `NORMAL`, `WARNING`, `DEGRADED`, `SAFE_STATE`
- [ ] Implement `StateEvaluator` class in C++20 with pure deterministic transition logic
- [ ] Implement velocity scaling per state as a lookup or constexpr table
- [ ] Implement heartbeat validity check (timeout > 500 ms → SAFE_STATE)
- [ ] Implement ultrasonic threshold rules:
  - WARNING: any sensor < warning threshold
  - DEGRADED: AI node unavailable, ultrasonic-only mode
  - SAFE_STATE: critical sensor failure or heartbeat loss
- [ ] Write unit tests for all nominal and fault transitions
- [ ] Write unit tests for boundary conditions (threshold edges, timeout boundary)
- [ ] Confirm SAFE_STATE can only be exited by manual reset
- [ ] Update `requirements/traceability.csv` with decision logic → requirement → test links
- [ ] Update `docs/safety_concept.md` if any rule deviates from the documented state machine

## Acceptance Criteria

- [ ] All state transitions are covered by at least one unit test
- [ ] All unit tests pass with `pytest` or `gtest` (framework to be confirmed)
- [ ] SAFE_STATE entry is triggered correctly for: heartbeat timeout, critical sensor failure
- [ ] SAFE_STATE cannot be exited without explicit manual reset signal
- [ ] Velocity scaling values match `requirements/interfaces.yaml` or documented thresholds
- [ ] No probabilistic, model-based, or AI-driven logic is present in `StateEvaluator`
- [ ] `requirements/traceability.csv` links each rule to at least one requirement and one test
- [ ] `decision_node` integrates `StateEvaluator` and publishes state on ROS2 topic

## Related Requirements

- SYS-SAFE-001 (SAFE_STATE entry on heartbeat loss)
- SYS-SAFE-002 (Manual reset required for SAFE_STATE exit)
- SYS-SAFE-003 (Deterministic decision logic, no AI in safety path)
- SYS-PERF-003 (Safe state latency < 150 ms total)
- SYS-PERF-001 (Perception-to-actuation ≤ 200 ms in NORMAL)
- To be linked: velocity scaling requirements per state

## Related Documents

- `docs/safety_concept.md` (state machine definition)
- `requirements/interfaces.yaml` (timing constraints)
- `requirements/system_requirements.md`
- `requirements/safety_requirements.md`
- `requirements/traceability.csv`

## Test Evidence

- Unit test report (all tests pass, zero failures)
- State transition coverage table showing each transition exercised
- Logbook entry confirming SAFE_STATE manual-reset behavior verified

## Safety / AI Boundary

- AI agents may assist with C++20 scaffolding, test structure, and documentation.
- AI agents shall not generate the transition rules themselves without engineer review and approval of each rule against requirements.
- The `StateEvaluator` is the ASIL-B-inspired monitoring path; its logic must be deterministic and explicitly approved.
- No LLM inference, cloud calls, or probabilistic outputs shall appear anywhere in the safety decision path.
- AI model outputs (camera inference) must not reach `StateEvaluator` inputs.

## Suggested Labels

`cplusplus` `safety` `testing` `ros2` `portfolio`

## Suggested Branch Name

`feature/m3-deterministic-decision-logic`

## Suggested Commit Message

```
feat: add deterministic state evaluator with unit tests
```
