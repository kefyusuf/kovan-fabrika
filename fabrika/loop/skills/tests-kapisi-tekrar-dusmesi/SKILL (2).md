---
name: tests-kapisi-tekrar-dusmesi
when_to_use: Bir degisiklik tests/ altini değiştiriyorsa (assertion silme/zayıflatma taraması)
version: 0.2.0
status: active
evidence: [K-106, K-102, canli-deneme]
tests: tests/skills/test_tests_kapisi.py
onay: kurucu (ask_user onayi, 2026-11-05)
---

## Semptom
`tests` kapısı ayni nedenle tekrar düşüyor: kodu geçirmek için test
silinmesi veya assertion zayıflatması. Kapı yeşil, davranış bozuk.

## Prosedür
1. Diff'te tests/ altı dosyalara bak (beceri.test_zayiflatma_tespiti).
2. Assertion silindiyse veya `assert True` gibi zayıf desen varsa: RET.
3. Test dosyası silinmişse: RET.
4. Meşru düzenleme (assert değiş tokuşu) ise: geç, gerekçeyi yaz.

## Doğrulama
`python tests/skills/test_tests_kapisi.py` — 5 vaka (silme, zayıflatma,
takas, tests/ dışı, dosya silme).

## Sınırlar
- Kapsam artışını ölçmez (satır sayısı yanıltıcıdır); **mutation testi devrede: mutasyon.py** (yapı imzalı mutantlar, eval+test öldürme skoru ölçülür).

<!-- aktiflesme: 2026-11-04 · onay: kurucu (ask_user onayi, 2026-11-05) -->
