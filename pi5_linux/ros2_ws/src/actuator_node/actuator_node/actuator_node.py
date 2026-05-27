#!/usr/bin/env python3
# Actuator node — Pi5 Linux domain.
# Responsibilities:
#   - Polls GPIO 25 (Pin 22) at 100 Hz for active-low e-stop from Pi400
#   - Drives red LED (GPIO 22) HIGH on e-stop assertion or SAFE_STATE
#   - Subscribes to /velocity_scale — drives DRV8833 IN1 (GPIO 12) with PWM
#   - DRV8833 IN2 (GPIO 16) = LOW → forward direction
#   - SAFE_STATE or e-stop: both IN1/IN2 LOW (motor stopped)
#   - Motor supply is from 4xAA battery via Motor Switch (independent of Pi power)
# Educational demonstrator — not ISO 26262 certified.

import lgpio
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Float32

GPIO_CHIP     = 4
GPIO_ESTOP    = 25  # Pin 22 — active-low e-stop input from Pi400 GPIO 25
GPIO_RED_LED  = 22  # Pin 15 — SAFE STATE indicator (diode-OR with Pi400)
GPIO_IN1      = 12  # Pin 32 — DRV8833 IN1 (Motor A, PWM speed)
GPIO_IN2      = 16  # Pin 36 — DRV8833 IN2 (Motor A, direction — LOW = forward)

MOTOR_PWM_FREQ_HZ = 1000   # 1 kHz software PWM on IN1
ESTOP_POLL_HZ     = 100


class ActuatorNode(Node):

    def __init__(self):
        super().__init__('actuator_node')
        self._gpio = lgpio.gpiochip_open(GPIO_CHIP)

        # E-stop input (active-low, internal pull-up)
        lgpio.gpio_claim_input(self._gpio, GPIO_ESTOP, lgpio.SET_PULL_UP)

        # Outputs — all LOW at startup (motor off, red LED off)
        lgpio.gpio_claim_output(self._gpio, GPIO_RED_LED, 0)
        lgpio.gpio_claim_output(self._gpio, GPIO_IN1, 0)
        lgpio.gpio_claim_output(self._gpio, GPIO_IN2, 0)

        self._estop_active  = False
        self._sw_safe_state = False
        self._velocity_scale = 0.0

        self.create_subscription(Float32, '/velocity_scale', self._on_velocity_scale, 1)
        self.create_subscription(Twist,   '/cmd_vel',        self._on_cmd_vel,        1)
        self.create_subscription(String,  '/system_state',   self._on_system_state,   5)
        self.create_timer(1.0 / ESTOP_POLL_HZ, self._poll_estop)

        self.get_logger().info(
            'actuator_node started — GPIO 12/16 DRV8833, e-stop GPIO 25 at 100 Hz')

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_velocity_scale(self, msg: Float32) -> None:
        self._velocity_scale = float(msg.data)
        self._apply_motor()

    def _on_cmd_vel(self, msg: Twist) -> None:
        # Fallback: if /velocity_scale is not published, use cmd_vel linear.x
        # (only applied when velocity_scale has not been updated recently)
        pass  # /velocity_scale is the primary interface

    def _on_system_state(self, msg: String) -> None:
        in_safe = (msg.data == 'SAFE_STATE')
        if in_safe != self._sw_safe_state:
            self._sw_safe_state = in_safe
            self._update_red_led()
            if in_safe:
                self.get_logger().warn('Software SAFE_STATE — motor stopped, red LED ON')
            else:
                self.get_logger().info('Software SAFE_STATE cleared')
            self._apply_motor()

    # ------------------------------------------------------------------
    # Motor control
    # ------------------------------------------------------------------

    def _apply_motor(self) -> None:
        """Drive DRV8833 IN1/IN2 based on velocity_scale and safe state."""
        if self._estop_active or self._sw_safe_state:
            self._motor_stop()
            return

        scale = max(0.0, min(1.0, self._velocity_scale))
        if scale <= 0.0:
            self._motor_stop()
        else:
            duty = scale * 100.0  # 0.0–100.0 percent
            lgpio.tx_pwm(self._gpio, GPIO_IN1, MOTOR_PWM_FREQ_HZ, duty)
            lgpio.gpio_write(self._gpio, GPIO_IN2, 0)  # forward direction

    def _motor_stop(self) -> None:
        """Stop motor: duty 0% on IN1, IN2 LOW.
        Note: freq must never be 0 — lgpio calculates micros=1e6/freq → error.
        Use duty=0 at valid frequency to hold output LOW via PWM engine."""
        lgpio.tx_pwm(self._gpio, GPIO_IN1, MOTOR_PWM_FREQ_HZ, 0.0)
        lgpio.gpio_write(self._gpio, GPIO_IN2, 0)

    # ------------------------------------------------------------------
    # E-stop polling (100 Hz)
    # ------------------------------------------------------------------

    def _poll_estop(self) -> None:
        val      = lgpio.gpio_read(self._gpio, GPIO_ESTOP)
        asserted = (val == 0)  # active-low

        if asserted and not self._estop_active:
            self._estop_active = True
            self._update_red_led()
            self._motor_stop()
            self.get_logger().warn('E-STOP ASSERTED (GPIO 25 LOW) — motor stopped')

        elif not asserted and self._estop_active:
            self._estop_active = False
            self._update_red_led()
            self.get_logger().info('E-stop released (GPIO 25 HIGH)')
            self._apply_motor()

    def _update_red_led(self) -> None:
        on = self._estop_active or self._sw_safe_state
        lgpio.gpio_write(self._gpio, GPIO_RED_LED, 1 if on else 0)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def destroy_node(self) -> None:
        # Stop PWM before freeing GPIO (duty=0, valid freq — never freq=0)
        lgpio.tx_pwm(self._gpio, GPIO_IN1, MOTOR_PWM_FREQ_HZ, 0.0)
        lgpio.gpio_write(self._gpio, GPIO_IN2, 0)
        lgpio.gpio_write(self._gpio, GPIO_RED_LED, 0)
        lgpio.gpio_free(self._gpio, GPIO_ESTOP)
        lgpio.gpio_free(self._gpio, GPIO_RED_LED)
        lgpio.gpio_free(self._gpio, GPIO_IN1)
        lgpio.gpio_free(self._gpio, GPIO_IN2)
        lgpio.gpiochip_close(self._gpio)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ActuatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
