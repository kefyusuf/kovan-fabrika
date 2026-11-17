# KOVAN — Kalite, Kapılar ve Ölçüm

> **v2 notu (4 Kasım 2026):** Güncel sistem tanımı [`SISTEM.md`](SISTEM.md).
> Eval v1 devrede (90 vakalık dondurulmuş set, bloklayıcı); tohumlanmış hata
> ölçümü `seedtest.py`; LLM-yargıçta ham uyum değil κ raporlanacak.

> Fabrikanın ürünü kanıttır; bu belge kanıtın nasıl üretildiğini ve nasıl
> çürütüldüğünü anlatır. Kural: **ölçmediğin şeyi iddia etme, iddia ettiğin
> şeyin setini yaz.**

---

## 1. Üç katmanlı doğrulama

| Katman | Ne | Örnek | Güvenilirlik | Tek başına kapı olabilir mi |
|---|---|---|---|---|
| **D1 Deterministik** | Aynı girdi → aynı sonuç | derleyici, tip denetimi, test, kural | Yüksek | **Evet** |
| **D2 İstatistiksel** | Örneklem üzerinden oran | eval seti, regresyon seti | Orta (n'e bağlı) | Evet, ama n ve CI raporlanır |
| **D3 Yargı** | Model/insan değerlendirmesi | kod incelemesi, rubrik | Düşük–orta | **Hayır**, tek başına |

**Kapı sırası ile katman hiyerarşisi aynı şey değil.** Sıra iş akışıdır: önce
D1 kapıları (politika, lint, tip, test, köken), sonra inceleme (D3), en son
eval (D2). Eval'in en sonda olması bilinçli: yalnızca incelemeden geçmiş aday
ölçülür — aksi halde ekip eval'e göre kod yazar ve ölçüm, hedefin yerine geçer.

**Yetki hiyerarşisi** ise D1 > D2 > D3'tür: iki kapı çelişirse deterministik
olan kazanır, sonra istatistiksel, en son yargı. Sıra maliyet/akış, hiyerarşi
güven meselesidir; ikisini karıştırmamak gerekir.

---

## 2. Kapılar

| # | Kapı | Katman | Sahip | Maliyet | Geçmezse |
|---|---|---|---|---|---|
| 1 | `policy` | D1 | Airlock | < 1 ms | blok + insan |
| 2 | `lint` | D1 | statik | ~1 s | revizyon |
| 3 | `types` | D1 | statik | ~5 s | revizyon |
| 4 | `tests` | D1 | test | ~30 s | revizyon |
| 5 | `provenance` | D1 | uyum | ~2 s | blok + insan |
| 6 | `review` | D3 | incelemeci | ~15 dk | revizyon |
| 7 | `eval` | D2 | ölçüm | ~5 dk | ret + geri alma |
| 8 | `cost` | muhasebe | finans | ~0 | uyarı + kısma |

**Fail-fast:** ilk bloklayıcı hatada durur. `cost` bloklamaz; uyarır.

**"Sinyal yok" kuralı:** bir kapı için ölçüm üretilmemişse kapı **geçmez**.
Bu, "ölçülmedi = geçti" varsayımını kapatır (`test_missing_eval_signal_is_not_a_pass`).

### 2.1 Test kapısının özel kuralı

Aday, kendi testini getirebilir; ama:

1. Test, koddan **önce** kırmızı olmalı (kayıt zorunlu).
2. Test silinemez; assertion zayıflatılamaz.
3. Yeni test, eski testin kapsadığı davranışı kapsamalı.
4. Meşru refactor istisnası: kapsam artıyorsa test sayısı azalabilir — gerekçeyle.

Bu kural olmadan `tests` kapısı bir tiyatroya dönüşür: ajan testi koda uydurur,
kapı yeşil olur, davranış bozulur.

### 2.2 İnceleme kapısı

- İnceleyici, kodu yazan **farklı bağlamda** çalışır.
- Gerekçe zorunlu; "LGTM" geçersiz.
- İnceleyici kodu düzeltmez; ret eder ve nedenini yazar.
- Rastgele %10 örnek insan denetimine gider (lastik damga tespiti).

---

## 3. Eval harness

### 3.1 Set türleri

| Tür | Amaç | Boyut (v1) | Kullanım | Dondurulmuş mu |
|---|---|---|---|---|
| **Unit** | Tek davranış | 200+ | Her PR | Hayır (kodla büyür) |
| **Regresyon** | Geçmiş hatalar | 50+ | Her PR | Evet (eklenir, çıkarılmaz) |
| **Adversarial** | Kırılma senaryoları | 30+ | Günlük | Evet |
| **Holdout** | Gerçek başarı | 30+ | **Yalnızca sürüm** | Evet, kör |
| **Transfer** | Genelleme | 20+ | Aylık | Evet |

### 3.2 Holdout disiplini (kendi yanmış holdout'umuzdan ders)

Aynı projede yaşanan somut olay: kural seti kendi yazdığı 30 vakada **F1 1.000**
aldı; gerçekçi holdout'ta **0.394**. Sonra kaçırılan holdout vakaları kural
yazımında kullanıldı ve o holdout da **yandı** — artık yayınlanabilir bir sayı
üretmiyor (bkz. `../STATUS.md` §4).

Bu yüzden:

1. **Holdout, üreten ajan tarafından görülmez.** Ayrı dizin, ayrı sahip.
2. **Holdout'a bakarak kural yazıldıysa, o set ölür.** Yeni set gerekir.
3. **Her rapor set kimliği taşır:** `{set, n, tarih, harness, model, seed}`.
4. **Yanmış set** `olcum/sets/retired/` altına taşınır; silinmez, "retired"
   etiketiyle kalır (neden yandığı kayıtlı).

### 3.3 Sürüm ve kanarya

```
yeni sürüm ──▶ gölge (geçmiş 50 görev) ──▶ kanarya (%10) ──▶ tam
                    │                          │
                    └─ uyum < %70 → ret        └─ regresyon → otomatik geri alma
```

Geri alma otomatiktir; insan onayı beklemez. Çünkü kötüleşen bir sürümü
"bir bakalım" diye bırakmak, ölçümün amacını ortadan kaldırır.

---

## 4. Metrikler

Her metrik için üç şey yazılır: **formül**, **kaynak**, **nasıl manipüle edilir**.

| Kısaltma | Formül | Kaynak | Manipülasyon riski | Önlem |
|---|---|---|---|---|
| **BMP** | birleşen PR / vardiya | git | Küçük, önemsiz PR'lar | PR başına ≥ 20 satır + issue bağı |
| **GPK** | ilk turda geçen / toplam görev | ledger | Kolay görev seçmek | Görev sınıfı dağılımı da raporlanır |
| **DSP** | merge sonrası insan diff satırı / PR | git | — | Ölçüm pahalı; örneklemle |
| **MBB** | (model + CI + insan) / birleşen PR | fatura + saat | İnsan saatini saymamak | İnsan dakikası $X ile |
| **ÖVD** | kullanılan beceri / önerilen | skills + tetiklenme | Önemsiz beceri üretmek | 30 gün kullanım şartı |
| **TKH** | tekrar eden fingerprint / toplam hata | lessons | Fingerprint'i çok geniş tutmak | Şema denetimi |
| **KKA** | sonraki 2 haftada hata / 100 PR | issue | Etiketlememek | Hata etiketi zorunlu |
| **GHS** | 06:00'da hazır rapor / gece | dosya | Boş raporu "hazır" saymak | 5 bölüm dolu şartı |

**Raporlama kuralı:** her sayı yanında `n` ve mümkünse güven aralığı.
`n < 20` ise sayı "gösterge" olarak etiketlenir, "sonuç" olarak sunulmaz.

---

## 5. Ölçüm protokolü

Her koşu bir **manifest** üretir:

```json
{
  "run_id": "2026-10-21T23:00:00Z",
  "set": "regression-v3",
  "n": 57,
  "harness": "kovan/0.2.0",
  "model": {"provider": "x", "name": "y", "tier": "T2"},
  "seed": 0,
  "cost_usd": 3.12,
  "result": {"pass": 41, "fail": 16, "score": 0.719},
  "artifacts": ["ledger.jsonl", "diffs/"],
  "notes": "16 hatanın 9'u aynı sınıf: test zayıflatma"
}
```

**Yasaklar:**
- "En iyi 3 koşudan biri" raporlamak.
- Farklı harness sonuçlarını aynı tabloda karşılaştırmak (harness farkı 10+ puan).
- Set değiştiğinde önceki sayıyla kıyaslamak (set kimliği farklıysa kıyas yok).
- Yüzdeyi n belirtmeden vermek.

**Zorunlu:** başarısız örneklerin listesi. Özet sayı, hata listesi olmadan
yayınlanmaz.

---

## 6. Kanıt seviyeleri

Belgelerde ve raporlarda her iddia bir seviye taşır:

| Seviye | Anlam | Örnek |
|---|---|---|
| **[A]** | Bu sistemde ölçüldü, komut/dosya ile tekrar edilebilir | "22 test geçiyor" |
| **[B]** | Birincil dış kaynak (resmî doküman, repo, makale) | arXiv kimliğiyle |
| **[C]** | İkinci el / ajan araştırması; kaynak var, doğrulanmadı | "X, Y'yi %30 azalttı" |
| **[D]** | Doğrulanamadı | "Muhtemelen böyledir" |

Rapor kuralı: [C] ve [D] yan yana yazılmaz; [C]'nin kaynağı verilir,
[D] "doğrulanamadı" başlığı altında toplanır.

---

## 7. Test piramidi (ajan çıktısı için)

| Tür | Ne yakalar | Maliyet | Zorunlu |
|---|---|---|---|
| **Birim** | Fonksiyon davranışı | Düşük | Evet |
| **Sözleşme** | Ajan ↔ araç arayüzü | Düşük | Evet |
| **Özellik tabanlı** | Uç durumlar (property) | Orta | C2'de evet |
| **Snapshot** | Beklenmeyen çıktı değişimi | Düşük | C1'de |
| **Adversarial** | Enjeksiyon, sır sızıntısı, kapsam aşımı | Orta | Haftalık |
| **Kaos** | Kesinti, kısmi başarısızlık | Yüksek | Aylık |

**Altın kural:** Ajanın yazdığı test, ajanın yazdığı kodu doğrulamak için
**tek başına** yeterli değildir. Bağımsız bir test yazarı veya property testi
gerekir.

---

## 8. Kalite kurulu

Kapılar çeliştiğinde (ör. `review` onay, `eval` ret) karar mercii:

| Durum | Karar veren | Kural |
|---|---|---|
| İki D1 kapısı çelişir | vardiya-müdürü | Deterministik olan kazanır |
| D1 geçti, D2 düştü | eval sahibi | D2 kazanır (davranış > test) |
| D3 onay, D2 ret | kalite kurulu | D2 kazanır; D3 gerekçesi kayda geçer |
| Eşik değişikliği önerisi | kurucu (C3) | 14 gün bekleme |

Kurul üyeleri: incelemeci, eval sahibi, kırmızı takım, insan. Ajan çoğunluğu
karar veremez — bu, "üreten ≠ onaylayan" kuralının kurul düzeyindeki hâli.

---

## 9. Bilinen ölçüm tuzakları

1. **Dairesellik:** Kuralı ve test setini aynı kişi yazarsa skor şişer.
2. **Küçük n:** 20 vakada %5 fark anlamsız; güven aralığı ±%20 olabilir.
3. **Hayatta kalma yanlılığı:** Yalnızca başarılı PR'ları ölçmek.
4. **Harness kayması:** Aynı model, farklı harness, 10+ puan fark.
5. **Set kayması:** Set güncellenip eski sayıyla kıyaslanması.
6. **Ölçümü optimize etme:** En sinsi olan; sistemin testi gevşetmesi.
7. **Görünmez insan emeği:** İnsan düzeltmesini saymamak.

Yedisi de bu belgede bir kurala bağlandı; hiçbiri "dikkat ederiz" ile geçiştirilmedi.
