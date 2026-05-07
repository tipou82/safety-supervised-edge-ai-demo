# System Requirements

## Scope

This document defines the system-level requirements for the Safety-Supervised Edge AI Demonstrator. Requirements are tagged for traceability to design and test.

## Functional Requirements

### Perception and Sensing

**SYS-FUNC-001**: Camera Perception
- The system shall capture images at minimum 10 Hz frame rate
- The system shall perform object detection using YOLOv8 or MobileNet
- The system shall publish detection results with bounding boxes and confidence scores
- **Priority**: Medium (development domain, not safety-critical)

**SYS-FUNC-002**: Ultrasonic Sensing
- The system shall provide ultrasonic distance measurements from 1 Grove Ultrasonic Ranger sensor
- The system shall detect obstacles in the range 2 cm to 350 cm
- The system shall publish obstacle data at minimum 10 Hz
- **Priority**: High (provides redundant perception)
- **Hardware note**: Single sensor (front-facing). Multi-sensor configuration deferred.

**SYS-FUNC-003**: Sensor Fusion
- The system shall compare camera detections with ultrasonic measurements
- The system shall detect conflicting sensor interpretations
- **Priority**: Medium

### Decision and Control

**SYS-FUNC-004**: Path Planning
- The system shall generate velocity commands based on perception inputs
- The system shall implement obstacle avoidance logic
- **Priority**: Medium

**SYS-FUNC-005**: Actuator Control
- The system shall convert velocity commands to motor PWM signals
- The system shall provide emergency stop capability via GPIO override
- **Priority**: High (safety-relevant interface)
- **Hardware note**: Motor driver and DC motors not present in current hardware build. GPIO pins reserved. Deferred to future milestone.

### Safety Supervision

**SYS-FUNC-006**: Q&A Watchdog Servicing (Pi5)
- The Pi5 health_node shall act as I2C master (GPIO 2/3) and service the Pi400 Q&A watchdog
- The health_node shall read the seed from Pi400 I2C register `0x00`, compute `response = seed XOR 0xA5A5A5A5`, and write to register `0x01`
- The response shall be sent within the open window: 50–100 ms after the last correctly acknowledged response
- **Priority**: Critical (safety-critical function)

**SYS-FUNC-007**: Q&A Watchdog Monitoring (Pi400)
- The Pi400 supervisor shall operate as I2C slave at address `0x40` (GPIO 2/3)
- The supervisor shall generate a new 32-bit random seed each watchdog cycle
- The supervisor shall validate each Pi5 response: value AND timing (50–100 ms window)
- failure_counter: +1 on wrong answer, too early, or timeout; −1 after 2 consecutive correct (min 0)
- The supervisor shall trigger SAFE_STATE when failure_counter ≥ 3
- **Priority**: Critical (safety-critical function)

**SYS-FUNC-008**: Safe State Enforcement
- The system shall transition to SAFE_STATE on watchdog timeout
- The system shall disable motor outputs in SAFE_STATE
- The system shall require manual reset to exit SAFE_STATE
- **Priority**: Critical (safety-critical function)

## Safety Requirements

### Architectural Safety

**SYS-SAFE-001**: AI Independence
- AI inference shall NOT be part of the runtime safety decision path
- Safety decisions shall be made by deterministic, rule-based logic only
- **Rationale**: AI outputs are unverified, cannot be trusted for safety decisions
- **ASIL**: B-inspired

**SYS-SAFE-002**: Spatial Independence
- Linux/ROS2 domain shall run on separate processor from QNX supervisor
- Memory corruption in Linux shall not affect QNX supervisor
- **Rationale**: FFI-inspired measure for spatial isolation
- **ASIL**: B-inspired

**SYS-SAFE-003**: Temporal Independence
- Safety decisions shall use QNX supervisor's local clock
- AI inference delays shall not affect safety response latency
- **Rationale**: FFI-inspired measure for temporal isolation
- **ASIL**: B-inspired

### Safety Mechanisms

**SYS-SAFE-004**: Q&A Watchdog Window Compliance
- The Pi5 shall send a correct response within the open window: 50 ms ≤ elapsed ≤ 100 ms after last acknowledged response
- Responses outside this window shall increment the failure counter, regardless of answer correctness
- The Pi400 shall use a monotonic clock for all window timing
- **Rationale**: Window enforcement detects both frozen processes (timeout) and scheduling anomalies (too early)
- **ASIL**: B-inspired

**SYS-SAFE-004a**: Q&A Watchdog Failure Counter
- failure_counter shall be incremented by 1 on any: incorrect response value, response before open window, or response after close window (timeout)
- failure_counter shall be decremented by 1 after 2 consecutive correct in-window responses (minimum value: 0)
- SAFE_STATE shall be triggered when failure_counter ≥ 3
- **Rationale**: Counter-based logic tolerates transient I2C glitches while detecting persistent failures
- **ASIL**: B-inspired

**SYS-SAFE-005**: Communication Validation
- Shared memory communication shall include CRC32 integrity check
- Invalid CRC shall trigger safe state transition
- **Rationale**: Detect data corruption in inter-processor communication
- **ASIL**: B-inspired

**SYS-SAFE-006**: Safe State Latency
- Time from watchdog window timeout (failure_counter reaching 3) to motor disable shall be <150 ms
- Safe state enforcement shall not depend on Linux cooperation
- Pi400 shall assert GPIO 25 LOW and illuminate red LED (GPIO 22) independently of Pi5
- **Rationale**: Bounded latency for hazard mitigation
- **ASIL**: B-inspired

