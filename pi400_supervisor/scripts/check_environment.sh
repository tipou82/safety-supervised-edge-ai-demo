#!/bin/bash
# check_environment.sh — Pi 400 platform access baseline check
# Run on Raspberry Pi 400 during M1.0 Platform Access Baseline.
# Supports Linux only. QNX supervisor setup is planned but not required for M1.0.
# Does not install packages. Prints status for manual logbook entry.
#
# NOTE: The QNX supervisor is planned and optional for this demonstrator.
# If QNX is not yet installed, run this script under Linux and document
# the fallback decision in the engineering logbook.

set -euo pipefail

echo "======================================================"
echo " Pi 400 Environment Check — M1.0 Platform Access Baseline"
echo " $(date)"
echo "======================================================"
echo ""

echo "--- QNX / Linux Status ---"
echo "NOTE: QNX supervisor is planned and optional. Linux fallback is acceptable."
echo "      Document the OS choice in the engineering logbook."
echo ""

echo "--- OS Release (Linux only) ---"
if [ -f /etc/os-release ]; then
    cat /etc/os-release
else
    echo "WARNING: /etc/os-release not found."
    echo "         If running QNX, use 'uname -a' instead (run manually)."
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

echo "--- Git Version ---"
if command -v git &>/dev/null; then
    git --version
else
    echo "git: not found (install with: sudo apt install git)"
fi
echo ""

echo "--- C++ Compiler Availability ---"
if command -v g++ &>/dev/null; then
    echo "g++: found ($(g++ --version | head -1))"
elif command -v c++ &>/dev/null; then
    echo "c++: found ($(c++ --version | head -1))"
else
    echo "g++/c++: not found (install with: sudo apt install build-essential)"
fi
echo ""

echo "======================================================"
echo " Check complete. Copy output above into engineering logbook."
echo " Remember to document QNX or Linux fallback decision explicitly."
echo "======================================================"
