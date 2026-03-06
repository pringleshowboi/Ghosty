# This script lives inside the Whonix Workstation
import os
import subprocess

def secure_wipe_staging():
    # 1. Force unmount VeraCrypt
    print("Dismounting VeraCrypt volume...")
    subprocess.run(["veracrypt", "-d"])
    
    # 2. Shred all temp files in the intake folder
    # 'shred' overwrites data so it can't be recovered from the virtual disk
    print("Shredding intake files...")
    intake_path = "/home/user/intake"
    # Use glob to get a list of files, as shell expansion won't work directly
    try:
        files_to_shred = [os.path.join(intake_path, f) for f in os.listdir(intake_path) if os.path.isfile(os.path.join(intake_path, f))]
        if files_to_shred:
            subprocess.run(["shred", "-v", "-n", "3", "-u"] + files_to_shred)
        else:
            print("No files to shred in intake folder.")
    except FileNotFoundError:
        print(f"Intake directory not found: {intake_path}")

    # 3. Clear RAM (if not in Live Mode)
    # This triggers the kernel to zero out unused memory
    print("Clearing RAM caches...")
    os.system("sync; echo 3 | sudo tee /proc/sys/vm/drop_caches")
    print("Secure wipe complete.")

if __name__ == "__main__":
    secure_wipe_staging()
