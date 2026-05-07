# Safety Concept

## Disclaimer

This is an educational demonstrator showcasing ASIL-B-inspired monitoring patterns. This system is **NOT** ISO 26262 certified and is **NOT** suitable for production safety-critical applications.

## Safety Philosophy

**Core Principle**: AI-based perception operates in the development domain. Runtime safety decisions are made by deterministic, rule-based logic on an independent supervisor.

**Key Insight**: We do not claim the AI is safe. We demonstrate architectural measures to detect and mitigate AI failures through independent monitoring.

## System States

The system operates in four distinct states, managed by the QNX-inspired supervisor.

### NORMAL State

**Definition**: All nodes operational, sensors healthy, watchdog receiving regular heartbeats.

**Characteristics**:
- Camera AI node publishing detections at expected rate
- Ultrasonic sensors providing valid distance measurements
- Health monitor heartbeat within timing bounds (e.g., 90-110 ms period for 10 Hz)
- No active faults or warnings

**Allowed Operations**:
- Full autonomous operation
- AI-based decision making in development domain
- Normal velocity commands to actuators

**Transition to WARNING**: Sensor data quality degraded, but safety-relevant functions still operational.

### WARNING State

**Definition**: Degraded sensing or minor faults detected, but system can continue with reduced functionality.

**Characteristics**:
- One sensor stream degraded (e.g., camera occlusion detected, ultrasonic timeout)
- Heartbeat jitter increased but within tolerance
- Non-critical ROS2 node failure

**Allowed Operations**:
- Reduced velocity limits (e.g., 50% max speed)
- Continued operation with redundant sensors
- Warning indication to operator

**Transition to NORMAL**: Fault cleared, sensor streams restored.

**Transition to DEGRADED**: Additional faults accumulate, primary perception path lost.

### DEGRADED State

**Definition**: Primary perception (AI) failed, but redundant sensing allows limited safe operation.

**Characteristics**:
- Camera AI node failure or timeout
- Operating on ultrasonic sensors only (short-range obstacle avoidance)
- Heartbeat present but system health degraded

**Allowed Operations**:
- Very low speed operation (e.g., 20% max speed, <0.5 m/s)
- Simple obstacle avoidance only
- No complex path planning
- Manual control recommended

**Transition to WARNING**: Camera AI node recovered.

**Transition to SAFE_STATE**: Watchdog timeout, all sensor failures, or operator command.

### SAFE_STATE

**Definition**: System halted in a safe configuration. All autonomous functions disabled.

**Characteristics**:
- Motors disabled (PWM outputs set to neutral/brake)
- Watchdog timeout exceeded (e.g., >500 ms since last heartbeat)
- Critical fault detected by supervisor
- Manual emergency stop activated

**Allowed Operations**:
- None (system halted)
- Emergency brake applied
- Status reporting only

**Transition to INIT**: Manual reset required after fault analysis.

## State Transition Rules

All state transitions are evaluated by the QNX-inspired supervisor using deterministic rules.

| Current State | Condition | Next State | Latency Requirement |
|---------------|-----------|------------|---------------------|
| NORMAL | Sensor timeout OR heartbeat jitter | WARNING | <50 ms |
| NORMAL | Watchdog timeout | SAFE_STATE | <100 ms |
| WARNING | Fault cleared | NORMAL | <200 ms |
| WARNING | Additional sensor fault | DEGRADED | <50 ms |
| WARNING | Watchdog timeout | SAFE_STATE | <100 ms |
| DEGRADED | AI node recovered | WARNING | <200 ms |
| DEGRADED | Watchdog timeout OR operator cmd | SAFE_STATE | <100 ms |
| SAFE_STATE | Manual reset | INIT | N/A |

## Safety Mechanisms

### 1. Q&A Watchdog Monitoring

**Implementation**: I2C challenge/response protocol between Pi5 (master) and Pi400 (slave at `0x40`).

**Protocol**:
1. Pi400 generates a new 32-bit random seed each cycle (register `0x00`).
2. Pi5 reads the seed via I2C, computes `response = seed XOR 0xA5A5A5A5`, and writes it back to register `0x01`.
3. Pi400 validates both the response value and its arrival time.

**Timing Window**:

| Window zone | Time since last correct response | Pi400 action |
|---|---|---|
| Closed (too early) | < 50 ms | failure_counter++ |
| Open (valid) | 50–100 ms | Validate answer |
| Timeout (too late) | > 100 ms | failure_counter++ |

