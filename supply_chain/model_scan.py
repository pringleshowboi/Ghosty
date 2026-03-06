import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Optional, Tuple

def which(name: str) -> Optional[str]:
    return shutil.which(name)

def run_cmd(cmd: list) -> Tuple[int, str, str]:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out, err

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--output", default="")
    ap.add_argument("--wazuh-log", default="")
    args = ap.parse_args()
    if not which("modelscan"):
        print("modelscan not found", file=sys.stderr)
        sys.exit(1)
    cmd = ["modelscan", "scan", args.model, "-o", "json"]
    code, out, err = run_cmd(cmd)
    if code != 0:
        print(err.strip() or "modelscan failed", file=sys.stderr)
        sys.exit(code)
    payload = {"scanner": "modelscan", "model": args.model, "result": json.loads(out)}
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    else:
        print(json.dumps(payload))
    if args.wazuh_log:
        os.makedirs(os.path.dirname(args.wazuh_log), exist_ok=True)
        with open(args.wazuh_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

if __name__ == "__main__":
    main()
