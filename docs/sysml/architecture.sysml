// SysML v2 Architecture Model
// Safety-Supervised Edge AI Demonstrator
// Updated: Q&A Watchdog via I2C, wired-OR red LED, GPIO 25 e-stop

package SafetySupervisedEdgeAI {

    // ─────────────────────────────────────────────────────────────
    // System Context
    // ─────────────────────────────────────────────────────────────

    part def SafetyDemoSystem {
        doc /* Dual-processor ASIL-B-inspired demonstrator.
                Pi5 (Linux/ROS2) handles AI perception.
                Pi400 (QNX-inspired supervisor) handles deterministic safety monitoring
                via an I2C Q&A watchdog with failure counter logic. */

        part linux_domain : LinuxROSDomain;
        part qnx_domain   : QNXSupervisorDomain;

        // External interfaces
        port env_sensing  : EnvironmentSensingPort;
        port actuator_if  : ActuatorControlPort;

        // Inter-domain communication
        connect linux_domain.i2c_master_port to qnx_domain.i2c_slave_port;
        connect qnx_domain.emergency_stop    to linux_domain.safety_override;
        connect qnx_domain.red_led_out       to linux_domain.red_led_in;   // wired-OR
    }

    // ─────────────────────────────────────────────────────────────
    // Linux / ROS2 Domain  (Raspberry Pi 5)
    // ─────────────────────────────────────────────────────────────

    part def LinuxROSDomain {
        doc /* Raspberry Pi 5, Raspberry Pi OS Bookworm, ROS2 Humble (built from source).
                Hosts AI perception, sensor fusion, path planning, and Q&A watchdog client. */

        part camera_ai  : CameraAINode;
        part ultrasonic : UltrasonicNode;
        part decision   : DecisionNode;
        part actuator   : ActuatorNode;
        part health     : HealthMonitorNode;

        // I2C watchdog master port (GPIO 2 SDA, GPIO 3 SCL)
        port i2c_master_port   : I2CMasterPort;
        // GPIO safety inputs/outputs
        port safety_override   : EmergencyStopInputPort;   // GPIO 25 input (active-low)
        port red_led_in        : RedLEDPort;               // GPIO 22, wired-OR

        // ROS2 topic connections
        connect camera_ai.detections to decision.ai_input;
        connect ultrasonic.obstacles to decision.sensor_input;
        connect decision.cmd_vel     to actuator.velocity_cmd;

        // Watchdog and LED connections
        connect health.i2c_watchdog_out  to i2c_master_port;
        connect safety_override          to actuator.emergency_stop_in;
        connect health.green_led_out     to health.green_led_gpio;   // GPIO 17
        connect decision.yellow_led_out  to decision.yellow_led_gpio; // GPIO 27
    }

    // ─────────────────────────────────────────────────────────────
    // QNX Supervisor Domain  (Raspberry Pi 400)
    // ─────────────────────────────────────────────────────────────

    part def QNXSupervisorDomain {
        doc /* Raspberry Pi 400, QNX 7.1 or Linux PREEMPT_RT fallback.
                Deterministic safety monitor. Rule-based logic only — no AI in safety path. */

        part watchdog_server : QAWatchdogServer;
        part safe_state_ctrl : SafeStateController;

        // I2C slave port (GPIO 2 SDA, GPIO 3 SCL), address 0x40
        port i2c_slave_port  : I2CSlavePort;
        // GPIO safety outputs
        port emergency_stop  : EmergencyStopOutputPort;  // GPIO 25 output (active-low)
        port red_led_out     : RedLEDPort;               // GPIO 22, wired-OR

        connect i2c_slave_port to watchdog_server.i2c_slave_in;
        connect watchdog_server.fault_detected to safe_state_ctrl.trigger;
        connect safe_state_ctrl.emergency_stop_gpio to emergency_stop;
        connect safe_state_ctrl.red_led_gpio to red_led_out;
    }

    // ─────────────────────────────────────────────────────────────
    // Node / Component Definitions
    // ─────────────────────────────────────────────────────────────

    part def CameraAINode {
        doc /* YOLOv8n/MobileNet object detection. Development domain — not safety-critical. */
        attribute inference_rate_hz : Real  = 10.0;
        attribute model_type        : String = "YOLOv8n";
        port image_in   : ImageStreamPort;
        port detections : DetectionArrayPort;
    }

    part def UltrasonicNode {
        doc /* Grove Ultrasonic Ranger, single-wire SIG on GPIO 23.
                Provides redundant close-range obstacle detection. */
        attribute range_cm     : Real[2]  = (2.0, 350.0);
        attribute publish_hz   : Real     = 10.0;
        attribute gpio_sig     : Integer  = 23;
        port obstacles : ObstaclePort;
    }

    part def DecisionNode {
        doc /* Path planning and velocity command generation.
                Also drives Yellow LED (DEGRADED indicator) on GPIO 27. */
        port ai_input        : DetectionArrayPort;
        port sensor_input    : ObstaclePort;
        port cmd_vel         : VelocityCommandPort;
        port yellow_led_out  : LEDControlPort;
        port yellow_led_gpio : LEDGPIOPort;    // GPIO 27, Pin 13
    }

    part def ActuatorNode {
        doc /* Motor PWM control. Polls emergency stop GPIO 25 at 100 Hz.
                Also drives Red LED (GPIO 22) on SAFE_STATE entry. */
        attribute estop_poll_hz : Real    = 100.0;
        attribute estop_gpio    : Integer = 25;
        attribute red_led_gpio  : Integer = 22;
        port velocity_cmd       : VelocityCommandPort;
        port emergency_stop_in  : EmergencyStopInputPort;
        port motor_pwm          : MotorControlPort;
        port red_led_out        : RedLEDPort;
    }

    part def HealthMonitorNode {
        doc /* I2C master watchdog client (GPIO 2/3).
                Reads seed from Pi400, computes response = seed XOR 0xA5A5A5A5,
                sends within 50–100 ms window. Also drives Green LED (GPIO 17). */

        attribute i2c_slave_addr  : Integer = 0x40;
        attribute seed_register   : Integer = 0x00;
        attribute resp_register   : Integer = 0x01;
        attribute response_mask   : Integer = 0xA5A5A5A5;
        attribute target_send_ms  : Real    = 70.0;   // aim for 70ms (well within 50–100ms)
        attribute green_led_gpio  : Integer = 17;
        attribute i2c_sda_gpio    : Integer = 2;
        attribute i2c_scl_gpio    : Integer = 3;

        port i2c_watchdog_out : I2CMasterPort;
        port green_led_out    : LEDControlPort;
        port green_led_gpio   : LEDGPIOPort;    // GPIO 17, Pin 11
    }

    part def QAWatchdogServer {
        doc /* I2C slave watchdog monitor (address 0x40, GPIO 2/3).
                Generates random seeds, validates Pi5 responses for timing and correctness.
                Manages failure counter — triggers safe state at count 3. */

        attribute slave_address       : Integer = 0x40;
        attribute seed_register       : Integer = 0x00;
        attribute resp_register       : Integer = 0x01;
        attribute response_mask       : Integer = 0xA5A5A5A5;
        attribute window_open_ms      : Real    = 50.0;
        attribute window_close_ms     : Real    = 100.0;
        attribute failure_threshold   : Integer = 3;
        attribute priority            : Integer = 250;   // QNX FIFO priority

        port i2c_slave_in    : I2CSlavePort;
        port fault_detected  : FaultSignalPort;
    }

    part def SafeStateController {
        doc /* Enforces safe state. Highest-priority process (255).
                Asserts GPIO 25 LOW (e-stop to Pi5) and GPIO 22 HIGH (red LED) on trigger. */

        attribute priority            : Integer = 255;
        attribute estop_gpio          : Integer = 25;
        attribute red_led_gpio_pin    : Integer = 22;

        port trigger              : FaultSignalPort;
        port emergency_stop_gpio  : EmergencyStopOutputPort;  // Pi400 GPIO 25
        port red_led_gpio         : RedLEDPort;               // Pi400 GPIO 22
    }

    // ─────────────────────────────────────────────────────────────
    // Q&A Watchdog Protocol Definition
    // ─────────────────────────────────────────────────────────────

    part def QAWatchdogProtocol {
        doc /* Defines the challenge/response sequence and failure counter logic.

                Cycle (initiated by Pi5 health_node):
                  1. Pi5 reads 4-byte seed from Pi400 register 0x00 (I2C read)
                  2. Pi5 computes: response = seed XOR 0xA5A5A5A5
                  3. Pi5 waits until ~70ms after last acknowledged response
                  4. Pi5 writes 4-byte response to Pi400 register 0x01 (I2C write)

                Pi400 validation:
                  elapsed = time_now - last_correct_response_time
                  timing_ok = (50ms ≤ elapsed ≤ 100ms)
                  answer_ok = (response == seed XOR 0xA5A5A5A5)

                  if timing_ok AND answer_ok:
                    consecutive_correct++
                    if consecutive_correct >= 2:
                      failure_counter = max(0, failure_counter - 1)
                      consecutive_correct = 0
                    last_correct_response_time = now
                  else:
                    failure_counter++
                    consecutive_correct = 0

                  if failure_counter >= 3:
                    assert_safe_state()   // GPIO 25 LOW + GPIO 22 HIGH
        */

        attribute window_open_ms    : Real    = 50.0;
        attribute window_close_ms   : Real    = 100.0;
        attribute response_mask     : Integer = 0xA5A5A5A5;
        attribute fail_threshold    : Integer = 3;
    }

    // ─────────────────────────────────────────────────────────────
    // System State Machine
    // ─────────────────────────────────────────────────────────────

    state def SystemStateMachine {
        doc /* Managed by QNX supervisor. SAFE_STATE requires manual reset.
                LED mapping: NORMAL→Green, DEGRADED→Yellow, SAFE_STATE→Red. */

        entry; then INIT;

        state INIT {
            doc /* System initialising. E-stop asserted by Pi400 at boot. */
        }

        state NORMAL {
            doc /* All nodes operational. Green LED ON. Full autonomous mode. */
        }

        state WARNING {
            doc /* Sensor degraded, system continues at 50% velocity. */
        }

        state DEGRADED {
            doc /* AI node failed. Ultrasonic-only operation at 20% velocity. Yellow LED ON. */
        }

        state SAFE_STATE {
            doc /* Motors disabled. Red LED ON (Pi5 GPIO 22 or Pi400 GPIO 22, wired-OR).
                    Q&A watchdog failure_counter reached 3 or operator command. */
        }

        transition INIT_to_NORMAL
            first INIT
            accept startup_ok      // Q&A watchdog first correct response received
            then NORMAL;

        transition NORMAL_to_WARNING
            first NORMAL
            accept sensor_degraded
            then WARNING;

        transition NORMAL_to_SAFE
            first NORMAL
            accept watchdog_fail   // failure_counter >= 3
            then SAFE_STATE;

        transition WARNING_to_NORMAL
            first WARNING
            accept fault_cleared
            then NORMAL;

        transition WARNING_to_DEGRADED
            first WARNING
            accept multiple_faults
            then DEGRADED;

        transition WARNING_to_SAFE
            first WARNING
            accept watchdog_fail
            then SAFE_STATE;

        transition DEGRADED_to_WARNING
            first DEGRADED
            accept ai_recovered
            then WARNING;

        transition DEGRADED_to_SAFE
            first DEGRADED
            accept watchdog_fail   // OR operator command
            then SAFE_STATE;

        transition SAFE_to_INIT
            first SAFE_STATE
            accept manual_reset    // No auto-recovery
            then INIT;
    }

    // ─────────────────────────────────────────────────────────────
    // Requirements
    // ─────────────────────────────────────────────────────────────

    requirement def <'SYS-001'> SystemShallMonitorLiveness {
        doc /* Pi400 shall monitor Pi5 liveness via I2C Q&A watchdog. */
        subject system : SafetyDemoSystem;
        require system.qnx_domain.watchdog_server;
    }

    requirement def <'SYS-002'> WatchdogWindowCompliance {
        doc /* Pi5 shall respond within the open window: 50–100ms after last correct response. */
        subject health : HealthMonitorNode;
        require health.target_send_ms >= 50.0;
        require health.target_send_ms <= 100.0;
    }

    requirement def <'SYS-003'> WatchdogFailureCounter {
        doc /* Pi400 shall trigger SAFE_STATE when failure_counter reaches 3. */
        subject wdg : QAWatchdogServer;
        require wdg.failure_threshold == 3;
    }

    requirement def <'SYS-004'> SystemShallEnterSafeState {
        doc /* System shall enter SAFE_STATE on failure_counter >= 3. */
        subject system : SafetyDemoSystem;
        assume wdg_failure_counter_gte_3;
        require system.state == SAFE_STATE;
    }

    requirement def <'SYS-005'> SafeStateLEDIndependence {
        doc /* Red LED shall be assertable independently by Pi5 or Pi400. */
        subject system : SafetyDemoSystem;
        require system.linux_domain.actuator.red_led_out.can_assert == true;
        require system.qnx_domain.safe_state_ctrl.red_led_gpio.can_assert == true;
    }

    requirement def <'SAFE-001'> AIShallNotDecideSafety {
        doc /* AI inference shall not be part of runtime safety decisions. */
        subject qnx : QNXSupervisorDomain;
        require !qnx.depends_on_ai_output;
    }

    requirement def <'SAFE-002'> SafetyShallBeDeterministic {
        doc /* Safety logic (Q&A validation, failure counter, state transitions) shall be deterministic. */
        subject wdg : QAWatchdogServer;
        require wdg.is_deterministic == true;
    }

    requirement def <'SAFE-003'> SafeStateLatency {
        doc /* Time from watchdog failure to motor disable shall be < 150ms. */
        subject system : SafetyDemoSystem;
        require system.safe_state_latency_ms < 150.0;
    }

    requirement def <'FFI-001'> SpatialIndependence {
        doc /* Linux and QNX domains shall run on separate processors. */
        subject system : SafetyDemoSystem;
        require system.linux_domain.processor != system.qnx_domain.processor;
    }

    requirement def <'FFI-002'> TemporalIndependence {
        doc /* Safety decisions shall use Pi400 local monotonic clock, not Pi5 clock. */
        subject qnx : QNXSupervisorDomain;
        require qnx.uses_local_clock == true;
    }

    requirement def <'FFI-003'> CommunicationIndependence {
        doc /* Safety channel (I2C Q&A + GPIO e-stop) shall not depend on ROS2 or shared memory. */
        subject system : SafetyDemoSystem;
        require !system.safety_channel_uses_ros2;
        require !system.safety_channel_uses_shared_memory;
    }

    // ─────────────────────────────────────────────────────────────
    // Port Definitions
    // ─────────────────────────────────────────────────────────────

    port def I2CMasterPort {
        doc /* I2C master port: GPIO 2 (SDA), GPIO 3 (SCL), 100 kHz. */
    }

    port def I2CSlavePort {
        doc /* I2C slave port: address 0x40. Registers: 0x00 seed (r), 0x01 response (w). */
    }

    port def EmergencyStopOutputPort {
        doc /* Active-low GPIO output. Pi400 GPIO 25 (Pin 22). LOW = stop asserted. */
    }

    port def EmergencyStopInputPort {
        doc /* Active-low GPIO input with pull-up. Pi5 GPIO 25 (Pin 22). */
    }

    port def RedLEDPort {
        doc /* Wired-OR red LED. Pi5 GPIO 22 and Pi400 GPIO 22, each via 1N4148 + 150Ω. */
    }

    port def LEDControlPort;
    port def LEDGPIOPort;
    port def FaultSignalPort;
    port def ImageStreamPort;
    port def DetectionArrayPort;
    port def ObstaclePort;
    port def VelocityCommandPort;
    port def MotorControlPort;
    port def EnvironmentSensingPort;
    port def ActuatorControlPort;
}
