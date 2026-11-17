# KOVAN — Yönetişim, Güvenlik ve Maliyet

> **v2 notu (4 Kasım 2026):** Güncel sistem tanımı [`SISTEM.md`](SISTEM.md).
> Uyum katmanı `uyum.py` devrede (import izin listesi + bağımlılık dosyası
> tespiti + kopya şüphesi + yinelenen fonksiyon = provenance sinyali);
> SBOM tohumu (`sbom.py`, SPDX 2.3, lock sürümleri) ve **egress kaydı**
> (`adapter_http --egress-log`) devrede. Kopya kod blok tespiti ve tam
> SPDX paket sürümü S4'ün kalanı.

> Bu belge hukuki tavsiye değildir. Regülasyon maddeleri **kaynaklı ama
> doğrulanmamış** ([C]) olarak işaretlendi; yayına girmeden önce bir hukukçu
> ve güncel resmî metinle teyit edilmelidir.

---

## 1. Tehdit modeli

| # | Tehdit | Senaryo | Etki | Kontrol |
|---|---|---|---|---|
| T1 | **Prompt enjeksiyonu** | Okunan dosya/web sayfası "kuralları yoksay" der | Ajan kapsam dışı iş yapar | İzolasyon + politika + kaynak ayrımı |
| T2 | **Sır sızıntısı** | Ajan `.env`'i okur, rapora yazar | Kimlik bilgisi ifşası | Secret yok + yasak yol + çıktı taraması |
| T3 | **Zehirli bağımlılık** | Ajan bilinmeyen paket ekler | Tedarik zinciri saldırısı | `provenance` kapısı + lisans listesi |
| T4 | **Bütçe kaçağı** | Döngü sonsuz yeniden dener | Fatura patlaması | Rezervasyon + tavan + devre kesici |
| T5 | **Kendini yetkilendirme** | Ajan kendi iznini/eşiğini değiştirir | Denetim çöker | C3 + yasak yol + ayrı defter |
| T6 | **Veri sızıntısı** | Müşteri kodu dış modele gider | Gizlilik ihlali | Sağlayıcı politikası + yerel model seçeneği |
| T7 | **Koordinasyon çakışması** | İki ajan aynı dosyayı ezer | Veri kaybı, yanlış merge | Worktree + dosya kilidi + tek yazıcı |

### 1.1 "Ölümcül üçlü" yasağı

Aynı oturumda şu üçü **birlikte** bulunamaz:

1. özel/az bilinen veri,
2. güvenilmeyen içerik (dış dosya, web, issue metni),
3. dışa iletişim (ağ, e-posta, PR açma).

İkisi olabilir, üçü olamaz. Bu kural, enjeksiyonun sızmaya dönüşmesini
mimari olarak engeller ([C] — Simon Willison'ın "lethal trifecta" çerçevesi).

---

## 2. İzolasyon

| Katman | Uygulama | Doğrulama |
|---|---|---|
| Süreç | Konteyner başına tek görev | imaj etiketi kayıtlı |
| Dosya | git worktree; ana ağaç salt-okunur | `git status` temiz |
| Ağ | Allowlist proxy; varsayılan kapalı | egress log |
| Secret | Ortamda yok; araç katmanında enjekte | `env` taraması |
| Kaynak | CPU/bellek/süre tavanı | cgroup limiti |
| Çıktı | Yalnızca `diff` + artefakt dışarı | çıktı taraması |

**Kural:** Ajan, "internete çıkabilir" değil, "şu 7 host'a çıkabilir" durumunda
çalışır. `goal.yaml → constraints.allowed_hosts` bunun tek kaynağıdır.

---

## 3. İnsan kapıları

| Sınıf | Örnek | Onay | Süre |
|---|---|---|---|
| C1 | Beceri aktivasyonu | eval + insan gözden geçirme | 1 gün |
| C2 | Ürün kodu | kapılar (otomatik) | — |
| C3 | Anayasa, eşik, model, kadro | kurucu + kapı bekçisi | 14 gün |
| Güvenlik | Ağ politikası, sandbox gevşetme | kapı bekçisi | anında |
| Hukuk | Lisans, dış veri | kurucu | 24 sa |
| Yayın | Sürüm, müşteriye dokunan değişiklik | kapı bekçisi | 24 sa |

**İki imza kuralı:** Öneriyi yazan ile onaylayan aynı kişi olamaz. Tek kişilik
kurulumda bile iki ayrı kayıt üretilir (öneri + onay); bu, ileride ikinci bir
insan eklendiğinde denetimin çalışmasını sağlar.

**Zaman aşımı:** C3 onayı 14 gün içinde gelmezse öneri `expired` olur ve
yeniden açılması gerekir. Sessizce bekleyen öneri birikmez.

---

## 4. Denetim ve kanıt

| Bileşen | Ne kaydeder | Saklama | Doğrulama |
|---|---|---|---|
| `ledger.jsonl` | Her karar + kapı sonucu | Süresiz | `verify()` hash zinciri |
| `lessons.jsonl` | Reddedilme nedeni + fingerprint | Süresiz | Şema |
| `skills/` | Beceri + kanıt + test | Sürümlü | Test |
| `reports/` | Sabah raporu | Süresiz | 5 bölüm kontrolü |
| Egress log | Dış çağrılar | 90 gün | Allowlist karşılaştırma |
| Maliyet kaydı | Token/USD | 24 ay | Fatura mutabakatı |

**Dış çapa (v0.2):** Defterin son hash'i günlük olarak ayrı bir yere (ör.
imzalı commit etiketi) yazılır. Amaç: tüm defterin topluca yeniden yazılmasını
fark edilebilir kılmak.

