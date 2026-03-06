# Individual Safety — Ghost Identity

- Zero-Knowledge: Never store PII or real names; use cryptographic IDs
- PKI IDs: Derive public IDs from secrets; expose only hex public IDs
- Ephemeral Workspaces: Build tasks in disposable VMs/containers; destroy after completion
- Anti-Forensics: Write temp artifacts to /dev/shm and wipe on exit
- Dead Man's Switch: Provide callable script to unmount all VeraCrypt volumes and wipe airlock
- Local-Only AI: Use local LLMs; no cloud telemetry
- Hidden Volumes: Each journalist has a VeraCrypt hidden volume; no centralized registry
- Tor-Only Queries: All OSINT queries routed via socks5h://127.0.0.1:9050
- Byline Masking: Auto-remove author breadcrumbs from published articles
- Evidence Timestamper: Hash evidence and store stamp; optional Tor-based public timestamp
