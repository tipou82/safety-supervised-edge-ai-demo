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
- The system shall convert velocity commands to motor PWM signals via `velocity_scale` (0.0–1.0)
- The system shall provide emergency stop capability via GPIO override (GPIO 25, active-low)
- The actuator node shall drive DRV8833 IN1 (GPIO 12) and IN2 (GPIO 16) with 3.3 V logic signals only
- The motor supply (DRV8833 VCC) shall be provided by the 4×AA battery box via Motor Switch — never from Raspberry Pi GPIO
- **Priority**: High (safety-relevant interface)

**SYS-FUNC-009**: Main Switch — Shared Power-Up Concept
- Both Raspberry Pi 5 and Raspberry Pi 400 shall be powered through the same shared power strip
- The power strip shall have one Main Switch that powers both boards simultaneously
- When the Main Switch is ON, both Pi5 and Pi400 shall boot without software intervention
- When the Main Switch is OFF, both boards shall power down simultaneously
- **Priority**: High (operational concept)

**SYS-FUNC-010**: Motor Switch — Separate Motor Supply
- The DRV8833 motor driver shall be powered by a separate 4×AA battery box
- The battery box shall have its own Motor Switch (independent of the Main Switch)
- Motor Switch ON: motor supply available to DRV8833; motor may rotate if software state allows
- Motor Switch OFF: motor supply removed; motor shall not rotate regardless of software state
- Pi5 GND, DRV8833 GND, and 4×AA battery negative shall share a common ground reference
- **Priority**: High (hardware safety measure)

**SYS-FUNC-011**: Boot Default — Motor Off
- The default `velocity_scale` at system boot shall be 0.0 (motor stopped)
- The motor command shall remain zero until the system successfully releases to NORMAL state
- No motor motion shall occur during BOOTING / INIT state, regardless of Motor Switch position
- **Priority**: Critical (prevents unintended motion during startup)

### Safety Supervision

**SYS-FUNC-006**: Q&A Watchdog Servicing (Pi5)
- The Pi5 health_node shall act as I2C master (GPIO 2/3) and service the Pi400 Q&A watchdog
- The health_node shall read the seed from Pi400 I2C register `0x00`, compute `response = seed XOR 0xA5A5A5A5`, and write to register `0x01`
- The response shall be sent within the open window: 50–100 ms after the last correctly acknowledged response
- **Priority**: Critical (safety-critical function)

**SYS-FUNC-007**: Q&A Watchdog Monitoring (Pi400)
- The Pi400 supervisor shall operate as a UDP server on port 9001 over dedicated Ethernet
- The supervisor shall generate a new 32-bit random seed each watchdog cycle
- The supervisor shall validate each Pi5 response: value AND timing (30ms window, 15ms closed + 15ms open)
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
- Window: 30ms total — 15ms closed (too early) + 15ms open (valid)
- The Pi5 shall send a correct response within the open window: 15 ms ≤ elapsed ≤ 30 ms from seed receipt
- Responses before 15ms (closed window) shall increment the failure counter
- No response by 30ms (timeout) shall increment the failure counter
- The Pi400 shall use a monotonic clock for all window timing
- Pi5 health_node cycles at 20ms — response at ~20ms ∈ [15ms, 30ms] ✓
- health_node UDP thread socket timeout 5ms — ensures pending seed checked within open window
- **Rationale**: 15ms closed window prevents spurious early responses; 20ms health_node cycle lands at centre of open window
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
- Time from first watchdog failure to motor disable shall be <150 ms
- Breakdown: 3 × 30ms window + 20ms GPIO + 10ms poll + 30ms motor = 150ms worst case
- Safe state enforcement shall not depend on Linux cooperation
- Pi400 shall assert GPIO 25 LOW and illuminate red LED (GPIO 22) independently of Pi5
- **Rationale**: Bounded latency for hazard mitigation. 30ms window × 3 = 90ms detection.
- **ASIL**: B-inspired

**SYS-SAFE-009**: State LED Indicators
- Green LED (Pi5 GPIO 17): shall be illuminated in INIT and NORMAL states only; OFF in WARNING, DEGRADED, SAFE_STATE
- Yellow LED (Pi5 GPIO 27): shall be illuminated in WARNING and DEGRADED states; OFF in INIT, NORMAL, SAFE_STATE
- Red LED (wired-OR: Pi5 GPIO 22 / Pi400 GPIO 22): shall be illuminated in SAFE_STATE
- Pi400 shall be able to assert the red LED independently of Pi5
- **Priority**: High

**SYS-SAFE-013**: Startup Release Criterion
- The system shall not release to NORMAL state unless all of the following are satisfied simultaneously:
  (a) Pi400 Q&A watchdog failure_counter < 3 (watchdog communication healthy),
  (b) All required ROS2 application nodes on Pi5 are alive (health_node flow check passes),
  (c) Ultrasonic sensor validity check passes (data received within validity timeout)
