#!/usr/bin/env python3
# Decision node — Pi5 Linux domain.
# M2 PLACEHOLDER: subscribes to /obstacles, publishes zero /cmd_vel.
# No obstacle avoidance or safety decisions implemented in M2.
# Also drives yellow LED (GPIO 27) when in DEGRADED state — M3.
# Educational demonstrator — not ISO 26262 certified.

import lgpio
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist

GPIO_CHIP       = 4
GPIO_YELLOW_LED = 27  # Pin 13 — DEGRADED state indicator


class DecisionNode(Node):

    def __init__(self):
        super().__init__('decision_node')
        self._gpio = lgpio.gpiochip_open(GPIO_CHIP)
        lgpio.gpio_claim_output(self._gpio, GPIO_YELLOW_LED, 0)

        self._cmd_pub = self.create_publisher(Twist, '/cmd_vel', 1)
        self.create_subscription(Range, '/obstacles', self._on_obstacle, 5)
        self.create_timer(0.05, self._publish_cmd)  # 20 Hz

        self.get_logger().info(
            'decision_node started — M2 placeholder, publishing zero /cmd_vel')

    def _on_obstacle(self, msg: Range) -> None:
        pass  # placeholder — obstacle avoidance logic deferred to M3

    def _publish_cmd(self) -> None:
        self._cmd_pub.publish(Twist())  # zero velocity

    def destroy_node(self) -> None:
        lgpio.gpio_write(self._gpio, GPIO_YELLOW_LED, 0)
        lgpio.gpio_free(self._gpio, GPIO_YELLOW_LED)
        lgpio.gpiochip_close(self._gpio)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DecisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
