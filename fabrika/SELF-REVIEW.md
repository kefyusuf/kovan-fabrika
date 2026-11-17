# KOVAN — Öz Denetim

> Bu dosya teslimatın parçasıdır, eki değil. Amaç: "ne yaptım" değil,
> **"neyi doğruladım, neyi doğrulamadım, nerede hedeften saptım"**.

---

## 1. Talep → teslim eşlemesi

| # | İstenen | Teslim edilen | Durum |
|---|---|---|---|
| 1 | Sabaha kadar araştırma | 7 paralel hat; 3 tam not + 4 özet; gece ajandası | Kısmi (bkz. §4.2) |
| 2 | Kendi kendine öğrenen yapı | `OGRENME.md` + beceri damıtma mekanizması (test edilmiş) | Mekanizma var, model yok |
| 3 | Kendi yapısını geliştiren | C0–C3 sınıfları, H4 halkası, anayasa, 14 gün kuralı | Tasarım tamam |
| 4 | Şirket tarzı yapı | `ORGANIZASYON.md` (14 ajan, 2 insan, devir/SLA/eskalasyon) + `loop/agents.yaml` | Tamam |
| 5 | Karpathy, Pocock, Superpowers, GSD | `ARASTIRMA.md` §1–§4, kaynaklı | Tamam (C seviyesi) |
| 6 | ADR, PRD gibi proje dosyaları | 8 doküman + 12 ADR + 5 sözleşme dosyası + çalışan kod | Tamam |
| 7 | Kendini review et | Bu dosya | Tamam |
| 8 | Hedefden şaşmadan | §4 sapma denetimi | 2 sapma, gerekçeli |
| 9 | "Loop goal" yöntemi | `README.md` §8, `loop/goal.yaml`, `runner.py`, 22 test | Çalışıyor |

---

## 2. Doğruladıklarım [A]

Bunlar iddia değil; komutla tekrar edilebilir.

| Ne | Komut | Sonuç |
|---|---|---|
| Test paketi | `python tests\test_runner.py` | **22/22 geçti**, 0.09 s |
| Uçtan uca kuru koşu | `python demo.py` | 4 görev → 2 kabul, 2 insan kapısı, 1 revizyon |
| Defter bütünlüğü | `Ledger(...).verify()` | `(True, 5, '')` — zincir sağlam |
| Sözleşme yükleme | `Spec.load('.')` | `kovan-gece-vardiyasi-v1`, 8 kapı, 2.4M token tavanı |
| Tahrif tespiti | `test_tampering_is_detected` | Değiştirilen kayıt yakalandı |
| Bütçe tavanı | `test_budget_exhaustion_stops` | Tavan aşan görev başlamadı |
| C3 kapısı | `test_c3_change_requires_human` | Tek denemede durdu, ısrar etmedi |
| Politika ihlali | `test_policy_violation_blocks_immediately` | `.secrets/` diff'i anında bloklandı |
| Beceri adayı | `test_repeated_failure_emits_skill_candidate` | 2. tekrarda aday üretildi |

### 2.1 Bağımsız denetimde bulunan ve düzeltilen üç hata

Teslimat, ikinci bir ajan tarafından denetlendi; üç gerçek hata bulundu.
Üçü de düzeltildi ve her biri için yeni test yazıldı.

| # | Hata | Neden ciddi | Düzeltme | Test |
|---|---|---|---|---|
| 1 | Sinyalsiz boolean kapı geçiyordu (`signals.get(name, True)`) | "Ölçülmedi = geçti" olurdu; lint/tip/test sinyali olmayan aday kabul edilirdi | Varsayılan `False`; eksik sinyal "sinyal yok" ile ret | `test_missing_boolean_signal_is_not_a_pass` |
| 2 | Anayasa dosyası korunmuyordu | C2 etiketli bir patch `loop/constitution.md`'yi düzenleyebilirdi | `forbidden_paths`'a constitution/gates/agents eklendi; test gerçek sözleşmeyi yükler | `test_constitution_file_is_protected` |
| 3 | Bütçe, gerçek harcamada aşılabiliyordu | Tahmin 1.000 token, gerçek 5.000 → kabul + negatif bakiye | Harcama sonrası bakiye negatifse iş `blocked`, döngü `butce_bitti` | `test_budget_overflow_blocks_before_verification` |

Ortak kök neden: kod, dokümandaki kuralı değil kendi varsayılanını uyguluyordu.
Bu, "testler geçiyor" ile "sözleşme uygulanıyor" arasındaki farkın somut kanıtı.
Dördüncü bir bulgu (kapı sırası ↔ D1/D2/D3 hiyerarşisi) doküman düzeltmesiyle
giderildi: yetki hiyerarşisi ile iş akışı sırası ayrı şeyler olarak yazıldı.

**Kapsam:** 20 dosya, 4.503 satır (kod + doküman; boş `__init__.py` dahil). `loop/runner.py` 635 satır,
testler 322 satır.

