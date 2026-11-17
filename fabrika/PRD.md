# KOVAN — Ürün Gereksinim Belgesi (PRD)

| Alan | Değer |
|---|---|
| Sürüm | 1.0 (konsept) |
| Tarih | 21 Ekim 2026 |
| Sahip | kurucu |
| Durum | **v2 yönlendirmesi geçerli** — sistem tanımı: [`SYSTEM.md`](SYSTEM.md) |
| İlgili | [`README.md`](README.md) · [`MIMARI.md`](MIMARI.md) · [`ADR.md`](ADR.md) · [`loop/goal.yaml`](loop/goal.yaml) |

---

## 1. Özet

KOVAN, bir yazılım ekibinin biriktirdiği işi (backlog) **gece boyunca işleyip**
sabaha (a) birleşmeye hazır PR'lar, (b) kaynaklı bir öğrenme raporu ve
(c) kendi yapısına dair ölçülmüş öneriler bırakan bir üretim hattıdır.

Ürün bir model değildir. Ürün üç şeydir:

1. **Kapı seti** — neyin kabul edileceğine karar veren, değişmez, ölçülebilir kurallar.
2. **Hafıza** — kendi hatalarından damıttığı beceri kütüphanesi ve değerlendirme seti.
3. **Rapor** — insanın 5 dakikada okuyup karar verebildiği tek sayfalık durum.

Satış cümlesi (henüz doğrulanmadı, bkz. §11):

> "Modelinizi değiştirmiyoruz. Backlog'unuzu, sabah okunabilir bir rapora
> ve birleşmeye hazır PR'lara çeviriyoruz — üstelik her karar denetlenebilir."

---

## 2. Problem

**P1 — Üretim arttı, kabul artmadı.**
Ajanlar kod üretimini hızlandırdı; ama darboğaz üretimden incelemeye kaydı.
Yüksek AI benimsemesinde PR sayısı ~%98 artarken inceleme süresi ~%91,
PR boyutu ~%154 artıyor (ikincil analiz; bkz. `arastirma/05-fabrikalar.md` [K30]). Sonuç:
"daha çok kod" değil, "daha çok okunmamış kod".

**P2 — Öğrenme birikmiyor.**
Her oturum sıfırdan başlıyor. Ajan aynı hatayı üçüncü kez yapıyor; hata
kaydedilmiyor, damıtılmıyor, tekrar kullanılabilir hale gelmiyor. Kurumun
bildiği şey, ajanın bildiği şey değil.

**P3 — Denetim kaybı.**
Otonomi arttıkça insan kapısı aşağı kayıyor: plandan koda, koddan "ajan
incelemesine". Bu, en az ölçülmüş alan. Kimin neyi neden onayladığı
çoğu sistemde kayıtlı değil.

**P4 — Ölçüm enflasyonu.**
Aynı model, farklı harness'ta 10+ puan farklı görünüyor. Ekipler benchmark
sayısına bakarak araç seçiyor; kendi işlerinde ne olduğunu ölçmüyor.

---

## 3. Vizyon ve konumlandırma

**Vizyon:** Bir yazılım ekibinin "ikinci vardiyası" olmak — ama sabah
hesap verebilen bir vardiya.

| KOVAN şudur | KOVAN şu değildir |
|---|---|
| Repo-native üretim hattı (dosya + git + CLI) | Barındırılan çok kiracılı SaaS |
| Kapı ve hafıza ürünü | Model veya IDE ürünü |
| İnsan kapısını **azaltan** değil, **anlamlı kılan** sistem | "İnsanı kaldıran" otonomi iddiası |
| Tek repo, tek hat ile başlayan | İlk günden filo yönetimi |
| Ölçülebilir iddia | Benchmark liderlik tablosu iddiası |

---

## 4. Kullanıcılar

| Persona | Durum | Acı | KOVAN'dan beklediği |
|---|---|---|---|
| **Yalnız teknik kurucu** | 1 kişi, 3 ürün, sınırsız backlog | Gece çalışamıyor; sabah ne yapacağını hatırlamıyor | Sabah 1 sayfa: ne oldu, ne bekliyor |
| **Küçük ürün ekibi** | 3–8 kişi, tek repo | İnceleme kuyruğu; ajan çıktısı güvenilmez | Kapılardan geçmiş, küçük PR'lar |
| **Platform ekibi** | 20+ kişi, çok repo | Standart yok; herkes kendi prompt'uyla | Politika + denetim + ölçüm |

