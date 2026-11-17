# Katkı Rehberi — KOVAN

Kısa versiyon: **her turda özellik → test → tam paket → doküman senkronu.**
Bu sıra projenin kendi Anayasası'ndan (m.2: üreten ≠ onaylayan) gelir ve
istisnasızdır.

## Geliştirme kurulumu

```bash
pip install -e fabrika --no-build-isolation   # gömülü Python'da gerekli
cd fabrika/loop
python tests/test_kovan_cli.py                # duman testi
python kovan.py plan                          # kuru mod: sıfır token
```

Gereksinimler: Python ≥ 3.11, `pyyaml>=6,<7`. Canlı mod **isteğe bağlıdır**
ve kendi API anahtarınızla çalışır; hiçbir test model çağrısı yapmaz.

**Taze klon notu:** `fabrika/loop/ornek-repo` yayında dosyalarıyla gelir
(git geçmişi hariç). Testler onun git deposu olmasını bekler — bir kez:

```bash
git -C fabrika/loop/ornek-repo init
git -C fabrika/loop/ornek-repo add -A
git -C fabrika/loop/ornek-repo commit -m "ornek-repo ilk sürüm"
```

## Test normu

- **19 test dosyası, tam paket yeşil olmadan PR açılmaz.** Sayı değişirse
  `SISTEM.md` toplam satırı güncellenir.
- Yeni davranış → önce test. Kapı mantığına dokunan değişiklikte
  `tests/test_runner.py` kapı sırası testleri korunmalı.
- Determinizm: `kuru_senaryo(isler, seed)` aynı seed → aynı kararlar.
- Her hafta retro `--log-saglik` koşar; log temizliği PR normudur.

## Kapı sırasına dokunma kuralları

Sıra: policy → tests → provenance → lint → types → review → eval → cost.
- Kapı sırası değişikliği **ADR** gerektirir (`fabrika/ADR.md`'ye kayıt).
- Bloklayıcı kapıyı uyarıya indirme PR'ı varsayılan olarak reddedilir.
- Eval eşiği (0.90) yalnızca mutasyon kanıtıyla değişir.

## PR normu

1. Şablonu doldurun (koşulan test sayısı + doküman senkronu checklist'i).
2. **Kendi PR'ınızı kendi onaylayamazsınız** (m.2) — bağımsız incelemeci
   ya da kurucu onayı gerekir.
3. Türkçe doküman normu: kullanıcıya dönük metin Türkçe; kod, kodun kendi
   konvansiyonunu izler.
4. Kanıt (`runs/`, `state/`, loglar) repoya girmez — `.gitignore` hazır.

## İletişim

- Hata: issue şablonu (log + yeniden üretme adımı zorunlu).
- Güvenlik: SECURITY.md akışı — asla halka açık issue değil.
- Davranış: CODE_OF_CONDUCT.md.
