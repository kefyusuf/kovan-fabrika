# KOVAN — Yol Haritası, Riskler, Öldürme Kriterleri

> 12 hafta. Her hafta tek bir çıktı ve tek bir kapı. "Haftalık hedef" cümlesi
> ölçülebilir değilse yazılmadı.

---

## 1. Kilometre taşları

| # | Hafta | Ad | Çıkış kriteri (kanıt) |
|---|---|---|---|
| **M0** | 0 | Konsept + çekirdek | Bu doküman seti + `runner.py` 22 test |
| **M1** | 1–2 | Tek hat, gerçek model | 1 adapter, 20 görevlik kuyruk, policy entegre |
| **M2** | 3–4 | Gerçek ölçüm | Eval set v1 (≥50), 20 görev uçtan uca, GPK/MBB ölçülmüş |
| **M3** | 5–6 | Gece vardiyası | 5 gece üst üste sabah raporu |
| **M4** | 7–8 | Beceri | 3 aday → 1 aktif beceri, gölge moddan geçmiş |
| **M5** | 9–10 | Kendini geliştirme | 1 C1 değişikliği kanaryadan geçmiş + geri alma testi |
| **M6** | 11–12 | Sertleştirme | Sandbox, SBOM, 2 hafta kesintisiz |

---

## 2. Haftalık plan

### Hafta 1 — Modeli bağla
- **İş:** `Adapter` implementasyonu (tek sağlayıcı, tek model); 3 araç: dosya oku/yaz, shell, arama. `policy` kapısını Airlock CLI'ya bağla.
- **Çıktı:** 5 gerçek görev, kuru koşu olmadan.
- **Kapı:** 5 görevden 3'ü kapılardan geçer (GPK ≥ %60 küçük n'de gösterge).
- **Risk:** Model çıktısı senaryodan çok daha gürültülü → ret oranı yüksek.

### Hafta 2 — Kuyruk ve maliyet
- **İş:** `backlog.yaml` (öncelik, bağımlılık, sınıf), token muhasebesi, maliyet manifesti, `butce-bekcisi` kuralları.
- **Çıktı:** 20 görevlik gerçek kuyruk; ilk maliyet raporu.
- **Kapı:** MBB ölçülmüş (tek sayı + n).
- **Risk:** Maliyet ilk hafta 3–5 kat sapar; tavan koymadan devam etmemek.

### Hafta 3 — Eval seti v1
- **İş:** Geçmiş 50 hatadan regresyon seti; 30 adversarial; set sahipliği ayrımı; manifest.
- **Çıktı:** `olcum/sets/regression-v1/`, `eval` kapısı gerçek.
- **Kapı:** Set, bilinen 5 hatayı yakalar (kappa > 0.6 iki etiketleyici arası).
- **Risk:** Set, kural yazan ajan tarafından görülürse yanar → erişim ayrımı.

### Hafta 4 — İlk gerçek ölçüm
- **İş:** 20 görev uçtan uca; GPK, BMP, MBB, DSP (örneklem); ilk retrospektif.
- **Çıktı:** `rapor/olcum-hafta-4.md` — sayılar + hata listesi.
- **Kapı:** Ölçüm tekrar edilebilir (aynı set, iki koşu, ±%5).
- **Risk:** Örneklem küçük; "sonuç" değil "gösterge" demeyi öğrenmek.

### Hafta 5 — Gece vardiyası iskeleti
- **İş:** H2 döngüsü: ajanda, zaman kutuları, kaynak allowlist, ham not → iddia.
- **Çıktı:** 1 gece, kısmi rapor.
- **Kapı:** Rapor 06:00'da dosyada (içerik zayıf olabilir).
- **Risk:** Ajan tavşan deliğine girer; zaman kutusu sert olmalı.

### Hafta 6 — Beş gece
- **İş:** 5 gece üst üste; her gece 2–4 not, 0–2 beceri adayı.
- **Çıktı:** 5 sabah raporu + `lessons` birikimi.
- **Kapı:** 5/5 rapor; en az 3 kaynaklı not/gece.
- **Risk:** Tekrar eden içerik; arşivci tekrar birleştirmesi devreye girmeli.

