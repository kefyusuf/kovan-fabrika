# Removes the KOVAN night task.
Unregister-ScheduledTask -TaskName "KOVAN-Night" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "KOVAN-Night removed (if it existed)."
