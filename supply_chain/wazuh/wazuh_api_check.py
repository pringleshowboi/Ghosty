import os
import sys
import requests

def main():
    base = os.environ.get("WAZUH_URL", "")
    user = os.environ.get("WAZUH_USER", "")
    pwd = os.environ.get("WAZUH_PASS", "")
    if not base or not user or not pwd:
        print("Set WAZUH_URL, WAZUH_USER, WAZUH_PASS", file=sys.stderr)
        sys.exit(1)
    try:
        r = requests.get(f"{base}/security/user/authenticate", auth=(user, pwd), verify=False, timeout=10)
    except Exception as e:
        print(f"API error: {e}", file=sys.stderr)
        sys.exit(2)
    if r.status_code != 200:
        print(f"Auth failed: {r.status_code}", file=sys.stderr)
        sys.exit(3)
    print("Wazuh API reachable and credentials valid")

if __name__ == "__main__":
    main()
