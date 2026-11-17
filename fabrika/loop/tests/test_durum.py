"""durum komutu testleri."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import kovan  # noqa: E402


class DurumTest(unittest.TestCase):
    def _kos(self, tmp, run_id, kabul, blok, doluluk):
        d = Path(tmp) / "runs" / run_id
        d.mkdir(parents=True)
        ozet = {
            "run_id": run_id, "accepted": kabul, "blocked": blok, "rejected": 0,
            "revised": 0, "ertelenen": ["X"], "insan_kuyrugu": [], "doluluk": doluluk,
            "defter": {"ok": True, "kayit": 1},
        }
        (d / "ozet.json").write_text(json.dumps(ozet), encoding="utf-8")
        (d / "lessons.jsonl").write_text(
            json.dumps({"task": run_id, "gate": "tests", "detail": "d", "fingerprint": "fp1", "seen": 1}) + "\n",
            encoding="utf-8",
        )

    def calistir(self, tmp, *ek: str) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            kovan.main(["durum", "--runs", str(Path(tmp) / "runs"), "--vardiya-runs", str(Path(tmp) / "v"), *ek])
        return buf.getvalue()

    def test_bos_runs_sifir(self):
        with tempfile.TemporaryDirectory() as tmp:
            cikti = self.calistir(tmp)
            self.assertIn("Koşu          : 0", cikti)

    def test_toplamlar_dogru(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._kos(tmp, "a", 2, 1, 0.8)
            self._kos(tmp, "b", 3, 0, 0.6)
            cikti = self.calistir(tmp)
            self.assertIn("Koşu          : 2", cikti)
            self.assertIn("5 / 1", cikti)
            self.assertIn("tests", cikti)

    def test_json_mod(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._kos(tmp, "a", 1, 0, 0.5)
            cikti = self.calistir(tmp, "--json")
            d = json.loads(cikti)
            self.assertEqual(d["kosu_sayisi"], 1)
            self.assertEqual(d["toplam_kabul"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)