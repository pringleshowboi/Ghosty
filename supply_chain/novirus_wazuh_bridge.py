import argparse
import json
import os
import re
import subprocess
import sys
from typing import Optional

BEHAVIOR_RE = re.compile(r"^\[!!!\]\s+BEHAVIORAL ALERT:\s+(?P<msg>.+)$")
SIG_RE = re.compile(r"^\[\!\]\s+MALWARE FOUND \(Signature\):\s+(?P<file>.+)\s+\((?P<threat>.+)\)$")
HEUR_RE = re.compile(r"^\[\!\]\s+MALWARE FOUND \(Heuristic\):\s+(?P<file>.+)\s+\((?P<threat>.+)\)$")
REMEDIATE_RE = re.compile(r"^\[REMEDIATION\]\s+Deleting file:\s+(?P<file>.+)$")
REMEDIATE_RESULT_RE = re.compile(r"^(?P<result>SUCCESS|FAILED):\s+File (?:removed|could not remove)\.$")
CTX_HEADER_RE = re.compile(r"^--- Contextual Analysis Report ---$")
CTX_ENTRY_RE = re.compile(r"^\[\!\]\s+(?P<sev>\w+):\s+(?P<name>.+)\s+\(PID:\s+(?P<pid>\d+)\)\s*$")
CTX_REASON_RE = re.compile(r"^\s+Reason:\s+(?P<reason>.+)$")
CTX_PARENT_RE = re.compile(r"^\s+Parent PID:\s+(?P<ppid>\d+)\s*$")

def write_json_line(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

def run_novirus(exe_path: str, service: bool) -> subprocess.Popen:
    if not os.path.isfile(exe_path):
        raise FileNotFoundError(f"Not found: {exe_path}")
    args = [exe_path]
    if service:
        args.append("--service")
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(exe_path))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--service", action="store_true")
    ap.add_argument("--log", default=os.path.join(os.getcwd(), "wazuh_events.json"))
    ap.add_argument("--limit-seconds", type=int, default=20)
    args = ap.parse_args()

    p = run_novirus(args.exe, args.service)
    ctx_mode = False
    current_ctx: Optional[dict] = None
    try:
        elapsed = 0
        while True:
            line = p.stdout.readline()
            if not line:
                if p.poll() is not None:
                    break
                continue
            line = line.rstrip()
            if line.startswith("===") or line.startswith("NoVirus Security Engine"):
                continue
            m = BEHAVIOR_RE.match(line)
            if m:
                write_json_line(args.log, {"source": "novirus", "type": "behavior_alert", "message": m.group("msg"), "severity": "high"})
                continue
            m = SIG_RE.match(line)
            if m:
                write_json_line(args.log, {"source": "novirus", "type": "file_threat", "method": "signature", "file": m.group("file"), "threat": m.group("threat"), "severity": "high"})
                continue
            m = HEUR_RE.match(line)
            if m:
                write_json_line(args.log, {"source": "novirus", "type": "file_threat", "method": "heuristic", "file": m.group("file"), "threat": m.group("threat"), "severity": "medium"})
                continue
            m = REMEDIATE_RE.match(line)
            if m:
                write_json_line(args.log, {"source": "novirus", "type": "remediation_start", "file": m.group("file")})
                continue
            m = REMEDIATE_RESULT_RE.match(line)
            if m:
                write_json_line(args.log, {"source": "novirus", "type": "remediation_result", "result": m.group("result").lower()})
                continue
            if CTX_HEADER_RE.match(line):
                ctx_mode = True
                current_ctx = {}
                continue
            if ctx_mode:
                cm = CTX_ENTRY_RE.match(line)
                if cm:
                    current_ctx = {"source": "novirus", "type": "context_alert", "severity": cm.group("sev"), "process_name": cm.group("name"), "pid": int(cm.group("pid"))}
                    continue
                rm = CTX_REASON_RE.match(line)
                if rm and current_ctx is not None:
                    current_ctx["reason"] = rm.group("reason")
                    continue
                pm = CTX_PARENT_RE.match(line)
                if pm and current_ctx is not None:
                    current_ctx["parent_pid"] = int(pm.group("ppid"))
                    write_json_line(args.log, current_ctx)
                    current_ctx = None
                    ctx_mode = False
                    continue
        p.wait(timeout=5)
    finally:
        try:
            p.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    main()
