# Safety Requirements

## Disclaimer

This demonstrator implements ASIL-B-inspired safety requirements as an educational exercise. **This system is NOT ISO 26262 certified** and **NOT suitable for production use**.

## Hazard Analysis Summary

### Identified Hazards

**HAZ-001**: Unintended Vehicle Motion
- **Description**: Robot moves when it should stop, or moves in wrong direction
- **Severity**: S2 (Moderate - property damage, minor injury possible)
- **Controllability**: C2 (Normally controllable by operator)
- **Exposure**: E3 (Medium frequency in demonstration scenarios)
- **ASIL**: B (demonstrator uses ASIL-B-inspired measures)

**HAZ-002**: Collision with Obstacle
- **Description**: Robot fails to detect obstacle and collides
- **Severity**: S1 (Light - minor property damage)
- **Controllability**: C1 (Simple to control in demo environment)
- **Exposure**: E3 (Medium frequency)
- **ASIL**: A (covered by ASIL-B supervision)

## Safety Goals

**SG-001**: Prevent Unintended Motion
- The system shall prevent unintended motion by entering safe state on detected faults
- **ASIL**: B-inspired
- **Safe State**: Motors disabled, emergency brake applied
- **Fault Tolerance Time**: 150 ms (from fault detection to safe state)

**SG-002**: Detect Supervision Failure
- The system shall detect loss of supervision capability via watchdog mechanism
- **ASIL**: B-inspired
- **Detection Method**: Heartbeat timeout on independent supervisor

## Functional Safety Requirements

### FSR-001: Watchdog Monitoring

**Requirement**: The QNX supervisor shall monitor the Linux domain heartbeat signal.

**Details**:
- Heartbeat input: GPIO pin from Linux Health Monitor
- Expected frequency: 10 Hz ± 20%
- Timeout threshold: 500 ms
- Detection latency: <100 ms from timeout to detection

**Rationale**: Independent monitoring detects Linux domain failures (kernel panic, process crash, timing violation).

**ASIL**: B-inspired

**Verification**: Fault injection test - stop heartbeat, measure detection latency

### FSR-002: Safe State Transition

**Requirement**: On watchdog timeout or critical fault, the system shall transition to SAFE_STATE within 150 ms.

**Details**:
- Detection latency: <100 ms
- Decision latency: <20 ms (supervisor state machine)
- Actuation latency: <30 ms (GPIO emergency stop to motor disable)
- Total budget: 150 ms

**Rationale**: Bounded latency ensures hazard mitigation before collision at maximum speed (e.g., 1 m/s → 15 cm travel).

**ASIL**: B-inspired

**Verification**: End-to-end timing measurement with fault injection

### FSR-003: Deterministic Safety Logic

**Requirement**: Safety decisions shall be deterministic and rule-based. AI models shall NOT influence runtime safety decisions.

**Details**:
- Supervisor uses only: heartbeat timing, state enum, timeout thresholds
- No AI inference in QNX domain
- No neural network evaluation in safety path
- State machine transitions defined by lookup table

**Rationale**: AI outputs are unverified and non-deterministic. Safety decisions must be analyzable and predictable.

**ASIL**: B-inspired

**Verification**: Code review, static analysis, MISRA C compliance (subset)

### FSR-004: Spatial Isolation

**Requirement**: The QNX supervisor shall run on a physically separate processor from the Linux/ROS2 domain.

**Details**:
- Pi 5 hosts Linux/ROS2 (development domain)
- Pi 400 hosts QNX supervisor (safety monitoring domain)
- No shared memory within same address space
- GPIO and inter-board shared memory only

**Rationale**: FFI-inspired measure. Prevents memory corruption in Linux from affecting supervisor.

**ASIL**: B-inspired (architectural measure)

**Verification**: Deployment verification, fault injection (Linux kernel panic)

### FSR-005: Temporal Isolation

**Requirement**: Safety response latency shall not depend on Linux domain scheduling or AI inference time.

**Details**:
- Supervisor uses local monotonic clock
- Timeout evaluated independently of Linux timing
- QNX FIFO scheduling for supervisor threads (priority 250-255)

**Rationale**: FFI-inspired measure. Prevents timing interference from AI workload.

**ASIL**: B-inspired (architectural measure)

**Verification**: Timing measurement under Linux CPU stress test

### FSR-006: Communication Integrity

**Requirement**: Inter-processor communication shall include error detection and validation.

**Details**:
- Shared memory messages include CRC32 checksum
- Supervisor validates CRC before using data
- Invalid CRC treated as communication fault → SAFE_STATE
- Stale data detection via timestamp check

**Rationale**: Detect data corruption due to bit flips or software errors.

**ASIL**: B-inspired (safety mechanism)

**Verification**: Fault injection - corrupt shared memory, verify CRC detection

### FSR-007: Fail-Safe Default

**Requirement**: The system shall default to safe state (motors disabled) on startup and on any unhandled fault.

**Details**:
- Emergency stop GPIO asserted at supervisor boot
- Released only after valid heartbeat sequence observed
- Any unknown state or error code triggers SAFE_STATE

**Rationale**: Fail-safe design principle - prefer false positive over false negative.

**ASIL**: B-inspired (safety principle)

**Verification**: Power-on test, unknown state injection

### FSR-008: Single Point of Failure Analysis

**Requirement**: The system shall document single points of failure and their mitigation or acceptance.

**Known SPOFs**:
- GPIO wiring between boards (no redundancy) - **Accepted** for demo
- Common power supply (no dual PSU) - **Accepted** for demo
- QNX supervisor processor (no redundant supervisor) - **Accepted** for demo

**Mitigation**:
- Fail-safe defaults minimize hazard on SPOF failure
- Demonstration environment allows operator intervention

