// SysML v2 Architecture Model
// Safety-Supervised Edge AI Demonstrator

package SafetySupervisedEdgeAI {

    // System Context
    part def SafetyDemoSystem {
        doc /* Dual-processor architecture demonstrating ASIL-B-inspired
                monitoring of AI perception with deterministic safety supervision. */

        // Top-level partitions
        part linux_domain : LinuxROSDomain;
        part qnx_domain : QNXSupervisorDomain;

        // External interfaces
        port env_sensing : EnvironmentSensingPort;
        port actuator_if : ActuatorControlPort;

        // Inter-domain communication
        connect linux_domain.watchdog_out to qnx_domain.watchdog_in;
        connect qnx_domain.emergency_stop to linux_domain.safety_override;
    }

    // Linux/ROS2 Domain (Development/AI)
    part def LinuxROSDomain {
        doc /* Runs on Raspberry Pi 5. Hosts AI perception, sensor fusion,
                and path planning. NOT part of safety decision path. */

        part camera_ai : CameraAINode;
        part ultrasonic : UltrasonicNode;
        part decision : DecisionNode;
        part actuator : ActuatorNode;
        part health : HealthMonitorNode;

        // ROS2 topics
        connect camera_ai.detections to decision.ai_input;
        connect ultrasonic.obstacles to decision.sensor_input;
        connect decision.cmd_vel to actuator.velocity_cmd;
        connect health.heartbeat_gpio to watchdog_out;
        connect safety_override to actuator.emergency_stop_in;
    }

    // QNX Supervisor Domain (Safety Monitoring)
    part def QNXSupervisorDomain {
        doc /* Runs on Raspberry Pi 400 (QNX or Linux fallback).
                Deterministic safety monitor with rule-based logic only. */

        part watchdog_server : WatchdogServer {
            doc /* Monitors heartbeat from Linux domain.
                    Detects timeout and triggers safe state. */
        }

        part safe_state_ctrl : SafeStateController {
            doc /* Enforces safe state (emergency brake).
                    Direct GPIO control, independent of AI. */
        }

        connect watchdog_in to watchdog_server.heartbeat_in;
        connect watchdog_server.fault_detected to safe_state_ctrl.trigger;
        connect safe_state_ctrl.emergency_stop_gpio to emergency_stop;
    }

    // Node Definitions
    part def CameraAINode {
        doc /* YOLOv8/MobileNet object detection.
                Development domain - not safety-critical. */

        attribute inference_rate : Real = 10.0; // Hz
        attribute model_type : String = "YOLOv8n";

        port image_in : ImageStreamPort;
        port detections : DetectionArrayPort;
    }

    part def UltrasonicNode {
        doc /* HC-SR04 ultrasonic distance sensors.
                Redundant perception for close-range obstacles. */

        attribute num_sensors : Integer = 3;
        attribute range_cm : Real[2] = (2.0, 400.0);

        port obstacles : ObstaclePort;
    }

    part def DecisionNode {
        doc /* Path planning and velocity command generation.
                Runs in development domain on Linux. */

        port ai_input : DetectionArrayPort;
        port sensor_input : ObstaclePort;
        port cmd_vel : VelocityCommandPort;
    }

    part def ActuatorNode {
        doc /* Motor control with safety override.
                Accepts emergency stop from QNX supervisor. */

        port velocity_cmd : VelocityCommandPort;
        port emergency_stop_in : EmergencyStopPort;
        port motor_pwm : MotorControlPort;
    }

    part def HealthMonitorNode {
        doc /* Generates heartbeat signal for watchdog.
                Monitors ROS2 node liveness. */

        attribute heartbeat_freq : Real = 10.0; // Hz
        attribute gpio_pin : Integer = 17;

        port heartbeat_gpio : HeartbeatGPIOPort;
    }

    part def WatchdogServer {
        doc /* Deterministic safety monitor.
                Timeout threshold: 500ms. */

        attribute timeout_ms : Real = 500.0;
        attribute priority : Integer = 250; // QNX FIFO priority

        port heartbeat_in : HeartbeatGPIOPort;
        port fault_detected : FaultSignalPort;
    }

    part def SafeStateController {
        doc /* Enforces emergency stop.
                Highest priority process (255). */

        attribute priority : Integer = 255;

        port trigger : FaultSignalPort;
        port emergency_stop_gpio : EmergencyStopPort;
    }

    // State Machine
    state def SystemStateMachine {
        entry; then INIT;

        state INIT {
            doc /* System initialization and self-test. */
        }

        state NORMAL {
            doc /* All nodes operational, full autonomous mode. */
        }

        state WARNING {
            doc /* Degraded sensing, reduced velocity limits. */
        }

        state DEGRADED {
            doc /* AI failed, ultrasonic-only operation. */
        }

        state SAFE_STATE {
            doc /* System halted, motors disabled. */
        }

        transition INIT_to_NORMAL
            first INIT
            accept startup_ok
            then NORMAL;

        transition NORMAL_to_WARNING
            first NORMAL
            accept sensor_degraded
            then WARNING;

        transition NORMAL_to_SAFE
            first NORMAL
            accept watchdog_timeout
            then SAFE_STATE;

        transition WARNING_to_DEGRADED
            first WARNING
            accept multiple_faults
            then DEGRADED;

        transition DEGRADED_to_SAFE
            first DEGRADED
            accept critical_fault
            then SAFE_STATE;

        transition SAFE_to_INIT
            first SAFE_STATE
            accept manual_reset
            then INIT;
    }

    // Requirements Traceability
    requirement def <'SYS-001'> SystemShallMonitor {
        doc /* System shall monitor Linux domain liveness via heartbeat. */

        subject system : SafetyDemoSystem;
        require system.qnx_domain.watchdog_server;
    }

    requirement def <'SYS-002'> SystemShallDetectTimeout {
        doc /* System shall detect heartbeat timeout within 500ms. */

        subject wdg : WatchdogServer;
        require wdg.timeout_ms == 500.0;
    }

    requirement def <'SYS-003'> SystemShallEnterSafeState {
        doc /* System shall enter safe state on watchdog timeout. */

        subject system : SafetyDemoSystem;
        assume watchdog_timeout;
        require system.state == SAFE_STATE;
    }

    requirement def <'SAFE-001'> AIShalNotDecideSafety {
        doc /* AI inference shall not be part of runtime safety decisions. */

        subject qnx : QNXSupervisorDomain;
        require !qnx.depends_on_ai_output;
    }

    requirement def <'SAFE-002'> SafetyShallBeDeterministic {
        doc /* Safety logic shall be deterministic and rule-based. */

        subject wdg : WatchdogServer;
        require wdg.is_deterministic == true;
    }

    // FFI Requirements
    requirement def <'FFI-001'> SpatialIndependence {
        doc /* Linux and QNX domains shall run on separate processors. */

        subject system : SafetyDemoSystem;
        require system.linux_domain.processor != system.qnx_domain.processor;
    }

    requirement def <'FFI-002'> TemporalIndependence {
        doc /* Safety decisions shall not depend on Linux timing. */

        subject qnx : QNXSupervisorDomain;
        require qnx.uses_local_clock == true;
    }

    // Port Definitions
    port def ImageStreamPort;
    port def DetectionArrayPort;
    port def ObstaclePort;
    port def VelocityCommandPort;
    port def HeartbeatGPIOPort;
    port def EmergencyStopPort;
    port def FaultSignalPort;
    port def MotorControlPort;
    port def EnvironmentSensingPort;
    port def ActuatorControlPort;
}
