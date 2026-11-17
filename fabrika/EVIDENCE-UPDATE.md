# Kanıt Güncellemesi — Derin Araştırma Sonrası Konsept Düzeltmeleri

**Tarih:** 22 Ekim 2026
**Kaynak:** [`../arastirma/KOVAN-DERIN-ARASTIRMA-2026-10-22.md`](../arastirma/KOVAN-DERIN-ARASTIRMA-2026-10-22.md)
**Amaç:** Araştırma, konseptin bazı cümlelerini doğruladı, bazılarını düzeltilmesi gereken hale getirdi. Bu dosya, hangi dokümanda neyin değişeceğini tek yerde tutar.

---

## 1. Üç düzeltme (iddia → kanıt)

### D1 — "Kendi kendine öğrenen fabrika" ifadesi daraltılmalı

**Eski cümle:** "KOVAN, gece öğrenen, kendi yapısını geliştiren bir fabrikadır."
**Sorun:** Literatürdeki sistemler (DGM, SICA) model ağırlıklarını değiştirmiyor; **iskeleti** (ajan kodu, araç, kontrol akışı, prompt) değiştiriyor. DGM kendi metninde "frozen pretrained FMs" diyor; `DGM_outer.py` sabit, yani arama prosedürü evrilmiyor.
**Yeni cümle:** "KOVAN, donmuş model altında **iskeletini, becerisini ve kapı setini** evrimleştiren bir fabrikadır. Ağırlık öğrenmesi kapsam dışıdır."
**Etki:** README §3 (İ4), OGRENME §1 ve §6.4, ADR-F03.

### D2 — "Spec zorunluluğu azalıyor" değil, "onay kapıları kalkıyor"

**Eski cümle:** "Spec-driven araçlar spec zorunluluğunu azaltıyor; spec bakım yüküne dönüşüyor."
**Sorun:** Birincil dokümanlar artefaktın korunduğunu gösteriyor: Kiro "all three artifacts without approval gates"; Spec Kit "independent entry points, not mandatory phases"; GSD quick "skips research, discussion, plan-checker, verifier" ama `PLAN.md`+`SUMMARY.md` üretiyor. "Bakım yükü" gerekçesi resmî dokümanlarda yok. Tek istisna BMAD: "small changes go straight to build".
**Yeni cümle:** "2026'da araçlar **onay kapılarını** koşullu hale getirdi; spec artefaktı çoğunlukla korunuyor. Kaldırılan şey kapıysa, kaldırılan şey kanıttır."
**Etki:** PRD FR-02/FR-05, ADR-F05, OGRENME §3 (huni), KALITE §2.

### D3 — "Gece vardiyası" takvim kazancı değil, WIP artışı

**Eski cümle:** "Gece 7 saat üretim, sabah raporu."
**Sorun:** Üretim kapasitesi artarken kabul kapasitesi sabit: PR hacmi ×2, incelemede medyan süre +%441,5. Gece üretimi sabah kuyruğunu büyütür; akış hızlanmaz.
**Yeni cümle:** "Gece vardiyası, **sabah inceleme kapasitesi kadar** iş alır. Kapasitenin üstünde üretim, kaliteyi değil borcu büyütür."
**Etki:** README §3 (İ6), ORGANIZASYON §6, YOL-HARITASI H5–H6, `loop/goal.yaml` (max_parallel_workers).

---

## 2. Dört ekleme (konseptte yoktu)

### E1 — İnceleme bütçesi formülü

```
Haftalık inceleme yükü (saat) = Σ_PR ( LOC_PR / 500 ) + 0,25 × PR_sayısı
Kuyruk gecikmesi (M/M/1)      = (ρ / (1-ρ)) × (1/μ)
WIP limiti (Little)            = hedef cycle time × günlük PR sayısı
```