**SYS-SAFE-009**: State LED Indicators
- Green LED (Pi5 GPIO 17): shall be illuminated in NORMAL state
- Yellow LED (Pi5 GPIO 27): shall be illuminated in DEGRADED state (one of two sensor paths unreliable)
- Red LED (wired-OR: Pi5 GPIO 22 / Pi400 GPIO 22): shall be illuminated in SAFE_STATE
- Pi400 shall be able to assert the red LED independently of Pi5
- **Priority**: High

**SYS-SAFE-010**: Emergency Stop GPIO
- Emergency stop shall use GPIO 25: Pi400 GPIO 25 (Pin 22) output → Pi5 GPIO 25 (Pin 22) input
- Signal shall be active-low (0V = emergency stop active)
- Default state at Pi400 boot: LOW (asserted — fail-safe)
- **ASIL**: B-inspired

### State Management

**SYS-SAFE-007**: State Machine
- System shall implement states: INIT, NORMAL, WARNING, DEGRADED, SAFE_STATE
- All state transitions shall be deterministic and rule-based
- State transition rules shall be evaluated at 10 ms cycle time
- **ASIL**: B-inspired

**SYS-SAFE-008**: Degradation Management
- System shall reduce velocity limits in WARNING state (50% nominal)
- System shall operate on ultrasonic-only in DEGRADED state (20% nominal)
- **Rationale**: Graceful degradation reduces hazard severity

## Performance Requirements

**SYS-PERF-001**: Latency
- End-to-end latency from sensor input to actuator output shall be <200 ms (NORMAL state)
- Supervisor cycle time shall be 10 ms ± 1 ms

**SYS-PERF-002**: Throughput
- Camera AI node shall process minimum 10 frames per second
- ROS2 message queue shall not exceed 100 ms latency

**SYS-PERF-003**: Resource Utilization
- Supervisor CPU utilization shall be <10% (leaving margin for fault handling)
- Linux domain shall reserve 1 CPU core for real-time tasks

## Interface Requirements

**SYS-IF-001**: I2C Q&A Watchdog Interface
- I2C bus shall use GPIO 2 (SDA) and GPIO 3 (SCL) on both Pi5 and Pi400
- Pi5 shall be I2C master; Pi400 shall be I2C slave at address `0x40`
- Bus speed: 100 kHz; external 4.7 kΩ pull-ups to 3.3V on SDA and SCL
- Seed register: `0x00` (Pi400 write, Pi5 read, uint32_t)
- Response register: `0x01` (Pi5 write, Pi400 validate, uint32_t)
- Response algorithm: `response = seed XOR 0xA5A5A5A5`

**SYS-IF-002**: Emergency Stop GPIO
- Emergency stop shall use Pi400 GPIO 25 (Pin 22) → Pi5 GPIO 25 (Pin 22)
- Signal shall be active-low (0V = emergency stop active)
- Actuator node shall check emergency stop at 100 Hz
- Pi5 GPIO 25 shall have internal pull-up enabled

**SYS-IF-003**: Shared Memory
- Shared memory region shall be 4 KB, page-aligned
- Structure: magic number, state enum, heartbeat count, timestamp, CRC32
- Write access: Linux domain only; Read access: QNX domain only

**SYS-IF-004**: ROS2 Topics
- See [interfaces.yaml](interfaces.yaml) for detailed topic specifications

## Operational Requirements

**SYS-OPS-001**: Startup Sequence
- QNX supervisor shall boot first and assert emergency stop
- Linux domain shall complete ROS2 node bringup
- Health monitor shall start heartbeat after all nodes ready
- Supervisor shall release emergency stop after 10 consecutive valid heartbeats

**SYS-OPS-002**: Shutdown Sequence
- Graceful shutdown: Health monitor stops heartbeat
- Supervisor transitions to SAFE_STATE after timeout
- Motors disabled before system power down

**SYS-OPS-003**: Manual Reset
- Safe state exit shall require operator confirmation (e.g., button press)
- System shall perform self-test before returning to NORMAL state

## Environmental Requirements

**SYS-ENV-001**: Operating Conditions
- Temperature range: 0°C to 50°C (demonstration environment)
- Humidity: 10% to 80% non-condensing
- **Note**: Not qualified for automotive environmental conditions

**SYS-ENV-002**: Power Supply
- 5V power supply for both Raspberry Pi boards
- Power interruption shall trigger safe state (no UPS in this demo)

## Constraints and Assumptions

**SYS-CON-001**: Hardware Platform
- Raspberry Pi 5 (Linux domain) with 8 GB RAM minimum
- Raspberry Pi 400 (QNX domain, or Linux fallback)
- GPIO connectivity between boards required

**SYS-CON-002**: Software Platform
- Linux: Ubuntu 22.04, ROS2 Humble
- QNX: QNX 7.1 or Linux with PREEMPT_RT kernel (fallback)

**SYS-ASM-001**: Development Demonstrator
- This system is NOT certified to ISO 26262
- This system is NOT suitable for production use
- GPIO wiring is NOT redundant (single point of failure)

**SYS-ASM-002**: Fault Coverage
- Single faults considered (Linux domain failure, single sensor failure)
- Multiple simultaneous faults NOT covered in this demo
- Common-cause failures (power supply, GPIO hardware) NOT mitigated

## Traceability

All requirements shall be traced to:
- Design elements in architecture.md
- Test cases in tests/ directory
- SysML model elements in docs/sysml/architecture.sysml

See [traceability.csv](traceability.csv) for complete traceability matrix.

## Verification Strategy

| Requirement Type | Verification Method |
|------------------|---------------------|
| Functional | Integration test, demonstration |
| Safety | Fault injection, timing analysis |
| Performance | Measurement under load |
| Interface | Protocol compliance test |

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-05-05 | Initial | First draft, repository initialization |
