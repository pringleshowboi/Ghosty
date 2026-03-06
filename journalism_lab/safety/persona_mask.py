import os
import json
import requests

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

OLLAMA = env("OLLAMA_HOST", "http://localhost:11434")
MODEL = env("OLLAMA_MODEL", "llama3")

def mask_text(text):
    prompt = ("Rewrite the following text in a neutral newsroom style, removing unique stylometric markers. "
              "Avoid idioms and distinctive phrasing. Output only the rewritten text:\n") + text
    try:
        import ollama
        r = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}], host=OLLAMA)
        return r["message"]["content"]
    except Exception:
        url = OLLAMA.rstrip("/") + "/api/chat"
        body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}
        x = requests.post(url, json=body, timeout=60, stream=True)
        x.raise_for_status()
        parts = []
        for line in x.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    m = data.get("message", {})
                    c = m.get("content")
                    if c:
                        parts.append(c)
                except Exception:
                    pass
        return "".join(parts)

def main():
    import sys
    src = sys.stdin.read()
    out = mask_text(src)
    print(out)

if __name__ == "__main__":
    main()
