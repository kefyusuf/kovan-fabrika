# KOVAN gece gorevini kurar: her gece 23:00 (varsayilan), yerel python, kuru mod.
# Kullanim:  powershell -File gorev-kur.ps1 -Saat 23:00
param([string]$Saat = "23:00")
$eylem = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\gece-kos.ps1`""
$tetik = New-ScheduledTaskTrigger -Daily -At $Saat
Register-ScheduledTask -TaskName "KOVAN-Gece" -Action $eylem -Trigger $tetik `
    -Description "KOVAN gece hatti (kuru mod; model gerekmez)" -Force | Out-Null
Write-Host "KOVAN-Gece kuruldu: her gun $Saat. Kaldirma: gorev-sil.ps1"