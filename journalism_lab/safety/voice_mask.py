import os
import subprocess

def env(name, default):
    v = os.environ.get(name)
    return v if v else default

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

def local_mask(in_wav, out_wav):
    try:
        subprocess.run(["ffmpeg", "-y", "-i", in_wav, "-af", "asetrate=44100*0.95,atempo=1.05", out_wav], check=False)
    except Exception:
        pass

def main():
    import sys
    if len(sys.argv) < 3:
        print("usage: voice_mask <in.wav> <out.wav>", file=sys.stderr)
        return
    src, dst = sys.argv[1], sys.argv[2]
    if API_KEY:
        local_mask(src, dst)
    else:
        local_mask(src, dst)

if __name__ == "__main__":
    main()
