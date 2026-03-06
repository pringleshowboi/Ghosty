param(
  [string]$VMName = "Whonix-WS-Sentinel",
  [int]$DiskSizeGB = 100,
  [string]$OvaPath,
  [string]$OvaUrl
)
$ErrorActionPreference = "Stop"
function Get-VBoxManage {
  $v = Get-Command VBoxManage -ErrorAction SilentlyContinue
  if ($v) { return $v.Source }
  $candidates = @(
    "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe",
    "$env:ProgramFiles(x86)\Oracle\VirtualBox\VBoxManage.exe"
  )
  foreach ($c in $candidates) {
    if (Test-Path $c) { return $c }
  }
  throw "VBoxManage not found. Install VirtualBox or add it to PATH. Download: https://www.virtualbox.org/wiki/Downloads"
}
$VBoxManage = Get-VBoxManage
$work = Join-Path (Get-Location) ".whonix_import"
if (-not (Test-Path $work)) { New-Item -ItemType Directory -Path $work | Out-Null }
if (-not $OvaPath) {
  Write-Host ""
  Write-Host "Whonix Download Instructions:"
  Write-Host "1. Visit: https://www.whonix.org/wiki/Download"
  Write-Host "2. Click 'VirtualBox' under 'Virtual Machines'"
  Write-Host "3. Download the Whonix-Workstation OVA file"
  Write-Host "4. Common filename format: Whonix-LXQt-X.X.X.X.Intel_AMD64.ova"
  Write-Host "5. Save it to: $work\Whonix-Workstation.ova"
  Write-Host ""
  
  $manualPath = Read-Host "Enter path to downloaded Whonix-Workstation.ova or press Enter to open download page"
  
  if ($manualPath) {
    $OvaPath = $manualPath
  } else {
    Start-Process "https://www.whonix.org/wiki/Download"
    Write-Host "Download page opened. After downloading, run this script again with -OvaPath parameter"
    Write-Host "Example: .\local_setup.ps1 -OvaPath `"C:\Downloads\Whonix-Workstation.ova`""
    exit 0
  }
}
if (-not (Test-Path $OvaPath)) { throw "OVA not found: $OvaPath" }
$existing = & $VBoxManage list vms
$exists = $false
if ($LASTEXITCODE -eq 0) {
  if ($existing -match '\"' + [regex]::Escape($VMName) + '\"') { $exists = $true }
}
if (-not $exists) {
  & $VBoxManage import $OvaPath --vsys 0 --eula accept --vsys 1 --eula accept --vsys 1 --vmname $VMName
  if ($LASTEXITCODE -ne 0) { throw "Import failed. EULA acceptance may be required." }
} else {
  Write-Host "VM already exists: $VMName"
}
& $VBoxManage showvminfo $VMName | Out-Null
if ($LASTEXITCODE -ne 0) { throw "VM not found after import." }
$vdiDir = Join-Path "$env:USERPROFILE\VirtualBox VMs" $VMName
if (-not (Test-Path $vdiDir)) { New-Item -ItemType Directory -Path $vdiDir | Out-Null }
$vdi = Join-Path $vdiDir "veracrypt.vdi"
if (-not (Test-Path $vdi)) {
  & $VBoxManage createmedium disk --filename $vdi --size ($DiskSizeGB*1024)
  if ($LASTEXITCODE -ne 0) { throw "Failed creating VeraCrypt disk image." }
}
$storageCtl = "SATA Controller"
$mr = & $VBoxManage showvminfo $VMName --machinereadable
if ($LASTEXITCODE -eq 0) {
  $line = ($mr | Select-String -Pattern '^storagecontrollername0=' | Select-Object -First 1)
  if ($line) {
    $name = $line.Line -replace '^storagecontrollername0=\"(.+)\"$','$1'
    if ($name) { $storageCtl = $name }
  }
}
try {
  & $VBoxManage storageattach $VMName --storagectl $storageCtl --port 1 --device 0 --type hdd --medium $vdi
} catch {
  $storageCtl = "SATA"
  & $VBoxManage storagectl $VMName --name $storageCtl --add sata
  & $VBoxManage storageattach $VMName --storagectl $storageCtl --port 1 --device 0 --type hdd --medium $vdi
}
Write-Host "VM ready: $VMName"
Write-Host "Start with: VBoxManage startvm `"$VMName`""
Write-Host "Inside the VM, install VeraCrypt, then:"
Write-Host "sudo parted /dev/sdb --script mklabel gpt mkpart primary 0% 100%"
Write-Host "sudo veracrypt --text --create /dev/sdb1"
Write-Host "sudo mkdir -p /mnt/vault && sudo veracrypt --text --mount /dev/sdb1 /mnt/vault"
