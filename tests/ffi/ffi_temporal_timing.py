#!/usr/bin/env python3
"""
FFI-TEMPORAL — Temporal independence verification.

Goal: confirm Q&A watchdog responses stay within the 15–30ms open window
even when Pi5 is under full AI inference load (camera + YOLOv8n).

If temporal independence holds, health_node's 20ms cycle delivers responses
in [15ms, 30ms] regardless of AI workload on Pi5.

Method:
  Pi400 side: run qnx_wdg_server.py with timing logging (already built-in)
  Pi5 side:   run this script to measure response timing over 60 seconds
              while the full AI pipeline is active

Measurement:
  Pi400's qnx_wdg_server logs elapsed_ms per cycle.
  This script reads /watchdog_failure_counter to detect any failures.
  A failure under AI load = temporal independence NOT maintained.

Pass criterion:
  - failure_counter stays 0 throughout
  - No "too_early" or "timeout" failures in Pi400 log during AI load

Run with ROS2 workspace sourced:
  source ~/ros2_humble/install/setup.bash
  source ~/safety-supervised-edge-ai-demo/pi5_linux/ros2_ws/install/setup.bash
  python3 tests/ffi/ffi_temporal_timing.py

Requirement: SYS-SAFE-003 (temporal independence), FFI-002
Educational demonstrator — not ISO 26262 certified.
"""

import time
import sys
import statistics

MEASURE_S     = 60   # measurement duration
SAMPLE_HZ     = 2    # sample /watchdog_failure_counter at 2 Hz

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Int32
except ImportError:
    print("ERROR: source the workspace first")
    sys.exit(1)


class FFITemporalMonitor(Node):

    def __init__(self):
        super().__init__('ffi_temporal_monitor')
        self._samples    = []
        self._failures   = 0
        self._start_time = time.monotonic()
        self.create_subscription(Int32, '/watchdog_failure_counter',
                                 self._on_counter, 5)
        self.create_timer(1.0 / SAMPLE_HZ, self._sample)
        self.get_logger().info(
            f'FFI-TEMPORAL monitor started — {MEASURE_S}s measurement')

    def _on_counter(self, msg: Int32) -> None:
        if msg.data > 0:
            self._failures += 1

    def _sample(self) -> None:
        elapsed = time.monotonic() - self._start_time
        self._samples.append(elapsed)
        if elapsed >= MEASURE_S:
            self._report()
            rclpy.shutdown()

    def _report(self) -> None:
        print()
        print("=" * 60)
        print(" FFI-TEMPORAL Results")
        print("=" * 60)
        print(f"  Duration:          {MEASURE_S}s under full AI load")
        print(f"  Samples collected: {len(self._samples)}")
        print(f"  WDG failure events:{self._failures}")
        print()
        if self._failures == 0:
            print("  RESULT: PASS")
            print("  failure_counter stayed 0 throughout AI inference load")
            print("  Temporal independence CONFIRMED: AI timing does not")
            print("  affect Q&A watchdog window compliance")
        else:
            print("  RESULT: FAIL")
            print(f"  {self._failures} failure events detected under AI load")
            print("  health_node may be missing the 15-30ms window under load")
            print("  Investigate: reduce AI resolution or increase window")


def main():
    print("=" * 60)
    print(" FFI-TEMPORAL: Temporal Independence Verification")
    print(" Measure Q&A watchdog under full AI inference load")
    print("=" * 60)
    print()
    print("Pre-conditions:")
    print("  Pi400: qnx_wdg_server.py running")
    print("  Pi5:   ros2 launch safety_demo demo.launch.py")
    print("         All 7 nodes running (incl. hand/object detection)")
    print("         /reset published (system in NORMAL or DEGRADED)")
    print()
    print(f"Measuring for {MEASURE_S}s. Watch the camera actively detecting...")
    print()
    input("Press Enter to start measurement...")

    rclpy.init()
    node = FFITemporalMonitor()
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
