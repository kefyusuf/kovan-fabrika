"""S1 runbook tatbikatı testleri."""

from __future__ import annotations

import io
import json
import contextlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tatbikat  # noqa: E402


class TatbikatTest(unittest.TestCase):
    def test_bes_adim_gecer(self):
        sonuc = tatbikat.tatbikat()
        self.assertTrue(sonuc["gecildi"], sonuc["adimlar"])
        self.assertEqual(len(sonuc["adimlar"]), 5)
        for a in sonuc["adimlar"]:
            self.assertTrue(a["gecti"], a)

    def test_a3_stop_dosyasi_onur_eslenir(self):
        sonuc = tatbikat.tatbikat()
        a3 = next(a for a in sonuc["adimlar"] if a["ad"] == "A3 durdurma")
        self.assertTrue(a3["gecti"])
        self.assertIn("insan_durdurdu", a3["not"])

    def test_json_cikti_alanlari(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            kod = tatbikat.ana(["--json"])
        self.assertEqual(kod, 0)
        d = json.loads(buf.getvalue())
        self.assertIn("gecildi", d)
        self.assertEqual(len(d["adimlar"]), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)