**Ne kanıtlanmadı:** Bu testler *mekanizmanın* çalıştığını kanıtlar; *ürünün*
işe yaradığını kanıtlamaz. İkisi arasındaki fark bu belgenin ana konusu.

---

## 3. Doğrulamadıklarım [C]/[D]

| # | İddia | Neden doğrulanmadı | Nasıl doğrulanır |
|---|---|---|---|
| 1 | Gerçek modelle çalışır | Adapter boş; API anahtarı/bütçe yok | v0.2: tek model, 20 görev |
| 2 | Kapılar kaliteyi artırır | Eval seti yok | v0.2: 50 vakalık set + GPK ölçümü |
| 3 | Maliyet PR başına ≤ 6 USD | Hiç model çağrısı yapılmadı | v0.2: fatura + manifest |
| 4 | Gece vardiyası değer üretir | Hiç gerçek gece koşusu yok | v0.3: 5 gece üst üste |
| 5 | 12 haftalık plan gerçekçi | Plan, kanıt değil | Haftalık kapılar |
| 6 | Pazar/müşteri var | Görüşme yapılmadı | 3 müşteri görüşmesi |
| 7 | Araştırma sayıları (sürüm, tarih, benchmark) | Ajan özetleri; tam metin doğrulanmadı | `ARASTIRMA.md` §9 listesi |
| 8 | Hukuki uyum yeterli | Hukukçu incelemedi | Uzman + resmî metin |
| 9 | "Kendini geliştirme" güvenli | Sadece C3 kapısı test edildi; gerçek saldırı senaryosu yok | Kırmızı takım tatbikatı |
| 10 | İki imza kuralı işler | Tek insan var | İkinci insan veya süreç tatbikatı |

**Dürüst cümle:** Bu teslimat bir **konsept + doğrulanmış iskelet**tir, çalışan
bir fabrika değil. "Çalışıyor" diyebileceğim tek şey döngü çekirdeği ve
sözleşmelerdir.

---

## 4. Hedefden saptım mı?

Kendi koyduğum hedef: *"sabaha kadar araştırıp, kendi kendine öğrenen,
kendi yapısını geliştiren, şirket tarzı bir yapı; ADR/PRD gibi tam proje
dosyalarıyla."* Buna göre üç karar denetlendi:

### 4.1 ADR'ler tek dosyada (sapma: düşük)
**Karar:** 12 ADR, `ADR.md` içinde tek dosya; ayrı `adr/ADR-F01.md` dosyaları değil.
**Gerekçe:** Tek sayfada taranabilirlik; 12 kararın bütününü görmek, tek tek
açmaktan hızlı. `docs/adr/` ayrımı Airlock'ta zaten var.
**Sapma mı?** Biçimsel olarak evet, özde hayır. Ayrı dosyalar istenirse
bölmek 10 dakikalık iş; ama tek dosya, kararlar arası çelişkiyi görmeyi
kolaylaştırıyor. **Karar: kabul.**

### 4.2 Dört araştırma notu dosyalanamadı (sapma: orta)
**Ne oldu:** 7 araştırma hattından 3'ü tam not yazabildi (`arastirma/`),
4'ü yalnızca özet döndürdü (araç bütçesi). Özetler `ARASTIRMA.md`'ye **[C]**
etiketiyle işlendi; kaynakça korundu.
**Sapma mı?** Evet: "tam kaynaklı araştırma" hedefinin bir kısmı eksik.
**Telafi:** Her iddia [C] işaretli, doğrulama listesi §3'te, kaynaklar
`ARASTIRMA.md` §10'da. Uydurma yok; eksik var. **Karar: kabul, ama eksik.**

### 4.3 Gece vardiyasını zamanlanmış göreve bağlamadım (sapma: bilinçli)
**Karar:** "Loop goal" mekanizması anlatıldı ve kodlandı; ama gerçek bir
gece 23:00 cron görevi **kurulmadı**.
**Gerekçe:** Geri dönüşü olmayan bir harcama taahhüdü (her gece token/USD).
Bu, kullanıcının kararı; benim varsayımım değil.
**Sapma mı?** Hayır — kapsam dışı bırakıldı ve açıkça söylendi. Tek adımda
kurulabilir (README §8).

### 4.4 Genel hüküm
İki biçimsel/ölçüsel sapma var, ikisi de belgelendi; hedefin özünden
(kanıtlı, öğrenen, şirket gibi çalışan bir yapı) sapma yok.

---

## 5. En zayıf üç varsayım

Bunlar çürütülürse konsept değil, **plan** değişir.

**V1 — "Gece öğrenmesinin değeri maliyetinden yüksektir."**
Gece 7 saat × 40 USD = gece başına 40 USD; ayda ~1.200 USD. Karşılığında
ayda 1–2 aktif beceri bekleniyor. Bir beceri, tekrar eden bir hatayı
engelliyorsa değerli; engellemiyorsa pahalı bir günlük. **Test:** 6. haftada
"beceri başına maliyet" ölçülmeli. Şu an bu sayı **yok**.

