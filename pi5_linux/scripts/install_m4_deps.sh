#!/usr/bin/env bash
# M4 dependency installation — Pi5 only (Raspberry Pi OS Bookworm).
# Installs camera AI dependencies: picamera2, MediaPipe, Ultralytics YOLOv8n.
# Run once before building the ROS2 workspace for M4.
# Educational demonstrator — not ISO 26262 certified.

set -euo pipefail

echo "======================================================"
echo " M4 Camera AI Dependency Installation"
echo " Pi5 / Raspberry Pi OS Bookworm only"
echo "======================================================"
echo ""

# picamera2 — RPi OS package (do not use pip3 version)
echo "--- Installing picamera2 ---"
sudo apt install -y python3-picamera2

# OpenCV headless (no GUI, saves space)
echo "--- Installing OpenCV ---"
pip3 install --break-system-packages opencv-python-headless

# MediaPipe — hand detection
echo "--- Installing MediaPipe ---"
pip3 install --break-system-packages mediapipe

# Ultralytics — YOLOv8n (downloads model on first run ~6 MB)
echo "--- Installing Ultralytics ---"
pip3 install --break-system-packages ultralytics

echo ""
echo "======================================================"
echo " Verification"
echo "======================================================"
python3 -c "from picamera2 import Picamera2; print('[PASS] picamera2')" 2>/dev/null || echo "[FAIL] picamera2"
python3 -c "import mediapipe; print('[PASS] mediapipe', mediapipe.__version__)" 2>/dev/null || echo "[FAIL] mediapipe"
python3 -c "import ultralytics; print('[PASS] ultralytics', ultralytics.__version__)" 2>/dev/null || echo "[FAIL] ultralytics"
python3 -c "import cv2; print('[PASS] opencv', cv2.__version__)" 2>/dev/null || echo "[FAIL] opencv"

echo ""
echo "Done. Now rebuild the ROS2 workspace:"
echo "  cd ~/safety-supervised-edge-ai-demo/pi5_linux/ros2_ws"
echo "  source ~/ros2_humble/install/setup.bash"
echo "  colcon build --merge-install"