**Rationale**: Complete fault tolerance not required for demonstrator. SPOFs documented for honesty.

**ASIL**: N/A (informational)

**Verification**: Design review, FMEA (simplified)

## Safety Mechanisms

### SM-001: Watchdog Timer

**Type**: Detection mechanism for temporal faults

**Implementation**: QNX supervisor monitors GPIO heartbeat, timeout = 500 ms

**Fault Coverage**: Linux kernel panic, process hang, timing violation, power loss on Linux board

**Diagnostic Coverage**: High (>99% for covered faults)

**Limitation**: Does not detect "babbling idiot" if heartbeat continues but system is malfunctioning

### SM-002: CRC Integrity Check

**Type**: Detection mechanism for data corruption

**Implementation**: CRC32 checksum on shared memory messages

**Fault Coverage**: Bit flips, memory corruption, software write errors

**Diagnostic Coverage**: >99.999% (Hamming distance of CRC32)

**Limitation**: Does not detect malicious tampering (no cryptographic authentication)

### SM-003: State Consistency Check

**Type**: Detection mechanism for invalid states

**Implementation**: Supervisor validates state enum against allowed values

**Fault Coverage**: Software errors leading to invalid state, undefined behavior

**Diagnostic Coverage**: 100% for out-of-range enum values

### SM-004: Emergency Stop Override

**Type**: Actuation mechanism for safe state enforcement

**Implementation**: QNX supervisor directly controls emergency stop GPIO, bypasses Linux domain

**Fault Coverage**: Any Linux domain failure, ensures safe state achievable

**Diagnostic Coverage**: N/A (actuation, not detection)

## Safety Requirements Allocation

| Requirement | Allocated to | Implementation |
|-------------|--------------|----------------|
| FSR-001 | QNX Watchdog Server | GPIO monitoring, timeout detection |
| FSR-002 | QNX Safe State Controller | Emergency stop GPIO assertion |
| FSR-003 | QNX domain (both components) | No AI libraries, rule-based code |
| FSR-004 | System architecture | Dual processor deployment |
| FSR-005 | QNX domain | Local clock, FIFO scheduling |
| FSR-006 | Both domains | CRC generation (Linux), validation (QNX) |
| FSR-007 | QNX Safe State Controller | Default GPIO state at boot |
| FSR-008 | Documentation | FMEA, design review |

## ASIL Decomposition

This demonstrator uses ASIL-B-inspired measures without formal decomposition. For reference, typical decomposition would be:

**Function**: Prevent Unintended Motion (ASIL B)

**Decomposition**:
- **Path 1** (ASIL B): Watchdog supervision on QNX domain
  - FSR-001, FSR-002, FSR-003, FSR-004, FSR-005 fully implemented

- **Path 2** (QM): AI perception on Linux domain
  - No ASIL requirements, development quality only

**Independence**: Physical processor separation, different OS, separate power-on self-test

**Rationale**: If Path 1 detects Path 2 failure, ASIL B goal achieved

## Safety Validation Plan

### Fault Injection Tests

**FI-001**: Heartbeat Stop
- Stop Health Monitor process
- Verify watchdog timeout detection <500 ms
- Verify safe state transition <150 ms

**FI-002**: Heartbeat Corruption
- Send invalid heartbeat pattern (stuck-at-high)
- Verify timeout detection (no edge transitions)

**FI-003**: Shared Memory Corruption
- Flip bits in CRC field
- Verify supervisor detects invalid CRC
- Verify safe state transition

**FI-004**: Linux Kernel Panic
- Trigger kernel oops or panic via module
- Verify heartbeat stops
- Verify safe state transition

**FI-005**: Supervisor CPU Starvation
- Launch CPU stress on QNX domain
- Verify supervisor cycle time remains <12 ms
- Verify safety latency within budget

### Timing Analysis Tests

**TA-001**: End-to-End Latency
- Measure heartbeat stop to motor disable
- Verify <150 ms at 95th percentile

**TA-002**: Supervisor Cycle Time
- Measure watchdog server cycle time over 1 hour
- Verify 10 ms ± 1 ms, no outliers >12 ms

**TA-003**: Interference Test
- Run AI inference at maximum load on Linux
- Verify no impact on QNX supervisor timing

### Functional Tests

**FT-001**: Startup Sequence
- Power on system, verify safe state default
- Verify heartbeat required before operation enabled

**FT-002**: State Transitions
- Exercise all state transitions: NORMAL → WARNING → DEGRADED → SAFE_STATE
- Verify state machine behavior per specification

**FT-003**: Manual Reset
- Enter SAFE_STATE, verify manual reset required
- Verify system does not auto-recover from safe state

## Compliance Statement

This demonstrator is **NOT** compliant with ISO 26262:2018 for the following reasons:

- Development process does not follow V-model with safety assessments
- No independent safety audits or functional safety assessments
- Tools (compiler, OS, libraries) not qualified per ISO 26262-8
- Hardware not qualified (no redundancy, no ECC memory, no lockstep cores)
- Quantitative safety analysis not performed (FIT rates, PMHF)

This demonstrator **DOES** implement technical measures inspired by ASIL B:

- Independent safety monitor with deterministic logic
- FFI-inspired architectural measures (spatial, temporal isolation)
- Safety mechanisms with diagnostic coverage
- Fault injection testing strategy

## References

- ISO 26262:2018 Part 3 Clause 6 (Hazard analysis and risk assessment)
- ISO 26262:2018 Part 6 Clause 7 (Architectural design)
- IEC 61508-2:2010 Clause 7.4 (Software safety requirements)
- MISRA C:2012 (Coding standard, partial compliance)
