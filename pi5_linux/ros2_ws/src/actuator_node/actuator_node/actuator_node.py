#!/usr/bin/env python3
# Actuator node — Pi5 Linux domain.
# Responsibilities:
#   - Polls GPIO 25 (Pin 22) at 100 Hz for active-low e-stop from Pi400
#   - Drives red LED (GPIO 22) HIGH on e-stop assertion
#   - Subscribes to /cmd_vel — motor PWM scaffolding (no hardware yet)
# Educational demonstrator — not ISO 26262 certified.

import lgpio
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

GPIO_CHIP     = 4
GPIO_ESTOP    = 25  # Pin 22 — active-low e-stop input from Pi400 GPIO 25
GPIO_RED_LED  = 22  # Pin 15 — SAFE STATE indicator (diode-OR with Pi400)

ESTOP_POLL_HZ = 100


class ActuatorNode(Node):

    def __init__(self):
        super().__init__('actuator_node')
        self._gpio = lgpio.gpiochip_open(GPIO_CHIP)
        lgpio.gpio_claim_input(self._gpio, GPIO_ESTOP, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_output(self._gpio, GPIO_RED_LED, 0)

        self._estop_active = False
        self._sw_safe_state = False   # software SAFE_STATE from decision_node

        self.create_subscription(Twist, '/cmd_vel', self._on_cmd_vel, 1)
        self.create_subscription(String, '/system_state', self._on_system_state, 5)
        self.create_timer(1.0 / ESTOP_POLL_HZ, self._poll_estop)

        self.get_logger().info(
            'actuator_node started — polling e-stop GPIO 25 at 100 Hz')

    def _on_system_state(self, msg: String) -> None:
        in_safe = (msg.data == 'SAFE_STATE')
        if in_safe and not self._sw_safe_state:
            self._sw_safe_state = True
            self._update_red_led()
            self.get_logger().warn('Software SAFE_STATE — red LED ON')
        elif not in_safe and self._sw_safe_state:
            self._sw_safe_state = False
            self._update_red_led()
            self.get_logger().info('Software SAFE_STATE cleared')

    def _update_red_led(self) -> None:
        # Red LED ON if hardware e-stop OR software SAFE_STATE
        on = self._estop_active or self._sw_safe_state
        lgpio.gpio_write(self._gpio, GPIO_RED_LED, 1 if on else 0)

    def _on_cmd_vel(self, msg: Twist) -> None:
        if self._estop_active or self._sw_safe_state:
            return  # drop commands in safe state
        # Motor PWM implementation deferred — no hardware in M2

    def _poll_estop(self) -> None:
        val = lgpio.gpio_read(self._gpio, GPIO_ESTOP)
        asserted = (val == 0)  # active-low

        if asserted and not self._estop_active:
            self._estop_active = True
            self._update_red_led()
            self.get_logger().warn('E-STOP ASSERTED (GPIO 25 LOW) — safe state')

        elif not asserted and self._estop_active:
            self._estop_active = False
            self._update_red_led()
            self.get_logger().info('E-stop released (GPIO 25 HIGH)')

    def destroy_node(self) -> None:
        lgpio.gpio_write(self._gpio, GPIO_RED_LED, 0)
        lgpio.gpio_free(self._gpio, GPIO_ESTOP)
        lgpio.gpio_free(self._gpio, GPIO_RED_LED)
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
