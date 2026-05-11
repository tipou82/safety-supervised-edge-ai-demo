#!/usr/bin/env python3
# object_detection_node — Pi5, M7 Spatial FFI.
# Owns: YOLOv8n model only. Does NOT own picamera2.
# Runs as a separate Linux process from hand_detection_node.
# MMU provides spatial isolation: a YOLOv8n fault cannot corrupt MediaPipe state.
#
# Subscribes:
#   /hand_detections  (std_msgs/String JSON)   — hand presence, bbox, conf
#   /hand_roi         (sensor_msgs/CompressedImage) — JPEG ROI from hand_detection_node
#
# Publishes:
#   /detections  (std_msgs/String JSON) at 10 Hz — full result for decision_node
#
# Educational demonstrator — not ISO 26262 certified.

import json
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String

try:
    from ultralytics import YOLO
    import numpy as np
    _YOLO_OK = True
except ImportError:
    _YOLO_OK = False

try:
    import cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

OBJ_CONF_MIN = 0.40
PUBLISH_HZ   = 10


class ObjectDetectionNode(Node):

    def __init__(self):
        super().__init__('object_detection_node')

        self._det_pub = self.create_publisher(String, '/detections', 5)
        self._yolo    = self._init_yolo()

        # Latest state from hand_detection_node
        self._hand           = False
        self._hand_conf      = 0.0
        self._hand_distance_m = float('inf')
        self._frame          = 0
        self._hits           = 0
        self._obj_name       = None
        self._obj_conf       = 0.0
        self._last_hand_t    = time.monotonic()

        self.create_subscription(String,           '/hand_detections',
                                 self._on_hand,    5)
        self.create_subscription(CompressedImage,  '/hand_roi',
                                 self._on_roi,     5)

        # Publish at 10 Hz even without ROI (for camera_valid liveness)
        self.create_timer(1.0 / PUBLISH_HZ, self._publish)

        self.get_logger().info(
            f'object_detection_node M7 — separate process from hand_detection_node '
            f'(MMU spatial isolation). yolo={self._yolo is not None}')

    def _init_yolo(self):
        if not _YOLO_OK:
            self.get_logger().warn('ultralytics not found — object classification inactive')
            return None
        try:
            model = YOLO('yolov8n.pt')
            self.get_logger().info('YOLOv8n loaded')
            return model
        except Exception as e:
            self.get_logger().warn(f'YOLOv8n load failed: {e}')
            return None

    def _on_hand(self, msg: String) -> None:
        try:
            d = json.loads(msg.data)
            self._hand           = d.get('hand', False)
            self._hand_conf      = d.get('hand_conf', 0.0)
            self._hand_distance_m = d.get('hand_distance_m', float('inf'))
            self._frame          = d.get('frame', 0)
            self._hits           = d.get('hits', 0)
            self._last_hand_t    = time.monotonic()
            if not self._hand:
                self._obj_name = None
                self._obj_conf = 0.0
                self._hand_distance_m = float('inf')
        except (json.JSONDecodeError, KeyError):
            pass

    def _on_roi(self, msg: CompressedImage) -> None:
        if self._yolo is None or not _CV2_OK:
            return
        try:
            buf = np.frombuffer(bytes(msg.data), np.uint8)
            roi = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if roi is None or roi.size == 0:
                return

            for r in self._yolo(roi, verbose=False, conf=OBJ_CONF_MIN):
                for box in r.boxes:
                    name = self._yolo.names[int(box.cls)]
                    conf = float(box.conf)
                    if name != 'person' and conf >= OBJ_CONF_MIN:
                        self._obj_name = name
                        self._obj_conf = round(conf, 3)
                        self.get_logger().info(
                            f'HAND+OBJ  hand={self._hand_conf:.2f}  '
                            f'obj={name} ({conf:.2f})')
                        return
            self._obj_name = None
            self._obj_conf = 0.0
        except Exception as e:
            self.get_logger().debug(f'YOLOv8n error: {e}')

    def _publish(self) -> None:
        self._det_pub.publish(String(data=json.dumps({
            'status':          'RUNNING',
            'hand':            self._hand,
            'hand_conf':       self._hand_conf,
            'hand_distance_m': self._hand_distance_m,
            'object':          self._obj_name,
            'object_conf':     self._obj_conf,
            'frame':           self._frame,
            'detections':      self._hits,
        })))


def main(args=None):
    rclpy.init(args=args)
    node = ObjectDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
