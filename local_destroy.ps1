param(
  [string]$VMName = "Whonix-WS-Sentinel"
)
$ErrorActionPreference = "Stop"
function Get-VBoxManage {
  $v = Get-Command VBoxManage -ErrorAction SilentlyContinue
  if (-not $v) { throw "VBoxManage not found. Install VirtualBox and ensure VBoxManage is in PATH." }
  return $v.Source
}
$VBoxManage = Get-VBoxManage
try {
  $state = & $VBoxManage showvminfo $VMName --machinereadable | Select-String -Pattern '^VMState='
} catch {
  throw "VM not found: $VMName"
}
if ($state -and $state.ToString() -match 'running') {
  & $VBoxManage controlvm $VMName acpipowerbutton
  Start-Sleep -Seconds 5
  $tries = 0
  while ($tries -lt 12) {
    $s = & $VBoxManage showvminfo $VMName --machinereadable | Select-String -Pattern '^VMState='
    if ($s -and $s.ToString() -match 'poweroff') { break }
    Start-Sleep -Seconds 5
    $tries++
  }
  if ($tries -ge 12) {
    & $VBoxManage controlvm $VMName poweroff
  }
}
& $VBoxManage unregistervm $VMName --delete
Write-Host "VM $VMName removed and associated disks deleted."