- If startup criteria are not met, the system shall enter SAFE_STATE directly
- **Priority**: Critical (prevents unintended motion on incomplete startup)
- **ASIL**: B-inspired

**SYS-SAFE-014**: Safe State Motor Override
- In SAFE_STATE, the actuator node shall force `velocity_scale = 0.0` regardless of any incoming velocity command
- In SAFE_STATE, the actuator node shall de-assert PWM on DRV8833 IN1 and IN2 (both LOW)
- Safe State has priority over any `velocity_scale` command from the decision node
- **Priority**: Critical
- **ASIL**: B-inspired

**SYS-SAFE-012**: Camera-Based Hand Distance — Supplementary SAFE_STATE Trigger
- When `camera_valid=true` AND camera-estimated hand distance < 0.20m, the system shall enter SAFE_STATE
- Camera distance is estimated using the pinhole model: `distance = (hand_width × focal_length) / bbox_width_px`
- This is an AI-derived measurement (depends on MediaPipe bounding box) with ±30% accuracy
- Threshold 0.20m provides wider margin than ultrasonic SAFE_DISTANCE (0.15m) to account for lower accuracy
- This is a **supplementary** trigger — it does NOT replace the ultrasonic safety path (SYS-SAFE-011)
- **Requires calibration**: FOCAL_LENGTH_PX must be validated on the deployed hardware
- **ASIL consideration**: AI-derived input — weaker safety argument than ultrasonic; documented limitation
- **Priority**: High

**SYS-SAFE-010**: Emergency Stop GPIO
- Emergency stop shall use GPIO 25: Pi400 GPIO 25 (Pin 22) output → Pi5 GPIO 25 (Pin 22) input
- Signal shall be active-low (0V = emergency stop active)
- Default state at Pi400 boot: LOW (asserted — fail-safe)
- **ASIL**: B-inspired

**SYS-SAFE-011**: Proximity FTTI — Hand Detection to SAFE_STATE
- When `camera_valid=true` (camera AI sensor path active) AND ultrasonic distance drops below SAFE_DISTANCE (0.15 m), the system shall enter SAFE_STATE within **100 ms** of the ultrasonic measurement that triggers the threshold breach.
- This requirement applies under Interpretation B: the deterministic ultrasonic path is the timed safety trigger; camera AI contributes `camera_valid` only and does not directly enter the safety path.
- **Rationale**: A human hand detected in the operating area must cause the system to halt within a bounded time to prevent injury. 100 ms bounds the worst-case latency from the proximity measurement to motor inhibit.
- **Implementation**: ultrasonic_node at ≥ 20 Hz (50 ms period) + decision_node StateEvaluator at ≥ 50 Hz (20 ms period) → worst-case FTTI = 50 + 20 + 10 (overhead) = 80 ms < 100 ms.
- **AI safety boundary**: Camera AI output (raw detections) does NOT enter the safety path. Only `camera_valid` (boolean liveness flag) is used by StateEvaluator. The proximity trigger is ultrasonic only.
- **ASIL**: B-inspired
- **Priority**: Critical

### State Management

**SYS-SAFE-007**: State Machine
- System shall implement states: INIT, NORMAL, WARNING, DEGRADED, SAFE_STATE
- All state transitions shall be deterministic and rule-based
- State transition rules shall be evaluated at 10 ms cycle time
- **ASIL**: B-inspired

**SYS-SAFE-008**: Degradation Management
- System shall reduce velocity limits in WARNING state (20% nominal, velocity_scale = 0.2)
- System shall operate on ultrasonic-only in DEGRADED state (20% nominal, velocity_scale = 0.2)
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

**SYS-IF-001**: UDP Q&A Watchdog Interface
- Transport: UDP port 9001 over dedicated Ethernet (192.168.50.x)
- Pi400 role: UDP server (binds 0.0.0.0:9001)
- Pi5 role: UDP client (health_node sends responses, receives seeds and status)
- Seed packet: `{"type":"seed","seed":<uint32>,"seq":<uint8>,"crc":<uint16>}`
- Response packet: `{"type":"response","seed":<uint32>,"response":<uint32>,"seq":<uint8>,"crc":<uint16>}`
- Response algorithm: `response = seed XOR 0xA5A5A5A5`
- E2E protection: CRC-16/CCITT-FALSE + uint8 sequence counter
- Note: I2C BSC slave not feasible on BCM2711 (Pi400) — see DD-002

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
- Main Switch ON: Pi400 supervisor boots and immediately asserts e-stop GPIO 25 LOW (fail-safe); red LED ON
- Main Switch ON: Pi5 boots, ROS2 nodes start; `velocity_scale` defaults to 0.0; motor off
- health_node begins UDP Q&A watchdog exchange with Pi400 supervisor
- Pi400 releases e-stop (GPIO 25 HIGH) only after startup release criterion (SYS-SAFE-013) is met
- System transitions from INIT → NORMAL; green LED ON
- Motor Switch may be activated at any time; motor rotates only after NORMAL is reached

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
