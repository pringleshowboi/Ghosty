import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Tuple

def run_cmd(cmd: list) -> Tuple[int, str, str]:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out, err

def ensure_tool(name: str) -> Optional[str]:
    return shutil.which(name)

def write_wazuh_log(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

def generate_sbom(target: str, fmt: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.close()
    if fmt == "cyclonedx-json":
        cmd = ["syft", target, "-o", "cyclonedx-json"]
    else:
        cmd = ["syft", target, "-o", "json"]
    code, out, err = run_cmd(cmd)
    if code != 0:
        os.unlink(tmp.name)
        raise RuntimeError(err.strip() or "syft failed")
    with open(tmp.name, "w", encoding="utf-8") as f:
        f.write(out)
    return tmp.name

def grype_scan_sbom(sbom_path: str) -> dict:
    cmd = ["grype", f"sbom:{sbom_path}", "-o", "json"]
    code, out, err = run_cmd(cmd)
    if code != 0:
        raise RuntimeError(err.strip() or "grype failed")
    return json.loads(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--sbom-format", default="cyclonedx-json", choices=["cyclonedx-json", "json"])
    ap.add_argument("--output", default="")
    ap.add_argument("--wazuh-log", default="")
    args = ap.parse_args()
    if not ensure_tool("syft"):
        print("syft not found", file=sys.stderr)
        sys.exit(1)
    if not ensure_tool("grype"):
        print("grype not found", file=sys.stderr)
        sys.exit(1)
    sbom_file = generate_sbom(args.target, args.sbom_format)
    try:
        report = grype_scan_sbom(sbom_file)
    finally:
        try:
            os.unlink(sbom_file)
        except Exception:
            pass
    payload = {"scanner": "grype", "target": args.target, "result": report}
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    else:
        print(json.dumps(payload))
    if args.wazuh_log:
        write_wazuh_log(args.wazuh_log, payload)

if __name__ == "__main__":
    main()