Kalibrasyon: 400 LOC ≈ 0,8–1,0 saat (Cisco/SmartBear); μ=10 PR/gün tabanında ρ=0,625 → ~4 saat (Google <4 saat), ρ=0,80 → 9,6 saat, ρ=0,89 → ~19 saat (Faros %441), ρ=0,95 → 45,6 saat. Kuyruk *uzunluğu* ile kuyruk *süresi* karıştırılmamalı.
**Nereye:** PRD §9 (BMP yerine "review-hours/PR"), KALITE §4, ORGANIZASYON §8.

### E2 — Tohumlanmış hata seti

Kapıların gerçekten yakaladığını ölçen tek yöntem: PR'a bilinen hatalar enjekte et, kapının yakalama oranını ölç. Ajan-ajan incelemesinin kusur yakalama oranı bugün **ölçülmemiş**; en yakın veri gözlemsel (yorumların %73,8'i kod değiştiriyor, ama "hata yakaladı" değil).
**Nereye:** KALITE §3.1 (yeni set türü: `seeded`), YOL-HARITASI H3.

### E3 — Yargıç kalibrasyonu

LLM-yargıçta ham uyum, şansa göre düzeltilmiş κ'yı 33,8–41,3 puan şişiriyor; "%85 uyum" ≈ κ 0,48. Bu yüzden:
- Kapı raporu **κ** verir, ham uyum vermez.
- Pozisyon/uzunluk yanlılığı test edilir.
- Yargıç asla tek kapı değildir.
**Nereye:** KALITE §2.2 ve §7.

### E4 — Kimlik, izolasyon, geri alma

- Ajan ortamına secret konmaz; OIDC ile kısa ömürlü kimlik, repo/branch kapsamı.
- Dosya ve ağ izolasyonu **birlikte**; biri eksikse diğeri işlevsiz.
- `soft-delete` + yedek izolasyonu + geri alma tatbikatı.
- Referans olay: 9 saniyede silinen veritabanı; kök neden aynı token'la erişilen yedekler.
**Nereye:** YONETISIM §2, §4, §8; `loop/goal.yaml sandbox`.

---

## 3. Doğrulanan altı ilke

| İlke | Kanıt durumu |
|---|---|
| İ1 Kanıt yoksa iş yok | **Doğrulandı** — benchmark emekliliği, κ şişmesi, test hacking |
| İ2 İki vites | **Doğrulandı** — üretim/kabul ayrımı |
| İ3 Değişmez çekirdek | **Doğrulandı** — DGM arama prosedürünü sabit tutuyor |
| İ4 Öğrenme = dosya | **Doğrulandı** — bellek fiilen dosya; alternatif sevk edilmiyor |
| İ5 Değerlendirici tavandır | **Doğrulandı** — üç bağımsız kanıt hattı |
| İ6 Üretim = inceleme kapasitesi | **Doğrulandı ve sayısallaştı** — formül eklendi |

---

## 4. Doküman eşlemesi (uygulanacak düzeltmeler)

| Doküman | Bölüm | Değişiklik |
|---|---|---|
| `README.md` | §3 İ4, İ6 | D1 ve D3 cümleleri |
| `PRD.md` | §7 FR-02, FR-05; §9 | D2; review-hours metriği |
| `MIMARI.md` | §8 | WIP limiti formülü |
| `ORGANIZASYON.md` | §6, §8 | Gece kapasitesi; inceleme-saati karnesi |
| `OGRENME.md` | §1, §6.4 | D1; "iskelet evrimi" tanımı |
| `KALITE.md` | §2, §3, §4, §7 | E2, E3, review-hours |
| `YONETISIM.md` | §2, §4, §8 | E4 |
| `YOL-HARITASI.md` | H3, H5–H6 | Seeded set; gece kapasitesi |

Bu düzeltmeler **henüz uygulanmadı**; bu dosya, uygulanacak değişikliklerin denetlenebilir listesidir. Uygulama ayrı bir iş kalemi (v0.2).

---

## 5. Yeni açık sorular

