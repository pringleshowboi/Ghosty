import os
import shutil
import subprocess

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

VERA_MOUNT = env("VERACRYPT_MOUNT", "/mnt/ghost_vault")
AIRLOCK_DIR = env("AIRLOCK_DIR", "/var/tmp/airlock")
STAGING_DIR = env("STAGING_DIR", os.path.join(VERA_MOUNT, "intake", "staging"))

def wipe(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass

def unmount_veracrypt():
    try:
        subprocess.run(["veracrypt", "--text", "--dismount", VERA_MOUNT], check=False)
    except Exception:
        pass

def main():
    wipe(AIRLOCK_DIR)
    wipe(STAGING_DIR)
    unmount_veracrypt()

if __name__ == "__main__":
    main()
