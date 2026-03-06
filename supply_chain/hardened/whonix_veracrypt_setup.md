# Whonix + VeraCrypt Hardened Layer for Proxmox

Goal: run the entire AD Anomaly Hunter stack inside a Whonix-Workstation VM whose disk is a VeraCrypt encrypted volume mounted on Proxmox. The setup gives you:
- Tor-routed management plane (no clearnet leaks)
- Cold-boot attack resistance (VeraCrypt pre-boot auth + hidden OS option)
- Snapshot-immune evidence locker (VeraCrypt outer volume + hidden inner volume)

## 0. Prerequisites on Proxmox
- Upload Whonix-Gateway and Whonix-Workstation qcow2 images to `/var/lib/vz/images/<vmid>/`
- Create Linux Bridge `vmbr1` (internal only, no NIC attached) for isolated Tor gateway
- Reserve a USB passthrough port for the VeraCrypt rescue stick (optional but recommended)

## 1. VeraCrypt Encrypted Disk (CLI recipe)

Create an encrypted volume that Proxmox can later attach to the Whonix-Workstation:

```bash
# on Proxmox host
apt install veracrypt -y
dd if=/dev/zero of=/var/lib/vz/images/ahunter-vcrypt.img bs=1M count=30720   # 30 GB
veracrypt --text --create /var/lib/vz/images/ahunter-vcrypt.img \
  --password="$(openssl rand -base64 32)" \
  --encryption=AES-Twofish-Serpent --hash=sha-512 --filesystem=ext4 \
  --size=30720 --volume-type=normal --pim=0 --random-source=/dev/urandom
```

Store the password in your password manager; we’ll feed it to the VM later via a oneshot systemd service so it auto-mounts at boot.

## 2. Whonix-Gateway VM (tor-router)
- Create VM: `qm create 200 --memory 2048 --net0 virtio,bridge=vmbr0` (vmbr0 = clearnet NIC)
- Import disk: `qm importdisk 200 /var/lib/vz/images/whonix-gateway.qcow2 local-lvm`
- Attach as scsi0, enable QEMU agent
- Add second NIC on `vmbr1` (internal) for Workstation uplink
- Start VM; verify Tor bootstrap: `systemctl status tor@default`

## 3. Whonix-Workstation VM (AD Anomaly Hunter host)
- Create VM: `qm create 201 --memory 4096 --cores 4 --net0 virtio,bridge=vmbr1`
- Import workstation disk: `qm importdisk 201 /var/lib/vz/images/whonix-workstation.qcow2 local-lvm` → scsi0
- Add encrypted data disk: `qm set 201 --scsi1 /var/lib/vz/images/ahunter-vcrypt.img`
- Enable QEMU agent, CPU host passthrough (for AES-NI acceleration)
- Optional: USB passthrough for YubiKey or rescue stick:
  `qm set 201 --usb0 host=1050:0407`  # YubiKey 5 example

## 4. Auto-Mount VeraCrypt Volume inside Workstation

Create a systemd unit that unlocks and mounts the encrypted disk at boot:

```bash
# inside Whonix-Workstation
sudo tee /etc/systemd/system/ahunter-crypt.service <<'EOF'
[Unit]
Description=Mount AD Anomaly Hunter encrypted volume
After=systemd-modules-load.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/veracrypt --text --mount /dev/sdb1 /mnt/ahunter --password="%h" --pim=0 --protect-hidden=no
ExecStop=/usr/bin/veracrypt --text --dismount /dev/sdb1
# store password in root-owned env file
EnvironmentFile=/etc/ahunter-vcrypt.env

[Install]
WantedBy=multi-user.target
EOF

echo "VC_PASS=YOUR_VERY_LONG_PASSWORD" | sudo tee /etc/ahunter-vcrypt.env
sudo chmod 600 /etc/ahunter-vcrypt.env
sudo systemctl daemon-reload
sudo systemctl enable ahunter-crypt.service
```

## 5. Relocate Docker Root to Encrypted Volume

```bash
sudo mkdir -p /mnt/ahunter/docker
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "data-root": "/mnt/ahunter/docker",
  "hosts": ["unix:///var/run/docker.sock"],
  "dns": ["10.137.0.1"]   # Whonix-Gateway Tor DNS
}
EOF
sudo systemctl restart docker
```

## 6. Clone AD Anomaly Hunter & Spin Stack

```bash
cd /mnt/ahunter
git clone https://github.com/yourfork/AD-AnomalyHunter.git
cd AD-AnomalyHunter
docker compose up -d
```

Access the Streamlit dashboard only through Tor Browser at:
`http://<workstation-10.137.x.y>:8502` (never bind to 0.0.0.0)

## 7. Hidden Volume for Evidence Locker (Optional)

If you need plausible deniability or want to store sensitive incident data:

```bash
veracrypt --text --create /var/lib/vz/images/ahunter-vcrypt.img --type=hidden --size=10240 --password=OUTER_PASS --filesystem=ext4
# follow interactive prompts to create inner hidden volume
# mount inner volume manually when needed:
veracrypt --mount /dev/sdb1 /mnt/ahunter-hidden --password=INNER_PASS --protect-hidden=yes
```

## 8. Proxmox Backup & Snapshot Notes

- Encrypted disk is **opaque** to Proxmox backup; only free space is copied, so backups remain small.
- Snapshots work, but the encrypted volume must be mounted inside the guest after rollback.
- Never snapshot the Gateway while Tor circuits are live; stop Tor service first to avoid descriptor replay issues.

## 9. Operational Hardening Checklist

- [ ] Disable Whonix-Workstation clearnet emergency updates: `sudo systemctl mask whonix-firewall-restarter`
- [ ] Pin Ollama model hashes to prevent supply-chain poisoning
- [ ] Set Docker log-driver to `none` or forward to encrypted volume only
- [ ] Rotate VeraCrypt header backup to external USB after any password change
- [ ] Use `torify` wrapper for any ad-hoc Python scripts that might phone home

Result: your entire AD Anomaly Hunter lab runs inside a Tor-routed, VeraCrypt-armored VM on Proxmox — OS-level compromise becomes exponentially harder and forensics footprint is encrypted at rest.