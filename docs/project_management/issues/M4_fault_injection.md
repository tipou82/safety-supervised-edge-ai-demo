# M4: Fault Injection

## Goal

Demonstrate that the system responds correctly to selected fault conditions by executing documented fault-injection scenarios and recording the resulting system behavior. Provide engineering evidence of degraded and safe-state handling without making certified fault-coverage claims.

## Scope

- Fault-injection test framework (script or manual procedure)
- At least five defined and executed fault-injection scenarios
- Documented expected behavior per scenario (from `docs/safety_concept.md`)
- Documented actual behavior per scenario (logbook entries)
- Pass/fail determination per scenario against acceptance criteria
- Test report summarizing all results

## Out of Scope

- Certified fault coverage analysis or quantitative FMEA metrics
- ISO 26262 ASIL-B fault injection methodology claims
- Hardware fault injection (pin shorting, power interruption) — software simulation only unless explicitly planned
- Regression of all unit tests (covered in M3)

## Engineering Tasks

- [ ] Define fault-injection scenarios (minimum five):
  - FI-01: Ultrasonic sensor timeout (no reading for > 500 ms)
  - FI-02: Camera AI node process stop (SIGKILL or equivalent)
  - FI-03: All three ultrasonic sensors return out-of-range values simultaneously
  - FI-04: Malformed or invalid sensor message on ROS2 topic
  - FI-05: Heartbeat GPIO signal delayed beyond 500 ms timeout
- [ ] Document expected system response for each scenario against `docs/safety_concept.md`
- [ ] Implement or script each fault-injection procedure
- [ ] Execute each scenario and record actual system state and timing
- [ ] Measure safe-state transition latency for relevant scenarios (target < 150 ms)
- [ ] Record all results in `docs/logbook.md` with date, scenario ID, expected, actual, and pass/fail
- [ ] Write `tests/fault_injection/` test scripts or procedures
- [ ] Compile test report (`docs/fault_injection_report.md`)
- [ ] Update `requirements/traceability.csv` with fault-injection test links

## Acceptance Criteria

- [ ] At least five fault-injection scenarios are defined, executed, and documented
- [ ] Each scenario has a recorded expected outcome and actual outcome
- [ ] SAFE_STATE is entered within 150 ms of fault trigger for time-critical scenarios (FI-01, FI-05)
- [ ] Camera process stop (FI-02) results in DEGRADED state, not SAFE_STATE, per state machine rules
- [ ] Invalid sensor data (FI-04) is rejected without crashing the decision node
- [ ] All results are recorded in `docs/logbook.md` and summarized in `docs/fault_injection_report.md`
- [ ] No scenario results in undefined or undocumented system behavior
- [ ] `requirements/traceability.csv` links fault scenarios to requirements and safety mechanisms

## Related Requirements

- SYS-SAFE-001 (SAFE_STATE entry on heartbeat loss)
- SYS-SAFE-004 (DEGRADED state on AI node failure)
- SYS-PERF-003 (Safe state latency < 150 ms)
- SYS-SAFE-005 (Invalid input rejection)
- To be linked: fault detection and response requirements

## Related Documents

- `docs/safety_concept.md` (state machine and transition rules)
- `docs/ffi_argument.md` (FFI effectiveness analysis)
- `requirements/interfaces.yaml` (timing constraints)
- `requirements/traceability.csv`
- `docs/logbook.md`
- `tests/fault_injection/`

## Test Evidence

- `docs/fault_injection_report.md` with scenario table (ID, description, expected, actual, pass/fail)
- Logbook entries for each scenario execution
- Timing measurements for safe-state transition latency (log output or oscilloscope trace)
- `tests/fault_injection/` scripts or procedures that can be re-run

## Safety / AI Boundary

- AI agents may assist with test script scaffolding, scenario documentation, and report formatting.
- AI agents shall not determine pass/fail outcomes; the engineer must review and approve each result.
- Fault-injection scenarios must be defined against documented requirements, not inferred by an AI agent.
- This milestone does not claim certified fault coverage. The report shall state explicitly that this is a demonstrator-level fault-injection exercise.
- No ISO 26262 fault coverage metrics shall be claimed.

## Suggested Labels

`testing` `safety` `ros2` `python` `portfolio`

## Suggested Branch Name

`feature/m4-fault-injection`

## Suggested Commit Message

```
test: add fault injection scenarios and test report
```
