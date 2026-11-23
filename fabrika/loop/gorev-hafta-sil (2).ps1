# KOVAN haftalik gorevini kaldirir.
Unregister-ScheduledTask -TaskName "KOVAN-Hafta" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "KOVAN-Hafta kaldirildi (varsa)."