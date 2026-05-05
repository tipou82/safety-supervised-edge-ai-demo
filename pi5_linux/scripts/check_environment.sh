#!/bin/bash
# check_environment.sh — Pi 5 platform access baseline check
# Run on Raspberry Pi 5 during M1.0 Platform Access Baseline.
# Does not install packages. Prints status for manual logbook entry.

set -euo pipefail

echo "======================================================"
echo " Pi 5 Environment Check — M1.0 Platform Access Baseline"
echo " $(date)"
echo "======================================================"
echo ""

echo "--- OS Release ---"
if [ -f /etc/os-release ]; then
    cat /etc/os-release
else
    echo "WARNING: /etc/os-release not found"
fi
echo ""

echo "--- Kernel Version ---"
uname -r
echo ""

echo "--- Hostname ---"
hostname
echo ""

echo "--- IP Addresses ---"
ip addr show | grep -E "^[0-9]+:|inet " | grep -v "127.0.0.1"
echo ""

echo "--- Python Version ---"
if command -v python3 &>/dev/null; then
    python3 --version
else
    echo "python3: not found"
fi
echo ""

echo "--- Git Version ---"
if command -v git &>/dev/null; then
    git --version
else
    echo "git: not found"
fi
echo ""

echo "--- Camera Command Availability ---"
if command -v rpicam-hello &>/dev/null; then
    echo "rpicam-hello: found ($(which rpicam-hello))"
elif command -v libcamera-hello &>/dev/null; then
    echo "libcamera-hello: found ($(which libcamera-hello))"
else
    echo "rpicam-hello: not found"
    echo "libcamera-hello: not found"
    echo "NOTE: Install libcamera-apps or rpicam-apps if camera testing is needed."
fi
echo ""

echo "--- GPIO Package Hints ---"
if python3 -c "import RPi.GPIO" 2>/dev/null; then
    echo "RPi.GPIO: available"
else
    echo "RPi.GPIO: not importable (install with: sudo apt install python3-rpi.gpio)"
fi

if command -v gpioinfo &>/dev/null; then
    echo "gpiod (gpioinfo): found ($(which gpioinfo))"
else
    echo "gpiod (gpioinfo): not found (install with: sudo apt install gpiod)"
fi
echo ""

echo "======================================================"
echo " Check complete. Copy output above into engineering logbook."
echo "======================================================"