Birincil persona: **yalnız teknik kurucu**. Sebep: karar verici ile kullanıcı
aynı kişi; geri bildirim döngüsü en kısa; C3 onayı tek imza.

---

## 5. Hedefler ve hedef-dışı

### Hedefler (12 hafta)

| # | Hedef | Ölçüt |
|---|---|---|
| O1 | Gece vardiyası güvenilir çalışsın | 10 gecenin ≥8'inde sabah raporu 06:00'da hazır |
| O2 | Kapılar iş görsün | C2 görevlerde ilk turda kapı geçme oranı ≥ %50 (hafta 8), ≥ %65 (hafta 12) |
| O3 | Öğrenme biriksin | Üretilen beceri adaylarının ≥ %30'u sonraki 2 hafta içinde en az 1 kez kullanılsın |
| O4 | Denetim kanıtlansın | Her karar hash zinciriyle doğrulanabilir; tahrif testi geçsin |
| O5 | Maliyet öngörülebilir olsun | Birleşen PR başına maliyet ≤ 6 USD (12 haftalık ortalama) |

### Hedef-dışı (bilinçli olarak yapılmayacak)

| # | Yapılmayacak | Neden |
|---|---|---|
| X1 | Model eğitimi / fine-tune | Ayrı bütçe, ayrı uzmanlık; önce kapı problemi çözülmeli |
| X2 | Çok kiracılı barındırma | Güvenlik yüzeyi 10 katına çıkar; tek kullanıcıda doğrulanmadan olmaz |
| X3 | IDE / editör | Var olan harness'lar yeterli; rekabet değil entegrasyon |
| X4 | "İnsansız yazılım" iddiası | Ölçümler aksini söylüyor; iddia güven kaybettirir |
| X5 | Kendi kendini yayınlama (otomatik deploy) | C3 sınıfı; insan kapısı zorunlu |

---

## 6. Kullanıcı hikâyeleri

**US-01 — Sabah raporu.** Yalnız kurucu olarak sabah kahve alırken tek sayfada
şunu görmek istiyorum: gece ne öğrenildi (kaynaklı), ne üretildi, ne reddedildi
ve bugün ilk üç iş ne. *Kabul:* rapor 5 dakikada okunur; her iddia bir dosya
veya URL'ye bağlıdır; "doğrulanamadı" bölümü boş bırakılamaz (boşsa "yok" yazar).

**US-02 — Güvenli PR.** Küçük ekip üyesi olarak, sabah gelen PR'ın testlerden
geçtiğini, inceleyicinin gerekçe yazdığını ve yasak dosyalara dokunmadığını
görmek istiyorum. *Kabul:* PR açıklaması kapı sonuçlarını tablo olarak içerir;
inceleme gerekçesi tek cümlelik "LGTM" olamaz.

**US-03 — Tekrarlayan hatanın durması.** Kurucu olarak, aynı hatanın üçüncü
kez olmasını istemiyorum. *Kabul:* aynı kapı + aynı neden 2 kez görülürse
`skills.proposed.jsonl`'a aday düşer; aday bir sonraki vardiyada test edilir.

**US-04 — Durdurma.** Kurucu olarak, gece 02:00'de bir şeyin ters gittiğini
görünce tek komutla durdurmak istiyorum. *Kabul:* `STOP` dosyası konduğunda
yeni iş alınmaz; 60 saniye içinde rapor yazılır; yarım kalan iş "yarım" olarak
işaretlenir.

**US-05 — Ölçüm dürüstlüğü.** Platform ekibi olarak, "eval %95" cümlesinin
hangi sette, kaç örnekle, hangi tarihte ölçüldüğünü görmek istiyorum.
*Kabul:* her metrik kaydı `{set, n, tarih, harness, model}` taşır.

**US-06 — Yapı önerisi.** Kurucu olarak, sistemin kendi kadrosunu değiştirme
önerisini gerekçeli ve ölçülmüş görmek istiyorum. *Kabul:* öneri bir ADR
taslağıdır; "hangi metrik, ne kadar, nasıl ölçülecek" içerir; onaylanmadan
uygulanmaz.

