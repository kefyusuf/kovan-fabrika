# KOVAN Operasyon Simülasyonu — 5 gün (seed 7)

> **Dürüstlük:** kuru mod simülasyonu. Model sinyalleri senaryodan;
> kapasite, kapılar, defter, kaynak rotasyonu ve GPK hesabı GERÇEK kod yollarıdır.
> token sayıları gerçek fatura değil, muhasebe alıştırmasıdır.


## 1. Günlük tablo

| Gün | Saat | Kabul | Blok | Ret | Rev. | Ertelenen | Doluluk | Havuz | Gece raporu |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 3.0 | 6 | 1 | 0 | 1 | 13 | 93% | 13 | ✓ |
| 2 | 3.0 | 6 | 1 | 0 | 3 | 13 | 93% | 13 | ✓ |
| 3 | 3.0 | 6 | 1 | 0 | 1 | 13 | 93% | 13 | ✓ |
| 4 | 1.5 | 4 | 1 | 0 | 1 | 15 | 95% | 13 | ✓ |
| 5 | 3.0 | 6 | 1 | 0 | 1 | 13 | 93% | 13 | ✓ |

## 2. Toplamlar

- Toplam kabul: **28** · Toplam token: 139,200 · Kabul başına token (proxy): 4,971.4
- **Run-bazlı GPK: 57%** (16/28 görev-koşu çifti)
- Vardiya raporu: 5 (GHS proxy: her gün ✓)

## 3. Gözlemler

- Gün 4: kapasite yarıya düşünce kabul 4, ertelenen 15 — valf çalışıyor.
- Sır okuma isteği gün 1,2,3,4,5 her seferinde policy kapısında bloklandı — tekrar eden sistematik istek, eğitim değildir.
- - Run-bazlı GPK %57: ilk turda kabul edilmeyen görevler revizyon/erteleme maliyeti üretiyor — test yazarı becerisinin önceliği artmalı.

## 4. Mekanik checkler (retro'dan)

- `python kovan.py plan --saat 3.0` — ertelenenler için ayrı kapasite günü planla

## 5. Canlıya geçişte ne değişir

- Yalnızca `--adapter http` + anahtar: kapasite, kapılar, defter, rotasyon aynı.
- token/maliyet gerçek faturaya döner; GPK/GHS hesapları aynı formüllerle kalır.
- Kırılganlık: model varyansı → ilk tur ret oranı değişebilir; kapılar aynı kalır.