### Hafta 7 — Damıtma
- **İş:** `SKILL.md` şeması, 5 adımlı damıtma, test zorunluluğu, gölge mod.
- **Çıktı:** 3 beceri adayı, her biri testli.
- **Kapı:** Adaylardan biri gölgede 20 görevde ölçülmüş.
- **Risk:** Slogan beceriler; "davranış değişikliği" testi bunu kesmeli.

### Hafta 8 — İlk aktif beceri
- **İş:** 1 beceriyi aktive et; önce/sonra ölçümü (aynı görev sınıfı).
- **Çıktı:** `skills/*/SKILL.md` + ölçüm kaydı.
- **Kapı:** Hedef metrikte ≥ %10 iyileşme veya maliyette ≥ %15 düşüş.
- **Risk:** İyileşme gürültüden ayırt edilemez → 2 hafta tekrar.

### Hafta 9 — C1 önerisi ve kanarya
- **İş:** Prompt/kadro değişikliği önerisi (ADR taslağı), gölge → kanarya → tam.
- **Çıktı:** 1 kanarya sürümü, geri alma tatbikatı.
- **Kapı:** Geri alma 60 saniyede çalışır.
- **Risk:** Geri alma test edilmezse, ilk gerçek olayda çalışmaz.

### Hafta 10 — Yapı önerisi
- **İş:** H4: ledger'dan 1 ADR taslağı ("hangi rol gereksiz", "hangi kapı yavaş").
- **Çıktı:** `oneri/ADR-F13-*.md`, ölçüm planıyla.
- **Kapı:** Öneri, 14 günlük beklemeye alınır (uygulanmaz).
- **Risk:** Öneri sayısı şişer; haftada ≤ 2 sınırı.

### Hafta 11 — Sertleştirme
- **İş:** Sandbox (konteyner + allowlist), SBOM, egress log, S1 runbook tatbikatı.
- **Çıktı:** İzolasyon kanıtı (ağ kesikken çalışma), `uyum/sbom.json`.
- **Kapı:** Sandbox dışına yazma denemesi bloklanır.
- **Risk:** Sandbox, hızı %30 düşürür; bu kabul edilmeli.

### Hafta 12 — Kapanış
- **İş:** 2 hafta kesintisiz koşu; tüm metrikler; dürüst kapanış raporu.
- **Çıktı:** `rapor/v1-kapanis.md` — ne oldu, ne olmadı.
- **Kapı:** Öldürme kriterlerinin hiçbiri tetiklenmemiş.
- **Risk:** "Başarı" anlatısı baskısı; rapor kötü haberi önce yazar.

---

## 3. Risk kaydı

| # | Risk | Olasılık | Etki | Önlem | Tetikleyici |
|---|---|---|---|---|---|
| R1 | Ajan çıktısı güvenilmez, ret oranı yüksek | Yüksek | Orta | Küçük görev + güçlü spec | GPK < %25 (hafta 4) |
| R2 | Eval seti yanar / dairesel olur | Yüksek | Yüksek | Sahiplik ayrımı + set kimliği | Aynı sette 2. kez iyileştirme |
| R3 | Maliyet tavanı aşılır | Orta | Yüksek | Rezervasyon + kademe düşürme | MBB > 10 USD (2 hafta) |
| R4 | Gece raporu içeriksizleşir | Orta | Orta | Zaman kutusu + "boş" etiketi | 3 gece üst üste < 2 not |
| R5 | İnceleme darboğazı | Yüksek | Orta | İ6: inceleme bütçesi | Kuyruk > 2 gün |
| R6 | Beceri enflasyonu | Orta | Orta | Kullanım sayacı + çürüme | 10 beceri, < 3 kullanım |
| R7 | Prompt enjeksiyonu | Orta | Yüksek | İzolasyon + ölçümlü üçlü yasağı | Herhangi bir S1 olay |
| R8 | Sır sızıntısı | Düşük | Çok yüksek | Secret yok + yasak yol | `.env` diff'te |
| R9 | Lisans ihlali | Düşük | Yüksek | Provenance + allowlist | Yeni bağımlılık |
| R10 | Kendini yetkilendirme | Düşük | Çok yüksek | C3 + yasak yol + defter | Anayasa diff'i |
| R11 | Tek kişiye bağımlılık | Yüksek | Orta | Tüm kararlar dosyada | Kurucu 7 gün yok |
| R12 | "Fabrika" metaforunun satmaması | Orta | Düşük | Ürün adı kapı+hafıza | 3 müşteri görüşmesi |

