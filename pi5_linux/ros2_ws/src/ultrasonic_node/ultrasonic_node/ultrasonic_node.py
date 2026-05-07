#!/usr/bin/env python3
# Ultrasonic node — Pi5 Linux domain.
# Reads Grove Ultrasonic Ranger on GPIO 23 (single-wire SIG protocol via lgpio).
# Publishes /obstacles (sensor_msgs/Range) at 10 Hz.
# Educational demonstrator — not ISO 26262 certified.

import time
import lgpio
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range

GPIO_CHIP    = 4   # Pi5 RP1 southbridge
GPIO_SIG     = 23  # Pin 16 — Grove Ultrasonic Ranger SIG
PUBLISH_HZ   = 10
TRIGGER_US   = 10  # µs trigger pulse
TIMEOUT_S    = 0.03


class UltrasonicNode(Node):

    def __init__(self):
        super().__init__('ultrasonic_node')
        self._gpio = lgpio.gpiochip_open(GPIO_CHIP)
        self._pub = self.create_publisher(Range, '/obstacles', 5)
        self.create_timer(1.0 / PUBLISH_HZ, self._publish)
        self.get_logger().info('ultrasonic_node started — Grove Ranger on GPIO 23 (Pin 16)')

    def _read_distance_m(self) -> float | None:
        try:
            # Trigger: output 10 µs HIGH
            lgpio.gpio_claim_output(self._gpio, GPIO_SIG, 0)
            lgpio.gpio_write(self._gpio, GPIO_SIG, 1)
            time.sleep(TRIGGER_US / 1_000_000)
            lgpio.gpio_write(self._gpio, GPIO_SIG, 0)

            # Echo: switch to input and measure pulse width
            lgpio.gpio_claim_input(self._gpio, GPIO_SIG)

            deadline = time.monotonic() + TIMEOUT_S
            while lgpio.gpio_read(self._gpio, GPIO_SIG) == 0:
                if time.monotonic() > deadline:
                    return None
            t_start = time.monotonic()

            deadline = time.monotonic() + TIMEOUT_S
            while lgpio.gpio_read(self._gpio, GPIO_SIG) == 1:
                if time.monotonic() > deadline:
                    return None
            t_end = time.monotonic()

            # Grove Ultrasonic Ranger: distance = pulse_width * 340 / 2
            distance_m = (t_end - t_start) * 340.0 / 2.0
            return distance_m
        except Exception as e:
            self.get_logger().debug(f'Ultrasonic read error: {e}')
            return None

    def _publish(self) -> None:
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'ultrasonic_front'
        msg.radiation_type = Range.ULTRASOUND
        msg.field_of_view = 0.26   # ~15 degrees
        msg.min_range = 0.02
        msg.max_range = 3.50

        dist = self._read_distance_m()
        if dist is not None and 0.02 <= dist <= 3.50:
            msg.range = dist
        else:
            msg.range = float('inf')

        self._pub.publish(msg)

    def destroy_node(self) -> None:
        lgpio.gpiochip_close(self._gpio)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