---

## 5. Uyum çerçevesi

| Çerçeve | Ne ister | Bizde karşılığı | Durum |
|---|---|---|---|
| **ISO/IEC 42001** | AI yönetim sistemi: politika, rol, risk, sürekli iyileştirme | anayasa + kadro + risk kaydı | Kısmi |
| **NIST AI RMF** | Yönet–Haritala–Ölç–Yönet döngüsü | H1–H4 halkaları | Kısmi |
| **EU AI Act** | Risk sınıfı, teknik dokümantasyon, insan gözetimi | C sınıfları + defter | Kısmi |
| **SBOM** (SPDX/CycloneDX) | Bağımlılık envanteri | `uyum/sbom.json` | Yok |
| **SLSA** | Tedarik zinciri seviyesi | imzalı artefakt | Yok |

**EU AI Act zaman çizelgesi [C]:** Yüksek-risk kategorileri için Ek III
yükümlülükleri 2 Aralık 2027, Ek I 2 Ağustos 2028 olarak raporlandı.
Bu tarihler değişebilir; yayın öncesi resmî metinden teyit edilmeli.
Ayrıca: bir kod üretim aracının hangi risk sınıfına girdiği, **kullanım
bağlamına** bağlıdır (ör. işe alım kararı veren bir sistemle aynı kefeye
konmaz). Bu değerlendirme hukukçudur, mühendis değil.

---

## 6. Lisans ve köken (provenance)

Kurallar:

1. **Kaynağı gösterilemeyen kod birleşmez.** Her patch, hangi spec + hangi
   dosyalardan türediğini taşır.
2. **Bağımlılık eklemek C3'tür.** Ajan kendi başına paket ekleyemez.
3. **Lisans allowlist:** MIT, Apache-2.0, BSD, ISC. GPL/AGPL ve bilinmeyen
   lisans → insan kararı.
4. **Kopyala-yapıştır tespiti:** Aday diff'inde 40+ satırlık birebir dış kod
   varsa `provenance` kapısı işaretler.
5. **AI üretimi etiketi:** commit mesajında `Co-authored-by: kovan` ve
   PR açıklamasında üretim kaydı bulunur.

**Hukuki not [C]:** Üretken kodun telif durumu ülkeye ve davaya göre değişiyor;
ABD'de 2026'da bir temyiz kararının eğitim verisi iddialarını daralttığı
raporlandı. Bu bir hukuki görüş değildir; ticari kullanım öncesi danışılmalıdır.

---

## 7. Maliyet modeli

### 7.1 Birim ekonomi

```
PR maliyeti = model + önbellek + CI + insan inceleme + altyapı
```

| Kalem | Tipik pay | Düşürme yolu |
|---|---|---|
| Model (üretim) | %45 | Model yönlendirme, daha küçük T1/T2 |
| Model (inceleme) | %20 | Önbellekli bağlam, ucuz model |
| Yeniden deneme | %15 | Daha iyi spec, daha iyi test |
| CI | %10 | Değişmez ortam, katman önbelleği |
| İnsan | %10 | Daha küçük PR, daha net gerekçe |

**Kaldıraçlar [C]:** önbellekli okuma belirgin biçimde ucuzlar (sağlayıcıya
göre ~%10 fiyat), toplu işleme ~%50 indirim sağlar. Sağlayıcı fiyatları
değişir; tablo `butce-bekcisi` tarafından aylık güncellenir.

### 7.2 Bütçe koruması

| Eşik | Davranış |
|---|---|
| %50 | Rapor: hız ve maliyet karşılaştırması |
| %80 | Model kademesi düşer (T3 → T2), paralellik 3 → 1 |
| %95 | Yalnızca devam eden görevler tamamlanır |
| %100 | Yeni görev alınmaz; rapor yazılır; döngü durur |

**Rezervasyon:** Her görev başlamadan `estimate_tokens` kadar bütçe ayrılır.
Bu, "yolda fark ederiz" ihtimalini kapatır (`test_budget_exhaustion_stops`).

### 7.3 Maliyet anti-pattern'i

"Bir PR'ı 40 dolara mal edip 6 dolar gibi raporlamak" — insan inceleme
dakikalarını saymamak. `MBB` metriği insan süresini de içerir; aksi halde
maliyet tablosu bir reklam afişine dönüşür.

