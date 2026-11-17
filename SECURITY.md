# Güvenlik Politikası — KOVAN

## Desteklenen sürümler

| Sürüm | Destek |
|---|---|
| 0.2.x | ✅ Aktif |
| 0.1.x | ❌ Sadece son sürüme yükseltin |

## Açıklık bildirimi

Lütfen güvenlik açıklarını **halka açık issue olarak bildirmeyin**.
GitHub'ın *Security Advisories → Report a vulnerability* akışını kullanın.
48 saat içinde dönüş yapıp doğrulama ve düzeltme planını paylaşıyoruz.
Düzeltme yayını SemVer'e göre patch sürümle gelir.

## Tasarım kaynaklı güvenlik kararları (bilinçli normlar)

1. **BYOK (bring-your-own-key):** API anahtarı yalnızca sizin makinenizde
   tutulur (`.anahtar*` dosyaları `.gitignore`'da). Anahtar KOVAN koduna
   gömülmez, repoya yazılmaz, telemetriyle gönderilmez.
2. **Egress günlüğü:** canlı adapter tüm model çağrılarını
   `egress*.jsonl`'e kaydeder (`.gitignore`'da). Adaptör sinyal üretmez;
   kapı kararları modelden bağımsız kalır.
3. **Fail-closed kapılar:** test/provenance/eval kapıları şüphede
   *bloklar*, geçmez. Kirli git ağacında doğrulama koşmaz.
4. **İnsan kapıları (C1/C3):** beceri aktivasyonu ve kırılma giderme
   insan onayı gerektirir; sistem kendi onayını kendi kabul edemez (m.2).
5. **SBOM:** her koşum SPDX 2.3 çıktısı üretir; üçüncü taraf bileşenler
   sürüm bilgisiyle listelenir.

## Kapsam dışı

- Canlı model çağrılarında **sağlayıcı tarafı** güvenlik (OpenAI-uyumlu
  servis): kendi anahtarınızı kullandığınızda veri akışının sağlayıcı
  politikaları sizin sorumluluğunuzdadır. Kuru mod (varsayılan) tamamen
  çevrimdışıdır ve model çağrısı yapmaz.
- Hedef depodaki üçüncü taraf kodun kendi güvenlik açıkları (SBOM +
  kendi SCA süreciniz ile izleyin).
