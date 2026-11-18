# Removes the KOVAN weekly task.
Unregister-ScheduledTask -TaskName "KOVAN-Week" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "KOVAN-Week removed (if it existed)."
