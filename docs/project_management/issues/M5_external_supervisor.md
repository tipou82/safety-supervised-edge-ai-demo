# M5: External Supervisor

## Goal

Implement or prototype the Raspberry Pi 400 supervisor concept, demonstrating watchdog-based heartbeat monitoring and emergency-stop assertion. If QNX 7.1 is unavailable or blocks progress, a Linux PREEMPT_RT fallback shall be documented and used honestly.

## Scope

- Supervisor implementation on Raspberry Pi 400 (QNX 7.1 target, Linux PREEMPT_RT fallback)
- Watchdog server monitoring heartbeat GPIO from Pi 5 (GPIO 17 in)
- Emergency-stop assertion on timeout (GPIO out, active-low, asserted at boot)
- Watchdog cycle: 10 ms ±1 ms
- Heartbeat timeout threshold: 500 ms
- Safe-state control at FIFO priority 255 (QNX) or equivalent high-priority thread (Linux)
- Honest documentation of whether QNX or Linux fallback was used
- Inter-processor wiring verification against `hardware/wiring.md`

## Out of Scope

- Claiming certified QNX safety behavior or RTOS certification
- Relying on QNX as a hard prerequisite if it blocks Pi 5 demonstration progress
- Shared memory implementation beyond what is defined in `requirements/interfaces.yaml`
- Any AI or LLM involvement in supervisor logic

## Engineering Tasks

- [ ] Confirm hardware: Raspberry Pi 400 with GPIO access and QNX or Linux OS
- [ ] Document OS selection decision in `docs/logbook.md` (QNX attempted / Linux fallback used)
- [ ] Implement `watchdog_server` (or Linux equivalent) monitoring heartbeat GPIO at 10 ms cycle
- [ ] Implement `safe_state_ctrl` (or Linux equivalent) asserting e-stop GPIO on timeout
- [ ] Set watchdog thread priority (FIFO 250 for watchdog, FIFO 255 for safe-state control)
- [ ] Verify e-stop GPIO is asserted at boot (fail-safe default)
- [ ] Verify e-stop GPIO is de-asserted only after valid heartbeat is received
- [ ] Measure watchdog cycle jitter and record in logbook (target ≤ 1 ms)
- [ ] Measure heartbeat-to-e-stop latency end-to-end (target < 150 ms total)
- [ ] Update `docs/qnx_supervisor.md` with actual implementation notes
- [ ] Update `hardware/wiring.md` if inter-processor wiring deviates from the plan
- [ ] Update `requirements/traceability.csv` with supervisor → requirement links

## Acceptance Criteria

- [ ] Watchdog server is running and monitoring heartbeat GPIO at 10 ms cycle
- [ ] E-stop GPIO is asserted at boot before first valid heartbeat
- [ ] E-stop GPIO is de-asserted after valid heartbeat is received from Pi 5
- [ ] E-stop GPIO is re-asserted within 150 ms of heartbeat loss (end-to-end)
- [ ] Watchdog cycle jitter is measured and documented (pass: ≤ 1 ms, or deviation noted)
- [ ] OS selection (QNX or Linux fallback) is documented honestly in `docs/qnx_supervisor.md`
- [ ] If Linux fallback was used, this is stated explicitly — no QNX is claimed
- [ ] Inter-processor GPIO wiring is verified against `hardware/wiring.md`

## Related Requirements

- SYS-SUP-001 (Watchdog cycle 10 ms ±1 ms)
- SYS-SUP-002 (E-stop asserted at boot, fail-safe default)
- SYS-SAFE-001 (SAFE_STATE entry on heartbeat loss)
- SYS-PERF-003 (Safe state latency < 150 ms total)
- SYS-COMM-001 (Heartbeat GPIO protocol, 10 Hz ±20%)

## Related Documents

- `docs/qnx_supervisor.md`
- `hardware/wiring.md`
- `hardware/gpio_mapping.md`
- `requirements/interfaces.yaml`
- `requirements/traceability.csv`
- `docs/logbook.md`

## Test Evidence

- Logbook entry confirming OS selection and rationale
- Oscilloscope or logic analyzer trace showing e-stop assertion at boot
- Timing measurement: heartbeat loss → e-stop assertion latency
- Watchdog cycle jitter measurement (log output or trace)
- `docs/qnx_supervisor.md` updated with actual implementation status

## Safety / AI Boundary

- AI agents may assist with supervisor code scaffolding, documentation, and timing analysis.
- AI agents shall not make decisions about whether QNX or Linux is sufficient for the demonstrator; this is an engineering judgment by the project owner.
- The supervisor implements deterministic rule-based logic only: heartbeat present → hold e-stop released; heartbeat absent → assert e-stop.
- No AI inference, LLM calls, or probabilistic logic shall appear in the supervisor.
- The supervisor shall be described as "ASIL-B-inspired watchdog demonstrator" in all documentation, not as a certified safety monitor.
- QNX shall be described as "planned", "attempted", or "prototyped" unless it is confirmed running on target hardware.

## Suggested Labels

`qnx` `cplusplus` `hardware` `safety` `portfolio`

## Suggested Branch Name

`feature/m5-external-supervisor`

## Suggested Commit Message

```
feat: add QNX supervisor watchdog prototype (or Linux fallback)
```
