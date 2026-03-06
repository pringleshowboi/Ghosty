import os
import json
import time
from typing import Dict, List
from supply_chain.wazuh.alerts_client import fetch_recent_alerts

STATUS_PATH = r"c:\ProgramData\Wazuh\logs\slack_status.json"
OUTPUT_PATH = r"c:\ProgramData\Wazuh\logs\supply_chain.json"

def load_statuses() -> Dict[str, Dict]:
    if os.path.isfile(STATUS_PATH):
        try:
            with open(STATUS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def detect_synthetic_identity(minutes: int = 60) -> List[Dict]:
    alerts = fetch_recent_alerts(minutes=minutes, limit=200)
    statuses = load_statuses()
    findings = []
    for a in alerts:
        user = a.get("agent", {}).get("name") or a.get("data", {}).get("user") or ""
        srcip = a.get("data", {}).get("srcip", "")
        if not user:
            continue
        st = statuses.get(user, {})
        if st.get("status") == "in_meeting":
            findings.append({
                "source": "identity_guard",
                "type": "synthetic_identity",
                "user": user,
                "srcip": srcip,
                "status": st,
                "alert": a
            })
    return findings

def main():
    items = detect_synthetic_identity(minutes=60)
    if items:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")

if __name__ == "__main__":
    main()
