import os
import json
import shutil

RAM_DIR = "/dev/shm/ghost_sentinel"

def ensure():
    os.makedirs(RAM_DIR, exist_ok=True)

def write_text(name, text):
    ensure()
    fp = os.path.join(RAM_DIR, name)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(text)
    return fp

def write_json(name, obj):
    ensure()
    fp = os.path.join(RAM_DIR, name)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return fp

def wipe():
    try:
        shutil.rmtree(RAM_DIR, ignore_errors=True)
    except Exception:
        pass
