param(
  [string]$ExePath = "C:\Users\arlek\Desktop\STUFF\Projects\Cybersec\AD\AnomalyHunter\NoVirus\build\NoVirus.exe",
  [string]$LogPath = "C:\ProgramData\Wazuh\logs\novirus_events.json"
)
if (-not (Test-Path -Path (Split-Path -Path $LogPath -Parent))) {
  New-Item -ItemType Directory -Path (Split-Path -Path $LogPath -Parent) -Force | Out-Null
}
python "$PSScriptRoot\novirus_wazuh_bridge.py" --exe $ExePath --service --log $LogPath
