# Registers the KOVAN night task: every night 23:00 (default), local python, dry mode.
# Usage:  powershell -File task-register.ps1 -Hour 23:00
param([string]$Hour = "23:00")
$eylem = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\night-run.ps1`""
$tetik = New-ScheduledTaskTrigger -Daily -At $Hour
Register-ScheduledTask -TaskName "KOVAN-Night" -Action $eylem -Trigger $tetik `
    -Description "KOVAN night line (dry mode; no model needed)" -Force | Out-Null
Write-Host "KOVAN-Night registered: every day at $Hour. Removal: task-remove.ps1"
