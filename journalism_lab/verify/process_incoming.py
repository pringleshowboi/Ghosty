import os
import subprocess

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

VERA_MOUNT = env("VERACRYPT_MOUNT", "/mnt/ghost_vault")
STAGING_DIR = env("STAGING_DIR", os.path.join(VERA_MOUNT, "intake", "staging"))
SAFE_DIR = os.path.join(VERA_MOUNT, "verify", "safe")

def ensure_dirs():
    os.makedirs(SAFE_DIR, exist_ok=True)

def sanitize(path):
    try:
        subprocess.run(["dangerzone", path], check=True)
    except Exception:
        pass

def scrub_metadata(path):
    try:
        subprocess.run(["exiftool", "-overwrite_original", "-all=", path], check=True)
    except Exception:
        pass

def process():
    for root, _, files in os.walk(STAGING_DIR):
        for f in files:
            p = os.path.join(root, f)
            sanitize(p)
            scrub_metadata(p)
            try:
                base = os.path.basename(p)
                dst = os.path.join(SAFE_DIR, base)
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(p, dst)
            except Exception:
                pass

def main():
    ensure_dirs()
    process()

if __name__ == "__main__":
    main()
