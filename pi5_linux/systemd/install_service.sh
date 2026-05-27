#!/bin/bash
# install_service.sh — Pi5: install and enable safety-demo systemd service
# Run once on Pi5: bash pi5_linux/systemd/install_service.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/safety-demo.service"
DEST="/etc/systemd/system/safety-demo.service"

echo "=== Installing safety-demo service on Pi5 ==="

# Adjust User= and paths if your username differs from 'yunpeng'
CURRENT_USER="$(whoami)"
if [ "$CURRENT_USER" != "yunpeng" ]; then
    echo "Note: replacing User=yunpeng with User=$CURRENT_USER in service file"
    sed "s/User=yunpeng/User=$CURRENT_USER/g; s|/home/yunpeng|/home/$CURRENT_USER|g" \
        "$SERVICE_FILE" > /tmp/safety-demo.service
    SERVICE_FILE="/tmp/safety-demo.service"
fi

sudo cp "$SERVICE_FILE" "$DEST"
sudo systemctl daemon-reload
sudo systemctl enable safety-demo.service
echo ""
echo "Service installed and enabled."
echo "Start now:    sudo systemctl start safety-demo"
echo "Check status: sudo systemctl status safety-demo"
echo "View logs:    journalctl -fu safety-demo"
