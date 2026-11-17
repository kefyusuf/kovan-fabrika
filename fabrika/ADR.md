# KOVAN — Mimari Karar Kayıtları (ADR)

> Her ADR tek bir kararı savunur: **bağlam → karar → sonuç → reddedilen
> alternatifler**. Kararlar geri alınabilir; ama geri alma da bir ADR ister.
> Sıra numarası `F` önekli çünkü bu, ayrı bir ürün hattı (Airlock ADR'leri
> 0001–0010 ile karışmamalı).

| # | Karar | Durum |
|---|---|---|
| [F01](#adr-f01) | Ürünün çıktısı kanıtlı değişikliktir | Kabul |
| [F02](#adr-f02) | Önce iskelet, sonra model | Kabul |
| [F03](#adr-f03) | Değişmez çekirdek / değişken kabuk | Kabul |
| [F04](#adr-f04) | Öğrenme birimi beceridir, kod değil | Kabul |
| [F05](#adr-f05) | Spec = çalıştırılabilir kabul kriteri | Kabul |
| [F06](#adr-f06) | Doğrulama hiyerarşisi: D1 > D2 > D3 | Kabul |
| [F07](#adr-f07) | Araç politikası Airlock'tan geçer | Kabul |
| [F08](#adr-f08) | Değişiklik sınıfları C0–C3 | Kabul |
| [F09](#adr-f09) | Model kademelendirme + bütçe tavanı | Kabul |
| [F10](#adr-f10) | Dosya + git + SQLite; workflow motoru yok | Kabul |
| [F11](#adr-f11) | Bellek append-only, silme yok | Kabul |
| [F12](#adr-f12) | Framework değil, desen ödünç alınır | Kabul |

---

## ADR-F01
### Ürünün çıktısı kanıtlı değişikliktir

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Piyasadaki ürünler "kod üretimi" ile ölçülüyor: satır, PR sayısı,
benchmark skoru. Ama üretilen kodun kabul edilmesi ayrı bir iş; ve ölçümler
PR sayısı artarken inceleme yükünün de arttığını gösteriyor ([C], bkz.
`arastirma/05-fabrikalar.md` [K30]).

**Karar.** KOVAN'ın çıktısı "kod" değil, **kanıtlı değişikliktir**: bir PR +
onu doğrulayan test + kapı sonuçları + defter kaydı. Bir PR, kanıtı olmadan
"iş" sayılmaz; bir gün "üretken" sayılmaz.

**Sonuçlar.**
- (+) Başarı metriği üretimle değil kabulle hizalanır.
- (+) Denetim, üretimin yan ürünü olur; sonradan eklenmez.
- (−) İlk haftalarda "yavaş" görünür: kanıt üretmek kod yazmaktan pahalı.
- (−) Kanıt kalitesi düşerse ürün değersizleşir; bu yüzden KALITE.md ayrı belge.

**Reddedilen.** "Yazılan satır sayısı" ve "PR sayısı" metrikleri — ikisi de
kolay manipüle edilir ve kaliteyle ters korelasyon gösterebilir.

---

## ADR-F02
### Önce iskelet, sonra model

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Ajan sistemleri genellikle modelle başlar: prompt yazılır, model
bağlanır, davranış gözlemlenir. Sonuç: hata modelde mi, akışta mı, kapıda mı
bilinmez. Ve her model değişiminde tüm sistem yeniden test edilir.

**Karar.** Döngü önce **deterministik bir durum makinesi** olarak yazılır
(`runner.py`): kapı sırası, bütçe, devre kesici, defter. Model, `Adapter`
arayüzünün arkasına en son takılır. Testler `ScriptedAdapter` ile modelsiz koşar.

**Sonuçlar.**
- (+) 22 test, model olmadan geçiyor; regresyonlar modelden bağımsız yakalanır.
- (+) Model değişimi tek dosyada olur; akış değişmez.
- (−) Başlangıçta "yapay" görünür: senaryo sinyalleri gerçek değil.
- (−) Adapter tasarımı yanlışsa, gerçek modelde sürpriz olur (v0.2 riski).

**Reddedilen.** "Önce prompt'u dene, mimariyi sonra çıkar" yaklaşımı — prototip
hızı kazandırır, ama ölçüm ve regresyon imkânını kaybettirir.

---

## ADR-F03
### Değişmez çekirdek / değişken kabuk

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** "Kendi kendini geliştiren sistem" tanımı, sistemin neyi
değiştirebileceği tanımlanmadan anlamsızdır. Her şeyi değiştirebilen bir
sistem, hiçbir şeyi güvenilir biçimde değiştiremez.

**Karar.** İki katman:
- **Çekirdek (değişmez):** anayasa, kapı sırası, eşikler, model seçimi,
  yasak yollar, bütçe tavanı. Yalnızca insan (C3).
- **Kabuk (değişken):** beceri, prompt, kod, test, kadro önerisi. Sistem
  önerir, kapılar kabul eder.

**Sonuçlar.**
- (+) "Kendini geliştirme" ölçülebilir bir alana hapsolur.
- (+) Denetim, çekirdeğin küçük olması sayesinde mümkün.
- (−) Bazı iyileştirmeler (ör. kapı sırası) yavaş ilerler: 14 gün bekleme.
- (−) Çekirdek yanlış tasarlanırsa, sistem yanlış yönde "güvenli" olur.

**Reddedilen.** Tam otonom kendini değiştirme (DGM tarzı, sınırsız) — literatürde
test hackleme vakaları belgeli; üretimde kabul edilemez.

---

## ADR-F04
### Öğrenme birimi beceridir, kod değil

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** "Kendini geliştirme" iki şekilde yapılabilir: (a) sistemin kendi
kodunu değiştirmesi, (b) sistemin prosedürlerini değiştirmesi. (a) güçlüdür
ama her değişiklik tüm sistemi etkiler ve geri alması zordur; ayrıca test
edilmesi, değişikliğin kendisi kadar karmaşıktır.

**Karar.** Öğrenmenin birimi **beceridir**: `skills/<ad>/SKILL.md` + testi +
kanıtı. Bir ders, en az 2 kez tekrarlamış bir hatadan doğar; testi yoksa
beceri sayılmaz. Kod değişikliği (C2) ayrı bir kanal; öğrenme kanalı değil.

**Sonuçlar.**
- (+) Geri alma kolay: dosyayı `status: archived` yap.
- (+) Beceri, farklı harness'larda taşınabilir (SKILL.md standardı).
- (−) Bazı iyileştirmeler prosedürle ifade edilemez (ör. performans).
- (−) Beceri sayısı şişebilir; çürüme mekanizması zorunlu.

**Reddedilen.** "Ajan kendi kodunu yazsın" (self-coding) birincil öğrenme yolu
olarak — ilgi çekici, ama denetimi ve geri almayı zorlaştırıyor.

---

## ADR-F05
### Spec = çalıştırılabilir kabul kriteri

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Spec-driven development akımı doğru bir sezgiye dayanıyor: kod
türev, spec kaynak. Ama pratikte spec dokümanı koda yetişemiyor; "spec drift"
denen, kimsenin okumadığı bir belge yığını oluşuyor.

**Karar.** Spec, **komut içeren** kabul kriterlerinden oluşur. Komutsuz kriter
reddedilir. Spec ile kod arasındaki fark, haftalık bir "drift denetimi" ile
ölçülür: spec'te olup kodda olmayan, kodda olup spec'te olmayan davranışlar.

**Sonuçlar.**
- (+) Spec, otomatik doğrulanabilir; "yorum" değil.
- (+) Drift ölçülebilir bir sayı olur.
- (−) Her kriteri komuta çevirmek yavaş; bazı nitel kriterler (UX) zorlanır.
- (−) Komut yazmak, test yazmakla neredeyse aynı iş; bazı ekipler bunu
  "çift iş" olarak görecek.

**Reddedilen.** Uzun prose spec + "plan mode" — okunmuyor, ölçülmüyor.
(Pocock'un plan mode'u bırakıp doküman + seam sözleşmesine geçmesi bu yönü
destekliyor [C].)

---

## ADR-F06
### Doğrulama hiyerarşisi: D1 > D2 > D3

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Ajan sistemlerinde "LLM-as-judge" yaygın; çünkü ucuz ve esnek.
Ama yargı, ölçüm değildir; kalibre edilmedikçe gürültü üretir. Ve tek başına
kapı olursa, sistem kendi kendini onaylar.

**Karar.** Üç katman: deterministik (D1) > istatistiksel (D2) > yargı (D3).
**Yetki** bu sıradır; **iş akışı** değildir: kapılar D1 → inceleme (D3) →
eval (D2) sırasıyla çalışır, çünkü eval yalnızca incelemeden geçmiş adayı
ölçmelidir. D3 tek başına kapı olamaz; D2 ile desteklenir. İnsan incelemesi de
D3'tür — bu yüzden rastgele örneklemle denetlenir.

**Sonuçlar.**
- (+) Ucuz ve kesin olan önce çalışır; pahalı yargı en sona kalır.
- (+) "Sinyal yok = geçti" varsayımı kapanır.
- (−) D1 ile ifade edilemeyen kalite (okunabilirlik, tasarım) ölçülemez kalır.
- (−) D2 için set bakımı sürekli iş; ihmal edilirse çürür.

**Reddedilen.** "Her şeyi LLM yargıçla değerlendir" — hızlı kurulur, ama
kalibrasyon ve tahrif direnci yok.

---

## ADR-F07
### Araç politikası Airlock'tan geçer

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Fabrikanın her ajanı dosya, shell ve ağ araçları kullanıyor.
Bu çağrıları her ajanın içinde ayrı ayrı denetlemek, N farklı politika ve
N farklı hata demek. Aynı projede çalışan bir araç-düzeyi politika motoru var
(Airlock): kural tabanı, karar hakemi, hash-zincirli defter.

**Karar.** Araç çağrıları Airlock'tan geçer; fabrika kendi politika motorunu
yazmaz. Fabrikanın `policy` kapısı, Airlock'un kararını **değişiklik düzeyinde**
tamamlar (dosya yolu, kapsam). İki defter ayrı: araç çağrısı defteri (Airlock)
ve karar defteri (KOVAN).

**Sonuçlar.**
- (+) Tek politika dili, tek denetim biçimi.
- (+) Fabrika, Airlock'un olgunlaşmasından doğrudan faydalanır.
- (−) Airlock'un bilinen boşlukları fabrikaya miras kalır (komut AST'si yok,
  proxy sıralı, platform kapsaması zayıf).
- (−) İki defterin korelasyonu ayrı bir iş (aynı `trace_id` şart).

**Reddedilen.** Fabrika içinde ikinci bir politika motoru — iki doğruluk
kaynağı, iki kaçış yolu.

---

## ADR-F08
### Değişiklik sınıfları C0–C3

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Her değişiklik aynı riski taşımıyor: bir yazım düzeltmesi ile
anayasa değişikliği aynı kapıdan geçemez. Ama sınıflandırma ajanın kendisine
bırakılırsa, ajan kendi işini "küçük" ilan eder.

**Karar.** Dört sınıf: C0 (yazım/biçim), C1 (beceri/prompt/doküman),
C2 (ürün kodu), C3 (anayasa/kapı/eşik/model/kadro). Sınıf spec'te atanır;
ajan sınıfı düşüremez. C3 hiçbir koşulda otomatik geçmez. Gece C2 kapalı.

**Sonuçlar.**
- (+) Risk ile süreç eşleşir; C0 hızlı, C3 yavaş.
- (+) Gece/gündüz ayrımı bu sınıflarla uygulanabilir.
- (−) Sınıf ataması tartışmalı olabilir (bir "küçük" refactor C2'dir).
- (−) Yanlış sınıf, ya gereksiz sürtünme ya da denetim boşluğu üretir.

**Reddedilen.** Tek sınıf ("her değişiklik aynı") — ya çok yavaş ya çok riskli.

---

## ADR-F09
### Model kademelendirme + bütçe tavanı

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** En yetenekli model her iş için gereksiz; en ucuz model her iş için
yetersiz. Ve sınırsız bütçe, öğrenmeyi değil harcamayı optimize eder.

**Karar.** Dört kademe: T0 (model yok), T1, T2, T3. Rol sözleşmesi kademeyi
belirler; bütçe %80'e gelince kademe düşer. Her vardiyanın token/USD tavanı
vardır; aşımda döngü durur, "biraz daha" yok.

**Sonuçlar.**
- (+) Maliyet öngörülebilir; fatura sürpriz olmaz.
- (+) Ucuz işler ucuz modelde kalır.
- (−) Kademe düşüşü kaliteyi düşürebilir; bu, eval ile izlenmeli.
- (−) Model fiyatları değişince tablo bayatlar; aylık güncelleme gerekir.

**Reddedilen.** "Tek güçlü model, her yerde" — basit, ama maliyet ve gecikme
açısından sürdürülemez.

---

## ADR-F10
### Dosya + git + SQLite; workflow motoru yok

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Dayanıklı iş akışı için Temporal, Airflow gibi motorlar var.
Ama ilk sürümde tek repo, tek kullanıcı ve düşük eşzamanlılık var. Motor
eklemek, çözülmemiş bir problemi (kapı kalitesi) altyapıyla gizlemek olur.

**Karar.** Durum dosyaları + git + SQLite indeks. Her tur yeniden başlatılabilir;
`state.json` ile `resume`. Eşzamanlılık en fazla 5 işçi, tek yazıcı kuralı.

**Sonuçlar.**
- (+) Anlaşılır, taşınabilir, hata ayıklaması kolay.
- (+) Git, denetim ve geri alma için hazır.
- (−) 10k+ görevde dosya tabanlı defter yavaşlar (O(n²) bilinen borç).
- (−) Çok makineli dağıtım yok; ölçekleme yeniden tasarım ister.

**Reddedilen.** Temporal/Kubernetes ile başlamak — erken optimizasyon; asıl
darboğaz orkestrasyon değil, kapı.

---

## ADR-F11
### Bellek append-only, silme yok

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Kendini geliştiren bir sistemin en tehlikeli hareketi, kendi
geçmişini yeniden yazması. O anda "öğrendi mi, öğrendiğini mi sandı"
sorusu cevaplanamaz hale gelir.

**Karar.** `ledger.jsonl`, `lessons.jsonl`, `skills.proposed.jsonl` yalnızca
eklenir. Yanlış kayıt silinmez; `supersedes` veya `[geçersiz]` notu eklenir.
Beceri `archived` olabilir; dosyası kalır. Hash zinciri bunu teknik olarak
zorlar.

**Sonuçlar.**
- (+) Denetim izi bütün; geriye dönük analiz mümkün.
- (+) Yanlış öğrenme, sonradan işaretlenebilir.
- (−) Depo büyür; indeks ve arşivleme gerekir.
- (−) Kişisel veri içeren kayıt silinemez → baştan maskelenmeli (v0.2 kuralı).

**Reddedilen.** "Yanlış kaydı sil, temiz tut" — denetimi bozar.

---

## ADR-F12
### Framework değil, desen ödünç alınır

**Durum:** Kabul · **Tarih:** 2026-10-21

**Bağlam.** Superpowers, GSD, Spec Kit, BMAD gibi olgun iskeletler var.
Bunları kurmak hızlı yol; ama hiçbiri fabrikanın üç ihtiyacını birlikte
karşılamıyor: (1) gece/gündüz ayrımı, (2) kendi kendini geliştirme sınıfları,
(3) kanıt defteri + bütçe muhasebesi.

**Karar.** Desenler alınır, motor yazılır. Özellikle alınanlar:

| Kaynak | Alınan desen | Neden |
|---|---|---|
| Superpowers | "test yoksa üretim kodu yok", taze doğrulama kanıtı, 5 tur breaker, SKILL.md | Kural sertliği, taşınabilirlik |
| Superpowers | Skill = prosedür, subagent = bağlam izolasyonu, hook = yaptırım | Üç ayrı mekanizma, üç ayrı iş |
| GSD | Faz/faz geçişleri, `STATE.md`/`ROADMAP.md` durum dosyaları, goal-backward doğrulama | Uzun görevlerde bağlam yönetimi |
| Spec Kit / Kiro | spec → plan → tasks ayrımı | Spec'in türevlenebilir olması |
| Pocock | Spec = karar kaydı + seam sözleşmesi; deterministik doğrulama (tsc/vitest) | "Plan mode" yerine ölçülebilir artefakt |
| Karpathy | Doğrulanabilirlik ekseni, autonomy slider, tek metrikli deney döngüsü | Görev sınıflandırması ve ölçüm |

**Alınmayanlar:** ağır çok-ajan seminerleri (MetaGPT/ChatDev tarzı rol
tiyatrosu), "plan mode" (ölçülemez), sınırsız otonomi, framework'e kilitlenme.

**Sonuçlar.**
- (+) Motor küçük (300 satır) ve kendi ihtiyacına göre.
- (+) Desenler test edilmiş; tekerleği yeniden icat etmiyoruz.
- (−) Framework'lerin hazır entegrasyonlarından (IDE, CI) yararlanamıyoruz.
- (−) Desenlerin bakımı bize ait; upstream düzeltmeleri gelmiyor.

**Reddedilen.** Superpowers/GSD'yi doğrudan kurmak — 3 ihtiyaçtan 2'si
karşılanmıyor ve kendi kendini geliştirme sınıfları dışarıda kalıyor.

---

## ADR-F13
### Proje kimliği: KOVAN markası + kovan-fabrika ad alanı

**Durum:** Kabul · **Tarih:** 2026-11-17

**Bağlam.** Public yayın öncesi repo/PyPI adı seçilmeli. Adaylar: bare
"kovan", "kovan-fabric", "kovan-fabrika". Arama doğrulaması (17 Kasım):
bare "kovan" GitHub'da alınmış — vertexclique/kovan (Rust wait-free
kütüphanesi) ve boratanrikulu/kovan ("engineering methodology →
infrastructure; agent + gates" — kavramsal çakışma yüksek); Ethereum
Kovan testnet sonuçları "kovan" aramalarını gömüyor. "fabric" baş
kelimesi AI/framework alanında kirli (danielmiessler/Fabric, Microsoft
Fabric, Hyperledger Fabric, Python Fabric); sistem ise fiilen
kapasite-bounded bir üretim hattı — kod ve doküman metaforu zaten
fabrika (vardiya, hat, kapı, üretim).

**Karar.** Marka: **KOVAN**; repo ve PyPI paketi: **`kovan-fabrika`**;
CLI komutu: `kovan`; İngilizce çerçeve README.en.md'de: "a
capacity-bounded, evidence-first software factory". pyproject zaten
uyumlu — geçiş maliyeti sıfır. `project.urls` gerçek repo adresi
yaratılınca tek satırla eklenir.

**Sonuçlar.**
- (+) Keşfedilebilirlik: "kovan-fabrika" tam-string araması yalnızca bizi verir.
- (+) Metafor bütünlüğü: doküman setiyle çelişki yok; geçiş maliyeti sıfır.
- (−) "kovan" ön ekli aramalar testnet ile yarışır; tam-string arama normu.
- (−) Türkçe ad alanı uluslararası hissi azaltır; README.en ve cognate
  ("fabrika" ~ factory) bunu telafi eder.

**Reddedilen.** bare "kovan" (alınmış + kavramsal çakışma);
"kovan-fabric" (kirli baş kelime + metafor uyumsuzluğu + geçiş
maliyeti); "kovan-os" (aşırı iddialı); İngilizcelendirme ("hivecraft"
benzeri — çökmüş alan: TheHive vb.).

---

## Karar günlüğü

| Tarih | Olay |
|---|---|
| 2026-10-21 | F01–F12 kabul edildi (konsept sürümü) |
| 2026-11-17 | F13 kabul edildi — proje kimliği: KOVAN / kovan-fabrika |
| — | F07, Airlock'un T1 modeli ölçülene kadar "kısmi" sayılır |
| — | F09'un fiyat tablosu aylık güncellenecek |
| — | F12, ilk gerçek görevde (v0.2) yeniden gözden geçirilecek |
