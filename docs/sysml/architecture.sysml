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

    // ── State Action Helper ───────────────────────────────────────────────────
    // Documents LED output and velocity scale for each state.
    // Verified on hardware 2026-05-08.

    action def StateEntry_INIT {
        doc /* Green LED: ON  |  Yellow LED: OFF  |  Red LED: OFF  |  vel_scale: 0.0 */
    }
    action def StateEntry_NORMAL {
        doc /* Green LED: ON  |  Yellow LED: OFF  |  Red LED: OFF  |  vel_scale: 1.0 */
    }
    action def StateEntry_WARNING {
        doc /* Green LED: ON  |  Yellow LED: OFF  |  Red LED: OFF  |  vel_scale: 0.5 */
    }
    action def StateEntry_DEGRADED {
        doc /* Green LED: ON  |  Yellow LED: ON   |  Red LED: OFF  |  vel_scale: 0.2 */
    }
    action def StateEntry_SAFE_STATE {
        doc /* Green LED: OFF |  Yellow LED: OFF  |  Red LED: ON   |  vel_scale: 0.0
                Red LED driven by: actuator_node (software path) OR Pi400 safe_state_ctrl (hardware path).
                Green LED driven OFF by: health_node on /system_state = SAFE_STATE.
                SAFE_STATE requires explicit manual reset — no auto-recovery. */
    }

    // ─────────────────────────────────────────────────────────────
    // System State Machine
    // ─────────────────────────────────────────────────────────────

    state def SystemStateMachine {
        doc /* Software state machine running in decision_node (Pi5, C++20 StateEvaluator).
                Evaluated at 20 Hz. Priority rules enforced in fixed order.
                SAFE_STATE requires manual reset — no auto-recovery.
                LED outputs and velocity scaling verified on hardware 2026-05-08.
                GPIO 25 e-stop (Pi400 hardware) is independent of this state machine. */

        entry; then INIT;

        state INIT {
            doc /* System initialising. Waiting for first valid sensor reading.
                    vel_scale=0.0. Green LED ON, Red LED OFF. */
            entry StateEntry_INIT;
        }

        state NORMAL {
            doc /* Both sensor paths valid. No obstacle within warning distance.
                    vel_scale=1.0. Green LED ON. */
            entry StateEntry_NORMAL;
        }

        state WARNING {
            doc /* Both sensors valid but obstacle within 0.50 m.
                    vel_scale=0.5. Green LED ON. */
            entry StateEntry_WARNING;
        }

        state DEGRADED {
            doc /* Exactly one sensor path valid (camera OR ultrasonic, not both).
                    vel_scale=0.2. Green LED ON, Yellow LED ON.
                    In M3: camera_valid=false always → DEGRADED is nominal operating state. */
            entry StateEntry_DEGRADED;
        }

        state SAFE_STATE {
            doc /* Any critical fault: obstacle < 0.15 m, both sensors gone,
                    or watchdog_failure_counter >= 3.
                    vel_scale=0.0. Green LED OFF, Red LED ON.
                    Latches — only exits via manual_reset when all conditions cleared. */
            entry StateEntry_SAFE_STATE;
        }

        // ── Transitions (priority order matches StateEvaluator rules) ─────────

        transition INIT_to_SAFE
            first INIT
            accept critical_fault   // watchdog>=3, distance<0.15m, both sensors gone
            then SAFE_STATE;

        transition INIT_to_DEGRADED
            first INIT
            accept system_ready_one_sensor  // system_ready AND exactly one sensor valid
            then DEGRADED;

        transition INIT_to_WARNING
            first INIT
            accept system_ready_warning     // system_ready AND distance < 0.50m
            then WARNING;

        transition INIT_to_NORMAL
            first INIT
            accept system_ready_clear       // system_ready AND both sensors valid AND clear
            then NORMAL;

        transition NORMAL_to_WARNING
            first NORMAL
            accept distance_below_warn      // ultrasonic_valid AND distance_m < 0.50
            then WARNING;

        transition NORMAL_to_DEGRADED
            first NORMAL
            accept one_sensor_lost          // exactly one sensor path becomes invalid
            then DEGRADED;

        transition NORMAL_to_SAFE
            first NORMAL
            accept critical_fault           // distance<0.15m, both sensors gone, watchdog>=3
            then SAFE_STATE;

        transition WARNING_to_NORMAL
            first WARNING
            accept obstacle_cleared         // distance >= 0.50m AND both sensors valid
            then NORMAL;

        transition WARNING_to_DEGRADED
            first WARNING
            accept one_sensor_lost
            then DEGRADED;

        transition WARNING_to_SAFE
            first WARNING
            accept critical_fault
            then SAFE_STATE;

        transition DEGRADED_to_NORMAL
            first DEGRADED
            accept both_sensors_recovered   // both camera_valid AND ultrasonic_valid AND clear
            then NORMAL;

        transition DEGRADED_to_WARNING
            first DEGRADED
            accept second_sensor_recovered_warning  // both valid but distance < 0.50m
            then WARNING;

        transition DEGRADED_to_SAFE
            first DEGRADED
            accept critical_fault           // distance<0.15m, both sensors gone, watchdog>=3
            then SAFE_STATE;

        transition SAFE_to_INIT
            first SAFE_STATE
            accept manual_reset_all_clear   // manual_reset=true AND all triggering conditions cleared
            then INIT;
    }

    // ─────────────────────────────────────────────────────────────
    // Dynamic Diagrams — Verified Interaction Scenarios
    // Verified on hardware 2026-05-08.
    // ─────────────────────────────────────────────────────────────

    // Scenario 1: Normal startup (M3 — camera placeholder)
    interaction def Scenario_Startup_M3 {
        doc /* Startup sequence with camera_ai_node placeholder (M3).
                Camera is always invalid in M3 → DEGRADED is nominal state.
                Verified: 2026-05-08. */

        occurrence nodes_boot         : SystemBoot;
        occurrence first_ultrasonic   : UltrasonicReading;
        occurrence state_safe         : SystemStateChange;   // INIT → SAFE_STATE
        occurrence state_degraded     : SystemStateChange;   // SAFE_STATE → INIT → DEGRADED
        occurrence led_red_on         : LEDEvent;            // red ON at SAFE_STATE
        occurrence led_green_off      : LEDEvent;            // green OFF at SAFE_STATE
        occurrence led_green_on2      : LEDEvent;            // green ON at DEGRADED
        occurrence led_red_off        : LEDEvent;            // red OFF at DEGRADED

        then nodes_boot;
        // Both sensors invalid at boot → Rule 3 triggers SAFE_STATE immediately
        then state_safe;             // INIT → SAFE_STATE
        then led_red_on;             // actuator_node: red LED ON
        then led_green_off;          // health_node: green LED OFF
        then first_ultrasonic;       // system_ready = true, ultrasonic_valid = true
        // state LATCHES in SAFE_STATE — manual reset required
        // Operator publishes /reset
        then state_degraded;         // SAFE_STATE → INIT → DEGRADED
        then led_green_on2;          // health_node: green LED ON
        then led_red_off;            // actuator_node: red LED OFF
    }

    // Scenario 2: Obstacle detection → SAFE_STATE entry and exit
    interaction def Scenario_ObstacleSafeState {
        doc /* Obstacle enters critical zone (<0.15m) from DEGRADED state.
                SAFE_STATE latches until manual reset with obstacle removed.
                Verified: 2026-05-08. */

        occurrence in_degraded      : SystemState;     // running in DEGRADED
        occurrence obstacle_near    : UltrasonicReading;  // distance < 0.15m
        occurrence safe_entry       : SystemStateChange;  // DEGRADED → SAFE_STATE
        occurrence led_red_on       : LEDEvent;           // red ON
        occurrence led_green_off    : LEDEvent;           // green OFF
        occurrence obstacle_removed : UltrasonicReading;  // distance > 0.15m
        occurrence state_latches    : SystemState;        // still SAFE_STATE (latch)
        occurrence manual_reset     : ResetEvent;         // /reset published
        occurrence back_to_degraded : SystemStateChange;  // SAFE_STATE → INIT → DEGRADED
        occurrence led_green_on     : LEDEvent;           // green ON
        occurrence led_red_off      : LEDEvent;           // red OFF

        then in_degraded;
        then obstacle_near;
        then safe_entry;        // StateEvaluator: distance < 0.15m → SAFE_STATE
        then led_red_on;
        then led_green_off;
        then obstacle_removed;
        then state_latches;     // Rule 1: latches even though condition cleared
        then manual_reset;
        then back_to_degraded;
        then led_green_on;
        then led_red_off;
    }

    // Scenario 3: Hardware e-stop (independent of state machine)
    interaction def Scenario_HardwareEstop {
        doc /* Pi400 asserts GPIO 25 LOW independently of software state machine.
                actuator_node forces motor commands to zero and lights red LED.
                decision_node state is NOT affected — e-stop is a hardware layer below it.
                This independence is the key FFI measure for the safety supervisor.
                Verified: 2026-05-08 (M2 e-stop test). */

        occurrence pi400_asserts    : GPIOEvent;       // Pi400 GPIO 25 → LOW
        occurrence actuator_detects : ActuatorEvent;   // actuator_node polls at 100 Hz
        occurrence motor_inhibit    : ActuatorEvent;   // motor commands zeroed
        occurrence led_red_hw       : LEDEvent;        // red LED ON (hardware path)
        occurrence sw_state_unchanged : SystemState;   // decision_node state unchanged
        occurrence pi400_releases   : GPIOEvent;       // Pi400 GPIO 25 → HIGH
        occurrence motor_restored   : ActuatorEvent;   // commands accepted again
        occurrence led_red_off      : LEDEvent;        // red LED OFF (if sw state not SAFE_STATE)

        then pi400_asserts;
        then actuator_detects;      // within 10 ms (100 Hz polling)
        then motor_inhibit;
        then led_red_hw;
        then sw_state_unchanged;    // decision_node continues in its own state
        then pi400_releases;
        then motor_restored;
        then led_red_off;
    }

    // Scenario 4: Q&A Watchdog failure → SAFE_STATE (M5 — not yet active)
    interaction def Scenario_WatchdogFailure {
        doc /* Pi400 Q&A watchdog failure_counter reaches 3.
                Pi400 asserts GPIO 25 AND red LED independently.
                Software state machine also enters SAFE_STATE via watchdog_failure_counter input.
                Two independent paths to SAFE_STATE: hardware (GPIO 25) + software (StateEvaluator).
                Status: NOT YET ACTIVE — Pi400 I2C slave implementation deferred to M5. */

        occurrence wdg_fail_1 : WatchdogEvent;   // failure_counter = 1
        occurrence wdg_fail_2 : WatchdogEvent;   // failure_counter = 2
        occurrence wdg_fail_3 : WatchdogEvent;   // failure_counter = 3 → threshold
        occurrence hw_estop   : GPIOEvent;        // Pi400 asserts GPIO 25 LOW (hardware path)
        occurrence sw_safe    : SystemStateChange; // StateEvaluator enters SAFE_STATE (software path)
        occurrence red_led_hw : LEDEvent;          // Pi400 GPIO 22 → red LED ON (hardware path)
        occurrence red_led_sw : LEDEvent;          // actuator_node GPIO 22 → red LED ON (software path)

        then wdg_fail_1;
        then wdg_fail_2;
        then wdg_fail_3;
        then hw_estop;     // Pi400 independent of Pi5
        then sw_safe;      // decision_node StateEvaluator (when wired in M5)
        then red_led_hw;
        then red_led_sw;
    }

    // ── Event Type Definitions ────────────────────────────────────────────────
    occurrence def SystemBoot;
    occurrence def SystemState;
    occurrence def SystemStateChange;
    occurrence def UltrasonicReading;
    occurrence def LEDEvent;
    occurrence def ResetEvent;
    occurrence def GPIOEvent;
    occurrence def ActuatorEvent;
    occurrence def WatchdogEvent;

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
