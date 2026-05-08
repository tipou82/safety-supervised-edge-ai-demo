#!/usr/bin/env python3
# camera_ai_node — Pi5 Linux domain, M4.
# Design Decision DD-001 Option C: MediaPipe Hands (hand detection) +
# YOLOv8n gated on ROI (held object classification).
#
# Publishes /detections (std_msgs/String, JSON) at 10 Hz.
# Serves annotated MJPEG stream on http://<pi5-ip>:8080 for live viewing.
# AI outputs do NOT enter the safety path.
# camera_valid in decision_node is a liveness boolean only — set by message arrival.
#
# Dependencies (install on Pi5 before running):
#   sudo apt install python3-picamera2
#   pip3 install mediapipe ultralytics opencv-python-headless simplejpeg
#
# Educational demonstrator — not ISO 26262 certified.

import io
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

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

try:
    import cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

CAPTURE_W     = 640
CAPTURE_H     = 480
PUBLISH_HZ    = 10
HAND_CONF_MIN = 0.60
OBJ_CONF_MIN  = 0.40
ROI_PAD_PX    = 25
MJPEG_PORT    = 8080


# ── MJPEG HTTP server ─────────────────────────────────────────────────────────

class _MJPEGHandler(BaseHTTPRequestHandler):
    """Serves a single-client MJPEG stream from the shared frame buffer."""

    def log_message(self, *args):
        pass  # suppress HTTP access logs

    def do_GET(self):
        if self.path != '/':
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type',
                         'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        try:
            while True:
                jpeg = _frame_buffer.get()
                if jpeg is None:
                    time.sleep(0.05)
                    continue
                self.wfile.write(b'--frame\r\n')
                self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                self.wfile.write(jpeg)
                self.wfile.write(b'\r\n')
        except (BrokenPipeError, ConnectionResetError):
            pass


class _FrameBuffer:
    """Thread-safe single-slot frame buffer for the MJPEG server."""

    def __init__(self):
        self._lock  = threading.Lock()
        self._frame = None

    def put(self, jpeg_bytes: bytes):
        with self._lock:
            self._frame = jpeg_bytes

    def get(self):
        with self._lock:
            return self._frame


_frame_buffer = _FrameBuffer()


def _start_mjpeg_server(port: int):
    server = HTTPServer(('0.0.0.0', port), _MJPEGHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ── ROS2 node ─────────────────────────────────────────────────────────────────

class CameraAINode(Node):

    def __init__(self):
        super().__init__('camera_ai_node')
        self._pub    = self.create_publisher(String, '/detections', 5)
        self._frame  = 0
        self._hits   = 0

        self._camera = self._init_camera()
        self._hands  = self._init_mediapipe()
        self._yolo   = self._init_yolo()

        # MJPEG server
        if _CV2_OK:
            _start_mjpeg_server(MJPEG_PORT)
            self.get_logger().info(
                f'MJPEG stream: http://<pi5-ip>:{MJPEG_PORT}  (open in browser)')
        else:
            self.get_logger().warn('cv2 not available — MJPEG stream disabled')

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
            time.sleep(0.5)
            self.get_logger().info(f'IMX708 started {CAPTURE_W}x{CAPTURE_H} RGB888')
            return cam
        except Exception as e:
            self.get_logger().warn(f'Camera init failed: {e}')
            return None

    def _init_mediapipe(self):
        if not _MP_OK:
            self.get_logger().warn(
                'mediapipe not found. Fix: pip3 install mediapipe')
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
                'ultralytics not found. Fix: pip3 install ultralytics')
            return None
        try:
            model = YOLO('yolov8n.pt')
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
            max(0, int(min(xs)) - ROI_PAD_PX),
            max(0, int(min(ys)) - ROI_PAD_PX),
            min(w, int(max(xs)) + ROI_PAD_PX),
            min(h, int(max(ys)) + ROI_PAD_PX),
        )

    def _classify_held_object(self, frame, x1, y1, x2, y2):
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

    def _annotate_and_stream(self, frame_rgb, landmarks, x1, y1, x2, y2,
                              hand_conf, obj_name, obj_conf, state_label):
        """Draw detections on frame and push JPEG to MJPEG buffer."""
        if not _CV2_OK:
            return
        # RGB → BGR for OpenCV
        img = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        if landmarks is not None:
            # Hand bounding box — green
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 220, 0), 2)
            label = f'Hand {hand_conf:.2f}'
            if obj_name:
                label += f'  +{obj_name} {obj_conf:.2f}'
                # Object label — yellow
                cv2.rectangle(img, (x1, y1 - 25), (x2, y1), (0, 220, 220), -1)
                cv2.putText(img, obj_name, (x1 + 4, y1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)
            cv2.putText(img, label, (x1, y2 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 0), 1)

            # MediaPipe landmarks — small dots
            mp.solutions.drawing_utils.draw_landmarks(
                img,
                landmarks,
                mp.solutions.hands.HAND_CONNECTIONS,
                mp.solutions.drawing_utils.DrawingSpec(
                    color=(0, 200, 0), thickness=1, circle_radius=2),
                mp.solutions.drawing_utils.DrawingSpec(
                    color=(0, 150, 0), thickness=1))

        # State overlay — top-left
        colour = (0, 220, 0)   # green = NORMAL
        if 'WARNING'    in state_label: colour = (0, 220, 220)   # yellow
        if 'DEGRADED'   in state_label: colour = (0, 140, 255)   # orange
        if 'SAFE_STATE' in state_label: colour = (0, 0, 220)     # red
        if 'INIT'       in state_label: colour = (180, 180, 180) # grey
        cv2.rectangle(img, (0, 0), (200, 28), (0, 0, 0), -1)
        cv2.putText(img, state_label, (6, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, colour, 2)

        _, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        _frame_buffer.put(jpeg.tobytes())

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
            frame = self._camera.capture_array()
        except Exception as e:
            self.get_logger().warn(f'Capture error: {e}')
            return

        h, w = frame.shape[:2]
        mp_result = self._hands.process(frame)

        hand      = False
        hand_conf = 0.0
        obj_name  = None
        obj_conf  = 0.0
        lm        = None
        x1 = y1 = x2 = y2 = 0

        if mp_result.multi_hand_landmarks:
            hand = True
            self._hits += 1
            lm = mp_result.multi_hand_landmarks[0]

            if mp_result.multi_handedness:
                hand_conf = round(
                    mp_result.multi_handedness[0].classification[0].score, 3)

            x1, y1, x2, y2 = self._hand_bbox(lm, w, h)
            obj_name, obj_conf = self._classify_held_object(frame, x1, y1, x2, y2)

            if obj_name:
                self.get_logger().info(
                    f'HAND+OBJ  hand={hand_conf:.2f}  '
                    f'obj={obj_name} ({obj_conf:.2f})')
            else:
                self.get_logger().debug(f'HAND  conf={hand_conf:.2f}')

        # Annotate and push to MJPEG stream
        state_label = 'RUNNING'
        self._annotate_and_stream(
            frame, lm, x1, y1, x2, y2,
            hand_conf, obj_name, obj_conf, state_label)

        self._pub.publish(String(data=json.dumps({
            'status':      'RUNNING',
            'hand':        hand,
            'hand_conf':   hand_conf,
            'object':      obj_name,
            'object_conf': obj_conf,
            'frame':       self._frame,
            'detections':  self._hits,
        })))

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
