"""Uyum katmanı (provenance sinyali) testleri."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compliance import bagimlilik_cikar, dosya_degisimi_var, kopya_blok_tara, sinyal  # noqa: E402

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


class CikarimTest(unittest.TestCase):
    def test_import_kokleri(self):
        self.assertEqual(bagimlilik_cikar(STDLIB_DIFF), {"json", "pathlib"})
        self.assertEqual(bagimlilik_cikar(UCUNCU_DIFF), {"requests"})

    def test_silinen_satir_sayilmaz(self):
        self.assertEqual(bagimlilik_cikar("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-import os\n"), set())

    def test_bagimlilik_dosyasi_tespiti(self):
        self.assertTrue(dosya_degisimi_var(REQ_DIFF))
        self.assertFalse(dosya_degisimi_var(STDLIB_DIFF))


class SinyalTest(unittest.TestCase):
    def test_stdlib_serbest(self):
        s = sinyal(STDLIB_DIFF)
        self.assertTrue(s["provenance"])
        self.assertIn("json", s["paketler"])

    def test_ucuncu_taraf_izinsiz_reddedilir(self):
        s = sinyal(UCUNCU_DIFF)
        self.assertFalse(s["provenance"])
        self.assertIn("requests", s["paketler"])

    def test_izin_listesiyle_serbest(self):
        with tempfile_dosya("paketler:\n  - requests\n") as yol:
            s = sinyal(UCUNCU_DIFF, yol)
        self.assertTrue(s["provenance"])

    def test_bagimlilik_dosyasi_reddedilir(self):
        s = sinyal(REQ_DIFF)
        self.assertFalse(s["provenance"])
        self.assertIn("C3", s["not"])

    def test_yinelenen_fonksiyon_tespit_edilir(self):
        diff = (
            "--- a/src/sicaklik.py\n+++ b/src/sicaklik.py\n@@ -4,2 +4,4 @@\n"
            "+def celsius_fahrenheit(c):\n+    return 0\n"
        )
        s = sinyal(diff, repo=REPO)
        self.assertIn("celsius_fahrenheit", s["yinelenen_fonksiyon"])

    def test_yeni_fonksiyon_yinelenmez(self):
        diff = "--- a/src/yeni.py\n+++ b/src/yeni.py\n@@ -0,0 +1,2 @@\n+def tamamen_yeni():\n+    return 1\n"
        s = sinyal(diff, repo=REPO)
        self.assertEqual(s["yinelenen_fonksiyon"], [])

    def test_kopya_suphesi_telif_basligi(self):
        diff = (
            "--- a/src/kopya.py\n+++ b/src/kopya.py\n@@ -0,0 +1,3 @@\n"
            "+# Copyright (c) 2026 Baskasi\n+def x():\n+    return 1\n"
        )
        s = sinyal(diff)
        self.assertFalse(s["provenance"])
        self.assertIn("kopya", s["not"])

    def test_spdx_basligi_reddedilir(self):
        diff = (
            "--- a/src/kopya.py\n+++ b/src/kopya.py\n@@ -0,0 +1,3 @@\n"
            "+// SPDX-License-Identifier: MIT\n+def x():\n+    return 1\n"
        )
        s = sinyal(diff)
        self.assertFalse(s["provenance"])

    def test_temiz_diff_kopya_suphesi_uyarilmaz(self):
        self.assertFalse(sinyal(STDLIB_DIFF)["provenance"] is False and "kopya" in sinyal(STDLIB_DIFF)["not"])

    def test_bos_diff_serbest(self):
        self.assertTrue(sinyal("")["provenance"])


class tempfile_dosya:
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


class KopyaBlokTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.repo = _git_repo(Path(self._t.name) / "r", {"uzun.py": UZUN_FN})

    def tearDown(self):
        self._t.cleanup()

    def test_yeniden_adlandirilmis_kopya_reddedilir(self):
        kopya = UZUN_FN.replace("def hesapla", "def hesapla_v2").replace("sirali", "dizi")
        diff = _diff_eski_yeni(UZUN_FN, kopya, "a/uzun.py", "b/uzun.py")
        s = sinyal(diff, repo=self.repo)
        self.assertFalse(s["provenance"])
        self.assertTrue(s["kopya_blok"])
        self.assertEqual(s["kopya_blok"][0]["fonksiyon"], "hesapla_v2")
        self.assertGreaterEqual(s["kopya_blok"][0]["skor"], 0.90)

    def test_kopya_varyantlarinin_hepsi_yakalanir(self):
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
            bulgular = kopya_blok_tara(self.repo, diff)
            self.assertTrue(bulgular, "varyant yakalanmadı")
            self.assertGreaterEqual(bulgular[0]["skor"], 0.90)

    def test_kisa_benzer_fonksiyon_bilgi_duzeyinde(self):
        kopya = UZUN_FN.splitlines()[0] + "\n    return 1\n"
        diff = "--- a/kisa.py\n+++ b/kisa.py\n@@ -0,0 +1,2 @@\n+def kisa(a):\n+    return a\n"
        s = sinyal(diff, repo=self.repo)
        self.assertTrue(s["provenance"])
        self.assertEqual(s["kopya_blok"], [])

    def test_ilgisiz_yeni_fonksiyon_temiz(self):
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
        s = sinyal(diff, repo=self.repo)
        self.assertTrue(s["provenance"], s["not"])
        self.assertEqual(s["kopya_blok"], [])

    def test_degismemis_fonksiyon_yeniden_raporlanmaz(self):
        diff = "--- a/uzun.py\n+++ b/uzun.py\n@@ -1,2 +1,3 @@\n def hesapla(liste):\n+    pass\n"
        s = sinyal(diff, repo=self.repo)
        self.assertEqual(s["kopya_blok"], [])

if __name__ == "__main__":
    unittest.main(verbosity=2)