**V2 — "Kapılar ajanı gerçekten durdurur."**
Test edilen şey, koşucunun kuralı uygulaması. Test edilmeyen şey, modelin
kapıyı atlatmak için *yaratıcı* davranması (test silme, kapsam kaydırma,
eşik değiştirme). Bir kural motoru, kuralı bilmeyen bir modele karşı
yazıldığında güçlüdür; kuralı bilen bir modele karşı yazıldığında kırılgan.
**Test:** kırmızı takım tatbikatı (v0.2, hafta 4).

**V3 — "Tek kişilik kurulumda iki imza kuralı işler."**
Kurucu hem öneriyi yazar hem onaylar; iki kayıt üretmek denetim *görüntüsü*
verir, denetim *işlevi* vermez. **Test:** ikinci bir insan (danışman, ortak)
eklenmeden C3 kuralı "teknik olarak çalışıyor, sosyal olarak çalışmıyor"
sayılmalı.

---

## 6. İç gerilimler (gizlenmedi)

1. **14 ajan ↔ inceleme bütçesi (İ6).** Kadro 14 rol, ama eşzamanlılık 3–5.
   Gerilim: rol sayısı bir "şirket" hissi veriyor; kapasite ise küçük.
   Çözüm: rollerin çoğu sıralı çalışır; kadro bir "yetenek envanteri", bir
   eşzamanlılık planı değil.
2. **"Gece öğrenir" ↔ öğrenme üretimi yavaşlatır.** Bir beceri aktive olunca
   kapılar sıkılaşır, ilk turda ret artar. Kısa vadede GPK düşer.
   Çözüm: GPK'yı beceri aktivasyonundan 2 hafta sonra ölç; geçiş dönemini
   ayrı raporla.
3. **C3'ün 14 günü ↔ 12 haftalık plan.** Yapı değişiklikleri yavaş; plan
   hızlı. Çözüm: H4 önerileri hafta 9'da başlar, uygulama hafta 12'yi geçer —
   plan bunu kabul ediyor.
4. **Dürüstlük ↔ sabah raporunun "işe yarar" hissi.** Kötü haber önce
   yazıldığında rapor demoralize edebilir. Çözüm: her kötü haberin yanına
   tek bir sonraki adım yazılır (rapor §5).
5. **"Kendi kendine" ↔ insan kapısı.** Sistem ne kadar otonom olursa, insan
   kapısı o kadar kritik olur. Bu bir çelişki değil, bir orantı: otomasyon
   arttıkça denetim noktası azalır ama ağırlaşır.

---

## 7. İnceleyici için kontrol listesi

Bir başkası bu teslimatı denetlerken şu 8 soruyu sorabilir:

1. `PRD.md` gereksinimleri ölçülebilir mi? (FR başına kabul kriteri var mı)
2. `ADR.md` kararları birbirini çürütüyor mu? (özellikle F03 ↔ F08)
3. `loop/goal.yaml` ile `constitution.md` çelişiyor mu? (yasak yollar, bütçe)
4. `runner.py` gerçekten fail-fast mi? (`evaluate` erken çıkıyor mu)
5. Defter tahrifi gerçekten yakalanıyor mu? (testi çalıştır, sonra elle boz)
6. `OGRENME.md`'deki "2 tekrar" eşiği `runner.py` ile aynı mı? (`>= 2`)
7. `KALITE.md` metrikleri `PRD.md` ile aynı tanımı mı kullanıyor?
8. `SELF-REVIEW.md` §3 listesi, `ARASTIRMA.md` §9 ile tutarlı mı?

Bu soruların altısı komutla, ikisi okumayla cevaplanır. Cevabı "hayır" olan
madde, düzeltilecek maddedir.

---

## 8. Sonraki üç adım (karar sırası)

1. **Karar:** İç fabrika mı, dış hizmet mi? (PRD §11) — bu, SLA ve risk
   profilini belirler; diğer her şey buna bağlı.
2. **v0.2:** Tek model adapter + 50 vakalık eval seti + 20 görev.
   Çıkış: GPK ve MBB ölçülmüş iki sayı.
3. **v0.3:** Gece vardiyası; 5 gece üst üste rapor. Çıkış: sabah raporu
   gerçekten okunuyor mu? (kullanıcı 5 dakikada karar verebiliyor mu)

**Yapılmayacak:** v0.2 bitmeden ajan sayısını artırmak, yeni beceri türleri
eklemek, marka/isim işine girmek.

---

## 9. Tek cümlelik hüküm

> Konsept, doğrulanmış bir iskelete ve dürüst bir eksik listesine sahip;
> iddia ettiği şeyi kanıtlamıyor, **kanıtlanabilir hale getiriyor** — ki
> bir konseptten beklenebilecek en fazla şey budur.
