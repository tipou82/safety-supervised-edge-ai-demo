# M2: ROS2 Sensor Pipeline

## Goal

Create the first working ROS2 communication pipeline on Raspberry Pi 5, with placeholder nodes publishing and consuming sensor data over defined topics. Establish the workspace structure that later milestones will build on.

## Scope

- ROS2 Humble workspace setup on Raspberry Pi 5 (Ubuntu 22.04)
- Placeholder or minimal implementations of: `camera_ai_node`, `ultrasonic_node`, `decision_node`, `actuator_node`, `health_node`
- ROS2 topic definitions consistent with `requirements/interfaces.yaml`
- GPIO heartbeat output on GPIO 17 at 10 Hz (health_node)
- Basic motor PWM scaffolding via L298N (actuator_node, non-safety logic only)
- `ros2 launch` entry point (`demo.launch.py`)
- Updated traceability linking nodes to requirements

## Out of Scope

- YOLOv8n or MobileNet AI model inference (deferred to M3/M4)
- Deterministic safety state machine implementation (deferred to M3)
- QNX supervisor integration (deferred to M5)
- Final safety logic or certified behavior of any kind

## Engineering Tasks

- [ ] Set up ROS2 Humble workspace (`pi5_linux/ros2_ws/`)
- [ ] Create `camera_ai_node` package with placeholder image publisher
- [ ] Create `ultrasonic_node` package publishing distance readings at 10 Hz
- [ ] Create `decision_node` package subscribing to sensor topics, publishing placeholder commands
- [ ] Create `actuator_node` package subscribing to motor commands, monitoring e-stop GPIO at 100 Hz
- [ ] Create `health_node` package generating heartbeat on GPIO 17 at 10 Hz
- [ ] Define ROS2 topic names and message types consistent with `requirements/interfaces.yaml`
- [ ] Write `demo.launch.py` launching all nodes
- [ ] Confirm `colcon build` completes without errors
- [ ] Confirm all nodes start and publish on expected topics (`ros2 topic list`, `ros2 topic echo`)
- [ ] Update `requirements/traceability.csv` with node-to-requirement links

## Acceptance Criteria

- [ ] `colcon build` completes without errors or warnings that indicate broken interfaces
- [ ] `ros2 launch safety_demo demo.launch.py` starts all five nodes without crash
- [ ] `ros2 topic list` shows all topics defined in `requirements/interfaces.yaml`
- [ ] Ultrasonic distance data is published and visible via `ros2 topic echo`
- [ ] Heartbeat signal is generated on GPIO 17 at approximately 10 Hz
- [ ] E-stop GPIO 27 is monitored by `actuator_node` at 100 Hz
- [ ] `requirements/traceability.csv` is updated to link nodes to requirements
- [ ] No safety decision logic is implemented in this milestone (placeholder logic only)

## Related Requirements

- SYS-PERF-001 (Perception-to-actuation latency ≤ 200 ms)
- SYS-PERF-002 (Heartbeat generation 100 ms ±20 ms)
- SYS-HW-001 to SYS-HW-003 (Ultrasonic sensor interface)
- SYS-COMM-001 (Heartbeat GPIO protocol)
- To be linked: ROS2 topic interface requirements

## Related Documents

- `requirements/interfaces.yaml`
- `requirements/traceability.csv`
- `docs/architecture.md`
- `hardware/gpio_mapping.md`

## Test Evidence

- `colcon build` output (clean)
- `ros2 topic list` output showing all expected topics
- `ros2 topic echo` output for ultrasonic distance topic (sample capture)
- Logic analyzer or oscilloscope trace confirming GPIO 17 heartbeat at 10 Hz (or equivalent software measurement)

## Safety / AI Boundary

- AI agents may assist with ROS2 scaffolding, package structure, and CMakeLists.
- AI agents shall not implement safety decision logic, even as placeholder behavior.
- The `decision_node` placeholder shall not make velocity or stop decisions based on sensor data in this milestone.
- GPIO 17 (heartbeat) and GPIO 27 (e-stop) are safety-critical pins; their behavior shall be reviewed by the engineer before deployment.
- No LLM calls or cloud AI calls shall be introduced into any node.

## Suggested Labels

`ros2` `python` `cplusplus` `hardware` `portfolio`

## Suggested Branch Name

`feature/m2-ros2-sensor-pipeline`

## Suggested Commit Message

```
feat: add ROS2 sensor pipeline with placeholder nodes and launch file
```
