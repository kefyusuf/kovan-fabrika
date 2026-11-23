# KOVAN haftalik kosesi — Cuma retrosu + tatbikat.
# Ciktilar reports/ altina yazilir; log UTF-8.
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$kok = Split-Path -Parent $PSScriptRoot
$loop = Join-Path $kok "loop"
Set-Location $loop
$tarih = Get-Date -Format "yyyy-MM-dd"

python retro.py --runs runs --vardiya-runs vardiya-runs --out reports 2>&1 |
    Out-File -FilePath (Join-Path $loop "reports\retro-$tarih.log") -Encoding utf8
python tatbikat.py 2>&1 |
    Out-File -FilePath (Join-Path $loop "reports\tatbikat-$tarih.log") -Encoding utf8