---

## 8. Olay müdahalesi

> **Tatbikat (4 Kasım 2026):** bu bölümün dört adımı `tatbikat.py` ile
> koşulur denetlendi (normal koşu, defter doğrulama, STOP ile durdurma,
> kirli klon üzerinde geri alma) — 4/4 PASS. A4'ün ilk sürümü satır sonu
> (CRLF) karşılaştırmasında yanlış düşmüştü; ölçüt `git status --porcelain`
> olarak düzeltildi.

| Seviye | Örnek | İlk yanıt | Kim |
|---|---|---|---|
| **S1** | Secret sızıntısı, yetkisiz yazma | Durdur + anahtarları döndür | kapı bekçisi (anında) |
| **S2** | Politikasız geçen C3, eval manipülasyonu | Durdur + geri al + kayıt | kurucu (1 sa) |
| **S3** | Bütçe aşımı, tekrarlayan hata patlaması | Kısıtla + rapor | vardiya-müdürü (anında) |
| **S4** | Tek görev hatası | Ders kaydı + devam | damitici (gün içi) |
| **S5** | Kalite düşüşü (regresyon) | Otomatik geri alma | eval (anında) |

**Runbook (S1):**
1. `STOP` dosyası → döngü durur.
2. Konteynerler durdurulur; ağ kesilir.
3. Defter son 24 saat taranır: hangi çağrı, hangi çıktı.
4. Etkilenen anahtarlar döndürülür.
5. Rapor: ne oldu, ne sızdı, ne kadar sürdü.
6. Politika güncellemesi (C3) — aynı olayın tekrarı imkânsız hale gelir.

**Kural:** Her S1/S2 olayı bir **anayasa veya kapı değişikliği** üretmek
zorundadır. Aksi halde olay "kapandı" sayılmaz; sadece "unutuldu" olur.

---

## 9. Politika örneği (Airlock kuralı)

```yaml
# politika/kovan.yaml (taslak)
rules:
  - id: deny-secrets
    match: { path: [".secrets/**", "**/*.pem", "**/.env"] }
    decision: block
    reason: "Sır dosyası okunamaz."

  - id: deny-constitution
    match: { path: ["anayasa/**", "loop/goal.yaml", "loop/gates.yaml"] }
    decision: block
    reason: "Anayasa değişikliği yalnızca insan onayıyla."

  - id: ask-new-dependency
    match: { event: "file_write", file: ["package.json", "pyproject.toml", "Cargo.toml"] }
    decision: ask
    reason: "Yeni bağımlılık C3 sınıfıdır."

  - id: deny-network-default
    match: { event: "network" }
    decision: block
    unless: { host_in: "${allowed_hosts}" }
    reason: "Varsayılan ağ kapalı."

  - id: deny-prod-deploy
    match: { command_regex: "(kubectl|terraform|aws|gcloud).*(apply|deploy|destroy)" }
    decision: block
    reason: "Üretim erişimi ajanda yok."
```

Bu kurallar Airlock'un mevcut biçimiyle uyumlu; `policy` kapısı aynı motoru
kullanır (ADR-F07).

---

## 10. Uyum kontrol listesi

| # | Kontrol | Kanıt | Durum |
|---|---|---|---|
| 1 | Anayasa yazılı ve yazma yasaklı | `loop/constitution.md` + politika | Var |
| 2 | Değişiklik sınıfları tanımlı | C0–C3 tablosu | Var |
| 3 | İnsan kapıları tanımlı | §3 tablo | Var |
| 4 | Denetim kaydı değiştirilemez | hash zinciri + test | Var |
| 5 | İzolasyon tanımlı | `goal.yaml` sandbox | Tanım var, kod yok |
| 6 | Bütçe tavanı ve durdurma | `goal.yaml` + test | Var |
| 7 | SBOM | `uyum/sbom.json` | **Yok** |
| 8 | Lisans allowlist | §6 | Tanım var, otomasyon yok |
| 9 | Olay runbook'u | §8 | Var (kâğıt) |
| 10 | Veri saklama politikası | §4 | Kısmi |
| 11 | Model sağlayıcı sözleşmesi | — | **Yok** |
| 12 | Çalışan/müşteri verisi ayrımı | — | **Yok** |

Son üç madde, ürünleşme öncesi kapatılması gereken gerçek boşluklar.

---

## 11. Bu belgenin kapsamadığı

- Model sağlayıcılarının kullanım şartları ve veri işleme ekleri.
- Müşteri sözleşmelerinde "AI ile üretildi" beyanı.
- İş hukuku (ajan çıktısının çalışan performansına etkisi).
- Sigorta ve sorumluluk.
- Vergi/muhasebe.

Bunlar "sonra bakarız" değil; **ürünleşme kapısının** parçaları. Konsept
aşamasında yazılmaları, sonradan sürpriz olmalarını engeller.
