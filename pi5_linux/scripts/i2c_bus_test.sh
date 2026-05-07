#!/usr/bin/env bash
# M2 hardware bring-up: I2C bus health check (Pi5 side).
# Verifies I2C-1 bus is up on GPIO 2/3 and scans for devices.
# Pi400 I2C slave software is not yet running — no device at 0x40 is expected yet.
# This script only confirms the bus is wired and functional.
# Educational demonstrator — not ISO 26262 certified.

set -euo pipefail

PASS="[PASS]"
FAIL="[FAIL]"
INFO="[INFO]"

echo "======================================================"
echo " M2 I2C Bus Health Check (Pi5 — master side)"
echo " Educational demonstrator — not ISO 26262 certified"
echo "======================================================"
echo ""
echo "Wiring expected:"
echo "  GPIO 2 (Pin 3) — SDA — connected to Pi400 GPIO 2 (Pin 3)"
echo "  GPIO 3 (Pin 5) — SCL — connected to Pi400 GPIO 3 (Pin 5)"
echo "  4.7 kΩ pull-ups to 3.3V on both SDA and SCL"
echo "  Common GND: Pi5 Pin 6 — Pi400 Pin 6"
echo ""

# --- Step 1: i2c-tools installed? ---
echo "--- Step 1: i2c-tools availability ---"
if command -v i2cdetect &>/dev/null; then
    echo "$PASS i2cdetect found: $(command -v i2cdetect)"
else
    echo "$FAIL i2cdetect not found."
    echo "       Install with: sudo apt install i2c-tools"
    exit 1
fi
echo ""

# --- Step 2: I2C bus device present ---
echo "--- Step 2: I2C bus device ---"
if ls /dev/i2c-1 &>/dev/null; then
    echo "$PASS /dev/i2c-1 present"
elif ls /dev/i2c-* &>/dev/null 2>&1; then
    BUSES=$(ls /dev/i2c-* 2>/dev/null | tr '\n' ' ')
    echo "$INFO /dev/i2c-1 not found; available buses: $BUSES"
    echo "       Ensure I2C is enabled: sudo raspi-config → Interface Options → I2C"
    echo "       Or add dtparam=i2c_arm=on to /boot/firmware/config.txt and reboot"
    exit 1
else
    echo "$FAIL No /dev/i2c-* devices found."
    echo "       Enable I2C: sudo raspi-config → Interface Options → I2C"
    exit 1
fi
echo ""

# --- Step 3: Bus scan ---
echo "--- Step 3: I2C bus scan (i2cdetect -y 1) ---"
echo "$INFO Scanning I2C-1 (GPIO 2/3)..."
echo ""
i2cdetect -y 1 2>&1 || true
echo ""
echo "$INFO Expected at this stage: no device at 0x40 (Pi400 slave not yet running)."
echo "$INFO If 0x40 appears, Pi400 I2C slave software is already active — unexpected but OK."
echo ""

# --- Step 4: Pull-up check (voltage level) ---
echo "--- Step 4: SDA/SCL idle voltage ---"
echo "$INFO With pull-ups fitted, SDA and SCL should idle near 3.3V when bus is free."
echo "$INFO Measure with multimeter: Pi5 Pin 3 (SDA) and Pin 5 (SCL) to GND."
echo "$INFO Expected: ~3.2–3.3V"
echo ""
read -r -p "Are both SDA and SCL reading ~3.3V idle? (yes/no/skip): " answer
case "$answer" in
    yes)  echo "$PASS Pull-up voltage confirmed." ;;
    skip) echo "$INFO Skipped — verify manually if I2C communication fails later." ;;
    *)    echo "$FAIL SDA/SCL not at 3.3V. Check pull-up resistors (4.7 kΩ to 3.3V) on both lines." ;;
esac
echo ""

echo "======================================================"
echo " I2C Bus Test Summary"
echo "======================================================"
echo "  Bus /dev/i2c-1: present"
echo "  Scan: complete (see output above)"
echo "  Next: once Pi400 I2C slave (address 0x40) is running,"
echo "        re-run and confirm 0x40 appears in scan."
echo "  Command: sudo i2cdetect -y 1"
echo ""
echo "Done."
