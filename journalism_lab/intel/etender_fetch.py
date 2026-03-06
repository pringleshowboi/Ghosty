import os
import json
import requests
from bs4 import BeautifulSoup

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

VERA_MOUNT = env("VERACRYPT_MOUNT", "/mnt/ghost_vault")
OUT_DIR = os.path.join(VERA_MOUNT, "intel", "etenders")
TOR = env("TOR_SOCKS", "socks5h://127.0.0.1:9050")
PROXIES = {"http": TOR, "https": TOR}

def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)

def fetch_listings():
    url = "https://etenders.treasury.gov.za/content/tender-bulletins"
    r = requests.get(url, proxies=PROXIES, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for a in soup.select("a"):
        href = a.get("href") or ""
        text = a.get_text(strip=True)
        if "/tender-bulletins" in href and text:
            items.append({"title": text, "url": href})
    return items

def write_out(items):
    fp = os.path.join(OUT_DIR, "listings.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    return fp

def main():
    ensure_dirs()
    items = fetch_listings()
    write_out(items)

if __name__ == "__main__":
    main()
