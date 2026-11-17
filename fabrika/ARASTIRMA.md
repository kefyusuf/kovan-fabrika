# KOVAN — Araştırma Notları

> Bu belge, konseptin hangi dış fikirlere dayandığını ve **hangi iddiaların
> doğrulanmadığını** kaydeder. Amaç literatür özeti değil; her bulgunun
> tasarıma nasıl dönüştüğünü göstermek.

**Kanıt seviyeleri:** **[A]** bu sistemde ölçüldü · **[B]** birincil dış kaynak
(resmî doküman, repo, arXiv) · **[C]** ikinci el / ajan araştırması, kaynak var
ama bağımsız doğrulanmadı · **[D]** doğrulanamadı.

**Yöntem.** Yedi paralel araştırma hattı: (1) Karpathy, (2) Matt Pocock,
(3) Superpowers + skill/subagent mimarisi, (4) GSD + spec-driven akımı,
(5) ticari/açık kaynak fabrikalar, (6) kendini geliştirme literatürü,
(7) yönetişim/uyum. Üç hattın tam notu `arastirma/` altında; diğer dördü
özet düzeyinde kaldı (araç bütçesi nedeniyle dosyalanamadı) ve burada **[C]**
olarak işaretli.

---

## 1. Andrej Karpathy — kısıt zekâ değil, doğrulanabilirlik

**Bulgu.** Karpathy'nin çerçevesinde "Software 3.0", bağlam/prompt/araç ile
programlamaktır; ama üretimde doğrulama, test, güvenlik ve insan anlayışı
zorunlu kalır. Ayırt edici cümle: *"Software 1.0 specifies, Software 2.0
verifies"* — bir iş ne kadar yeniden çalıştırılabilir ve ölçülebilirse o kadar
otomatikleşir. **[C]** (birincil metinler `arastirma/01-karpathy.md` §3.4'te
listeli)

**İkinci bulgu: otonomi kademelidir.** Karpathy'nin "autonomy slider"ı
(Tab → Cmd+K → Cmd+L → Cmd+I) bir ürün kontrol yüzeyidir; ajanı salıvermek
değil, doğrulanabilir dilimlerde çalıştırmaktır. **[C]**

**Üçüncü bulgu: minimal, tek depo, uçtan uca artefaktlar güvenilirliği artırır.**
micrograd (~150 satır), llm.c (~1.000), nanochat (tek kadran, tek metrik),
autoresearch (3 dosya, tek metrik `val_bpb`). Küçük ve anlaşılır sistem,
denetlenebilir sistemdir. **[C]**

**Tasarıma aktarılan (→ ADR):**
- Görevleri **doğrulanabilirlik ekseninde** sınıflandır (F05, F08).
- Otonomiyi kademelendir; "slider" bir ürün yüzeyi olsun (F08).
- Tek metrikli, sabit bütçeli deney döngüsü (F09, KALITE §4).
- Tek depo, küçük artefakt, az bağımlılık (F10).

**Aktarılmayan:** "vibe coding" pratikleri üretim hattına girmez; prototip
hızı ile üretim kabulü aynı şey değil.

---

## 2. Matt Pocock — spec bir karar kaydı, plan mode değil

**Bulgu.** Pocock, "plan mode" yaklaşımını bırakıp doküman + **seam sözleşmesi**
yaklaşımına geçti: spec, uzun bir plan değil, alınan kararların ve dikey
kesitin (seam) sözleşmesi. İdeal seam sayısı 1; spec yalnızca çok oturumlu
işlerde yazılır. **[C]**

**Doğrulama disiplini.** Deterministik araçlar (`tsc`, Vitest, lint, pre-commit/CI)
asıl kapı; retrospektif ise "daha dikkatli olalım" değil, **mekanik bir check**
üretir. **[C]**

**İnceleme.** İki eksende, ayrı bağlamda: *Standards* ve *Spec*. Her bulgu
sitasyon ister (dosya + satır). Alt-ajan çıktısı **hipotez** sayılır, kanıt değil. **[C]**

**Skill/subagent/script ayrımı.** Skill = prosedür; subagent = bağlam izolasyonu
(tek seviye); script/CI = deterministik, insansız yaptırım. **[C]**

