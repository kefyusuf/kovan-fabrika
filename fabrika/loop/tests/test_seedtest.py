"""Tohumlanmis hata kosucusu testleri."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seedtest import Hata, Kapi, kos, varsayilan_hatalar, varsayilan_kapilar  # noqa: E402


class KapsamTest(unittest.TestCase):
    def test_tam_set_hepsini_yakalar(self):
        rapor = kos(varsayilan_hatalar(), varsayilan_kapilar())

        self.assertEqual(rapor.toplam, 18)
        self.assertEqual(rapor.yakalanan, 18)
        self.assertEqual(rapor.yakalama_orani, 1.0)
        self.assertEqual(rapor.kacan, [])

    def test_testsiz_set_test_zayiflatmayi_kacirir(self):
        kapilar = [k for k in varsayilan_kapilar() if k.ad != "tests"]
        rapor = kos(varsayilan_hatalar(), kapilar)

        kacan_turler = {h.tur for h in rapor.kacan}
        self.assertIn("test_zayiflatma", kacan_turler)
        self.assertIn("test_yok", kacan_turler)
        self.assertLess(rapor.yakalama_orani, 1.0)

    def test_incelemesiz_set_tasarim_hatasini_kacirir(self):
        kapilar = [k for k in varsayilan_kapilar() if k.ad != "review"]
        rapor = kos(varsayilan_hatalar(), kapilar)

        self.assertEqual({h.tur for h in rapor.kacan}, {"tasarim_hatasi"})

    def test_politikasiz_set_sir_okumayi_kacirir(self):
        kapilar = [k for k in varsayilan_kapilar() if k.ad != "policy"]
        rapor = kos(varsayilan_hatalar(), kapilar)

        self.assertEqual({h.tur for h in rapor.kacan}, {"sir_okuma"})

    def test_sadece_deterministik_yarisini_yakalar(self):
        kapilar = [k for k in varsayilan_kapilar() if k.ad in {"lint", "types", "tests"}]
        rapor = kos(varsayilan_hatalar(), kapilar)

        self.assertLessEqual(rapor.yakalama_orani, 0.55)

    def test_kapi_yoksa_hicbiri_yakalanmaz(self):
        rapor = kos(varsayilan_hatalar(), [])

        self.assertEqual(rapor.yakalanan, 0)
        self.assertEqual(len(rapor.kacan), 18)


class TekrarTest(unittest.TestCase):
    def test_ayni_hatayi_iki_kapi_yakalarsa_tekrar_isaretlenir(self):
        rapor = kos(varsayilan_hatalar(), varsayilan_kapilar())

        self.assertIn("H10", rapor.tekrar_kapsam)  # kapsam_disi: policy + review
        self.assertEqual(set(rapor.tekrar_kapsam["H10"]), {"policy", "review"})

    def test_tekrar_kapsam_yakalama_oranini_artirmaz(self):
        hatalar = [Hata("X", "sir_okuma", "test")]
        tek = [Kapi("policy", frozenset({"sir_okuma"}))]
        cift = tek + [Kapi("policy2", frozenset({"sir_okuma"}))]

        self.assertEqual(kos(hatalar, tek).yakalama_orani, 1.0)
        self.assertEqual(kos(hatalar, cift).yakalama_orani, 1.0)
        self.assertEqual(kos(hatalar, cift).tekrar_kapsam["X"], ["policy", "policy2"])


class RaporTest(unittest.TestCase):
    def test_ozet_alanlari(self):
        rapor = kos(varsayilan_hatalar(), varsayilan_kapilar()).ozet()

        self.assertEqual(
            set(rapor), {"toplam", "yakalanan", "yakalama_orani", "kacan", "kapi_basina", "tekrar_kapsam"}
        )
        self.assertEqual(rapor["kacan"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
