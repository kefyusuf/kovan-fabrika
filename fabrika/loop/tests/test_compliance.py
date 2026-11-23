"""Uyum katmanı (provenance sinyali) testleri."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compliance import extract_dependencies, has_dependency_change, scan_copy_blocks, signal  # noqa: E402

REPO = Path(__file__).resolve().parent.parent / "ornek-repo"

STDLIB_DIFF = (
    "--- a/src/x.py\n+++ b/src/x.py\n@@ -1,2 +1,4 @@\n"
    "+import json\n"
    "+from pathlib import Path\n"
    " import os\n"
)
UCUNCU_DIFF = (
    "--- a/src/x.py\n+++ b/src/x.py\n@@ -1,2 +1,3 @@\n"
    "+import requests\n"
    " import os\n"
)
REQ_DIFF = (
    "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -1 +1,2 @@\n"
    "+requests==2.0.0\n"
)


class ExtractionTest(unittest.TestCase):
    def test_import_roots(self):
        self.assertEqual(extract_dependencies(STDLIB_DIFF), {"json", "pathlib"})
        self.assertEqual(extract_dependencies(UCUNCU_DIFF), {"requests"})

    def test_deleted_lines_not_counted(self):
        self.assertEqual(extract_dependencies("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-import os\n"), set())

    def test_dependency_file_detected(self):
        self.assertTrue(has_dependency_change(REQ_DIFF))
        self.assertFalse(has_dependency_change(STDLIB_DIFF))


class SignalTest(unittest.TestCase):
    def test_stdlib_free(self):
        s = signal(STDLIB_DIFF)
        self.assertTrue(s["provenance"])
        self.assertIn("json", s["paketler"])

    def test_unauthorized_third_party_rejected(self):
        s = signal(UCUNCU_DIFF)
        self.assertFalse(s["provenance"])
        self.assertIn("requests", s["paketler"])

    def test_allowlisted_free(self):
        with temp_text_file("paketler:\n  - requests\n") as yol:
            s = signal(UCUNCU_DIFF, yol)
        self.assertTrue(s["provenance"])

    def test_dependency_file_rejected(self):
        s = signal(REQ_DIFF)
        self.assertFalse(s["provenance"])
        self.assertIn("C3", s["not"])

    def test_duplicate_function_detected(self):
        diff = (
            "--- a/src/sicaklik.py\n+++ b/src/sicaklik.py\n@@ -4,2 +4,4 @@\n"
            "+def celsius_fahrenheit(c):\n+    return 0\n"
        )
        s = signal(diff, repo=REPO)
        self.assertIn("celsius_fahrenheit", s["yinelenen_fonksiyon"])

    def test_new_function_not_flagged(self):
        diff = "--- a/src/yeni.py\n+++ b/src/yeni.py\n@@ -0,0 +1,2 @@\n+def tamamen_yeni():\n+    return 1\n"
        s = signal(diff, repo=REPO)
        self.assertEqual(s["yinelenen_fonksiyon"], [])

    def test_copy_suspicion_copyright_header(self):
        diff = (
            "--- a/src/kopya.py\n+++ b/src/kopya.py\n@@ -0,0 +1,3 @@\n"
            "+# Copyright (c) 2026 Baskasi\n+def x():\n+    return 1\n"
        )
        s = signal(diff)
        self.assertFalse(s["provenance"])
        self.assertIn("kopya", s["not"])

    def test_spdx_header_rejected(self):
        diff = (
            "--- a/src/kopya.py\n+++ b/src/kopya.py\n@@ -0,0 +1,3 @@\n"
            "+// SPDX-License-Identifier: MIT\n+def x():\n+    return 1\n"
        )
        s = signal(diff)
        self.assertFalse(s["provenance"])

    def test_clean_diff_no_copy_suspicion(self):
        self.assertFalse(signal(STDLIB_DIFF)["provenance"] is False and "kopya" in signal(STDLIB_DIFF)["not"])

    def test_empty_diff_free(self):
        self.assertTrue(signal("")["provenance"])


class temp_text_file:
    """Küçük içerikli geçici dosya (with ile)."""

    def __init__(self, icerik: str):
        self.icerik = icerik
        self.yol: Path | None = None

    def __enter__(self) -> str:
        import tempfile

        fh = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        fh.write(self.icerik)
        fh.close()
        self.yol = Path(fh.name)
        return str(self.yol)

    def __exit__(self, *a):
        self.yol.unlink(missing_ok=True)
import subprocess


def _git_repo(dizin, dosyalar):
    """Geçici git deposu kurar; kopya tarama testleri için."""
    dizin.mkdir(parents=True)
    for rel, icerik in dosyalar.items():
        p = dizin / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(icerik, encoding="utf-8", newline="\n")
    adimlar = (
        ["init", "-q"],
        ["add", "-A"],
        ["-c", "user.name=k", "-c", "user.email=k@l", "commit", "-q", "-m", "x"],
    )
    for komut in adimlar:
        subprocess.run(["git", *komut], cwd=str(dizin), capture_output=True)
    return dizin


UZUN_FN = (
    "def hesapla(liste):\n"
    '    if not liste:\n'
    '        raise ValueError("bos")\n'
    "    sirali = sorted(liste)\n"
    "    adet = len(sirali)\n"
    "    toplam = 0.0\n"
    "    for deger in sirali:\n"
    "        toplam += float(deger)\n"
    "    ort = toplam / adet\n"
    "    dusuk = sirali[0]\n"
    "    yuksek = sirali[-1]\n"
    "    if adet % 2:\n"
    "        orta = sirali[adet // 2]\n"
    "    else:\n"
    "        orta = (sirali[adet // 2 - 1] + sirali[adet // 2]) / 2\n"
    "    sapma = 0.0\n"
    "    for deger in sirali:\n"
    "        sapma += (deger - ort) ** 2\n"
    "    return sapma / (adet or 1)\n"
)


def _diff_eski_yeni(eski_metin, yeni_metin, yol="a/x.py", yol2="b/x.py"):
    import difflib

    eski = eski_metin.splitlines(keepends=True)
    yeni = yeni_metin.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(eski, yeni, fromfile=yol, tofile=yol2, lineterm="\n")
    )


class CopyBlockTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.repo = _git_repo(Path(self._t.name) / "r", {"uzun.py": UZUN_FN})

    def tearDown(self):
        self._t.cleanup()

    def test_renamed_copy_rejected(self):
        kopya = UZUN_FN.replace("def hesapla", "def hesapla_v2").replace("sirali", "dizi")
        diff = _diff_eski_yeni(UZUN_FN, kopya, "a/uzun.py", "b/uzun.py")
        s = signal(diff, repo=self.repo)
        self.assertFalse(s["provenance"])
        self.assertTrue(s["kopya_blok"])
        self.assertEqual(s["kopya_blok"][0]["fonksiyon"], "hesapla_v2")
        self.assertGreaterEqual(s["kopya_blok"][0]["skor"], 0.90)

    def test_all_copy_variants_caught(self):
        """Dedektör sağlamlığı: kozmetik varyantlar kopyayı gizleyemez.

        Ad değişimi, yorum ekleme, format değişimi, metin sabiti değişimi
        ve satır sırası değişimi — hepsi yapı imzasında yakalanır.
        """

        def kopya(ek=None):
            v = UZUN_FN.replace("def hesapla", "def hesapla_kopya")
            return ek(v) if ek else v

        varyantlar = [
            kopya(),
            kopya(lambda s: s.replace("sirali", "dizi")),
            kopya(lambda s: s.replace("    toplam = 0.0", "    # not\n    toplam = 0.0")),
            kopya(lambda s: s.replace("    ort = toplam / adet", "    ort=toplam/adet")),
            kopya(lambda s: s.replace('raise ValueError("bos")', 'raise ValueError("x")')),
            kopya(lambda s: s.replace(
                "    dusuk = sirali[0]\n    yuksek = sirali[-1]",
                "    yuksek = sirali[-1]\n    dusuk = sirali[0]",
            )),
        ]
        for varyant in varyantlar:
            diff = _diff_eski_yeni(UZUN_FN, varyant, "a/uzun.py", "b/uzun.py")
            bulgular = scan_copy_blocks(self.repo, diff)
            self.assertTrue(bulgular, "varyant yakalanmadı")
            self.assertGreaterEqual(bulgular[0]["skor"], 0.90)

    def test_short_similar_function_info_level(self):
        kopya = UZUN_FN.splitlines()[0] + "\n    return 1\n"
        diff = "--- a/kisa.py\n+++ b/kisa.py\n@@ -0,0 +1,2 @@\n+def kisa(a):\n+    return a\n"
        s = signal(diff, repo=self.repo)
        self.assertTrue(s["provenance"])
        self.assertEqual(s["kopya_blok"], [])

    def test_unrelated_new_function_clean(self):
        ilgisiz = UZUN_FN.replace("hesapla", "bambaska").replace("+", "x")  # yer tutucu
        yeni = (
            "def bambaska(veriler):\n"
            "    sonuc = 0\n"
            "    for v in veriler:\n"
            "        sonuc = sonuc * 3 + len(v)\n"
            "    while sonuc > 1000:\n"
            "        sonuc = sonuc // 2\n"
            "    if sonuc % 7 == 0:\n"
            '        return "yedi"\n'
            "    return sonuc\n"
        )
        diff = "--- a/yeni.py\n+++ b/yeni.py\n@@ -0,0 +1,9 @@\n" + "".join(
            "+" + s for s in yeni.splitlines(keepends=True)
        )
        s = signal(diff, repo=self.repo)
        self.assertTrue(s["provenance"], s["not"])
        self.assertEqual(s["kopya_blok"], [])

    def test_unchanged_function_not_reported(self):
        diff = "--- a/uzun.py\n+++ b/uzun.py\n@@ -1,2 +1,3 @@\n def hesapla(liste):\n+    pass\n"
        s = signal(diff, repo=self.repo)
        self.assertEqual(s["kopya_blok"], [])

if __name__ == "__main__":
    unittest.main(verbosity=2)
