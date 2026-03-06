import os
import json
import time

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

VERA_MOUNT = env("VERACRYPT_MOUNT", "/mnt/ghost_vault")
LOG_DIR = os.path.join(VERA_MOUNT, "vault", "logs")
LOG_PATH = os.path.join(LOG_DIR, "audit.jsonl")

def ensure_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)

def write_entry(action, details):
    ensure_dirs()
    entry = {"ts": int(time.time()), "action": action, "details": details}
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    write_entry("init", {"status": "ok"})

if __name__ == "__main__":
    main()