---

## 7. Fonksiyonel gereksinimler

Öncelik: **M**ust / **S**hould / **C**ould. Her gereksinim tek bir halkaya aittir.

### Halka 1 — Görev döngüsü (dakikalar)

| # | Gereksinim | Öncelik | Kabul kriteri |
|---|---|---|---|
| FR-01 | Hedef sözleşmesi okunur ve doğrulanır | M | `goal.yaml` yoksa veya `goal.id` boşsa döngü başlamaz |
| FR-02 | Issue → spec + çalıştırılabilir kabul kriteri | M | Her kriter bir komut içerir; komutsuz kriter reddedilir |
| FR-03 | Test-önce: kod yazılmadan kırmızı test | M | Testin önce başarısız olduğu kaydı yoksa kod kapıya girmez |
| FR-04 | Sınırlı kapsamlı patch üretimi | M | Patch yalnızca spec'te listelenen dosyalara dokunur |
| FR-05 | Bağımsız inceleme | M | İnceleyici farklı bağlamda çalışır; gerekçe zorunlu |
| FR-06 | Sıralı kapı zinciri + fail-fast | M | İlk bloklayıcı hatada sonraki kapı çalışmaz |
| FR-07 | Değişiklik sınıfı ve insan kapısı | M | C3 hiçbir koşulda otomatik geçmez |
| FR-08 | İzolasyon: worktree + konteyner | M | Ajan ana çalışma ağacına yazamaz; ağ allowlist'e tabidir |

### Halka 2 — Vardiya döngüsü (7 saat)

| # | Gereksinim | Öncelik | Kabul kriteri |
|---|---|---|---|
| FR-09 | Gece ajandası ve zaman kutusu | M | Her blok için ayrılmış süre ve çıktı tanımlı |
| FR-10 | Kaynaklı araştırma | M | Her iddia URL/arXiv kimliği taşır; erişilemeyen "doğrulanamadı" |
| FR-11 | Beceri damıtma | M | Beceri adayı: tetikleyici, prosedür, doğrulama, test |
| FR-12 | Sabah raporu | M | 5 bölüm dolu; 06:00'da dosyada; tek sayfa |
| FR-13 | Ders kaydı ve tekrar tespiti | S | Aynı parmak izi 2. kez görülünce aday açılır |

### Halka 3 — Sürüm döngüsü (günler)

| # | Gereksinim | Öncelik | Kabul kriteri |
|---|---|---|---|
| FR-14 | Kanarya + otomatik geri alma | M | Eval eşiğin altına düşerse sürüm geri alınır |
| FR-15 | Model/bütçe yönlendirmesi | S | %80 bütçede kademe düşer; %100'de durur |
| FR-16 | Beceri aktivasyonu | S | Beceri, uygulandığı görev sınıfında ölçülmeden "aktif" olmaz |

### Halka 4 — Yapı döngüsü (haftalar)

| # | Gereksinim | Öncelik | Kabul kriteri |
|---|---|---|---|
| FR-17 | Yapı önerisi (ADR taslağı) | S | Öneri: bağlam, karar, beklenen etki, ölçüm planı |
| FR-18 | Denetim defteri | M | Append-only; hash zinciri; `verify` tahrifi gösterir |
| FR-19 | Bellek bakımı | C | Çürüme raporu: kullanılmayan beceri/not listesi; silme yok |

---

## 8. Fonksiyonel olmayan gereksinimler

| # | Gereksinim | Eşik / kabul |
|---|---|---|
| NFR-01 | Maliyet | PR başına ≤ 6 USD; vardiya ≤ 40 USD; aşımda durur |
| NFR-02 | Dayanıklılık | Kesintiden sonra `resume` ile devam; tamamlanan iş tekrar edilmez |
| NFR-03 | İzolasyon | Ajan başına ayrı worktree + konteyner; secret yok |
| NFR-04 | Denetlenebilirlik | Her karar: ne, neden, hangi kapı, hangi kanıt |
| NFR-05 | Taşınabilirlik | Skill/kadro tanımı harness'tan bağımsız (SKILL.md + YAML) |
| NFR-06 | Gözlemlenebilirlik | Her tur için span: görev, kapı, model, token, süre |
| NFR-07 | Gizlilik | Kod ve secret dışarı çıkmaz; yalnızca allowlist ağ |
| NFR-08 | Dil | Rapor Türkçe; kod/commit mesajları İngilizce; terimler sözlükte |

