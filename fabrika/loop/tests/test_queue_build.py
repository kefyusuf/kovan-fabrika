"""Kanitli is onerisi ureticisi testleri."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import queue_build  # noqa: E402
import yaml  # noqa: E402


def _kur(tmp: Path):
    runs = tmp / "runs"
    d = runs / "ornek-01"
    d.mkdir(parents=True)
    ders = [
        {"task": "A", "gate": "tests", "detail": "başarısız", "fingerprint": "f1", "seen": 1},
        {"task": "B", "gate": "tests", "detail": "başarısız", "fingerprint": "f1", "seen": 1},
        {"task": "C", "gate": "tests", "detail": "başarısız", "fingerprint": "f1", "seen": 1},
    ]
    (d / "lessons.jsonl").write_text("\n".join(json.dumps(k) for k in ders) + "\n", encoding="utf-8")
    ozet = {"accepted": 2, "blocked": 0, "ertelenen": [], "doluluk": 0.9}
    (d / "ozet.json").write_text(json.dumps(ozet), encoding="utf-8")

    vd = tmp / "vardiya-runs" / "v1"
    vd.mkdir(parents=True)
    kirilma = {"payload": {"type": "kirilma_raporu", "veri": {"kirilma_senaryolari": ["tasarim_hatasi"]}}}
    (vd / "ledger.jsonl").write_text(json.dumps(kirilma) + "\n", encoding="utf-8")
    return runs, vd


class KuyrukUretTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.runs, self.vd = _kur(self.tmp)

    def tearDown(self):
        self._t.cleanup()

    def test_tekrar_eden_ders_onerisi(self):
        liste = queue_build.oneriler(self.runs, self.vd)
        c1 = [o for o in liste if o["sinif"] == "C1" and "test" in o["baslik"].lower()]
        self.assertTrue(c1)
        self.assertEqual(c1[0]["kanit"]["seen"], 3)

    def test_kirilma_c3_onerisi(self):
        liste = queue_build.oneriler(self.runs, self.tmp / "vardiya-runs")
        c3 = [o for o in liste if o["sinif"] == "C3"]
        self.assertTrue(c3)
        self.assertIn("tasarim_hatasi", c3[0]["baslik"])

    def test_yuksek_doluluk_onerisi(self):
        liste = queue_build.oneriler(self.runs, self.vd)
        self.assertTrue(any("kapasite" in o["baslik"].lower() for o in liste))

    def test_yaml_yazilir_ve_onay_alani(self):
        liste = queue_build.oneriler(self.runs, self.vd)
        y, _ = queue_build.yaz(liste, self.tmp / "out")
        veri = yaml.safe_load(y.read_text(encoding="utf-8"))
        self.assertTrue(all("gerekce" in i for i in veri["isler"]))
        self.assertTrue((self.tmp / "out" / "oneri-raporu.md").exists())

    def test_bos_veri_onerisiz(self):
        bos = self.tmp / "bosluk"
        bos.mkdir()
        liste = queue_build.oneriler(bos, self.tmp / "v")
        self.assertEqual(liste, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)