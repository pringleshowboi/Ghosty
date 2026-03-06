# Ghost Sentinel (Journalism Lab) 

- Environment: Whonix-Workstation inside VirtualBox
- Principle: Compartmentalization; no data leaks to host
- Language/Stack: Python, Bash, Markdown
- Network: Route all traffic through Tor proxy 127.0.0.1:9050
- Telemetry: Disable analytics and phone-home in scripts and tools
- Persistence: Write all investigative data to VeraCrypt mount path
- Mount path env: VERACRYPT_MOUNT, default /mnt/ghost_vault
- Staging path env: STAGING_DIR, default /mnt/ghost_vault/intake/staging
- OnionShare dir env: ONIONSHARE_DIR, default ~/OnionShare
- Proxies env: TOR_SOCKS, default socks5h://127.0.0.1:9050
- Tools required: onionshare-cli, dangerzone, exiftool, veracrypt
- Forbidden: direct internet without TOR_SOCKS, plaintext logs outside VERACRYPT_MOUNT
