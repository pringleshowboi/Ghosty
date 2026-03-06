import os
import re
import subprocess

def scrub_text(path):
    with open(path, "r", encoding="utf-8") as f:
        t = f.read()
    t = re.sub(r"(?im)^by\\s+[^\\n]+$", "Ghost Sentinel Agent", t)
    t = re.sub(r"(?im)^author:\\s*[^\\n]+$", "Ghost Sentinel Agent", t)
    with open(path, "w", encoding="utf-8") as f:
        f.write(t)

def scrub_metadata(path):
    try:
        subprocess.run(["exiftool", "-overwrite_original", "-all=", path], check=False)
    except Exception:
        pass

def main():
    import sys
    for p in sys.argv[1:]:
        if p.lower().endswith((".md", ".txt")):
            scrub_text(p)
        scrub_metadata(p)

if __name__ == "__main__":
    main()
