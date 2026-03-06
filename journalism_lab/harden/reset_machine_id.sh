#!/bin/bash
set -euo pipefail
sudo systemctl stop dbus || true
sudo rm -f /etc/machine-id /var/lib/dbus/machine-id
sudo systemd-machine-id-setup
echo "machine-id reset"
