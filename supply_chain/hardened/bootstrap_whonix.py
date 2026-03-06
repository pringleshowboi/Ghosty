#!/usr/bin/env python3
"""
Whonix-Workstation post-boot helper:
1. Mount VeraCrypt volume (expects VC_PASS env var)
2. Relocate Docker root to encrypted disk
3. Start AD Anomaly Hunter stack
4. Optional: create hidden volume for incident locker
Run as root inside Whonix-Workstation VM on Proxmox.
"""
import os
import sys
import subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from vc_utils import mount_veracrypt_device, docker_root_to_encrypted, ensure_torified_dns

def main():
    # 1. Mount encrypted data disk
    print("[*] Mounting VeraCrypt volume...")
    mount_veracrypt_device("/dev/sdb1", "/mnt/ahunter")
    print("[+] Volume mounted at /mnt/ahunter")

    # 2. Move Docker to encrypted disk
    print("[*] Moving Docker root...")
    docker_root_to_encrypted(Path("/mnt/ahunter/docker"))
    print("[+] Docker root relocated")

    # 3. Clone / update repo (idempotent)
    repo = Path("/mnt/ahunter/AD-AnomalyHunter")
    if not repo.exists():
        print("[*] Cloning repo into encrypted volume...")
        subprocess.run([
            "git", "clone",
            "https://github.com/yourfork/AD-AnomalyHunter.git",
            str(repo)
        ], check=True)
    else:
        print("[*] Pulling latest changes...")
        subprocess.run(["git", "-C", str(repo), "pull"], check=False)

    # 4. Bring up stack
    print("[*] Starting AD Anomaly Hunter stack...")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=repo, check=True)

    # 5. Sanity checks
    if not ensure_torified_dns():
        print("[!] WARNING: DNS is not torified; containers may leak")
    else:
        print("[+] DNS queries routed through Whonix-Gateway")

    print("[+] Done. Dashboard available (inside Whonix) at:")
    print("    http://10.137.x.y:8502  (binds only to workstation internal IP)")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[-] Run as root inside Whonix-Workstation")
        sys.exit(1)
    main()