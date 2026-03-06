# CTI CDB Exporter Usage

This utility converts the JSONL IOC feed produced by `news_agent.py` into Wazuh-compatible CDB list files (Constant Database). These lists can be referenced by Wazuh rules to perform real-time lookups of malicious IPs, domains, and file hashes.

## Quick Start

1. Run the CTI ingestion to populate the JSONL file:
   ```powershell
   python -m supply_chain.cti.news_agent --log c:\ProgramData\Wazuh\logs\supply_chain.json
   ```

2. Export IOCs to CDB lists:
   ```powershell
   python -m supply_chain.cti.cdb_exporter --infile c:\ProgramData\Wazuh\logs\supply_chain.json --out c:\ProgramData\Wazuh\lists
   ```

3. Configure Wazuh Manager to use the lists:
   - Place the generated `.cdb` files in `/var/ossec/etc/lists/` on the Wazuh manager (or the path specified in your `ossec.conf`).
   - Reference them in rules using the `list` attribute:
     ```xml
     <rule id="100002" level="10">
       <if_sid>5712</if_sid>
       <list field="srcip">etc/lists/malicious-ips.cdb</list>
       <description>Connection from known malicious IP.</description>
     </rule>
     ```

## Files Generated

- `malicious-ips.cdb` – IPv4 addresses (key only, value `:1`)
- `malicious-domains.cdb` – Domains/URLs (key only, value `:1`)
- `malicious-hashes.cdb` – SHA-256 file hashes (key only, value `:1`)

All files are plain text with `key:value` lines; Wazuh compiles them into binary CDB at manager start-up.