**Tasarıma aktarılan:** F05 (komutlu kabul kriteri), F06 (deterministik >
yargı), KALITE §2.2 (gerekçeli inceleme), ORGANIZATION §5 (devirde artefakt).

---

## 3. Superpowers — süreç motoru, prompt koleksiyonu değil

**Bulgu.** `obra/superpowers` (MIT, Jesse Vincent / Prime Radiant) **v7.0.0
(2026-10-10)** itibarıyla 15 model-çağrılı beceriden oluşan bir süreç motoru;
slash komutlar yalnızca üç ince kabuk. Değeri kapsamda değil, **kural
sertliğinde**: "test yoksa üretim kodu yok", "taze doğrulama kanıtı olmadan
'bitti' denmez", "5 tur sonra breaker", ve modelin kendine verdiği bahaneleri
listeleyen "rationalization" tabloları. **[B]** (repo + release notları;
`arastirma/03-superpowers.md`)

**Maliyet bulgusu.** Açılışta ~22k token yükleme, tek oturumda 603k'ya çıkan
controller context'i, compaction sonrası 20.000 karakterde kesilen skill
yüzünden 18 düzeltme turu — hepsi issue olarak belgeli. **[C]**

**Resmî Claude Code tarafı.** Skill = gövdesi kullanılınca yüklenen dizin;
subagent = ayrı bağlam + kendi araç seti; hook = izin sisteminden önce çalışan
deterministik kapı. Üçü birlikte "süreç" ile "yaptırım"ı ayırır. **[C]**

**Tasarıma aktarılan:** F02 (test edilebilir iskelet), F04 (SKILL.md birimi),
F06 (kanıt > iddia), KALITE §2.1 (test zayıflatma yasağı), `loop/agents.yaml`
devir kuralları.

**Aktarılmayan:** 15 becerinin tamamını taşımak. KOVAN 14 rol + 5–8 beceri ile
başlar; beceri sayısı bir başarı göstergesi değil (LEARNING §7).

---

## 4. GSD ve spec-driven akımı — spec'in sınırı

**Bulgu (GSD).** `gsd-build/get-shit-done` arşivlendi; geliştirme
`open-gsd/gsd-core` altında sürüyor (v1.18.0, MIT) **[C]**. Kritik ayrıntı:
GSD'de `SPEC.md` **opsiyonel**; yani akımın "spec = tek doğruluk kaynağı"
sloganı, aracın kendi uygulamasında mutlak değil **[C]**. GSD'nin asıl katkısı
spec değil, **faz yönetimi**: `STATE.md`, `ROADMAP.md`, faz geçişleri,
goal-backward doğrulama.

**Bulgu (akım).** Spec Kit (`/specify` → `/plan` → `/tasks`), Kiro
(spec → design → tasks), BMAD (rol tabanlı ajan takımı) aynı ihtiyacın farklı
çözümleri. Ortak iddia: kod türev, spec kaynak. Ortak arıza: **spec drift** —
spec güncellenmez, kimse okumaz, kod tek gerçek olur. **[C]**

**Tasarıma aktarılan:** F05 (spec = çalıştırılabilir kriter + drift denetimi),
ARCHITECTURE §6 (faz/durum dosyaları), YOL-HARITASI haftalık çıktı disiplini.

**Ders.** "Spec yaz" bir çözüm değil; **spec'in ölçülmesi** çözüm. Bu yüzden
KOVAN'da spec, komut içermeyen cümleleri kabul etmiyor.

---

## 5. Yazılım fabrikaları — pazar konsolide, mimari yakınsadı

**Bulgu 1: sekiz ortak desen.** Görev başına izole VM/konteyner; plan → uygula
→ test → inceleme; inceleme ajanı; çoklu ajan rolleri; insan onay kapıları;
filo yönetimi; model yönlendirme; kalıcı ortam. Her desen en az iki üründe
birinci el belgeyle doğrulandı. **[C]** (`arastirma/05-fabrikalar.md` §7)

**Bulgu 2: benchmark ayrıştı.** Aynı model farklı harness'ta 58.0–69.9 arası
gösteriliyor; panolar arası fark 20+ puan. Tek sayı artık anlamlı değil. **[C]**

