#!/usr/bin/env python3
"""
FFI-COMM — Communication independence verification.

Goal: confirm UDP Q&A watchdog is unaffected by ROS2/DDS topic flooding.
If communication independence holds, flooding ROS2 topics does NOT
cause watchdog failures — the UDP channel is isolated from DDS.

Method:
  1. Run full system (ros2 launch + Pi400 watchdog server)
  2. Flood /obstacles at 200 Hz with artificial data (10× nominal rate)
  3. Monitor /watchdog_failure_counter throughout
  4. Pass criterion: failure_counter stays 0 during flood

This tests that the UDP watchdog socket is isolated from DDS middleware
congestion on Pi5.

Run with ROS2 workspace sourced:
  source ~/ros2_humble/install/setup.bash
  source ~/safety-supervised-edge-ai-demo/pi5_linux/ros2_ws/install/setup.bash
  python3 tests/ffi/ffi_comm_ros_flood.py

Requirement: FFI-003 (communication independence)
Educational demonstrator — not ISO 26262 certified.
"""

import sys
import time
import threading

FLOOD_HZ     = 200   # 10× nominal /obstacles rate
FLOOD_S      = 30
MONITOR_S    = 35

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Range
    from std_msgs.msg import Int32
except ImportError:
    print("ERROR: source the workspace first")
    sys.exit(1)


class FFICommFloodNode(Node):

    def __init__(self):
        super().__init__('ffi_comm_flood')

        self._flood_pub  = self.create_publisher(Range, '/obstacles', 50)
        self._failures   = 0
        self._start_time = time.monotonic()
        self._flooding   = True

        self.create_subscription(Int32, '/watchdog_failure_counter',
                                 self._on_counter, 5)

        # Flood timer
        self.create_timer(1.0 / FLOOD_HZ, self._flood)

        # Stop flood and report after FLOOD_S
        self.create_timer(FLOOD_S,  self._stop_flood)
        self.create_timer(MONITOR_S, self._report)

        self.get_logger().info(
            f'FFI-COMM flood node started — {FLOOD_HZ} Hz for {FLOOD_S}s')

    def _on_counter(self, msg: Int32) -> None:
        if msg.data > 0:
            self._failures += 1

    def _flood(self) -> None:
        if not self._flooding:
            return
        msg = Range()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'ffi_flood'
        msg.radiation_type  = Range.ULTRASOUND
        msg.field_of_view   = 0.26
        msg.min_range       = 0.02
        msg.max_range       = 3.50
        msg.range           = 1.0   # safe distance — won't trigger SAFE_STATE
        self._flood_pub.publish(msg)

    def _stop_flood(self) -> None:
        self._flooding = False
        self.get_logger().info(f'Flood stopped after {FLOOD_S}s — monitoring 5s more')

    def _report(self) -> None:
        elapsed = time.monotonic() - self._start_time
        print()
        print("=" * 60)
        print(" FFI-COMM Results")
        print("=" * 60)
        print(f"  Flood rate:          {FLOOD_HZ} Hz (10× nominal)")
        print(f"  Flood duration:      {FLOOD_S}s")
        print(f"  Monitor duration:    {elapsed:.1f}s")
        print(f"  WDG failure events:  {self._failures}")
        print()
        if self._failures == 0:
            print("  RESULT: PASS")
            print("  failure_counter stayed 0 during ROS2 topic flood")
            print("  Communication independence CONFIRMED: DDS congestion")
            print("  does not affect UDP watchdog channel")
        else:
            print("  RESULT: FAIL")
            print(f"  {self._failures} watchdog failures during ROS2 flood")
            print("  UDP socket may be sharing resources with DDS middleware")
        rclpy.shutdown()


def main():
    print("=" * 60)
    print(" FFI-COMM: Communication Independence Verification")
    print(f" Flood /obstacles at {FLOOD_HZ} Hz — UDP watchdog must be unaffected")
    print("=" * 60)
    print()
    print("Pre-conditions:")
    print("  Pi400: qnx_wdg_server.py running")
    print("  Pi5:   ros2 launch safety_demo demo.launch.py")
    print("         /reset published (system in NORMAL or DEGRADED)")
    print()
    print(f"Will flood /obstacles at {FLOOD_HZ} Hz for {FLOOD_S}s")
    print("WARNING: This will trigger WARNING/SAFE_STATE due to message flood")
    print("         but the UDP watchdog failure_counter must stay 0")
    print()
    input("Press Enter to start flood test...")

    rclpy.init()
    node = FFICommFloodNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, Exception):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
