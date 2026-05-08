#!/usr/bin/env python3
# camera_ai_node — Pi5 Linux domain, M4.
# Design Decision DD-001 Option C: MediaPipe Hands (hand detection) +
# YOLOv8n gated on ROI (held object classification).
#
# Publishes /detections (std_msgs/String, JSON) at 10 Hz.
# AI outputs do NOT enter the safety path.
# camera_valid in decision_node is a liveness boolean only — set by message arrival.
#
# Dependencies (install on Pi5 before running):
#   sudo apt install python3-picamera2
#   pip3 install mediapipe ultralytics opencv-python-headless
#
# Educational demonstrator — not ISO 26262 certified.

import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

try:
    from picamera2 import Picamera2
    _PICAM_OK = True
except ImportError:
    _PICAM_OK = False

try:
    import mediapipe as mp
    _MP_OK = True
except ImportError:
    _MP_OK = False

try:
    from ultralytics import YOLO
    import numpy as np
    _YOLO_OK = True
except ImportError:
    _YOLO_OK = False

CAPTURE_W     = 640
CAPTURE_H     = 480
PUBLISH_HZ    = 10
HAND_CONF_MIN = 0.60
OBJ_CONF_MIN  = 0.40
ROI_PAD_PX    = 25


class CameraAINode(Node):

    def __init__(self):
        super().__init__('camera_ai_node')
        self._pub = self.create_publisher(String, '/detections', 5)
        self._frame  = 0
        self._hits   = 0

        self._camera = self._init_camera()
        self._hands  = self._init_mediapipe()
        self._yolo   = self._init_yolo()

        self.create_timer(1.0 / PUBLISH_HZ, self._tick)
        self.get_logger().info(
            f'camera_ai_node M4 ready — '
            f'camera={self._camera is not None} '
            f'mediapipe={self._hands is not None} '
            f'yolo={self._yolo is not None}')

    # ── initialisation ────────────────────────────────────────────────────────

    def _init_camera(self):
        if not _PICAM_OK:
            self.get_logger().warn(
                'picamera2 not found — camera inactive. '
                'Fix: sudo apt install python3-picamera2')
            return None
        try:
            cam = Picamera2()
            cfg = cam.create_preview_configuration(
                main={'size': (CAPTURE_W, CAPTURE_H), 'format': 'RGB888'})
            cam.configure(cfg)
            cam.start()
            time.sleep(0.5)   # sensor warm-up
            self.get_logger().info(f'IMX708 started {CAPTURE_W}x{CAPTURE_H} RGB888')
            return cam
        except Exception as e:
            self.get_logger().warn(f'Camera init failed: {e}')
            return None

    def _init_mediapipe(self):
        if not _MP_OK:
            self.get_logger().warn(
                'mediapipe not found — hand detection inactive. '
                'Fix: pip3 install mediapipe')
            return None
        hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=HAND_CONF_MIN,
            min_tracking_confidence=0.5)
        self.get_logger().info(f'MediaPipe Hands ready (conf≥{HAND_CONF_MIN})')
        return hands

    def _init_yolo(self):
        if not _YOLO_OK:
            self.get_logger().warn(
                'ultralytics not found — object classification inactive. '
                'Fix: pip3 install ultralytics')
            return None
        try:
            model = YOLO('yolov8n.pt')   # downloads ~6 MB on first run
            self.get_logger().info('YOLOv8n loaded (held-object classifier)')
            return model
        except Exception as e:
            self.get_logger().warn(f'YOLOv8n load failed: {e}')
            return None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _hand_bbox(self, landmarks, w, h):
        xs = [lm.x * w for lm in landmarks.landmark]
        ys = [lm.y * h for lm in landmarks.landmark]
        return (
            max(0,  int(min(xs)) - ROI_PAD_PX),
            max(0,  int(min(ys)) - ROI_PAD_PX),
            min(w,  int(max(xs)) + ROI_PAD_PX),
            min(h,  int(max(ys)) + ROI_PAD_PX),
        )

    def _classify_held_object(self, frame, x1, y1, x2, y2):
        """YOLOv8n on hand ROI. Returns (class_name, conf) or (None, 0)."""
        if self._yolo is None or x2 <= x1 or y2 <= y1:
            return None, 0.0
        try:
            roi = frame[y1:y2, x1:x2]
            for r in self._yolo(roi, verbose=False, conf=OBJ_CONF_MIN):
                for box in r.boxes:
                    name = self._yolo.names[int(box.cls)]
                    conf = float(box.conf)
                    if name != 'person' and conf >= OBJ_CONF_MIN:
                        return name, round(conf, 3)
        except Exception as e:
            self.get_logger().debug(f'YOLO ROI error: {e}')
        return None, 0.0

    # ── main tick ─────────────────────────────────────────────────────────────

    def _tick(self):
        self._frame += 1

        if self._camera is None or self._hands is None:
            self._pub.publish(String(data=json.dumps({
                'status': 'INACTIVE', 'hand': False,
                'object': None, 'frame': self._frame,
            })))
            return

        try:
            frame = self._camera.capture_array()   # H×W×3 RGB
        except Exception as e:
            self.get_logger().warn(f'Capture error: {e}')
            return

        h, w = frame.shape[:2]
        mp_result = self._hands.process(frame)

        hand      = False
        hand_conf = 0.0
        obj_name  = None
        obj_conf  = 0.0

        if mp_result.multi_hand_landmarks:
            hand = True
            self._hits += 1
            lm = mp_result.multi_hand_landmarks[0]

            if mp_result.multi_handedness:
                hand_conf = round(
                    mp_result.multi_handedness[0].classification[0].score, 3)

            # Gate YOLOv8n on the hand ROI only
            x1, y1, x2, y2 = self._hand_bbox(lm, w, h)
            obj_name, obj_conf = self._classify_held_object(frame, x1, y1, x2, y2)

            if obj_name:
                self.get_logger().info(
                    f'HAND+OBJ  hand={hand_conf:.2f}  '
                    f'obj={obj_name} ({obj_conf:.2f})')
            else:
                self.get_logger().debug(f'HAND  conf={hand_conf:.2f}')

        payload = json.dumps({
            'status':      'RUNNING',
            'hand':        hand,
            'hand_conf':   hand_conf,
            'object':      obj_name,
            'object_conf': obj_conf,
            'frame':       self._frame,
            'detections':  self._hits,
        })
        self._pub.publish(String(data=payload))

    # ── cleanup ───────────────────────────────────────────────────────────────

    def destroy_node(self):
        if self._camera is not None:
            self._camera.stop()
        if self._hands is not None:
            self._hands.close()
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