**Bulgu 3: üretim metrikleri çelişkili.** Aynı soruya ("ajan PR'ları ne kadar
birleşiyor") dört farklı cevap: üretici raporu %67, hakemli karşılaştırma
%61.6, ikincil analiz %32.7 — farklı evrenler ölçülüyor. **[C]**

**Bulgu 4: asıl maliyet koordinasyon.** Bağımsız ölçümlerde geliştiriciler AI
ile yavaşlayabiliyor (METR RCT, %19; sonra veri güvenilmez ilan edildi),
DORA 2026 teslim hızında −%1.5 ve kararlılıkta −%7.2 ilişkisi buldu; ajan
PR'larının %79.4'ü aynı repoda eşzamanlı açık. **[C]**

**Bulgu 5: beş yapısal arıza.** Belirsizlik duvarı; inceleme darboğazı;
koordinasyon çakışması; ölçüm enflasyonu; denetim kaybı. **[C]**

**Tasarıma aktarılan:** İ6 (inceleme bütçesi), ARCHITECTURE §8 (tek yazıcı, worktree,
dosya kilidi), KALITE §3.2 (set kimliği, harness sabitleme), ADR-F07 (Airlock).

**Tasarıma aktarılmayan:** "Filo" ölçeği. 20 ajanlı bir kadro, ölçülmemiş bir
inceleme kuyruğudur; KOVAN 3–5 eşzamanlı işçiyle başlar.

---

## 6. Kendini geliştirme — öneriyi ajan üretir, kabulü kapı verir

**Bulgu 1: literatür gerçek ama dar.** Darwin Gödel Machine (arXiv:2505.22954)
SWE-bench'te %20 → %50; SICA (arXiv:2504.15228) %17 → %53; AlphaEvolve
(arXiv:2506.13131) 4×4 matris çarpımını 48 çarpıma indirdi. **[C]** (arXiv
kimlikleri ajan raporundan; tam metin doğrulanmalı)

**Bulgu 2: asıl darboğaz değerlendirici sadakati.** DGM'nin testleri hacklediği
belgeli; SWE-bench Verified üretilirken örneklerin önemli bir kısmı kusurlu
diye elendi. **[C]**

**Bulgu 3 — kendi ölçümümüz [A].** Aynı projede kural seti kendi yazdığı 30
vakada **F1 1.000**, gerçekçi holdout'ta **0.394** aldı; sonra holdout
"yanmış" ilan edildi (bkz. `../STATUS.md` §4). Bu, tüm konseptin en somut
gerekçesi: **dairesel ölçüm, ölçüm değildir.**

**Tasarıma aktarılan:** F06 (D1 > D2 > D3), KALITE §3.2 (holdout disiplini),
LEARNING §6.3 (eval değiştiren aday otomatik ret), F03 (değişmez çekirdek).

**Kritik ayrım.** "Kanıtla" (Gödel machine) yerine "ölç" (deney + kapı).
Daha zayıf garanti, ama uygulanabilir tek garanti.

---

## 7. Yönetişim — mimari kontrol, politika cümlesi değil

**Bulgu 1: çerçeveler.** ISO/IEC 42001 (AI yönetim sistemi), NIST AI RMF
(Yönet–Haritala–Ölç–Yönet), EU AI Act (risk sınıfları + teknik dokümantasyon +
insan gözetimi) aynı yöne bakıyor: **risk sınıfı, sahiplik, kanıt, gözetim**. **[C]**

**Bulgu 2: tarihler.** Ek III yüksek-risk yükümlülükleri 2 Aralık 2027, Ek I
2 Ağustos 2028 olarak raporlandı; "Ağustos 2026'da başlıyor" bilgisi eskimiş
görünüyor. **[C]** — yayın öncesi resmî metinden teyit şart.

**Bulgu 3: ölümcül üçlü.** Özel veri + güvenilmeyen içerik + dışa iletişim
aynı oturumda bulunmamalı. MCP'de token passthrough yasak; araç
annotation'ları güvenilir değil; devcontainer bir güvenlik sınırı değil. **[C]**

**Bulgu 4: tedarik zinciri.** SBOM (SPDX/CycloneDX), SLSA seviyeleri,
imzalı artefakt. **[C]**

**Bulgu 5: hukuk.** 2026'da bir temyiz kararının (Doe v. GitHub, 9. Cir.)
eğitim verisi iddialarını daralttığı raporlandı; telif riski sürüyor. **[C]**
— hukuki tavsiye değil.

**Tasarıma aktarılan:** YONETISIM §1–§9 (tehdit modeli, izolasyon, insan
kapıları, SBOM, runbook), anayasa madde 6 ve 8.

---

## 8. Sentez: bulgudan karara

| Bulgu | İlke | Karar |
|---|---|---|
| Doğrulanabilirlik otomasyonu belirler | İ1, İ5 | F05, F06 |
| Otonomi kademelidir | İ3 | F08 |
| Üretim ucuz, kabul pahalı | İ6 | inceleme bütçesi |
| Değerlendirici tavandır | İ5 | F06, KALITE §3 |
| Deney > kanıt | İ4 | F02, LEARNING §6.4 |
| Bellek dosyada birikir | İ4 | F11 |
| Çekirdek değişmez olmalı | İ3 | F03 |
| Koordinasyon maliyeti gerçek | — | ARCHITECTURE §8 |
| Politika araç düzeyinde olmalı | — | F07 |
| Taşınabilirlik harness'tan bağımsız | — | F12 |

---

## 9. Doğrulanamayanlar (dürüstlük listesi)

Bu belgede **[C]** işaretli her sayı, bir ajan araştırmasının özetidir; tam
metin veya resmî kaynak doğrulaması bu turda yapılmadı. Özellikle:

1. **Sürüm ve tarihler** (Superpowers v7.0.0, GSD v1.18.0, EU AI Act tarihleri)
   — 2026 sonbaharına ait; yayın öncesi teyit gerekir.
2. **Benchmark yüzdeleri** — harness ve tarih belirtilmeden karşılaştırılamaz;
   bu belgede bilinçli olarak tek tek verilmedi.
3. **METR/DORA bulguları** — RCT'nin kendi güncellemesi veriyi "güvenilmez"
   ilan etti; bu yüzden "AI yavaşlatır" demiyoruz, "ölçüm tartışmalı" diyoruz.
4. **Karpathy alıntıları** — X gönderilerinin tarihleri ve tam metinleri
   değişebilir; birincil arşiv `arastirma/01-karpathy.md`'de.
5. **Pocock pratikleri** — bir eğitmenin iş akışı; genellenebilirliği
   kanıtlanmadı.
6. **Hukuki durum** — hiçbir bölüm hukuki görüş değil.

Bir iddia **[D]** ise burada listelenmedi; çünkü konseptte kullanılmadı.

---

## 10. Kaynakça (özet)

**Birincil / resmî**
- `github.com/obra/superpowers` — README, `skills/`, release v7.0.0
- `github.com/open-gsd/gsd-core` — README, ADR-1820 (SPEC.md opsiyonel)
- `github.com/github/spec-kit` — `/specify`, `/plan`, `/tasks`
- `aihero.dev` — Matt Pocock, AI Hero içerikleri
- `karpathy.bearblog.dev`, `x.com/karpathy`, `github.com/karpathy/nanochat`
- `arxiv.org/abs/2505.22954` (DGM), `2504.15228` (SICA), `2506.13131` (AlphaEvolve)
- `iso.org/standard/81230.html` (ISO/IEC 42001), `nist.gov/itl/ai-risk-management-framework`
- `artificialintelligenceact.eu` — uygulama takvimi
- `modelcontextprotocol.io` — güvenlik notları

**İkincil / analiz**
- `arastirma/01-karpathy.md`, `arastirma/03-superpowers.md`, `arastirma/05-fabrikalar.md`
- `LLM-Self-Improvement-Report.md` (bu depo) — kendini geliştirme literatürü
- `STATUS.md` (bu depo) — dairesel ölçüm vakası

**Not:** Kaynak listesi, "okundu" iddiası değil, "erişildi" kaydıdır. Her
birinin tam metni yayın öncesi yeniden kontrol edilmeli.
