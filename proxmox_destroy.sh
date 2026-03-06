#!/bin/bash
set -euo pipefail

VMID="${1:-100}"

if ! command -v qm >/dev/null; then
  echo "Run on a Proxmox host (qm required)"; exit 1
fi

if ! qm status "$VMID" >/dev/null 2>&1; then
  echo "VMID $VMID not found"; exit 1
fi

echo "Collecting attached volumes..."
DISKS=$(qm config "$VMID" | awk -F': ' '/^scsi[0-9]+:|^sata[0-9]+:|^ide[0-9]+:/ {print $2}' | awk -F',' '{print $1}')

echo "Stopping VM if running..."
if qm status "$VMID" | grep -q running; then
  qm stop "$VMID" || true
fi

echo "Destroying VM and removing config..."
qm destroy "$VMID" --purge || qm destroy "$VMID" || true

for VOL in $DISKS; do
  if [[ "$VOL" == *":"* ]]; then
    echo "Freeing storage volume: $VOL"
    pvesm free "$VOL" || true
  fi
done

echo "Proxmox VM $VMID destroyed and volumes freed (best-effort)."

