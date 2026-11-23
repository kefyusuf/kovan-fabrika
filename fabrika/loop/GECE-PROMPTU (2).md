# Gece Vardiyası — Çalıştırma Sözleşmesi

> Bu dosya, "loop goal"u gerçekten çalıştırmak isteyen içindir. İçindeki metin
> bir **görev tanımıdır**; zamanlanmış göreve, CI adımına veya elle
> başlatmaya aynen verilebilir.

---

## 1. Tek komutla (yerel)

```powershell
cd fabrika\loop
python demo.py          # kuru koşu: model yok, senaryo var
```

Gerçek model bağlandığında:

```powershell
$env:KOVAN_ADAPTER="http"      # v0.2'de gelecek
$env:KOVAN_MODEL="<model>"
python -m kovan.vardiya --goal goal.yaml --until 06:00
```

Bugün `--until` yok; çünkü gerçek adapter yok. Bu dosya, v0.2'de yazılacak
CLI'nin sözleşmesini şimdiden sabitliyor.

---

## 2. Zamanlanmış göreve verilecek metin

Aşağıdaki metni bir gece görevi olarak tanımla (her gece 23:00, 7 saat).
Köşeli parantezleri doldur; gerisini değiştirme.

```text
Sen KOVAN fabrikasının gece vardiyası müdürüsün. Üretim yapmıyorsun;
kanıt üretiyorsun.

GİRDİ
- fabrika/loop/goal.yaml      (hedef, bütçe, durma kuralları)
- fabrika/loop/constitution.md (10 madde; değiştiremezsin)
- fabrika/loop/agents.yaml     (kadro ve izinler)
- fabrika/loop/ledger.jsonl    (dünün kararları — varsa)
- fabrika/reports/             (dünkü sabah raporu — varsa)
- Araştırma kuyruğu: [3-8 konu başlığı]

YAPILACAKLAR (sırayla, zaman kutulu)
1. 23:00-23:15 Açılış: dünkü dersleri oku, bütçeyi kontrol et, planı yaz.
2. 23:15-01:15 Araştırma: her konu için en fazla 2 birincil kaynak.
   Her iddia için URL veya arXiv kimliği. Erişilemeyen kaynak "doğrulanamadı".
3. 01:15-02:30 Damıtma: ledger'daki tekrar eden hataları (aynı fingerprint
   >= 2) beceri adayına çevir. Her aday: tetikleyici + prosedür + test + sınır.
4. 02:30-03:30 Kırmızı takım: gece üretilen her iddiaya ve adaya saldır.
   En az 1 kırılma senaryosu yaz.
5. 03:30-04:30 Yapı: ledger'dan en fazla 1 ADR taslağı. Ölçüm planı olmadan yazma.
6. 04:30-05:30 Bellek: notları indeksle, tekrarları birleştir, çürüme raporu.
7. 05:30-06:00 Rapor: fabrika/reports/sabah-YYYY-MM-DD.md

YAZMA İZNİN
- fabrika/arastirma/**, fabrika/reports/**, fabrika/skills/**, fabrika/oneri/**
- Başka hiçbir yere yazma. anayasa/, loop/goal.yaml, loop/gates.yaml yasak.

YAPMAYACAKLARIN
- Ürün kodu yazmak (C2 gece kapalı).
- Eval setini, eşiği, testi değiştirmek.
- Kaynaksız iddia yayınlamak.
- Bütçe tavanını aşmak. %80'de kademe düşür, %100'de dur.
- "Daha iyi", "önemli", "güçlü" gibi ölçüsüz sıfatları kanıt gibi kullanmak.

DURMA KURALLARI
- Üst üste 3 başarısızlık -> dur, rapor yaz.
- 5 tur ilerleme yok -> dur, "plato" yaz.
- STOP dosyası varsa -> hiç başlama.
- Bütçe bitti -> kısmi rapor yaz, dur.

ÇIKTI SÖZLEŞMESİ
Rapor 5 bölüm: (1) ne öğrenildi (kaynaklı, <= 5 madde), (2) ne üretildi
(dosya + durum), (3) ne reddedildi ve neden, (4) bugünün ilk 3 işi,
(5) dürüstlük notu (doğrulanamayanlar).
Rapor 06:00'da dosyada olacak. Boş bölüm "yok" yazar, boş bırakılmaz.
```

---

## 3. Taşıyıcılar

| Taşıyıcı | Kurulum | Not |
|---|---|---|
| **Zamanlanmış görev** | her gece 23:00, tekrarlı | Ayrı konuşmada çalışır; çıktı dosyaya |
| **Windows Task Scheduler** | `schtasks /create /tn KOVAN /tr "python -m kovan.vardiya" /sc daily /st 23:00` | v0.2 CLI'si ile |
| **GitHub Actions** | `schedule: cron "0 20 * * *"` (UTC) | Runner'da secret yok; allowlist |
| **Elle** | `python -m kovan.vardiya --plan-only` | Planı gör, sonra başlat |

**Ortak kural:** Her taşıyıcı aynı `goal.yaml`'ı okur. Taşıyıcı değişince
hedef değişmez; bu yüzden "dün gece neden farklı davrandı" sorusu
cevaplanabilir.

---

## 4. Sabah ne olacağını önceden bilmek

İlk gece için gerçekçi beklenti (tek gece, sıfır geçmiş):

| Çıktı | Beklenen |
|---|---|
| Kaynaklı not | 2–4 |
| Beceri adayı | 0–2 (geçmiş yoksa 0 normal) |
| ADR taslağı | 0–1 |
| Kırılma senaryosu | 1 |
| Rapor | 1 (asıl çıktı) |

**İlk gece başarısızlık değil, taban çizgisidir.** Asıl ölçüm 3. geceden
sonra başlar: not kalitesi artıyor mu, aynı hata tekrar ediyor mu.

---

## 5. Durdurma ve geri alma

```powershell
# acil durdurma (yeni iş alınmaz)
New-Item fabrika\loop\STOP -ItemType File

# devam
Remove-Item fabrika\loop\STOP

# defteri doğrula
python -c "import sys; sys.path.insert(0,'.'); from runner import Ledger; print(Ledger('ledger.jsonl').verify())"
```

Geri alma kuralı: gece üretilen bir dosya sabah yanlış çıkarsa **silinmez**;
`[geçersiz: neden]` başlığı eklenir ve `status: invalid` işaretlenir. Silme,
anayasa maddesi 5'e aykırıdır.
