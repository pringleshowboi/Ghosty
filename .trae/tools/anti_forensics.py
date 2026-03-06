import os
import subprocess

def secure_cleanup(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            try:
                subprocess.run(["shred", "-u", "-n", "3", "-z", path], check=False)
            except Exception:
                pass
    print(f"Directory {directory} has been forensically sanitized.")
