# hardened/  - Whonix + VeraCrypt integration helpers
# This folder contains scripts and docs to run the entire AD Anomaly Hunter stack
# inside a Whonix-Workstation VM on Proxmox with full-disk VeraCrypt encryption.
# Nothing here is Windows-specific; all commands are meant to be executed inside
# the Whonix-Workstation guest or on the Proxmox host.

from pathlib import Path
import subprocess
import os

def mount_veracrypt_device(device_path: str, mount_point: str, password_env: str = "VC_PASS"):
    """
    Mount a VeraCrypt volume inside Whonix-Workstation.
    Requires the password in the environment variable VC_PASS.
    """
    passwd = os.getenv(password_env)
    if not passwd:
        raise RuntimeError(f"Environment variable {password_env} not set")
    cmd = [
        "veracrypt", "--text", "--mount", device_path, mount_point,
        "--password", passwd, "--pim=0", "--protect-hidden=no"
    ]
    subprocess.run(cmd, check=True)

def umount_veracrypt_device(device_path: str):
    """Dismount a VeraCrypt volume by device path."""
    subprocess.run(["veracrypt", "--text", "--dismount", device_path], check=True)

def docker_root_to_encrypted(new_root: Path):
    """
    Rewrite /etc/docker/daemon.json to place Docker data on an encrypted volume.
    Restarts the Docker daemon.
    """
    new_root.mkdir(parents=True, exist_ok=True)
    config = {
        "data-root": str(new_root),
        "hosts": ["unix:///var/run/docker.sock"],
        "dns": ["10.137.0.1"]   # Whonix-Gateway Tor DNS
    }
    daemon_json = Path("/etc/docker/daemon.json")
    daemon_json.write_text(__import__("json").dumps(config, indent=2))
    subprocess.run(["systemctl", "restart", "docker"], check=True)

def ensure_torified_dns():
    """
    Verify that Docker will use the Whonix-Gateway for DNS.
    Returns True if /etc/resolv.conf points to 10.137.0.1
    """
    resolv = Path("/etc/resolv.conf").read_text()
    return "10.137.0.1" in resolv

if __name__ == "__main__":
    # Example: mount the data disk at /mnt/ahunter and relocate Docker
    mount_veracrypt_device("/dev/sdb1", "/mnt/ahunter")
    docker_root_to_encrypted(Path("/mnt/ahunter/docker"))
    print("Docker root moved to encrypted volume; Torified DNS active:", ensure_torified_dns())