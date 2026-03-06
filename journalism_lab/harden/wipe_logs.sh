#!/bin/bash
set -euo pipefail
sudo journalctl --rotate || true
sudo journalctl --vacuum-time=1s || true
sudo rm -rf /var/log/journal/* || true
sudo rm -rf /var/log/*.log* || true
sudo find /var/log -type f -name "*.gz" -delete || true
sudo sync
echo "logs wiped"
