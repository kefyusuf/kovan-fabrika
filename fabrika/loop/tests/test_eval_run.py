"""Eval v1 kosucusu testleri — gercek ornek-repo uzerinde."""

from __future__ import annotations

import difflib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval_run import run_eval  # noqa: E402

REPO = Path(__file__).resolve().parent.parent / "ornek-repo"
HEDEF = REPO / "sicaklik.py"  # diff üretimi için salt-okunur kaynak (testler KLON üzerinde koşar)
SET = Path(__file__).resolve().parent.parent / "eval_set" / "sicaklik-v1.jsonl"


def _diff(yeni_metin: str) -> str:
    eski = HEDEF.read_text(encoding="utf-8").splitlines(keepends=True)
    yeni = yeni_metin.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(eski, yeni, fromfile="a/sicaklik.py", tofile="b/sicaklik.py", lineterm="\n")
    )


KIRIK = _diff(
    '"""Sıcaklık dönüşüm örnek modülü (KOVAN ornek-repo)."""\n'
    "\n\n"
    "def celsius_fahrenheit(c: float) -> float:\n"
    "    return c * 9 / 5 + 33\n"
    "\n\n"
    "def fahrenheit_celsius(f: float) -> float:\n"
    "    return (f - 32) * 5 / 9\n"
    "\n\n"
    "def ortalama(degerler: list[float]) -> float:\n"
    "    if not degerler:\n"
    '        raise ValueError("boş liste")\n'
    "    return sum(degerler) / len(degerler)\n"
)


class EvalRunTest(unittest.TestCase):
    def setUp(self):
        # Gerçek ornek-repo'ya dokunma: her test geçici KLON üzerinde koşar.
        self._t = tempfile.TemporaryDirectory()
        klon = Path(self._t.name) / "r"
        subprocess.run(
            ["git", "clone", "--quiet", str(REPO), str(klon)],
            capture_output=True, text=True, timeout=120,
        )
        self.REPO = klon

    def tearDown(self):
        self._t.cleanup()

    def test_baseline_full_score(self):
        s = run_eval(self.REPO, SET)
        self.assertEqual(s["skor"], 1.0)
        self.assertEqual(s["toplam"], 90)

    def test_green_diff_no_effect(self):
        # Geçerli unified diff: dosyanın sonuna yalnızca bir gözlem satırı.
        mevcut = (self.REPO / "sicaklik.py").read_text(encoding="utf-8")
        s = run_eval(self.REPO, SET, _diff(mevcut + "# gozlem: eval v1\n"))
        self.assertEqual(s["skor"], 1.0)

    def test_broken_diff_drops_score(self):
        s = run_eval(self.REPO, SET, KIRIK)
        self.assertLess(s["skor"], 0.9)
        self.assertGreater(len(s["hatalar"]), 0)

    def test_inapplicable_diff_zero(self):
        s = run_eval(self.REPO, SET, "--- a/yok/olmayan.py\n+++ b/yok/olmayan.py\n@@ -1 +1 @@\n-x\n+y\n")
        self.assertEqual(s["skor"], 0.0)
        self.assertIn("uygulanamaz", s.get("hata", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)