#!/bin/bash
# install_service.sh — Pi400: install and enable safety-supervisor systemd service
# Run once on Pi400: bash pi400_supervisor/systemd/install_service.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/safety-supervisor.service"
DEST="/etc/systemd/system/safety-supervisor.service"

echo "=== Installing safety-supervisor service on Pi400 ==="

# Adjust User= if your username differs from 'yunpeng'
CURRENT_USER="$(whoami)"
if [ "$CURRENT_USER" != "yunpeng" ]; then
    echo "Note: replacing User=yunpeng with User=$CURRENT_USER in service file"
    sed "s/User=yunpeng/User=$CURRENT_USER/g; s|/home/yunpeng|/home/$CURRENT_USER|g" \
        "$SERVICE_FILE" > /tmp/safety-supervisor.service
    SERVICE_FILE="/tmp/safety-supervisor.service"
fi

sudo cp "$SERVICE_FILE" "$DEST"
sudo systemctl daemon-reload
sudo systemctl enable safety-supervisor.service
echo ""
echo "Service installed and enabled."
echo "Start now:    sudo systemctl start safety-supervisor"
echo "Check status: sudo systemctl status safety-supervisor"
echo "View logs:    journalctl -fu safety-supervisor"
