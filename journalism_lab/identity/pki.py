import os
import json
import hashlib
import secrets

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

VERA_MOUNT = env("VERACRYPT_MOUNT", "/mnt/ghost_vault")
ID_DIR = os.path.join(VERA_MOUNT, "identity")
SECRET_PATH = os.path.join(ID_DIR, "secret.key")
PUBLIC_PATH = os.path.join(ID_DIR, "public_id.json")

def ensure_dirs():
    os.makedirs(ID_DIR, exist_ok=True)

def generate():
    ensure_dirs()
    if not os.path.isfile(SECRET_PATH):
        s = secrets.token_bytes(32)
        with open(SECRET_PATH, "wb") as f:
            f.write(s)
    with open(SECRET_PATH, "rb") as f:
        s = f.read()
    pub = hashlib.sha256(s).hexdigest()
    data = {"public_id": "0x" + pub[:40]}
    with open(PUBLIC_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data

def main():
    out = generate()
    print(json.dumps(out))

if __name__ == "__main__":
    main()
