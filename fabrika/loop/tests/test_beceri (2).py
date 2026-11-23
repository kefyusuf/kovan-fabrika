"""Beceri yaşam döngüsü testleri (tmp kopya üzerinde)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import beceri  # noqa: E402

GERCEK_TEST = "tests/skills/test_tests_kapisi.py"


def tmp_skill(tmp, durum="proposed", kanit=2, tests=GERCEK_TEST, onay="kurucu"):
    d = Path(tmp) / "skills" / "test-beceri"
    d.mkdir(parents=True)
    kanitlar = ", ".join("K-" + str(i) for i in range(1, kanit + 1))
    satirlar = [
        "---",
        "name: test-beceri",
        "version: 0.1.0",
        f"status: {durum}",
        f"evidence: [{kanitlar}]",
        f"tests: {tests}",
        f"onay: {onay}",
        "---",
        "icerik",
    ]
    (d / "SKILL.md").write_text("\n".join(satirlar), encoding="utf-8")
    return beceri._frontmatter(d / "SKILL.md"), d / "SKILL.md"


class YasamTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = self._t.name

    def tearDown(self):
        self._t.cleanup()

    def test_test_yoksa_ret(self):
        b, _ = tmp_skill(self.tmp, tests="yok")
        ok, g = beceri.aktiflesme_kontrolu(b)
        self.assertFalse(ok)
        self.assertIn("test dosyası yok", g)

    def test_test_dosyasi_bulunamazsa_ret(self):
        b, _ = tmp_skill(self.tmp, tests="tests/skills/olmayan.py")
        ok, g = beceri.aktiflesme_kontrolu(b)
        self.assertFalse(ok)
        self.assertIn("bulunamadı", g)

    def test_kanit_yetersizse_ret(self):
        b, _ = tmp_skill(self.tmp, kanit=1)
        ok, g = beceri.aktiflesme_kontrolu(b)
        self.assertFalse(ok)
        self.assertIn("kanıt yetersiz", g)

    def test_onay_yoksa_ret(self):
        b, _ = tmp_skill(self.tmp, onay="")
        ok, g = beceri.aktiflesme_kontrolu(b)
        self.assertFalse(ok)
        self.assertIn("onay", g)

    def test_olcutler_tam_ise_onaylanir(self):
        b, dosya = tmp_skill(self.tmp)
        ok, g = beceri.aktiflesme_kontrolu(b)
        self.assertTrue(ok, g)
        beceri.durum_degistir(dosya, "active", "aktiflesme test")
        self.assertEqual(beceri._frontmatter(dosya)["durum"], "active")

    def test_zaten_aktifse_ret(self):
        b, _ = tmp_skill(self.tmp, durum="active")
        ok, g = beceri.aktiflesme_kontrolu(b)
        self.assertFalse(ok)
        self.assertIn("zaten aktif", g)

    def test_kullanim_ve_curume(self):
        d = Path(self.tmp) / "skills"
        d.mkdir(parents=True)
        for ad in ("a", "b"):
            sd = d / ad
            sd.mkdir()
            (sd / "SKILL.md").write_text(
                "---\nname: " + ad + "\nstatus: active\n---\n", encoding="utf-8"
            )
        beceri.kullanim_yaz(d, "a")
        eski = datetime.now(timezone.utc) - timedelta(days=100)
        with (d / "kullanim.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ad": "b", "ts": eski.isoformat()}) + "\n")
        r = beceri.rapor(d, simdi=datetime.now(timezone.utc))
        harita = {x["ad"]: x for x in r["beceriler"]}
        self.assertFalse(harita["a"]["cürüme_onerisi"])
        self.assertTrue(harita["b"]["cürüme_onerisi"])


import json  # noqa: E402

if __name__ == "__main__":
    unittest.main(verbosity=2)