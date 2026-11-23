# KOVAN gece gorevini kaldirir.
Unregister-ScheduledTask -TaskName "KOVAN-Gece" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "KOVAN-Gece kaldirildi (varsa)."