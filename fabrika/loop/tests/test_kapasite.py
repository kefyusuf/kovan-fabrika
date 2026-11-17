"""Kapasite valfi testleri."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kapasite import (  # noqa: E402
    Gorev,
    cakisan_cift,
    inceleme_saati,
    kabul_et,
    kapasite_saat,
    mm1_gecikme,
    wip_limiti,
)


class IncelemeSaatiTest(unittest.TestCase):
    def test_400_loc_bir_saat_eder(self):
        # 400/500 = 0.8 + 0.25 baglam = 1.05
        self.assertAlmostEqual(inceleme_saati(400), 1.05, places=3)

    def test_sifir_loc_sadece_baglam(self):
        self.assertAlmostEqual(inceleme_saati(0), 0.25, places=3)

    def test_negatif_loc_reddedilir(self):
        with self.assertRaises(ValueError):
            inceleme_saati(-1)


class KapasiteTest(unittest.TestCase):
    def test_iki_inceleyici_uc_saat(self):
        self.assertEqual(kapasite_saat(2, 3), 6)

    def test_negatif_girdi(self):
        with self.assertRaises(ValueError):
            kapasite_saat(-1, 3)


class KuyrukTest(unittest.TestCase):
    def test_lambda_8_mu_10(self):
        # Wq = rho / (mu - lam) gun = 0.8/2 = 0.4 gun = 9.6 saat
        self.assertAlmostEqual(mm1_gecikme(8, 10), 9.6, places=2)

    def test_dort_saat_esigi_rho_0625(self):
        self.assertAlmostEqual(mm1_gecikme(6.25, 10), 4.0, places=2)

    def test_19_saat_rho_0888(self):
        self.assertAlmostEqual(mm1_gecikme(8.878, 10), 19.0, places=1)

    def test_doygun_sistem_sonsuz(self):
        self.assertTrue(math.isinf(mm1_gecikme(10, 10)))
        self.assertTrue(math.isinf(mm1_gecikme(12, 10)))

    def test_sifir_mu_hata(self):
        with self.assertRaises(ValueError):
            mm1_gecikme(1, 0)


class WipTest(unittest.TestCase):
    def test_little_yasasi(self):
        self.assertEqual(wip_limiti(1.0, 8), 8)
        self.assertEqual(wip_limiti(0.5, 8), 4)

    def test_negatif(self):
        with self.assertRaises(ValueError):
            wip_limiti(-1, 8)


class CakismaTest(unittest.TestCase):
    def test_sekiz_pr(self):
        self.assertAlmostEqual(cakisan_cift(8), 28 * 0.198, places=3)

    def test_tek_pr(self):
        self.assertEqual(cakisan_cift(1), 0.0)


class KabulTest(unittest.TestCase):
    def test_oncelik_ve_kapasite(self):
        gorevler = [
            Gorev("K-101", 40, 1),
            Gorev("K-102", 320, 1),
            Gorev("K-103", 120, 2),
            Gorev("K-104", 600, 2),
            Gorev("K-105", 200, 3),
            Gorev("K-106", 90, 3),
        ]
        karar = kabul_et(gorevler, kapasite=3.0)

        self.assertEqual([g.id for g in karar.kabul], ["K-101", "K-102", "K-103", "K-106", "K-105"])
        self.assertEqual([g.id for g in karar.ertelenen], ["K-104"])
        self.assertLessEqual(karar.kullanilan_saat, 3.0)

    def test_bagimlilik_karsilanmazsa_ertelenir(self):
        gorevler = [
            Gorev("A", 900, 1),  # 2.05 saat, sigmaz
            Gorev("B", 40, 2, bagimlilik=("A",)),
        ]
        karar = kabul_et(gorevler, kapasite=1.0)

        self.assertEqual(karar.kabul, [])
        self.assertEqual([g.id for g in karar.ertelenen], ["A", "B"])

    def test_wip_limiti_uygulanir(self):
        gorevler = [Gorev(f"T{i}", 10, 1) for i in range(5)]
        karar = kabul_et(gorevler, kapasite=10.0, wip=2)

        self.assertEqual(len(karar.kabul), 2)
        self.assertEqual(len(karar.ertelenen), 3)

    def test_sifir_kapasite(self):
        karar = kabul_et([Gorev("T1", 10, 1)], kapasite=0.0)

        self.assertEqual(karar.kabul, [])
        self.assertEqual(karar.doluluk, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
