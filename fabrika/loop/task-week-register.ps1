# Registers the KOVAN weekly task: every Friday 18:00 (retro + drill, local, dry mode).
# Usage:  powershell -File task-week-register.ps1
$eylem = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\week-run.ps1`""
$tetik = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "18:00"
Register-ScheduledTask -TaskName "KOVAN-Week" -Action $eylem -Trigger $tetik `
    -Description "KOVAN weekly retro + S1 drill (dry mode)" -Force | Out-Null
Write-Host "KOVAN-Week registered: every Friday at 18:00. Removal: task-week-remove.ps1"
