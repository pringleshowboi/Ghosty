import argparse
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import zipfile
from typing import Dict, List, Tuple

SUSPICIOUS_PATTERNS = [
    r"socket\.socket",
    r"subprocess\.Popen",
    r"os\.system",
    r"exec\(.*\)",
    r"eval\(.*\)",
    r"base64\.b64decode",
    r"pickle\.loads",
    r"marshal\.loads",
    r"requests\.(get|post).*(http|https)",
    r"urllib\.request\.urlopen",
]

def score_findings(findings: List[Tuple[str, str]]) -> float:
    w = 0.0
    for _, pat in findings:
        if "pickle" in pat or "marshal" in pat:
            w += 0.3
        elif "subprocess" in pat or "os.system" in pat or "exec(" in pat or "eval(" in pat:
            w += 0.25
        elif "socket" in pat:
            w += 0.2
        elif "base64" in pat:
            w += 0.15
        else:
            w += 0.1
    return max(0.0, min(1.0, w))

def extract_archive(path: str) -> str:
    tmpdir = tempfile.mkdtemp()
    if tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as t:
            t.extractall(tmpdir)
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            z.extractall(tmpdir)
    else:
        raise ValueError("Unsupported archive")
    return tmpdir

def download_pypi(package: str, version: str) -> str:
    import requests
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError("PyPI metadata fetch failed")
    data = r.json()
    files = data.get("urls", [])
    sdist = None
    for f in files:
        if f.get("packagetype") in ("sdist", "bdist_wheel"):
            sdist = f.get("url")
            break
    if not sdist:
        raise RuntimeError("No downloadable file found")
    out = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(sdist)[1])
    out.close()
    rr = requests.get(sdist, timeout=60)
    if rr.status_code != 200:
        os.unlink(out.name)
        raise RuntimeError("Download failed")
    with open(out.name, "wb") as f:
        f.write(rr.content)
    return out.name

def scan_dir(root: str) -> List[Tuple[str, str]]:
    findings: List[Tuple[str, str]] = []
    pats = [(p, re.compile(p)) for p in SUSPICIOUS_PATTERNS]
    for base, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith((".py", ".js")):
                continue
            fp = os.path.join(base, fn)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for p, rx in pats:
                    if rx.search(content):
                        findings.append((fp, p))
            except Exception:
                continue
    return findings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", default="")
    ap.add_argument("--version", default="")
    ap.add_argument("--path", default="")
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--wazuh-log", default="")
    args = ap.parse_args()
    src_root = ""
    cleanup: List[str] = []
    try:
        if args.path:
            src_root = args.path
        elif args.package and args.version:
            archive = download_pypi(args.package, args.version)
            cleanup.append(archive)
            src_root = extract_archive(archive)
            cleanup.append(src_root)
        else:
            print("Provide --path or --package and --version", file=sys.stderr)
            sys.exit(1)
        findings = scan_dir(src_root)
        score = score_findings(findings)
        malicious = score >= args.threshold
        result: Dict[str, object] = {
            "package": args.package,
            "version": args.version,
            "source_path": src_root,
            "score": score,
            "malicious": malicious,
            "findings": [{"file": f, "pattern": p} for f, p in findings],
        }
        line = json.dumps(result)
        print(line)
        if args.wazuh_log:
            try:
                os.makedirs(os.path.dirname(args.wazuh_log), exist_ok=True)
                with open(args.wazuh_log, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass
        sys.exit(2 if malicious else 0)
    finally:
        for p in cleanup:
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                elif os.path.isfile(p):
                    os.unlink(p)
            except Exception:
                pass

if __name__ == "__main__":
    main()
