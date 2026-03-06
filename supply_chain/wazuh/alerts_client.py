import os
import requests

def _get_env():
    base = os.environ.get("WAZUH_HOST", "")
    user = os.environ.get("WAZUH_USER", "")
    pwd = os.environ.get("WAZUH_PASS", "")
    return base, user, pwd

def authenticate():
    base, user, pwd = _get_env()
    if not base or not user or not pwd:
        raise RuntimeError("Missing WAZUH_HOST/WAZUH_USER/WAZUH_PASS")
    r = requests.post(base.rstrip("/") + "/security/user/authenticate", json={"username": user, "password": pwd}, verify=False, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("data", {}).get("token", "")

def fetch_recent_alerts(minutes=10, limit=100):
    base, _, _ = _get_env()
    token = authenticate()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": limit, "sort": "timestamp:desc", "from": f"now-{minutes}m"}
    r = requests.get(base.rstrip("/") + "/alerts", headers=headers, params=params, verify=False, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("data", {}).get("items", [])
