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
        self.create_subscription(Twist, '/cmd_vel', self._on_cmd_vel, 1)
        self.create_timer(1.0 / ESTOP_POLL_HZ, self._poll_estop)

        self.get_logger().info(
            'actuator_node started — polling e-stop GPIO 25 at 100 Hz')

    def _on_cmd_vel(self, msg: Twist) -> None:
        if self._estop_active:
            return  # drop commands in safe state
        # Motor PWM implementation deferred — no hardware in M2

    def _poll_estop(self) -> None:
        val = lgpio.gpio_read(self._gpio, GPIO_ESTOP)
        asserted = (val == 0)  # active-low

        if asserted and not self._estop_active:
            self._estop_active = True
            lgpio.gpio_write(self._gpio, GPIO_RED_LED, 1)
            self.get_logger().warn('E-STOP ASSERTED (GPIO 25 LOW) — safe state')

        elif not asserted and self._estop_active:
            self._estop_active = False
            lgpio.gpio_write(self._gpio, GPIO_RED_LED, 0)
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
