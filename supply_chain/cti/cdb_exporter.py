import argparse
import os
import json
from typing import List, Dict

def write_cdb_list(iocs: List[Dict], out_dir: str):
    ips = []
    domains = []
    hashes = []
    for i in iocs:
        t = i.get("ioc_type")
        v = i.get("value")
        if not v:
            continue
        if t == "ipv4":
            ips.append(v)
        elif t in ("domain", "url"):
            domains.append(v)
        elif t == "filehash-sha256":
            hashes.append(v)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "malicious-ips.cdb"), "w", encoding="utf-8") as f:
        for ip in ips:
            f.write(f"{ip}:1\n")
    with open(os.path.join(out_dir, "malicious-domains.cdb"), "w", encoding="utf-8") as f:
        for d in domains:
            f.write(f"{d}:1\n")
    with open(os.path.join(out_dir, "malicious-hashes.cdb"), "w", encoding="utf-8") as f:
        for h in hashes:
            f.write(f"{h}:1\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="c:\\ProgramData\\Wazuh\\logs\\supply_chain.json")
    ap.add_argument("--out", default="c:\\ProgramData\\Wazuh\\lists")
    args = ap.parse_args()
    iocs = []
    if os.path.isfile(args.infile):
        with open(args.infile, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    it = json.loads(line)
                    if it.get("type") == "ioc":
                        iocs.append(it)
                except Exception:
                    pass
    if iocs:
        write_cdb_list(iocs, args.out)
        print(f"Wrote {len(iocs)} IOCs to CDB lists in {args.out}")

if __name__ == "__main__":
    main()