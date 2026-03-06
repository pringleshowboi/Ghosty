import os
import json
import time
import hashlib
import requests

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

VERA_MOUNT = env("VERACRYPT_MOUNT", "/mnt/ghost_vault")
OUT_DIR = os.path.join(VERA_MOUNT, "vault", "timestamps")
TOR = env("TOR_SOCKS", "socks5h://127.0.0.1:9050")
PROXIES = {"http": TOR, "https": TOR}

def ensure():
    os.makedirs(OUT_DIR, exist_ok=True)

def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_local_stamp(hash_hex):
    ensure()
    fp = os.path.join(OUT_DIR, f"{int(time.time())}_{hash_hex[:16]}.json")
    data = {"ts": int(time.time()), "sha256": hash_hex}
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return fp

def try_public_stamp(hash_hex):
    endpoint = os.environ.get("TIMESTAMP_ENDPOINT", "")
    if not endpoint:
        return None
    try:
        r = requests.post(endpoint, json={"sha256": hash_hex}, proxies=PROXIES, timeout=45)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def main():
    import sys
    if len(sys.argv) < 2:
        print("provide file path", file=sys.stderr)
        return
    target = sys.argv[1]
    h = hash_file(target)
    local_fp = write_local_stamp(h)
    pub = try_public_stamp(h)
    if pub:
        print(json.dumps({"local": local_fp, "public": pub}))
    else:
        print(json.dumps({"local": local_fp}))

if __name__ == "__main__":
    main()