**Failure Counter Rules**:
- Correct response in open window: no increment; after **2 consecutive** correct → failure_counter -= 1 (min 0)
- Any failure (wrong answer, too early, too late): failure_counter += 1
- failure_counter ≥ 3 → **SAFE_STATE**: Pi400 asserts emergency stop GPIO 25 LOW and illuminates red LED

**Diagnostic Advantage Over Simple GPIO Heartbeat**: A frozen or corrupted Linux process cannot generate a correct in-window response; a simple GPIO toggle could be maintained by a stuck-at oscillator with no software participation.

### 2. Plausibility Checking

**Sensor Fusion**: Compare camera AI detections with ultrasonic measurements.

**Range Checks**: Validate sensor values within physical bounds (e.g., ultrasonic 2cm - 400cm).

**Consistency**: Detect conflicting sensor interpretations.

### 3. Q&A Response Validation

**Not just timing**: Pi400 validates both the response value (`seed XOR 0xA5A5A5A5`) and its arrival within the open window (50–100 ms).

**Stuck-at detection**: A frozen Pi5 cannot compute a valid response — the process must be running and able to perform the XOR computation.

**Window enforcement**: Responses outside the 50–100 ms window increment the failure counter regardless of answer correctness. This detects scheduling pathologies on the Pi5.

### 4. Safe State Enforcement

**Hardware Override**: Pi400 asserts GPIO 25 LOW (active-low e-stop) to Pi5 GPIO 25. Pi5 actuator_node polls this at 100 Hz and disables motors within 30 ms.

**Red LED**: Pi400 drives GPIO 22 HIGH through 1N4148 diode to illuminate the red LED independently of Pi5.

**Independence**: Safe state mechanism does not rely on Linux kernel or ROS2.

**Fail-Safe**: GPIO 25 is asserted LOW at Pi400 boot and released only after watchdog establishes NORMAL state.

### 5. System State LED Indicators

| LED | Colour | Driven by | Condition |
|---|---|---|---|
| Green | GPIO 17 (Pi5) | health_node | NORMAL state |
| Yellow | GPIO 27 (Pi5) | health_node | DEGRADED mode (only one sensor path reliable) |
| Red | GPIO 22 (Pi5 OR Pi400, wired-OR) | actuator_node / safe_state_ctrl | SAFE STATE |

**DEGRADED definition**: Of the two sensor paths (camera AI and ultrasonic), only one is reliable. The system continues at 20% nominal velocity using ultrasonic-only obstacle avoidance.

## Fault Handling

### Transient Faults

**Example**: Momentary camera occlusion, single ultrasonic timeout.

**Response**: Log fault, continue operation in WARNING state if within tolerance.

**Recovery**: Automatic return to NORMAL when fault clears.

### Persistent Faults

**Example**: Camera AI node crash, repeated watchdog timeouts.

**Response**: Transition to DEGRADED or SAFE_STATE based on severity.

**Recovery**: Requires manual intervention and fault analysis.

### Systematic Faults

**Example**: Software bug causing consistent incorrect behavior.

**Mitigation**: Design diversity (independent supervisor), extensive testing, fault injection.

**Detection**: Plausibility checking, state consistency validation.

## Safety Integrity

### ASIL-B-Inspired Measures

This demonstrator implements architectural patterns inspired by ASIL-B requirements:

- **Independence**: Separate safety monitor on independent processor
- **Determinism**: Safety decisions are rule-based, not AI-based
- **Timing**: Bounded latency for safety-critical transitions
- **Testing**: Fault injection test suite planned

### What is NOT Claimed

- ISO 26262 certification (requires full process compliance)
- Quantified safety metrics (e.g., probabilistic failure rates)
- Production-ready software (this is a demonstrator)
- Tool qualification (compilers, static analyzers not qualified)

## Diagnostic Coverage

### Faults Detected

- Watchdog timeout (Linux domain failure)
- Sensor value out of range
- Heartbeat pattern anomaly
- ROS2 node crash
- Communication loss

### Faults NOT Detected

- AI perception errors within plausible range (limitation of demonstration)
- Subtle sensor degradation without timeout
- Cosmic ray bit flips (no ECC RAM in Raspberry Pi)

## References

- ISO 26262:2018 Part 3 (Concept Phase), Part 6 Clause 7 (Architectural Design)
- IEC 61508-2 Clause 7.4 (Safety-related software)
- MISRA C:2012 (Coding guidelines for safety-related C)
