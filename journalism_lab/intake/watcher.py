import os
import time
import shutil

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

ONIONSHARE_DIR = os.path.expanduser(env("ONIONSHARE_DIR", "~/OnionShare"))
VERA_MOUNT = env("VERACRYPT_MOUNT", "/mnt/ghost_vault")
STAGING_DIR = env("STAGING_DIR", os.path.join(VERA_MOUNT, "intake", "staging"))

def ensure_dirs():
    os.makedirs(STAGING_DIR, exist_ok=True)

def move_new_files():
    for root, _, files in os.walk(ONIONSHARE_DIR):
        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(STAGING_DIR, f)
            try:
                if not os.path.exists(dst):
                    shutil.move(src, dst)
            except Exception:
                pass

def main():
    ensure_dirs()
    while True:
        move_new_files()
        time.sleep(3)

if __name__ == "__main__":
    main()
