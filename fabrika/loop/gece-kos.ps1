# KOVAN gece kosesi — gorev zamanlayici bunu her gece calistirir.
# Cikislar runs/ ve vardiya-runs/ altina yazilir; log UTF-8.
# EVIDENCE §15: artefakt var ≠ kosu basarili — exit kodu ve log bütünlüğü
# state\gece-durum.log'a islenir; haftalik retro bunu --log-saglik ile tarar.
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$kok = Split-Path -Parent $PSScriptRoot
$loop = Join-Path $kok "loop"
Set-Location $loop
$id = Get-Date -Format "yyyyMMdd-HHmm"
New-Item -ItemType Directory -Force -Path (Join-Path $loop "state") | Out-Null

$kovanLog = Join-Path $loop "runs\gece-$id.log"
$vardiyaLog = Join-Path $loop "vardiya-runs\vardiya-$id.log"

python kovan.py run --run-id "gece-$id" --out runs `
    --tamamlanan (Join-Path $loop "state\tamamlanan.jsonl") 2>&1 |
    Out-File -FilePath $kovanLog -Encoding utf8
$kovanKod = $LASTEXITCODE

python vardiya.py run --id "vardiya-$id" 2>&1 |
    Out-File -FilePath $vardiyaLog -Encoding utf8
$vardiyaKod = $LASTEXITCODE

$kovanTemiz = $true
$vardiyaTemiz = $true
if (Test-Path $kovanLog) {
    $kovanTemiz = -not (Select-String -Path $kovanLog -Pattern "Traceback|UnicodeEncodeError" -Quiet)
}
if (Test-Path $vardiyaLog) {
    $vardiyaTemiz = -not (Select-String -Path $vardiyaLog -Pattern "Traceback|UnicodeEncodeError" -Quiet)
}
$evet = "EVET"; $hayir = "HAYIR"
$satir = "{0} | kovan-cikis: {1} temiz: {2} | vardiya-cikis: {3} temiz: {4}" -f `
    $id, $kovanKod, $(if ($kovanTemiz) { $evet } else { $hayir }), `
    $vardiyaKod, $(if ($vardiyaTemiz) { $evet } else { $hayir })
Add-Content -Path (Join-Path $loop "state\gece-durum.log") -Value $satir -Encoding utf8
