"""Dogrulama katmani testleri - gercek git deposu (ornek-repo) uzerinde."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verify import repo_gecerli_mi, sinyaller, uygula  # noqa: E402

REPO = Path(__file__).resolve().parent.parent / "ornek-repo"
KOMUT = "python -m unittest discover -s tests -t ."

YESIL = """--- a/tests/test_yeni.py
+++ b/tests/test_yeni.py
@@ -0,0 +1,8 @@
+from __future__ import annotations
+import unittest
+from sicaklik import celsius_fahrenheit
+
+class YeniTest(unittest.TestCase):
+    def test_50(self):
+        self.assertAlmostEqual(celsius_fahrenheit(50), 122.0)
+
+if __name__ == "__main__":
+    unittest.main()
"""

KIRMIZI = """--- a/tests/test_kirik.py
+++ b/tests/test_kirik.py
@@ -0,0 +1,8 @@
+from __future__ import annotations
+import unittest
+from sicaklik import celsius_fahrenheit
+
+class KirikTest(unittest.TestCase):
+    def test_yanlis(self):
+        self.assertAlmostEqual(celsius_fahrenheit(50), 999.0)
+
+if __name__ == "__main__":
+    unittest.main()
"""


class DogrulaTest(unittest.TestCase):
    def test_repo_gecerli(self):
        self.assertTrue(repo_gecerli_mi(REPO))

    def test_yesil_yama_tests_true(self):
        s = sinyaller(REPO, YESIL, KOMUT)
        self.assertTrue(s["tests"], s.get("not", ""))

    def test_kirmizi_yama_tests_false(self):
        s = sinyaller(REPO, KIRMIZI, KOMUT)
        self.assertFalse(s["tests"])

    def test_uygulanamaz_yama_tests_false(self):
        s = sinyaller(REPO, "--- a/yok/olmayan.py\n+++ b/yok/olmayan.py\n@@ -1 +1 @@\n-x\n+y\n", KOMUT)
        self.assertFalse(s["tests"])
        self.assertIn("uygulanamaz", s["not"])

    def test_bos_diff_fail_closed(self):
        s = sinyaller(REPO, "", KOMUT)
        self.assertFalse(s["tests"])

    def test_depo_geri_alinmis(self):
        kod = subprocess.run(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(kod, "")

    def test_geri_al_cli(self):
        kod = subprocess.run(
            [sys.executable, "verify.py", "--repo", str(REPO), "--rollback"],
            capture_output=True, text=True, cwd=str(REPO.parent),
        )
        self.assertEqual(kod.returncode, 0)
        self.assertIn("temiz", kod.stdout)

    def test_kirli_agac_uygulama_reddedilir(self):
        """Yayın güvenliği: commitlenmemiş işi olan ağaçta yama denenmez."""
        with tempfile.TemporaryDirectory() as tmp:
            klon = Path(tmp) / "r"
            subprocess.run(
                ["git", "clone", "--quiet", str(REPO), str(klon)],
                capture_output=True, timeout=120,
            )
            sicaklik = klon / "sicaklik.py"
            sicaklik.write_text(
                sicaklik.read_text(encoding="utf-8") + "\n# kullanici isini kaybetmemeli\n",
                encoding="utf-8",
            )
            ok, neden = uygula(klon, "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b\n")
            self.assertFalse(ok)
            self.assertIn("kirli", neden)
            # İçerik korunmuş olmalı: kullanıcının işi yerinde.
            self.assertIn("kullanici isini kaybetmemeli", sicaklik.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)