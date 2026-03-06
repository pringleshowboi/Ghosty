import argparse
import os
import csv
import json
import requests
from typing import List, Dict
from supply_chain.wazuh.alerts_client import fetch_recent_alerts

def write_lines(path: str, items: List[Dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")

def fetch_otx(api_key: str, limit: int = 50) -> List[Dict]:
    if not api_key:
        return []
    r = requests.get("https://otx.alienvault.com/api/v1/pulses/subscribed", headers={"X-OTX-API-KEY": api_key}, params={"limit": limit}, timeout=20)
    if r.status_code != 200:
        return []
    data = r.json()
    out = []
    for pulse in data.get("results", []):
        for ind in pulse.get("indicators", []):
            t = ind.get("type", "")
            v = ind.get("indicator", "")
            if not v:
                continue
            if t in ("IPv4", "domain", "URL", "FileHash-SHA256"):
                out.append({"source": "cti", "type": "ioc", "ioc_type": t.lower(), "value": v, "pulse_name": pulse.get("name", "")})
    return out

def fetch_feodo_ips() -> List[Dict]:
    url = "https://feodotracker.abuse.ch/downloads/ipblocklist.csv"
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return []
    lines = r.text.splitlines()
    out = []
    for line in lines:
        if line.startswith("#") or not line.strip():
            continue
        out.append({"source": "cti", "type": "ioc", "ioc_type": "ipv4", "value": line.strip(), "feed": "feodo"})
    return out

def fetch_cisa_kev() -> List[Dict]:
    url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return []
    data = r.json()
    out = []
    for v in data.get("vulnerabilities", []):
        cve = v.get("cveID", "")
        if cve:
            out.append({"source": "cti", "type": "cve", "value": cve, "desc": v.get("shortDescription", "")})
    return out

def correlate_alerts(iocs: List[Dict], minutes: int, log_path: str):
    alerts = fetch_recent_alerts(minutes=minutes, limit=200)
    ips = set([i["value"] for i in iocs if i.get("ioc_type") == "ipv4"])
    domains = set([i["value"] for i in iocs if i.get("ioc_type") in ("domain", "url")])
    matches = []
    for a in alerts:
        s = json.dumps(a)
        for ip in ips:
            if ip in s:
                matches.append({"source": "cti", "type": "ioc_match", "match": "ipv4", "value": ip, "alert": a})
        for d in domains:
            if d in s:
                matches.append({"source": "cti", "type": "ioc_match", "match": "domain", "value": d, "alert": a})
    if matches:
        write_lines(log_path, matches)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--otx-key", default=os.environ.get("OTX_API_KEY", ""))
    ap.add_argument("--log", default="c:\\ProgramData\\Wazuh\\logs\\supply_chain.json")
    ap.add_argument("--correlate-minutes", type=int, default=0)
    args = ap.parse_args()
    items = []
    items += fetch_otx(args.otx_key)
    items += fetch_feodo_ips()
    items += fetch_cisa_kev()
    if items:
        write_lines(args.log, items)
    if args.correlate_minutes and items:
        iocs = [i for i in items if i.get("type") == "ioc"]
        correlate_alerts(iocs, args.correlate_minutes, args.log)

if __name__ == "__main__":
    main()
