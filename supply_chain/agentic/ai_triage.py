import os
import json
import requests

def analyze_threat(wazuh_alert: dict) -> str:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    prompt = "You are a Senior SOC Analyst. Analyze this Wazuh alert:\n" + json.dumps(wazuh_alert) + "\n1. Identify the MITRE ATT&CK technique.\n2. Determine if this is an Anomaly or False Positive.\n3. Suggest an immediate containment action."
    try:
        import ollama
        r = ollama.chat(model=os.environ.get("OLLAMA_MODEL", "llama3"), messages=[{"role": "user", "content": prompt}], host=host)
        return r["message"]["content"]
    except Exception:
        url = host.rstrip("/") + "/api/chat"
        body = {"model": os.environ.get("OLLAMA_MODEL", "llama3"), "messages": [{"role": "user", "content": prompt}]}
        x = requests.post(url, json=body, timeout=60, stream=True)
        x.raise_for_status()
        full_content = []
        for line in x.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    msg = data.get("message", {})
                    content = msg.get("content")
                    if content:
                        full_content.append(content)
                except json.JSONDecodeError:
                    pass  # Ignore lines that are not valid JSON
        return "".join(full_content)
def summarize_news(items):
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    prompt = "Summarize these threats and suggest Wazuh rules to monitor:\n" + json.dumps(items)
    try:
        import ollama
        r = ollama.chat(model=os.environ.get("OLLAMA_MODEL", "llama3"), messages=[{"role": "user", "content": prompt}], host=host)
        return r["message"]["content"]
    except Exception:
        url = host.rstrip("/") + "/api/chat"
        body = {"model": os.environ.get("OLLAMA_MODEL", "llama3"), "messages": [{"role": "user", "content": prompt}]}
        x = requests.post(url, json=body, timeout=60, stream=True)
        x.raise_for_status()
        full_content = []
        for line in x.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    msg = data.get("message", {})
                    content = msg.get("content")
                    if content:
                        full_content.append(content)
                except json.JSONDecodeError:
                    pass  # Ignore lines that are not valid JSON
        return "".join(full_content)
