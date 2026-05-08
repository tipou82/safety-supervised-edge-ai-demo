#!/usr/bin/env python3
"""
FI-04 — Malformed sensor data on /obstacles.

Publishes Range messages with invalid values (NaN, negative, out-of-range)
to /obstacles. decision_node must reject them gracefully — no crash,
ultrasonic_valid set false, system degrades safely.

Run with ROS2 workspace sourced:
  source ~/ros2_humble/install/setup.bash
  source ~/safety-supervised-edge-ai-demo/pi5_linux/ros2_ws/install/setup.bash
  python3 tests/fault_injection/fi_04_malformed_sensor_data.py

Expected per test case:
  - NaN range:      ultrasonic_valid=false, no crash, DEGRADED (if camera valid)
  - Negative range: ultrasonic_valid=false, no crash
  - Inf range:      ultrasonic_valid=false, no crash
  - decision_node continues running throughout

Requirement: SYS-SAFE-005 (invalid input rejection)
Educational demonstrator — not ISO 26262 certified.
"""

import math
import time
import sys

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Range
except ImportError:
    print("ERROR: rclpy not found. Source the workspace first:")
    print("  source ~/ros2_humble/install/setup.bash")
    print("  source ~/safety-supervised-edge-ai-demo/pi5_linux/ros2_ws/install/setup.bash")
    sys.exit(1)

TEST_CASES = [
    ('NaN range',      float('nan')),
    ('Negative range', -1.0),
    ('Inf range',      float('inf')),
    ('Zero range',     0.0),
]

PUBLISH_COUNT = 10
PUBLISH_HZ    = 5


class FI04Node(Node):
    def __init__(self):
        super().__init__('fi_04_injector')
        self._pub = self.create_publisher(Range, '/obstacles', 5)

    def publish_malformed(self, label: str, range_val: float):
        msg = Range()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'fi_04_injector'
        msg.radiation_type  = Range.ULTRASOUND
        msg.field_of_view   = 0.26
        msg.min_range       = 0.02
        msg.max_range       = 3.50
        msg.range           = range_val

        for i in range(PUBLISH_COUNT):
            self.get_logger().info(
                f'FI-04 publishing {label}: range={range_val} ({i+1}/{PUBLISH_COUNT})')
            self._pub.publish(msg)
            time.sleep(1.0 / PUBLISH_HZ)


def main():
    print("=" * 60)
    print(" FI-04: Malformed Sensor Data")
    print(" Publish invalid /obstacles values — expect no crash")
    print("=" * 60)
    print()

    rclpy.init()
    node = FI04Node()

    for label, val in TEST_CASES:
        print(f"\n--- Publishing {label} ({val}) for {PUBLISH_COUNT} messages ---")
        input(f"Press Enter to start '{label}' injection...")
        node.publish_malformed(label, val)
        print(f"  Done. Verify decision_node is still running:")
        print(f"  ros2 node list | grep decision_node")
        still_ok = input(f"  decision_node still running? (yes/no): ").strip().lower()
        print(f"  {label}: {'PASS' if still_ok == 'yes' else 'FAIL'}")

    node.destroy_node()
    rclpy.shutdown()

    print()
    print("=" * 60)
    print(" FI-04 Complete")
    print(" All cases should PASS — no crash on malformed input")
    print("=" * 60)


if __name__ == '__main__':
    main()
