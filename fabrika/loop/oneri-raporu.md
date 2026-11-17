# İş Önerileri — kanıtlı

## O-01 — tests kapısı tekrarını azaltacak beceri kapsamı

- Sınıf: **C1** · LOC: 120 · Öncelik: 2
- Gerekçe: Aynı hata sınıfı 3 kez tekrar etti; beceri kapsamı genişletilmeli.
- Kanıt: `{"fingerprint": "46094f01273b", "seen": 3, "gate": "tests"}`

## O-02 — Canlı profilde yakalanmayan türler için kapı: tasarim_hatasi

- Sınıf: **C3** · LOC: 80 · Öncelik: 1
- Gerekçe: Kırmızı takım, canlı profilin bu hata türlerini kaçırdığını ölçtü.
- Kanıt: `{"canli_profili": 0.9444, "kirilma_senaryolari": ["tasarim_hatasi"], "tam_kapsam": 1.0, "tekrar_kapsam": ["H08", "H09", "H10", "H11", "H12", "H13", "H18"]}`

