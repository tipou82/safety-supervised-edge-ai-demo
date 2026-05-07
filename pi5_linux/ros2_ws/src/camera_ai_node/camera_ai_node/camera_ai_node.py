#!/usr/bin/env python3
# Camera AI node — Pi5 Linux domain.
# M2 PLACEHOLDER: logs startup only. No inference, no publishing.
# AI inference (YOLOv8n/MobileNet) and /detections topic deferred to M3.
# Educational demonstrator — not ISO 26262 certified.

import rclpy
from rclpy.node import Node


class CameraAINode(Node):

    def __init__(self):
        super().__init__('camera_ai_node')
        self.get_logger().info(
            'camera_ai_node started — M2 placeholder. '
            'AI inference and /detections deferred to M3.')

    def destroy_node(self) -> None:
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraAINode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
