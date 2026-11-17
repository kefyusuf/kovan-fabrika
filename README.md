# KOVAN — kovan-fabrika

![tests](https://github.com/kefyusuf/kovan-fabrika/actions/workflows/tests.yml/badge.svg)

**Kapasite-bounded, evidence-first yazılım üretim hattı** — *a capacity-bounded, evidence-first software factory.*

KOVAN, yazılım işlerini kapasite hesabıyla kabul eden, her değişikliği
kapı sırasından (policy → tests → provenance → lint → types → review →
eval → cost) geçiren, üretenle onaylayanı ayıran ve her kararı defterine
kanıtla yazan bir hattır. Kuru mod tamamen çevrimdışıdır (sıfır token);
canlı mod yalnızca kendi API anahtarınızla çalışır (BYOK).

## Hızlı başlangıç

```bash
pip install -e fabrika --no-build-isolation   # gömülü Python'da gerekli
cd fabrika/loop
kovan plan          # kapasite planı (kuru, deterministik)
kovan run           # kapı sıralı koşum + defter + SBOM
python retro.py     # haftalık retro + mekanik checkler
```

Detaylı kurulum ve taze klon notu: [fabrika/CONTRIBUTING.md](CONTRIBUTING.md).

## Doküman haritası

| Belge | İçerik |
|---|---|
| [fabrika/SISTEM.md](fabrika/SISTEM.md) | v2 sistem tanımı: 3 hat, bileşen tablosu, 167 test |
| [fabrika/README.md](fabrika/README.md) | 6 ilke (İ1–İ6), dosya haritası, kurulum |
| [fabrika/ADR.md](fabrika/ADR.md) | Mimari karar kayıtları (F01–F13) |
| [fabrika/EVIDENCE-UPDATE.md](fabrika/EVIDENCE-UPDATE.md) | Kanıt güncellemeleri (§1–§18) |
| [CHANGELOG.md](CHANGELOG.md) | Sürüm geçmişi (SemVer) |

## Normlar

- **Üreten ≠ onaylayan (m.2):** sistem kendi onayını kendi kabul edemez.
- **İnsan kapıları (C1/C3):** beceri aktivasyonu ve kırılma giderme insan onayı ister.
- **Fail-closed:** şüphede kapı bloklar, geçmez; kirli git ağacında doğrulama koşmaz.
- **Kanıt:** her koşum defter (JSONL) + SBOM (SPDX 2.3) + gece durum kaydı üretir.

Güvenlik açığı bildirimi: [SECURITY.md](SECURITY.md) — halka açık issue kullanmayın.

## Lisans

Apache-2.0 — bkz. [LICENSE](LICENSE).