1. **Tohumlanmış hata seti nasıl kurulur?** Geçmiş 100 PR'dan hata enjeksiyonu ile mi, sentetik mi?
2. **İnceleme-saati nasıl ölçülür?** GitHub olay loglarından oturum süresi çıkarılabilir mi?
3. **κ kalibrasyonu için insan etiketi kimden?** Tek kişilik kurulumda etiketleyici kim?
4. **Gece kapasitesi nasıl tavanlanır?** Sabah kaç PR inceleyebiliyorsun; bu sayı ölçüldü mü?
5. **"İskelet evrimi" hangi dosyalarda izinli?** `skills/`, `kadro/`, `loop/` — hangisi C1, hangisi C3?

---

## 6. Tek karar önerisi

v0.2 kapsamına iki iş eklenmeli:
1. **Review budget + review-hours metriği** (gece kapasitesini tavanlar).
2. **Tohumlanmış hata seti** (kapıların gerçekten yakaladığını ölçer).

İkisi de mevcut mimariye eklenebilir; yeni bileşen gerektirmez. Ve ikisi de, "fabrika" iddiasının ölçülebilir tek zeminini kurar.

---

## 7. Canlı profil sapması (S2 · 4 Kasım 2026)

Gerçek model bağlantısı (adapter_http.py) ve gerçek doğrulama katmanı
(dogrula.py) devreye alındı. İki kayıt:

1. **Runner boolean sinyal hatası düzeltildi.** `signal` alanlı bir kapıda
   boolean `False`, sayısal `0.0` sayılıp kapıyı geçiriyordu. Artık boolean
   sinyal her koşulda boolean sayılır; regresyon testi eklendi
   (test_runner: `test_bool_signal_with_signal_field_is_boolean`).
2. **Canlı profil (gates-canli.yaml):** review ve eval kapıları geçici
   olarak *uyarıcı*. Gerekçe: S2'de bu kapılar sinyal üretmiyor. Bu bir
   gevşetme değil ertelemedir: her satırda tarihli gerekçe var ve S3'te
   (eval v1 ≥50 vaka + bağımsız incelemeci) bloklayıcıya dönecek. Kapı
   *kaldırılmadı*; sinyal üretilmeyen kapı zaten fail-closed düşüyor.

---

## 8. S3 güncellemesi (4 Kasım 2026)

1. **Eval v1 devrede ve bloklayıcı.** `eval_set/sicaklik-v1.jsonl` — 90
   vakalık dondurulmuş set (golden değerler mevcut referans davranıştan;
   set davranış değişimini yakalar, matematiksel doğruluğu kanıtlamaz).
   `eval_kos.py` diff'i depoya uygulayıp seti koşar, skor 0,90 eşiğiyle
   bloklayıcı. Kırık formül diff'i skoru 0,90'ın altına düşürdü (testte
   doğrulandı). Canlı profilde eval artık `blocking: true`.
2. **Set yazarı hatası da yakalandı:** ilk sette `ortalama` vakaları
   argüman açılımı yüzünden 7 tutarsızlık üretti; skor 0,922'ye düştü.
   Set düzeltildi → 90/90. Ders: eval seti de kapıdan geçmeli.
3. **Bağımsız incelemeci sözleşmesi:** `incelemeci.py` — ikinci model uç
   noktası, yapılandırılmış karar JSON'u, gerekçesiz onay otomatik ret.
   `--inceleme-url` verildiğinde review kapısı programatik olarak
   bloklayıcıya yükselir ve kararlar rapora düşer; verilmezse uyarıcı kalır.
4. **Gece hattı çalışıyor (kuru mod).** `vardiya.py`: yerel kaynaklardan
   kaynaklı not (15 iddia), tekrar eden dersten beceri adayı (seen ≥ 2),
   seedtest tabanlı kırılma raporu (canlı profilin kaçırdığı tür:
   tasarım hatası), defter istatistiğinden ölçüm planlı ADR taslağı ve
   5 bölümlü sabah raporu. C2 gece kapalı; model bağlandığında aynı hat
   adapter'a geçer, dosya sözleşmesi değişmez.
