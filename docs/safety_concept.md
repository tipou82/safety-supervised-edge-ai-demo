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

### 1. Watchdog Monitoring

**Implementation**: GPIO-based heartbeat from Health Monitor to Watchdog Server.

**Timeout Threshold**: 500 ms (configurable based on system timing analysis).

**Action on Timeout**: Immediate transition to SAFE_STATE with motor disable.

### 2. Plausibility Checking

**Sensor Fusion**: Compare camera AI detections with ultrasonic measurements.

**Range Checks**: Validate sensor values within physical bounds (e.g., ultrasonic 2cm - 400cm).

**Consistency**: Detect conflicting sensor interpretations.

### 3. Heartbeat Pattern Validation

**Not just presence**: Supervisor checks heartbeat timing consistency.

**Jitter Tolerance**: ±20% of nominal period acceptable in NORMAL state.

**Pattern Analysis**: Detect stuck-at faults (constant high or low GPIO).

### 4. Safe State Enforcement

**Hardware Override**: Supervisor has direct GPIO connection to motor enable line.

**Independence**: Safe state mechanism does not rely on Linux kernel or ROS2.

**Fail-Safe**: System defaults to safe state on power loss or supervisor fault.

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