---

## 9. Metrikler

Tanımlar [`KALITE.md`](KALITE.md) §4'te. Burada yalnızca hedef tablosu var.
**Hiçbiri henüz ölçülmedi**; "başlangıç" kolonu bu yüzden boş.

| Kısaltma | Metrik | 12 hafta hedefi | Ölçüm |
|---|---|---|---|
| **BMP** | Birleşen PR / vardiya | ≥ 1.5 | git log + merge kaydı |
| **GPK** | İlk turda kapı geçme oranı | ≥ %65 | ledger |
| **DSP** | İnsan düzeltme satırı / PR | ≤ 25 satır | merge sonrası diff |
| **MBB** | Maliyet / birleşen PR | ≤ 6 USD | model faturası + ledger |
| **ÖVD** | Kabul edilen beceri / önerilen | ≥ %30 | skills + kullanım kaydı |
| **TKH** | Tekrarlayan hata oranı | ≤ %15 | lessons fingerprint |
| **KKA** | Kaçan regresyon / 100 PR | ≤ 1 | sonraki 2 hafta içi hata |
| **GHS** | Gece hazır rapor oranı | ≥ %80 | reports/ dosya sayımı |

**Anti-metrik:** "yazılan satır sayısı". Ölçülmeyecek; çünkü satır sayısı
kaliteyle ters korelasyon gösterebilir ve en kolay manipüle edilen sayıdır.

---

## 10. Sürüm kapsamı

| Sürüm | Kapsam | Çıkış kriteri |
|---|---|---|
| **v0.1** (mevcut) | Kuru koşu: sözleşmeler, koşucu, kapılar, defter, demo | 22 test + örnek rapor |
| **v0.2** | Gerçek adapter (tek model), gerçek eval seti (≥ 50 vaka), maliyet ölçümü | 20 görevde uçtan uca; GPK ölçülmüş |
| **v0.3** | Gece vardiyası: araştırma + damıtma + sabah raporu | 5 gece üst üste rapor |
| **v1.0** | Kanarya, geri alma, C3 onay akışı, çoklu hat (3 işçi) | 2 hafta kesintisiz; KKA ölçülmüş |

---

## 11. Açık sorular ve bağımlılıklar

1. **İsim/marka:** "KOVAN" çalışma adı; tarama yapılmadı. (Airlock'ta da açık.)
2. **İlk müşteri:** iç fabrika mı, dış hizmet mi? Fiyat modeli buna bağlı.
3. **Model sağlayıcı:** tek sağlayıcı mı, yönlendirme mi? C3 kararı.
4. **Eval seti nereden:** kendi geçmiş PR'ları mı, sentetik mi? Dış veri gizlilik riski.
5. **Türkçe/İngilizce:** ürün dili İngilizce, doküman dili Türkçe mi? Şimdilik öyle.
6. **Bağımlılık:** Airlock'un araç-düzeyi politikası olgunlaşmadan fabrika
   güvenlik iddiasını tam kuramaz (bkz. `../STATUS.md`).

---

## 12. Ek: kabul testi matrisi (v0.2 için)

| Senaryo | Girdi | Beklenen |
|---|---|---|
| Mutlu yol | 1 C1 görev | Kapılar geçer, PR açılır, defter 1 kayıt |
| Test zayıflatma | Aday testi siler | `tests` kapısı reddeder; ders yazılır |
| Sır okuma | Diff `.secrets/` içerir | `policy` bloklar; insan kapısı; revizyon yok |
| C3 | Anayasa değişikliği | Anında `blocked`; tek denemede durur |
| Bütçe | Tavanın %99'u | Yeni görev alınmaz; rapor yazılır |
| Kesinti | Vardiya ortasında süreç ölür | `resume`; tamamlanan tekrar edilmez |
| Tahrif | Defter satırı değiştirilir | `verify` ilk kırılma noktasını verir |
