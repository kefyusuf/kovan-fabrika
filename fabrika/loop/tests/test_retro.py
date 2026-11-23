"""Haftalık retro testleri."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import retro  # noqa: E402


def _kur(tmp: Path):
    runs = tmp / "runs"
    d = runs / "ornek-01"
    d.mkdir(parents=True)
    kararlar = [
        {"payload": {"type": "decision", "task": "A", "kind": "accepted"}},
        {"payload": {"type": "decision", "task": "B", "kind": "revise"}},
        {"payload": {"type": "decision", "task": "B", "kind": "rejected"}},
    ]
    (d / "ledger.jsonl").write_text(
        "\n".join(json.dumps(k) for k in kararlar) + "\n", encoding="utf-8"
    )
    (d / "lessons.jsonl").write_text(
        json.dumps({"task": "B", "gate": "tests", "detail": "başarısız", "fingerprint": "f1", "seen": 1}) + "\n"
        + json.dumps({"task": "A", "gate": "tests", "detail": "başarısız", "fingerprint": "f1", "seen": 1}) + "\n",
        encoding="utf-8",
    )
    (d / "ozet.json").write_text(
        json.dumps({"accepted": 1, "blocked": 0, "ertelenen": ["X", "Y"], "doluluk": 0.8}),
        encoding="utf-8",
    )
    return runs


class RetroTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.runs = _kur(self.tmp)

    def tearDown(self):
        self._t.cleanup()

    def test_gpk_vekili_dogru(self):
        g = retro.gpk_hesapla([self.runs / "ornek-01" / "ledger.jsonl"])
        self.assertEqual(g["gorev"], 2)
        self.assertEqual(g["ilk_tur_kabul"], 1)
        self.assertEqual(g["gpk"], 0.5)

    def test_run_bazli_gpk_kosulari_karistirmaz(self):
        """Aynı görev iki koşuda farklı sonuç alırsa her koşum ayrı sayılır."""
        d2 = self.runs / "ornek-02"
        d2.mkdir(parents=True)
        (d2 / "ledger.jsonl").write_text(
            json.dumps({"payload": {"type": "decision", "task": "A", "kind": "rejected"}}) + "\n",
            encoding="utf-8",
        )
        g = retro.gpk_hesapla(
            [self.runs / "ornek-01" / "ledger.jsonl", d2 / "ledger.jsonl"]
        )
        self.assertEqual(g["gorev"], 3)  # (ornek-01,A) (ornek-01,B) + (ornek-02,A)
        self.assertEqual(g["ilk_tur_kabul"], 1)
        self.assertEqual(g["gpk"], round(1 / 3, 3))

    def test_mekanik_check_tests_tetiklenir(self):
        s = retro.uret(self.runs, self.tmp / "v", self.tmp / "out")
        komutlar = [c["komut"] for c in s["checkler"]]
        self.assertTrue(any("test_tests_kapisi" in k for k in komutlar), komutlar)

    def test_ertelenen_check_komutlu(self):
        s = retro.uret(self.runs, self.tmp / "v", self.tmp / "out")
        self.assertTrue(any(c["tetik"].startswith("2 iş ertelendi") for c in s["checkler"]))

    def test_rapor_dosyasi_bes_bolumlu(self):
        s = retro.uret(self.runs, self.tmp / "v", self.tmp / "out")
        icerik = Path(s["dosya"]).read_text(encoding="utf-8")
        for baslik in ("GPK", "Kapı trendi", "Beceri durumu", "Mekanik checkler", "Dürüstlük"):
            self.assertIn(baslik, icerik)

    def test_bos_veri_durustlugu(self):
        bos = self.tmp / "bosluk"
        bos.mkdir()
        s = retro.uret(bos, self.tmp / "v", self.tmp / "out")
        self.assertEqual(s["gpk"]["gorev"], 0)
        self.assertGreaterEqual(len(s["checkler"]), 1)  # rutin bakım komutu


class LogSaglikTest(unittest.TestCase):
    """§15 dersi: artefakt var ≠ kosu basarili — log butunlugu mekanik kontrol."""

    def test_temiz_loglar_bozuk_listesi_bos(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "runs"
            runs.mkdir()
            (runs / "gece-1.log").write_text("Kabul: 4 is\nDefter: OK\n", encoding="utf-8")
            sonuc = retro.log_saglik(runs)
            self.assertEqual(sonuc, {"taranan": 1, "bozuk": []})

    def test_traceback_iceren_log_yakalanir(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "runs"
            runs.mkdir()
            (runs / "gece-1.log").write_text(
                "Traceback (most recent call last):\nUnicodeEncodeError: charmap\n",
                encoding="utf-8",
            )
            (runs / "gece-2.log").write_text("temiz\n", encoding="utf-8")
            sonuc = retro.log_saglik(runs)
            self.assertEqual(sonuc["taranan"], 2)
            self.assertEqual(sonuc["bozuk"], ["gece-1.log"])

    def test_utf16_eski_powerShell_logu_yakalanir(self):
        """PS 5.1 varsayılan Out-File UTF-16 yazar — BOM algılanmalı."""
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "runs"
            runs.mkdir()
            (runs / "eski.log").write_text(
                "Traceback (most recent call last):\n", encoding="utf-16"
            )
            sonuc = retro.log_saglik(runs)
            self.assertEqual(sonuc["bozuk"], ["eski.log"])

    def test_uret_log_bozugu_check_uretir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runs = tmp_path / "runs"
            runs.mkdir()
            (runs / "gece-bozuk.log").write_text("Traceback: x\n", encoding="utf-8")
            out = tmp_path / "out"
            sonuc = retro.uret(runs, tmp_path / "vr", out, bugun=datetime(2026, 11, 16, tzinfo=timezone.utc))
            self.assertEqual(sonuc["istatik"]["log_bozuk"], 1)
            checkler = [c for c in sonuc["checkler"] if "--log-health" in c["komut"]]
            self.assertTrue(checkler, "bozuk log varken --log-health checki uretilmedi")

    def test_cli_log_saglik_cikis_kodu(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runs = tmp_path / "runs"
            runs.mkdir()
            self.assertEqual(retro.ana(["--log-health", "--runs", str(runs), "--out", str(tmp_path)]), 0)
            (runs / "bozuk.log").write_text("Traceback: x\n", encoding="utf-8")
            self.assertEqual(retro.ana(["--log-health", "--runs", str(runs), "--out", str(tmp_path)]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)