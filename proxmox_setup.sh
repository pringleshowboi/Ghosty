#!/bin/bash
set -euo pipefail

VMID="${VMID:-100}"
VM_NAME="${VM_NAME:-whonix-ws-sentinel}"
STORAGE_POOL="${STORAGE_POOL:-local-lvm}"
BRIDGE="${BRIDGE:-vmbr0}"
MEMORY_MB="${MEMORY_MB:-4096}"
CORES="${CORES:-4}"
VERACRYPT_DISK_SIZE="${VERACRYPT_DISK_SIZE:-100G}"
WHONIX_QCOW2="${WHONIX_QCOW2:-}"
TOR_SOCKS="${TOR_SOCKS:-}"

if ! command -v qm >/dev/null; then
  echo "This must run on a Proxmox host with qm available."
  exit 1
fi

if [ -n "$TOR_SOCKS" ]; then
  export https_proxy="$TOR_SOCKS"
  export http_proxy="$TOR_SOCKS"
fi

echo "VMID=$VMID"
echo "VM_NAME=$VM_NAME"
echo "STORAGE_POOL=$STORAGE_POOL"
echo "BRIDGE=$BRIDGE"
echo "MEMORY_MB=$MEMORY_MB"
echo "CORES=$CORES"
echo "VERACRYPT_DISK_SIZE=$VERACRYPT_DISK_SIZE"

if [ -z "${WHONIX_QCOW2}" ]; then
  echo "Path or URL to Whonix Workstation KVM qcow2 image is required."
  echo "Example (KVM): https://www.whonix.org/wiki/Download#KVM"
  read -r -p "Enter path or URL to Whonix KVM qcow2 (leave blank to abort): " WHONIX_QCOW2
fi

if [ -z "${WHONIX_QCOW2}" ]; then
  echo "No image provided. Aborting."
  exit 1
fi

WORKDIR="$(pwd)/.whonix_import"
mkdir -p "$WORKDIR"
QCOW2_LOCAL="$WORKDIR/whonix-ws.qcow2"

if [[ "$WHONIX_QCOW2" =~ ^https?:// ]]; then
  echo "Downloading qcow2..."
  if command -v wget >/dev/null; then
    wget -O "$QCOW2_LOCAL" "$WHONIX_QCOW2"
  else
    curl -fL -o "$QCOW2_LOCAL" "$WHONIX_QCOW2"
  fi
else
  cp "$WHONIX_QCOW2" "$QCOW2_LOCAL"
fi

if [ ! -s "$QCOW2_LOCAL" ]; then
  echo "qcow2 not found or empty: $QCOW2_LOCAL"
  exit 1
fi

echo "Creating VM..."
qm create "$VMID" \
  --name "$VM_NAME" \
  --memory "$MEMORY_MB" \
  --cores "$CORES" \
  --cpu host \
  --machine q35 \
  --scsihw virtio-scsi-pci \
  --agent enabled=1 \
  --ostype l26 \
  --net0 virtio,bridge="$BRIDGE"

echo "Importing disk..."
qm importdisk "$VMID" "$QCOW2_LOCAL" "$STORAGE_POOL"

echo "Attaching disk and boot order..."
qm set "$VMID" --scsi0 "$STORAGE_POOL:vm-$VMID-disk-0"
qm set "$VMID" --boot order=scsi0

echo "Adding VeraCrypt raw disk..."
qm set "$VMID" --scsi1 "$STORAGE_POOL:$VERACRYPT_DISK_SIZE"

cat > veracrypt_install.sh << 'EOF'
#!/bin/bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y wget xz-utils
echo "Download VeraCrypt .deb and install with: sudo dpkg -i veracrypt-*.deb"
EOF
chmod +x veracrypt_install.sh

echo "VM created. Start with: qm start $VMID"
echo "Then copy veracrypt_install.sh into the VM and run it."