---

## 4. Öldürme kriterleri

Bunlar "kötü gidiyor" hissi değil, **durma** koşullarıdır. Tetiklendiğinde
proje durur, yeniden tasarlanır veya kapanır.

| # | Kriter | Eşik | Karar |
|---|---|---|---|
| **Ö1** | Kapı geçme oranı | Hafta 6'da GPK < %25 (n ≥ 20) | Yaklaşımı değiştir: görevleri küçült, spec'i sertleştir |
| **Ö2** | Birim maliyet | 2 hafta MBB > 10 USD | Durdur: ekonomi çalışmıyor |
| **Ö3** | Gece güvenilirliği | 10 gecenin < 5'inde rapor | H2'yi kapat: gece vardiyası hazır değil |
| **Ö4** | Regresyon | KKA > 5 / 100 PR | Durdur: hız kaliteyi yiyor |
| **Ö5** | Öğrenme | 3 ayda 0 beceri aktive edilemedi | "Öğrenen fabrika" iddiasını bırak; üretim hattı olarak devam et |
| **Ö6** | Denetim | Defter doğrulanamıyor (1 kez) | Anında dur: tüm iddialar geçersiz |

**Ö6 özeldir:** Tek bir doğrulama hatası, diğer tüm metrikleri anlamsız kılar.

---

## 5. Bu gece ne yapılabilir (gerçekçi)

Bu teslimat bir gece içinde üretildi; aynı gecenin **genelleştirilebilir**
planı şu:

| Saat | İş | Çıktı | Durum |
|---|---|---|---|
| 21:00–22:00 | Hedef sözleşmesi + kapsam | `goal.yaml` | ✅ yapıldı |
| 22:00–23:30 | Paralel araştırma (7 hat) | `arastirma/*.md` | ✅ 3 dosya + özetler |
| 23:30–01:00 | Konsept + PRD | `README.md`, `PRD.md` | ✅ |
| 01:00–02:00 | Mimari + org | `MIMARI.md`, `ORGANIZASYON.md` | ✅ |
| 02:00–03:00 | Çekirdek kod + test | `loop/runner.py`, 22 test | ✅ |
| 03:00–04:00 | Öğrenme + kalite + yönetişim | 3 belge | ✅ |
| 04:00–05:00 | ADR + yol haritası | `ADR.md`, bu dosya | ✅ |
| 05:00–06:00 | Öz denetim + sabah raporu | `SELF-REVIEW.md` | ✅ |

**Yapılamayanlar (dürüstçe):** gerçek model bağlantısı, gerçek eval seti,
gerçek maliyet, pazar görüşmesi, hukuk incelemesi. Bunlar bir gecede
"yapılmış gibi" gösterilemez; `SELF-REVIEW.md`'de eksik olarak listeli.

---

## 6. Sabah kontrol listesi (5 dakika)

1. `fabrika/loop/ornek-cikti/sabah-raporu-ornek.md` — rapor okunur mu?
2. `fabrika/loop/tests/` — 22 test geçiyor mu? (`python tests\test_runner.py`)
3. `fabrika/ADR.md` — 12 kararın hepsi tek sayfada anlaşılıyor mu?
4. `fabrika/SELF-REVIEW.md` — en zayıf üç varsayım kabul edilebilir mi?
5. Karar: M1'e geçilsin mi, yoksa kapsam mı daraltılsın?

Beşinci madde tek gerçek karardır; diğer dördü onu besler.
