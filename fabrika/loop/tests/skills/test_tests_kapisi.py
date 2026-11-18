"""tests-kapisi-tekrar-dusmesi becerisinin doğrulama testleri (5 vaka)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from skill import test_zayiflatma_tespiti  # noqa: E402


class TespitTest(unittest.TestCase):
    def test_silme_ihlal(self):
        diff = (
            "--- a/tests/test_x.py\n+++ b/tests/test_x.py\n@@ -1,3 +1,2 @@\n"
            " import os\n-    self.assertEqual(a, b)\n"
        )
        s = test_zayiflatma_tespiti(diff)
        self.assertTrue(s["ihlal"])
        self.assertIn("silindi", s["neden"])

    def test_zayiflatma_ihlal(self):
        diff = (
            "--- a/tests/test_x.py\n+++ b/tests/test_x.py\n@@ -1,3 +1,3 @@\n"
            "-    self.assertEqual(a, b)\n+    self.assertTrue(True)\n"
        )
        s = test_zayiflatma_tespiti(diff)
        self.assertTrue(s["ihlal"])
        self.assertIn("zayıflatıldı", s["neden"])

    def test_takas_ihlal_degil(self):
        diff = (
            "--- a/tests/test_x.py\n+++ b/tests/test_x.py\n@@ -1,3 +1,3 @@\n"
            "-    self.assertEqual(a, b)\n+    self.assertEqual(b, a)\n"
        )
        self.assertFalse(test_zayiflatma_tespiti(diff)["ihlal"])

    def test_tests_disi_etkisiz(self):
        diff = (
            "--- a/src/x.py\n+++ b/src/x.py\n@@ -1,2 +1,2 @@\n"
            "-import os\n+import sys\n"
        )
        self.assertFalse(test_zayiflatma_tespiti(diff)["ihlal"])

    def test_dosya_silme_ihlal(self):
        diff = (
            "diff --git a/tests/eski.py b/tests/eski.py\ndeleted file mode 100644\n"
            "--- a/tests/eski.py\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-    assert x\n"
        )
        s = test_zayiflatma_tespiti(diff)
        self.assertTrue(s["ihlal"])
        self.assertIn("silindi", s["neden"])


if __name__ == "__main__":
    unittest.main(verbosity=2)