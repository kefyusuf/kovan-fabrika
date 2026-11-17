# KOVAN haftalik gorevini kurar: her Cuma 18:00 (retro + tatbikat, yerel, kuru mod).
# Kullanim:  powershell -File gorev-hafta-kur.ps1
$eylem = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\hafta-kos.ps1`""
$tetik = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "18:00"
Register-ScheduledTask -TaskName "KOVAN-Hafta" -Action $eylem -Trigger $tetik `
    -Description "KOVAN haftalik retro + S1 tatbikat (kuru mod)" -Force | Out-Null
Write-Host "KOVAN-Hafta kuruldu: her Cuma 18:00. Kaldirma: gorev-hafta-sil.ps1"