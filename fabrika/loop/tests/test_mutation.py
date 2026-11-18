"""Mutasyon testi testleri — küçük maks ile hızlı."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mutation  # noqa: E402

REPO = mutation.BURASI / "ornek-repo"
SET = mutation.BURASI / "eval_set" / "sicaklik-v1.jsonl"
KOMUT = "python -m unittest discover -s tests -t ."


class MutasyonTest(unittest.TestCase):
    def test_mutasyon_skoru_tam(self):
        s = mutation.kos(REPO, SET, KOMUT, maks=3)
        self.assertEqual(s["denenen"], 3)
        self.assertEqual(s["olen"], 3)
        self.assertEqual(s["mutasyon_skoru"], 1.0)

    def test_rapor_alanlari(self):
        s = mutation.kos(REPO, SET, KOMUT, maks=2)
        self.assertIn("aday_sayisi", s)
        self.assertIn("hayatta_kalanlar", s)
        for k in s["mutantlar"]:
            self.assertIn("olduren", k)
            self.assertIn("eval_skor", k)
            self.assertIn("testler_gecti", k)

    def test_maks_limiti(self):
        s = mutation.kos(REPO, SET, KOMUT, maks=1)
        self.assertEqual(s["denenen"], 1)

    def test_gercek_repo_dokunulmaz(self):
        once = (REPO / "sicaklik.py").read_text(encoding="utf-8")
        mutation.kos(REPO, SET, KOMUT, maks=2)
        sonra = (REPO / "sicaklik.py").read_text(encoding="utf-8")
        self.assertEqual(once, sonra)


if __name__ == "__main__":
    unittest.main(verbosity=2)