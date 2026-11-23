# KOVAN weekly run — the Friday retro + the drill.
# Outputs are written under reports/; the log is UTF-8.
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$kok = Split-Path -Parent $PSScriptRoot
$loop = Join-Path $kok "loop"
Set-Location $loop
$tarih = Get-Date -Format "yyyy-MM-dd"

python retro.py --runs runs --shift-runs vardiya-runs --out reports 2>&1 |
    Out-File -FilePath (Join-Path $loop "reports\retro-$tarih.log") -Encoding utf8
python drill.py 2>&1 |
    Out-File -FilePath (Join-Path $loop "reports\tatbikat-$tarih.log") -Encoding utf8
