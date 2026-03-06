import socket
import json
import os
import time
from typing import List

LOG_PATH = r"c:\ProgramData\Wazuh\logs\supply_chain.json"

def safe_port_probe(host: str = "127.0.0.1", ports: List[int] = None, timeout: float = 0.3) -> List[int]:
    if ports is None:
        ports = [22, 80, 443, 3389, 5985]
    open_ports = []
    for p in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            if s.connect_ex((host, p)) == 0:
                open_ports.append(p)
            s.close()
        except Exception:
            pass
    return open_ports

def log_probe(host: str, open_ports: List[int]) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    payload = {
        "source": "purple_team",
        "type": "probe",
        "host": host,
        "open_ports": open_ports,
        "ts": int(time.time())
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

def main():
    host = "127.0.0.1"
    open_ports = safe_port_probe(host)
    log_probe(host, open_ports)

if __name__ == "__main__":
    main()
