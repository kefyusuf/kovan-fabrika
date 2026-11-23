"""Operasyon simülasyonu testleri — hızlı (kısa gün) ve deterministik."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import simulasyon  # noqa: E402

REPO = simulasyon.BURASI / "ornek-repo"


class SimulasyonTest(unittest.TestCase):
    def _kos(self, tmp: Path, gun: int, seed: int, saat: float = 3.0) -> dict:
        sim = Path(tmp) / f"sim-{gun}-{seed}"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            kod = simulasyon.ana(
                ["--gun", str(gun), "--seed", str(seed), "--saat", str(saat), "--out", str(sim)]
            )
        self.assertEqual(kod, 0)
        return json.loads((sim / "simulasyon-ozeti.json").read_text(encoding="utf-8")), sim

    def test_3_gun_artefakt_uretir(self):
        with tempfile.TemporaryDirectory() as tmp:
            sonuc, sim = self._kos(Path(tmp), 3, 7)
            self.assertTrue((sim / "simulasyon-raporu.md").exists())
            self.assertTrue((sim / "simulasyon-ozeti.json").exists())
            self.assertEqual(len(sonuc["gunluk"]), 3)
            self.assertTrue((sim / "reports").exists())  # retro çıktısı

    def test_deterministik(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, _ = self._kos(Path(tmp), 3, 7)
        with tempfile.TemporaryDirectory() as tmp:
            b, _ = self._kos(Path(tmp), 3, 7)
        self.assertEqual(a["toplam_kabul"], b["toplam_kabul"])
        self.assertEqual(
            [g["kabul"] for g in a["gunluk"]], [g["kabul"] for g in b["gunluk"]]
        )

    def test_kriz_gunu_valf_calisir(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, _ = self._kos(Path(tmp), 4, 7)  # gün 4: saat yarıya düşer
            gun4 = next(g for g in s["gunluk"] if g["gun"] == 4)
            self.assertLess(gun4["saat"], 3.0)

    def test_gercek_repo_dokunulmaz(self):
        once = (REPO / "sicaklik.py").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            self._kos(Path(tmp), 3, 7)
        sonra = (REPO / "sicaklik.py").read_text(encoding="utf-8")
        self.assertEqual(once, sonra)

    def test_rotasyon_geceleri_yazar(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, sim = self._kos(Path(tmp), 2, 7)
            gecmis = sim / "vardiya" / "kaynak-gecmisi.jsonl"
            self.assertTrue(gecmis.exists())
            satirlar = [json.loads(s) for s in gecmis.read_text(encoding="utf-8").splitlines() if s]
            self.assertGreater(len(satirlar), 0)
            self.assertIn("kaynak", satirlar[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)