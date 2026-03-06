import os
import json
import requests

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

VERA_MOUNT = env("VERACRYPT_MOUNT", "/mnt/ghost_vault")
OUT_DIR = os.path.join(VERA_MOUNT, "intel", "cipc")
TOR = env("TOR_SOCKS", "socks5h://127.0.0.1:9050")
PROXIES = {"http": TOR, "https": TOR}

def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)

def search_company(name):
    url = "https://api.example.cipc/search"
    try:
        r = requests.get(url, params={"q": name}, proxies=PROXIES, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"company": name, "directors": []}

def map_directors(names):
    out = []
    for n in names:
        out.append(search_company(n))
    fp = os.path.join(OUT_DIR, "mapping.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return fp

def main():
    ensure_dirs()
    names = os.environ.get("COMPANY_NAMES", "")
    items = [s for s in names.split(",") if s.strip()]
    map_directors(items)

if __name__ == "__main__":
    main()
