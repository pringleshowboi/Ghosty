import os
import json
import time
import requests

def query_ollama_models(host: str) -> list:
    try:
        r = requests.get(host.rstrip("/") + "/api/tags", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("models", [])
    except Exception:
        pass
    return []

def generate_aibom() -> dict:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    models = query_ollama_models(host)
    entry = {
        "project": "GhostProtocol-Sovereign-Mesh",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "models": [],
        "privacy_guarantee": "All inference runs local; no external exfiltration",
        "runtime": {"ollama_host": host}
    }
    found = False
    for m in models:
        name = m.get("name", "")
        if name:
            entry["models"].append({
                "name": name,
                "sha256": m.get("digest", "unknown"),
                "source": "local-ollama"
            })
            if name == model:
                found = True
    if not found and model:
        entry["models"].append({
            "name": model,
            "sha256": "unknown",
            "source": "local-ollama"
        })
    return entry

def write_aibom(path: str) -> str:
    data = generate_aibom()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path

if __name__ == "__main__":
    out = os.path.join(os.getcwd(), "aibom.json")
    write_aibom(out)
    print(out)
