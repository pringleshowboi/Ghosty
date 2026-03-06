# Ransomware Simulation Script (Harmless)
# Creates 60 files quickly to trigger behavioral monitor

$targetDir = "test_scan_area"
if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Force -Path $targetDir }

Write-Host "Starting Ransomware Simulation..."
for ($i=1; $i -le 60; $i++) {
    $file = "$targetDir\ransom_test_file_$i.txt"
    Set-Content -Path $file -Value "Encrypted data simulation $i"
    Write-Host "Created $file"
}
Write-Host "Simulation Complete."