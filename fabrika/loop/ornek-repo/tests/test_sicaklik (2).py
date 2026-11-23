"""ornek-repo testleri — başlangıçta yeşil."""

from __future__ import annotations

import unittest

from sicaklik import celsius_fahrenheit, fahrenheit_celsius, ortalama


class SicaklikTest(unittest.TestCase):
    def test_donme_noktasi(self):
        self.assertAlmostEqual(celsius_fahrenheit(0), 32.0)

    def test_kaynama_noktasi(self):
        self.assertAlmostEqual(celsius_fahrenheit(100), 212.0)

    def test_tersi_donusum(self):
        self.assertAlmostEqual(fahrenheit_celsius(celsius_fahrenheit(37)), 37.0, places=6)

    def test_bos_liste_hata(self):
        with self.assertRaises(ValueError):
            ortalama([])


if __name__ == "__main__":
    unittest.main()
