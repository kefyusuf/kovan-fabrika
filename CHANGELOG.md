# Değişiklik Günlüğü — KOVAN

Format: [Keep a Changelog](https://keepachangelog.com/tr/) · Sürümleme: [SemVer](https://semver.org/lang/tr/).
Tüm tarihler UTC. Bu günlük `fabrika/` paketini (kovan-fabrika) izler.

## [0.2.1] — 2026-11-16

### Düzeltildi
- **Windows konsol tuzağı (cp1252):** stdout/stderr bir PIPE'a bağlıyken Türkçe
  `print` süreci `UnicodeEncodeError` ile öldürüyordu; 10 gece koşusu
  artefaktlar yazıldıktan *sonra* çökmüştü. 11 CLI girişine `konsol.hazirla()`
  bağlandı (UTF-8 + `errors="replace"`).
- `gece-kos.ps1` / `hafta-kos.ps1`: `PYTHONIOENCODING=utf-8`, log UTF-8,
  `--tamamlanan` yolu değişkenle sağlam geçiriliyor.
- Kuyruk ilerlemesi kanıtlandı: `state/tamamlanan.jsonl` 5→6 kayıt
  (K-106); blok/ertelenenler hâlâ kayda girmez (m.4 kuralı).

### Eklendi
- `retro.py --log-saglik`: koşum loglarında çöküm imzası taraması
  (Traceback/UnicodeEncodeError; UTF-16 BOM algılama dahil). Bozuk log varsa
  çıkış kodu 1 — haftalık retro bunu mekanik check olarak üretir.
- `state/gece-durum.log`: her gece iki koşumun çıkış kodu + log temizliği
  kaydı.
- CI: `test_kuyruk_uret.py` + `test_konsol.py` listeye girdi; "Log bütünlüğü
  taraması" adımı eklendi.
- Sektör normu dosyaları: CHANGELOG, SECURITY, CONTRIBUTING, CoC, PR/issue
  şablonları; pyproject PEP 639 lisans + classifiers.

### Paket
- `konsol` modülü py-modules'a eklendi (kurulumda eksik kalmasın).
- Sürüm 0.2.0 → 0.2.1.

## [0.2.0] — 2026-11-08 (v2 sistem)

### Eklendi
- 3 hat mimarisi: **vardiya** (gece kaynağı taraması), **gece** (kapı
  sıralı koşum), **hafta** (retro + tatbikat); 14→6 rol.
- Kuyruk ilerlemesi: `--tamamlanan` ile kabul edilen işler kayda geçer,
  bloklananlar girmez.
- `dogrula.py`: git apply + gerçek test koşumu; kirli ağaç koruması
  (fail-closed) ve `--geri-al`.
- `uyum.py`: kopya blok tespiti (yapı imzası, 6 varyant sağlamlık testli),
  yinelenen fonksiyon, izin listesi.
- `adapter_http.py`: OpenAI-uyumlu adapter, egress günlüğü; sinyal üretmez.
- `sbom.py`: SPDX 2.3 JSON (NTIA minimum öğelerine yönelik).
- `mutasyon.py`: AST mutasyonları + öldürme skoru (6/6 mutant öldü).
- `tatbikat.py`: S1 runbook 5 adım (5/5 PASS); `simulasyon.py` N günlük
  operasyon simülasyonu; `kuyruk_uret.py` kanıtlı iş önerileri.
- Canlı kapı sırası: policy→tests→provenance→lint→types→review→eval
  (bloklayıcı, 0.90)→cost.

## [0.1.0] — 2026-11-04 (ilk hat)

### Eklendi
- `kovan.py` çekirdek: kapasite-bounded plan/run/verify/status; defter
  (JSONL), bütçe, devre kesici, plato, resume.
- `kapasite.py`: LOC→saat, M/M/1 kuyruk, kabul kararı; `seedtest.py`
  deterministik senaryolar.
- Zamanlayıcı kurulumları: KOVAN-Gece (23:00), KOVAN-Hafta (Cuma 18:00).
