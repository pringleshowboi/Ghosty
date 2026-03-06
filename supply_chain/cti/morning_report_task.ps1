# 8 AM Daily CTI Morning Report
# Run this script via Windows Task Scheduler at 08:00 every day
# Action: powershell.exe -ExecutionPolicy Bypass -File "C:\Users\arlek\Desktop\STUFF\Projects\Cybersec\AD\AnomalyHunter\supply_chain\cti\morning_report_task.ps1"

$env:OTX_API_KEY = Get-Content "C:\Users\arlek\Desktop\STUFF\Projects\Cybersec\AD\AnomalyHunter\.env" | Select-String "OTX_API_KEY" | ForEach-Object { $_ -replace "OTX_API_KEY=", "" }

python -m supply_chain.cti.news_agent --log "C:\ProgramData\Wazuh\logs\supply_chain.json" --correlate-minutes 1440

python -m supply_chain.cti.cdb_exporter --infile "C:\ProgramData\Wazuh\logs\supply_chain.json" --out "C:\ProgramData\Wazuh\lists"

python -c "
import feedparser, os, json, requests, sys
feed = feedparser.parse('https://isc.sans.edu/rssfeed.xml')
items = [e.title for e in feed.entries[:5]] if hasattr(feed, 'entries') else []
prompt = 'Summarize these threats and suggest Wazuh rules to monitor:\n' + json.dumps(items)
host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
try:
    import ollama
    r = ollama.chat(model=os.environ.get('OLLAMA_MODEL', 'llama3'), messages=[{'role': 'user', 'content': prompt}], host=host)
    summary = r['message']['content']
except Exception:
    url = host.rstrip('/') + '/api/chat'
    body = {'model': os.environ.get('OLLAMA_MODEL', 'llama3'), 'messages': [{'role': 'user', 'content': prompt}]}
    x = requests.post(url, json=body, timeout=60)
    x.raise_for_status()
    summary = x.json().get('message', {}).get('content', '')
with open('C:\\ProgramData\\Wazuh\\logs\\morning_report.txt', 'w', encoding='utf-8') as f:
    f.write(summary)
"

Write-Host "Morning report generated at C:\ProgramData\Wazuh\logs\morning_report.txt"