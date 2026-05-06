#!/usr/bin/env bash
# M1.1 – Pi5 Hardware Component Bring-up: camera detection smoke test.
# This script checks for camera tools and devices only.
# It is NOT part of any ROS2 node or AI inference pipeline.

set -euo pipefail

PASS="[PASS]"
FAIL="[FAIL]"
TODO="[TODO]"
INFO="[INFO]"

echo "======================================================"
echo " M1.1 Camera Detection Smoke Test"
echo " Educational demonstrator — not ISO 26262 certified"
echo "======================================================"
echo ""

# --- 1. Check camera tools ---
echo "--- Step 1: Camera tool availability ---"

RPICAM_HELLO=""
if command -v rpicam-hello &>/dev/null; then
    RPICAM_HELLO=$(command -v rpicam-hello)
    echo "$PASS rpicam-hello found: $RPICAM_HELLO"
elif command -v libcamera-hello &>/dev/null; then
    RPICAM_HELLO=$(command -v libcamera-hello)
    echo "$PASS libcamera-hello found (older alias): $RPICAM_HELLO"
else
    echo "$INFO rpicam-hello / libcamera-hello not available on Ubuntu 24.04."
    echo "       Using 'cam' (libcamera-tools) instead."
fi

CAM_TOOL=""
if command -v cam &>/dev/null; then
    CAM_TOOL=$(command -v cam)
    echo "$PASS cam (libcamera-tools) found: $CAM_TOOL"
else
    echo "$FAIL cam not found. Install with: sudo apt install libcamera-tools"
fi

V4L2=""
if command -v v4l2-ctl &>/dev/null; then
    V4L2=$(command -v v4l2-ctl)
    echo "$PASS v4l2-ctl found: $V4L2"
else
    echo "$FAIL v4l2-ctl not found."
    echo "       To install: sudo apt install v4l-utils"
fi

echo ""

# --- 2. Check /dev/video devices ---
echo "--- Step 2: Video devices ---"
VIDEO_DEVS=$(ls /dev/video* 2>/dev/null || true)
if [[ -n "$VIDEO_DEVS" ]]; then
    COUNT=$(echo "$VIDEO_DEVS" | wc -w)
    echo "$PASS $COUNT /dev/video device(s) found:"
    echo "$VIDEO_DEVS" | tr ' ' '\n' | sed 's/^/       /'
else
    echo "$FAIL No /dev/video* devices found."
fi
echo ""

# --- 3. Check device tree for camera ---
echo "--- Step 3: Device tree camera entries ---"
if ls /proc/device-tree/cam* &>/dev/null; then
    echo "$PASS Camera device tree entries present:"
    ls /proc/device-tree/cam* | sed 's/^/       /'
else
    echo "$FAIL No camera entries in /proc/device-tree."
fi
echo ""

# --- 4. List cameras with cam / rpicam / libcamera ---
echo "--- Step 4: Camera list ---"
if [[ -n "$RPICAM_HELLO" ]]; then
    echo "$INFO Running: ${RPICAM_HELLO} --list-cameras"
    CAMERA_LIST=$(timeout 10 "$RPICAM_HELLO" --list-cameras 2>&1 || true)
    echo "$CAMERA_LIST"
    if echo "$CAMERA_LIST" | grep -qi "available camera"; then
        echo "$PASS Camera(s) detected by rpicam/libcamera."
    elif echo "$CAMERA_LIST" | grep -qi "no cameras"; then
        echo "$FAIL No cameras detected. Check CSI ribbon cable and camera module."
    else
        echo "$TODO Could not determine camera status from output. Review above."
    fi
elif [[ -n "$CAM_TOOL" ]]; then
    echo "$INFO Running: cam --list (libcamera-tools)"
    CAMERA_LIST=$(timeout 10 cam --list 2>&1 || true)
    echo "$CAMERA_LIST"
    if echo "$CAMERA_LIST" | grep -qi "Available cameras" && \
       echo "$CAMERA_LIST" | grep -qiE "^\s+[0-9]+:"; then
        echo "$PASS Camera(s) detected by libcamera cam tool."
    elif echo "$CAMERA_LIST" | grep -qi "Available cameras"; then
        echo "$FAIL CSI interface found but no camera module detected."
        echo "       Check: CSI ribbon cable fully inserted, correct orientation."
        echo "       Check: camera module physically connected and powered."
    else
        echo "$TODO Could not determine camera status. Review output above."
    fi
else
    echo "$TODO Skipped — no camera tool available."
    echo "       Install with: sudo apt install libcamera-tools"
fi
echo ""

# --- 5. v4l2 device info (if available) ---
echo "--- Step 5: v4l2 device info ---"
if [[ -n "$V4L2" ]]; then
    echo "$INFO Running: v4l2-ctl --list-devices"
    v4l2-ctl --list-devices 2>&1 | sed 's/^/       /' || true
    echo "$PASS v4l2-ctl output complete."
else
    echo "$TODO Skipped — v4l2-ctl not installed."
    echo "       Install with: sudo apt install v4l-utils"
fi
echo ""

# --- Summary ---
echo "======================================================"
echo " Camera Test Summary"
echo "======================================================"
echo ""
echo "Next steps if camera not detected:"
echo "  1. sudo apt install libcamera-tools v4l-utils  (Ubuntu 24.04)"
echo "  2. Check CSI cable: fully inserted, metal contacts facing correct direction"
echo "  3. Re-run this script"
echo ""
echo "This script does NOT start a camera preview (no display available)."
echo "To test still capture once camera is detected:"
echo "  cam -c 0 --capture=1 -o /tmp/test_capture.jpg"
echo "  ls -lh /tmp/test_capture.jpg"
echo ""
echo "Done."