5. **Döngü hedefi devreye alındı (4 Kasım 2026).** `kovan.py durum` —
   tüm koşuların çapraz metrikleri (kabul/blok/ret, revizyon, ortalama
   doluluk, en çok düşen kapılar, tekrar eden dersler, vardiya sayısı).
   Windows Görev Zamanlayıcı'ya **KOVAN-Gece** görevi kuruldu: her gece
   23:00 yerel python, kuru mod (sıfır token); çıktılar `runs/` ve
   `vardiya-runs/` altına + log yan dosyasına. Kaldırma: `gorev-sil.ps1`.
   Model anahtarı geldiğinde `gece-kos.ps1` içine `--adapter http` satırı
   eklenir; hat aynı kalır. Görev, elle bir kez koşturularak doğrulandı
   (gece-20261104-2026 / vardiya-20261104-2026; iki defter de sağlam).
7. **Provenance sinyali gerçek ölçüme bağlandı.** `uyum.py`: diff'ten
   yeni import köklerini çıkarır; stdlib serbest, üçüncü taraf yalnızca
   `uyum-izinli.yaml` listesindeyse serbest, bağımlılık dosyası değişimi
   ise REDDET (C3). Böylece canlı profilde dört bloklayıcı kapının
   hepsi (policy, tests, provenance, eval) gerçek ölçümle çalışır;
   review koşullu (incelemeci), cost uyarı. SBOM (SPDX) ve kopya kod
   tespiti S4'te.

---

## 9. S4 ilk adım — "dikkatli tur" (4 Kasım 2026)

Hiçbir mevcut test bozulmadı (93 → 103, hepsi yeşil); ornek-repo çalışma
ağacı temiz; önceki iki defter değişmedi.

1. **SBOM tohumu (`sbom.py`):** depo .py'ları `ast` ile taranır (exec yok);
   stdlib ve yerel modüller SBOM'a girmez, üçüncü taraf SPDX 2.3 Package
   olur (kuruluysa sürüm, yoksa NOASSERTION). ornek-repo: packages = 0
   (yalnızca stdlib + yerel).
2. **Kopya şüphesi (uyum.py):** eklenen satırlarda Copyright/SPDX başlığı
   → provenance False, gerekçe "insan kararı". seedtest'in `kopya_kod`
   hata türü artık ölçülebilir sinyale bağlandı.
3. **`dogrula.py --geri-al`:** depoyu HEAD'e döndürüp temizliği raporlar.
4. **`kovan.py --kanarya N`:** kabul edilenlerin yalnızca ilk N'i koşulur;
   kalanlar kapasiteyi harcamış sayılır (dürüst muhasebe) ve rapor
   başlığına KANARYA damgası düşer.
5. **Lock dosyasından sürüm okuma:** `sbom.py` requirements/pyproject'teki
   sabitlenmiş sürümleri öncelikler; modül→dağıtım eşlemesi
   `packages_distributions()` ile çözülür (yaml → PyYAML).
6. **Yinelenen fonksiyon tespiti (uyum):** diff'in eklediği fonksiyon adları
   depodakilerle kesişirse `uyum_not`'a düşer — bloklayıcı değil, review
   sinyali. Fail-closed değil: bilgi katmanı.
7. **Egress kaydı (adapter_http):** her dış çağrı `--egress-log` verilirse
   JSONL'e yazılır (ts, host, model, sonuç) — YONETISIM §4 denetim
   maddesinin ilk somut parçası.

---

## 10. İlk otonom gece + ilk sistem-düzeltmesi (5 Kasım 2026)

**KOVAN-Gece 04.11.2026 23:00'te kendiliğinden çalıştı** (LastTaskResult 0):
- kovan: 4 kabul / 1 blok (K-107, politika) / 1 revizyon; defter 6 kayıt sağlam;
- vardiya: 15 kaynaklı iddia, beceri adayı, kırılma raporu, ADR taslağı, sabah raporu;
- C2 yazılmadı (anayasa m.3 uyumlu).

