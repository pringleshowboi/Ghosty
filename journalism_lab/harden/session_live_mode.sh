#!/bin/bash
set -euo pipefail

echo "Mounting tmpfs for /tmp and /var/tmp ..."
sudo mount -t tmpfs -o size=2G tmpfs /tmp || true
sudo mount -t tmpfs -o size=1G tmpfs /var/tmp || true

echo "Disabling shell history for this session ..."
export HISTFILE=/dev/null
unset HISTFILE
export HISTSIZE=0
export HISTCONTROL=ignorespace:ignoredups

echo "Setting journald to volatile storage (runtime only) ..."
if [ -w /etc/systemd/journald.conf ]; then
  sudo cp /etc/systemd/journald.conf /etc/systemd/journald.conf.bak || true
  sudo sed -i 's/^#\?Storage=.*/Storage=volatile/' /etc/systemd/journald.conf
  sudo systemctl restart systemd-journald || true
fi

echo "Session live-mode applied. All temp writes go to RAM; history disabled."
echo "Reboot to revert journald; unmount tmpfs with: sudo umount /tmp /var/tmp"

