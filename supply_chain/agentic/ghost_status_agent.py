import os
import json
import time
import socket
import requests
import argparse

OUT_PATH = r"c:\ProgramData\Wazuh\logs\ghost_status.json"

def port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except Exception:
        return False

def try_http(url: str, proxies: dict = None, timeout: float = 5.0) -> bool:
    try:
        r = requests.get(url, proxies=proxies, timeout=timeout, headers={"User-Agent": "curl/7.88"})
        return r.status_code == 200 and len(r.content) > 0
    except Exception:
        return False

def sample_status() -> dict:
    tor_env = os.environ.get("TOR_SOCKS", "socks5h://127.0.0.1:9050")
    vera_mount = os.environ.get("VERACRYPT_MOUNT", "/mnt/ghost_vault")
    proxies_list = [
        {"http": tor_env, "https": tor_env},
        {"http": "socks5h://host.docker.internal:9050", "https": "socks5h://host.docker.internal:9050"},
        {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
    ]
    tor_port_ok = port_open("127.0.0.1", 9050) or port_open("host.docker.internal", 9050)
    tor_http_ok = False
    for p in proxies_list:
        if try_http("https://check.torproject.org/", proxies=p):
            tor_http_ok = True
            break
    direct_ok = try_http("https://check.torproject.org/")
    vault_ok = os.path.exists(vera_mount)
    tracked = False
    if tor_http_ok and not direct_ok and vault_ok:
        tracked = False
    else:
        tracked = True
    return {
        "tracked": tracked,
        "ts": int(time.time()),
        "signals": {
            "tor_port": tor_port_ok,
            "tor_http": tor_http_ok,
            "direct_http": direct_ok,
            "vault_present": vault_ok,
            "veracrypt_mount": vera_mount
        }
    }

def write_once():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    data = sample_status()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)

def loop(period: int = 15):
    while True:
        try:
            write_once()
        except Exception:
            pass
        time.sleep(period)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--period", type=int, default=15)
    args = ap.parse_args()
    if args.loop:
        loop(args.period)
    else:
        write_once()

if __name__ == "__main__":
    main()
