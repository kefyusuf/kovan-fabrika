# ADR Taslağı (otomatik öneri — C3, insan onayı bekler)

**Bağlam.** Defter istatistiği: {"accepted": 79, "blocked": 17, "revise": 23} · en çok düşen kapı: `policy`.

**Öneri.** `policy` kapısının ret nedenlerinin tekrarını azaltacak
beceri adayına öncelik ver (varsa). Kadro/eşik değişikliği önerilmez.

**Ölçüm planı.** 2 hafta boyunca aynı kapının ilk tur ret oranı;
başarı ölçütü: %15 görece düşüş. Ölçülemezse öneri reddedilir.
