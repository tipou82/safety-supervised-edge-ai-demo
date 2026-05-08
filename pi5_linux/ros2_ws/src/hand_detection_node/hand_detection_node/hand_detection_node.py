#!/usr/bin/env python3
# hand_detection_node — Pi5, M7 Spatial FFI.
# Owns: picamera2 (IMX708) + MediaPipe Hands.
# Runs as a separate Linux process from object_detection_node.
# MMU provides spatial isolation between the two AI algorithms.
#
# Publishes:
#   /hand_detections  (std_msgs/String JSON) at 10 Hz — hand presence + bbox
#   /hand_roi         (sensor_msgs/CompressedImage) — JPEG ROI, only when hand detected
#   MJPEG stream      on http://<pi5-ip>:8080
#
# object_detection_node subscribes to /hand_roi to run YOLOv8n.
# decision_node subscribes to /detections (published by object_detection_node).
#
# Educational demonstrator — not ISO 26262 certified.

import io
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String

try:
    from picamera2 import Picamera2
    _PICAM_OK = True
except ImportError:
    _PICAM_OK = False

try:
    import mediapipe as mp
    import numpy as np
    _MP_OK = True
except ImportError:
    _MP_OK = False

try:
    import cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

CAPTURE_W     = 640
CAPTURE_H     = 480
PUBLISH_HZ    = 10
HAND_CONF_MIN = 0.60
ROI_PAD_PX    = 25
MJPEG_PORT    = 8080


# ── MJPEG server ──────────────────────────────────────────────────────────────

class _FrameBuffer:
    def __init__(self):
        self._lock, self._frame = threading.Lock(), None

    def put(self, jpeg: bytes):
        with self._lock:
            self._frame = jpeg

    def get(self):
        with self._lock:
            return self._frame


_fb = _FrameBuffer()


class _MJPEGHandler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path != '/':
            self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        try:
            while True:
                j = _fb.get()
                if j is None:
                    time.sleep(0.05); continue
                self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n')
                self.wfile.write(j)
                self.wfile.write(b'\r\n')
        except (BrokenPipeError, ConnectionResetError):
            pass


def _start_mjpeg(port):
    s = HTTPServer(('0.0.0.0', port), _MJPEGHandler)
    threading.Thread(target=s.serve_forever, daemon=True).start()


# ── ROS2 node ─────────────────────────────────────────────────────────────────

class HandDetectionNode(Node):

    def __init__(self):
        super().__init__('hand_detection_node')

        self._det_pub = self.create_publisher(String,           '/hand_detections', 5)
        self._roi_pub = self.create_publisher(CompressedImage,  '/hand_roi',        5)

        self._camera = self._init_camera()
        self._hands  = self._init_mediapipe()

        if _CV2_OK:
            _start_mjpeg(MJPEG_PORT)
            self.get_logger().info(f'MJPEG stream: http://<pi5-ip>:{MJPEG_PORT}')

        self._frame_count = 0
        self._hit_count   = 0
        self.create_timer(1.0 / PUBLISH_HZ, self._tick)

        self.get_logger().info(
            f'hand_detection_node M7 — separate process from object_detection_node '
            f'(MMU spatial isolation). camera={self._camera is not None} '
            f'mediapipe={self._hands is not None}')

    def _init_camera(self):
        if not _PICAM_OK:
            self.get_logger().warn('picamera2 not found')
            return None
        try:
            cam = Picamera2()
            cam.configure(cam.create_preview_configuration(
                main={'size': (CAPTURE_W, CAPTURE_H), 'format': 'RGB888'}))
            cam.start()
            time.sleep(0.5)
            self.get_logger().info(f'IMX708 started {CAPTURE_W}×{CAPTURE_H}')
            return cam
        except Exception as e:
            self.get_logger().warn(f'Camera init failed: {e}')
            return None

    def _init_mediapipe(self):
        if not _MP_OK:
            self.get_logger().warn('mediapipe not found')
            return None
        h = mp.solutions.hands.Hands(
            static_image_mode=False, max_num_hands=1,
            min_detection_confidence=HAND_CONF_MIN,
            min_tracking_confidence=0.5)
        self.get_logger().info('MediaPipe Hands ready')
        return h

    def _hand_bbox(self, lm, w, h):
        xs = [l.x * w for l in lm.landmark]
        ys = [l.y * h for l in lm.landmark]
        return (max(0, int(min(xs)) - ROI_PAD_PX),
                max(0, int(min(ys)) - ROI_PAD_PX),
                min(w, int(max(xs)) + ROI_PAD_PX),
                min(h, int(max(ys)) + ROI_PAD_PX))

    def _tick(self):
        self._frame_count += 1

        if self._camera is None or self._hands is None:
            self._det_pub.publish(String(data=json.dumps(
                {'status': 'INACTIVE', 'hand': False, 'frame': self._frame_count})))
            return

        try:
            frame = self._camera.capture_array()
        except Exception as e:
            self.get_logger().warn(f'Capture: {e}')
            return

        h, w = frame.shape[:2]
        result = self._hands.process(frame)

        hand = False
        hand_conf = 0.0
        x1 = y1 = x2 = y2 = 0
        lm_obj = None

        if result.multi_hand_landmarks:
            hand = True
            self._hit_count += 1
            lm_obj = result.multi_hand_landmarks[0]
            if result.multi_handedness:
                hand_conf = round(
                    result.multi_handedness[0].classification[0].score, 3)
            x1, y1, x2, y2 = self._hand_bbox(lm_obj, w, h)

            # Publish ROI for object_detection_node
            if _CV2_OK and x2 > x1 and y2 > y1:
                roi_bgr = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_RGB2BGR)
                ok, jpeg = cv2.imencode('.jpg', roi_bgr,
                                        [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ok:
                    roi_msg = CompressedImage()
                    roi_msg.header.stamp = self.get_clock().now().to_msg()
                    roi_msg.format = 'jpeg'
                    roi_msg.data   = jpeg.tobytes()
                    self._roi_pub.publish(roi_msg)

        # Publish detection info
        self._det_pub.publish(String(data=json.dumps({
            'status':    'RUNNING',
            'hand':      hand,
            'hand_conf': hand_conf,
            'bbox':      [x1, y1, x2, y2],
            'frame':     self._frame_count,
            'hits':      self._hit_count,
        })))

        # MJPEG annotation
        if _CV2_OK:
            img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            if lm_obj:
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 220, 0), 2)
                cv2.putText(img, f'Hand {hand_conf:.2f}',
                            (x1, y2 + 18), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 220, 0), 1)
                if _MP_OK:
                    mp.solutions.drawing_utils.draw_landmarks(
                        img, lm_obj, mp.solutions.hands.HAND_CONNECTIONS,
                        mp.solutions.drawing_utils.DrawingSpec(
                            color=(0, 200, 0), thickness=1, circle_radius=2),
                        mp.solutions.drawing_utils.DrawingSpec(
                            color=(0, 150, 0), thickness=1))
            _, j = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
            _fb.put(j.tobytes())

    def destroy_node(self):
        if self._camera:
            self._camera.stop()
        if self._hands:
            self._hands.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HandDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