**Sistemin kendi yakaladığı kusur:** beceri adayı her gece yeniden
üretiliyordu (3 kopya birikmişti). Tekrar eden ders, tekrar eden "yeni
öğrenme" değildir — damıtma idempotent yapıldı: adaylar paylaşılan
dizine yazılır, varsa yazılmaz, deftere `beceri_adayi_zaten_var` düşer.
Regresyon testi: iki koşumda dosya sayısı artmaz, rapor "Zaten adaydı" yazar.

---

## 13. Yayın paketi (10 Kasım 2026)

1. **Güvenlik: kirli ağaç koruması.** `dogrula.uygula` artık `git status
   --porcelain` kirli ise uygulamayı REDDEDER — canlı modda kullanıcının
   commitlenmemiş işini `reset --hard` silemez (fail-closed, testli).
2. **Kurulum:** `fabrika/pyproject.toml` + entry point'ler
   (`kovan/vardiya/tatbikat/beceri`). Kanıt: `pip install -e fabrika
   --no-build-isolation` sonrası `kovan plan` repo kökünden çalıştı;
   kapasite valfi saat=2'de K-103'ü doğru erteledi. Not: py-modules
   `loop/` altında olduğundan `package-dir` eşlemesi gerekti.
3. **Yapılandırma:** `loop/kullanici.yaml` — kullanıcı varsayılanları tüm
   alt komutlara uygulanır, CLI ezer. Argparse tuzağı (alt ayrıştırıcı
   varsayılanı ana varsayılanı ezer) testle belgelendi.
4. **README.en.md** (İngilizce hızlı başlangıç + güvenlik uyarıları) ve
   **CI** (`.github/workflows/tests.yml`: 15 test dosyası + tatbikat).
5. **.gitignore:** koşu kanıtları, loglar ve anahtar dosyaları hariç.

**Public kullanım hedefi:** self-hosted, bring-your-own-key geliştirici.
Barındırılan servis (SaaS) X2 hedef-dışıdır (YONETISIM).

---

## 12. S4 kapanış parçaları (10 Kasım 2026)

1. **Kopya kod blok tespiti (seviye 2):** `uyum.kopya_blok_tara` — diff,
   geçici klon'a uygulanır; yeni fonksiyon gövdeleri, **yapı imzası** ile
   (tanımlayıcı/sayı/metin maskelenmiş token dizisi) depodaki fonksiyonlarla
   karşılaştırılır. Eşik: ≥12 satır, benzerlik ≥0,90; kendi eski hali hariç.
   Kanıt demo: `istatistik` fonksiyonunun değişkenleri yeniden adlandırılmış
   kopyası skor 1,0 → provenance False. Canlı profil: kopya şüphesi
   provenance'ı False yapar (fail-closed, insan kararı gerekir).
2. **S1 runbook tatbikatı (`tatbikat.py`):** normal koşu, defter doğrulama,
   STOP ile durdurma, kirli klon üzerinde geri alma — 4/4 PASS. A4'ün ilk
   sürümündeki CRLF karşılaştırma hatası `git status --porcelain` ölçütüyle
   düzeltildi.
3. **Kanarya muhasebesi:** `--kanarya N` koşulan işleri N'e indirir; kalan
   işler kapasiteyi harcamış sayılır (ertelenen olarak deftere geçer).
4. **Haftalık retro otomasyonu (`retro.py`):** defterden GPK vekili hesaplar
   (ilk karar kabul ise ilk tur sayılır), kapı trendini çıkarır ve **koşulabilir
   mekanik checkler** üretir (ORGANIZASYON §6 kuralı). Bilinen sınır: GPK
   vekili tüm koşuları karıştırır — run-bazlı ayrım S3b.
5. **Tatbikata A5 kaos adımı:** kesinti → resume; koşucu kabul edilmiş işi
   tekrar etmez, düşen işi sonraki vardiyada yeniden dener (fail-closed davranış
   tatbikatla kanıtlandı — 5/5 PASS).

**Kalan:** yalnızca girdi — API anahtarı (canlı ölçüm) ve gerçek backlog
(GPK/MBB). Ayrıca mutasyon testi devrede: ilk 6 mutantın **tamamı eval ve
gerçek test koşumu tarafından öldürüldü** — "kapılar yakalıyor" iddiası
artık yaptırım kanıtlı (§12'nin devamı, 10 Kasım 2026).

---

## 11. İlk beceri aktive edildi (5 Kasım 2026)

**Önce sistem iki kez kendini onaylamayı REDDETTİ** (m.2 çalışıyor):
`AKTİFLEŞTİRME RED: insan onay notu yok`. Sonra kurucu kararı soruldu
(ask_user) ve onay kayda geçirildi.

- **Beceri:** `tests-kapisi-tekrar-dusmesi` v0.2.0 — prosedürü gerçek koda
  çevrildi: `beceri.test_zayiflatma_tespiti(diff)` (5 vaka testli: silme,
  `assert True` zayıflatma, meşru takas, tests/ dışı, dosya silme).
- **Yürütme koşullu:** koşucu beceriyi yalnızca `status: active` iken
  uygular; proposed beceri pipeline'ı etkileyemez (m.6 kod karşılığı).
- **Canlı simülasyon kanıtı:** `assert True` ile geçen yama →
  `tests=False`, not: "beceri taraması: assertion zayıflatıldı",
  `kullanim.jsonl`'a kullanım kaydı düştü (ÖVD artık ölçülebilir).
- **Yaşam döngüsü:** proposed → active → stale (90 gün) → archived;
  aktifleşme ölçütleri: beceri testi geçiyor + kanıt ≥ 2 görev + insan
  onayı. Çürüme raporu: `beceri.py rapor`.

**Öğrenme döngüsü ilk kez uçtan uca kapandı:** hata → ders → beceri
adayı → insan onayı → aktif beceri → pipeline'da yaptırım → kullanım
sayacı. Ağırlık öğrenmesi yok; **dosya öğrenmesi var** (İ4).

---

## 14. Kuyruk ilerlemesi devrede (10-16 Kasım 2026)

**Gerçek otonom operasyon verisi:** 04-15 Kasım arası **10 gece koşusu**
(Zamanlayıcı, LastTaskResult hep 0) + **ilk haftalık retro (W46)** + ilk
tatbikat koşumu. Toplam: 34 kabul / 8 blok, tüm defterler sağlam.

Bu haftanın üç düzeltmesi:
1. **Tatbikat logu kodlama hatası:** Windows redirection Türkçe karakterde
   UnicodeEncodeError üretiyordu; görev "başarılı" görünüyordu ama log
   yarım kalıyordu. `PYTHONIOENCODING=utf-8` + `Out-File -Encoding utf8`
   ile düzeltildi; elle koşumla doğrulandı (5/5 PASS, log okunur).
2. **Gece hattına kaynak rotasyonu:** her gece aynı 15 kaynak yerine,
   okunanlar geçmişe yazılır (kaynak-gecmisi.jsonl) ve okunmamışlar
   taranır; hepsi tükenirse açık "TEKRAR TARAMA" işaretiyle yeniden
   okunur. İlk turda rotasyon kodunun çözümlü-yol hatası sessizce 0 kaynak
   okunmasına yol açmıştı — panodan yakalandı, düzeltildi, testlendi.
3. **Completion-aware kuyruk:** `--tamamlanan` ile kabul edilen işler
   kayda geçer ve sonraki gece atlanır — kuyruk ilerler. Düzeltme:
   bloklanan işler de kayda yazılıyordu (tekrar eden ihlal trendi
   kaybolacaktı); yalnızca kabul edilenler kayda geçer, bloklananlar
   sonraki gece yeniden denenir (testle sabitlendi).

**ÖVD ilk gerçek veri:** tek aktif beceri (tests-kapisi-tekrar-dusmesi),
kullanım sayacı kullanim.jsonl'de. Sayı henüz tekil; 30 günlük pencere
sonunda ÖVD = kullanım / 30 ölçülebilir olacak.

---

## 15. Gece koşularının print çökmesi — kök neden ve kapanış (16 Kasım 2026)

**Belirti:** 10 gece defteri sağlam, ozet ve raporlar yazılmış; ama her gece
logunda `UnicodeEncodeError: 'charmap' codec can't encode 'ş'` ve
`state/tamamlanan.jsonl` hiç oluşmamış (kuyruk ilerlemiyor).

**Kök neden:** Python, stdout bir PIPE'a bağlıyken yerel kodlamayı (cp1252)
kullanır; Türkçe karakterli `print` süreci son satırda öldürür. Tüm
artefaktlar print'ten ÖNCE yazıldığı için koşu "başarılı" görünüyordu —
ama çıkış kodu bozuluyor ve sonraki adım/log yarım kalıyordu. Ayrıca
`--tamamlanan` eski gece-kos sürümünde hiç geçilmiyordu; bu yüzden kayıt
dosyası yoktu.

**Düzeltme:**
1. `konsol.py` + 11 CLI girişinde `konsol.hazirla()`: stdout/stderr
   `encoding="utf-8", errors="replace"`. Çıktı kaybolmaz, süreç ölmez.
2. `gece-kos.ps1` / `hafta-kos.ps1`: `PYTHONIOENCODING=utf-8` +
   `Out-File -Encoding utf8` (Türkçe log artık okunur).
3. `--tamamlanan` yolu önce değişkene alınıp açıkça geçirildi.
4. `pyproject.toml` py-modules'a `konsol` eklendi (kurulumda eksik kalmasın).

**Kanıt (uçtan uca, Zamanlayıcı'nın kullandığı girişle):** `gece-kos.ps1`
elle koşuldu → `runs/gece-20261116-0941`: 5 kabul / 8, 4 kabul + 1 blok,
defter OK; `state/tamamlanan.jsonl` oluştu (236 bayt, yalnız kabul
edilenler); log **temiz** (Traceback yok, Türkçe okunur). Bu gece 23:00'ten
itibaren kuyruk ilerleyecek.

**Ders:** "Artefaktlar var" ≠ "koşu başarılı". Exit code ve log bütünlüğü
panoya girmeli — bu düzeltmeyle gece raporu bunu da kontrol eder hale geldi.\n
---

## 16. Kuyruk ilerlemesi kanıtı + log bütünlüğü ağı + publish hazırlığı (16 Kasım 2026)

**Kuyruk ilerlemesi (§15'in vaadi, artık gerçek):** `gece-kos.ps1` elle
koşuldu → `state/tamamlanan.jsonl` 5→6 kayda büyüdü (K-106 kabul edilip
kayda geçti); blok/ertelenenler yine kayda girmedi (m.4 kuralı korunuyor).
Sistem artık aynı geceyi iki kez yaşamıyor: tamamlanan işler tekrar
seçilmiyor.

**Gece durum defteri (yeni güvenlik ağı):** `gece-kos.ps1` artık her iki
koşumun **çıkış kodunu** ve loglarının **çöküm imzası** içerip içermediğini
kontrol edip `state/gece-durum.log`'a yazıyor. İlk kayıt:
`20261116-1353 | kovan-cikis: 0 temiz: EVET | vardiya-cikis: 0 temiz: EVET`.

**Retro mekanik checki — `python retro.py --log-saglik`:** runs\*.log'u
tarar; Traceback/UnicodeEncodeError içerenleri raporlar, bozuk varsa çıkış
1. Kritik bulgu: eski PowerShell logları **UTF-16 (BOM'lu)** yazılmıştı —
UTF-8 okuma "Traceback"i göremiyordu (NUL'lar karakter aralarına giriyor).
BOM algılama eklendi ve test edildi (UTF-16 testi dahil, retro 6→11 test).
Canlı tarama 9 bozuk log yakaladı; bunlar kanıt olarak `runs/arsiv/`e
taşındı (tarama kapsamı dışı, diskte duruyor).

**Publish hazırlığı:**
1. `pip install -e fabrika --no-build-isolation` → kovan-fabrika 0.2.1
   kuruldu (editable, loop/); `kovan --help` ve `vardiya --help` çıkış 0.
   Not: CLI dosyaları (backlog vb.) cwd'e göre çözülür — entry point'in
   boş dizinde `plan` vermesi beklenen davranış.
2. CI: test listesine `test_kuyruk_uret.py` + `test_konsol.py` eklendi
   (19 dosya); "Log bütünlüğü taraması" adımı girildi (`--log-saglik`).
3. `.gitignore`: `fabrika/loop/state/` ve `fabrika/loop/reports/` eklendi
   (çalışma zamanı durumu repoya girmez; defter/kanıt yerelde kalır).
4. Sürüm 0.2.0 → 0.2.1.

**Ders:** İzleme zinciri tamamlanmalı — artefakt (ozet/rapor) yazılsa bile
çıkış kodu + log bütünlüğü + kuyruk ilerlemesi ayrı sinyallerdir; artık
üçü de kayda geçiyor (gece-durum.log → retro --log-saglik → tamamlanan.jsonl).
\n\n
---

## 17. Sektörel norm kapanışı (16 Kasım 2026)

Norm denetimi beş boşluk buldu; hepsi bu turda kapatıldı:

1. **Norm dosyaları** (hepsi fabrika/ altında, Türkçe): CHANGELOG.md
   (Keep a Changelog + SemVer; 0.1.0→0.2.1), SECURITY.md (açıklık
   bildirimi + BYOK/egress tasarım kararları), CONTRIBUTING.md
   (tur normu, kapı sırası dokunulmazlığı, m.2 PR kuralı),
   CODE_OF_CONDUCT.md (Contributor Covenant 2.1 modeli). Depo kökünde
   `.github/PULL_REQUEST_TEMPLATE.md` + `ISSUE_TEMPLATE/` (bug + feature,
   norm checklist'li). LICENSE Apache-2.0 paket dizinine kopyalandı.
2. **pyproject PEP 639:** `license = "Apache-2.0"` (SPDX expression) +
   `license-files = ["LICENSE"]`; classifiers 9; `pyyaml>=6,<7` aralık
   kilidi; build-system setuptools>=77. **Öğrenilen:** license
   expression kullanılınca License classifier setuptools 77+ tarafından
   *hata* olarak reddediliyor — classifier kaldırıldı. Kanıt:
   `pip install -e fabrika` çıkış 0; metadata: License-Expression
   Apache-2.0, Requires-Dist pyyaml<7,>=6.
3. **SBOM NTIA güçlendirme:** kök paket (hedef proje adı/sürümü
   pyproject'ten, yoksa NOASSERTION), her pakete `supplier`, DOC→kök
   DESCRIBES + kök→paket DEPENDS_ON ilişkileri. sbom 6→8 test.
4. **Sürümleme:** 0.2.1 changelog'a işlendi; SemVer normu yazılı.

**Sonuç:** Norm denetim tablosundaki beş boşluk kapatıldı; 162/162 test.
Kalan tek tek satırlık iş: `project.urls` — gerçek GitHub repo adresi
yaratılınca eklenir (uydurma URL yazılmadı).
\n\n
---

## 18. Proje kimliği kararı — ADR-F13 (17 Kasım 2026)

İsim araştırması yapıldı ve karar ADR-F13 olarak kayda geçti: marka
**KOVAN**, repo/PyPI **`kovan-fabrika`**, CLI `kovan`. Kanıt: bare
"kovan" GitHub'da alınmış (vertexclique/kovan; boratanrikulu/kovan —
kavramsal çakışma) ve Kovan testnet aramaları gömüyor; "fabric" AI
alanında kirli (danielmiessler/Fabric vb.); "kovan-fabrika" tam-string
araması boş. pyproject zaten uyumlu; tek bekleyen `project.urls`
(gitHub repo adresi yaratılınca). Karar workspace hafızasına da yazıldı.
\n