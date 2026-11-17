"""Gece vardiyasi testleri — izole sahte runs diziniyle."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vardiya  # noqa: E402
from runner import Ledger  # noqa: E402

KAYNAK = Path(__file__).resolve().parent.parent / "kaynak-kuyrugu.yaml"


def calistir(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        kod = vardiya.main(list(argv))
    return kod, buf.getvalue()


def sahte_runs(tmp: str) -> Path:
    """Ayni fingerprinti 2 kez iceren sahte kovan kosusu."""
    d = Path(tmp) / "runs" / "sahte-01"
    d.mkdir(parents=True)
    ders = '{"task": "K-9", "gate": "tests", "detail": "başarısız", "fingerprint": "abc123", "seen": 1}'
    (d / "lessons.jsonl").write_text((ders + "\n") * 2, encoding="utf-8")
    ledger = [
        {"payload": {"type": "decision", "kind": "accepted", "gates": [{"gate": "policy", "ok": True, "blocking": True}]}},
        {"payload": {"type": "decision", "kind": "rejected", "gates": [{"gate": "tests", "ok": False, "blocking": True}]}},
    ]
    (d / "ledger.jsonl").write_text("\n".join(json.dumps(k) for k in ledger) + "\n", encoding="utf-8")
    return d.parent


class VardiyaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        sahte_runs(self.tmp)

    def tearDown(self):
        self._tmp.cleanup()

    def _kos(self, run_id: str) -> Path:
        kod, _ = calistir("run", "--id", run_id, "--runs", str(Path(self.tmp) / "runs"), "--out", str(self.tmp))
        self.assertEqual(kod, 0)
        return Path(self.tmp) / run_id

    def test_uctan_uca_artefakt_uretir(self):
        run = self._kos("v1")
        for ad in ("plan.md", "notlar.md", "kirilma.md", "sabah-raporu.md", "ledger.jsonl"):
            self.assertTrue((run / ad).exists(), ad)
        self.assertTrue((run / "oneri" / "ADR-taslagi.md").exists())

    def test_defter_dogrulanir(self):
        run = self._kos("v2")
        ok, kayit, neden = Ledger(run / "ledger.jsonl").verify()
        self.assertTrue(ok, neden)
        self.assertGreaterEqual(kayit, 6)

    def test_tekrar_eden_dersten_beceri_adaayi(self):
        run = self._kos("v3")
        adaylar = list((Path(self.tmp) / "beceri-adaylari").glob("*.md"))
        self.assertEqual(len(adaylar), 1)
        icerik = adaylar[0].read_text(encoding="utf-8")
        self.assertIn("status: proposed", icerik)
        self.assertIn("K-9", icerik)

    def test_idempotent_ikinci_kosum_yeniden_uretmez(self):
        self._kos("v8a")
        ilk = list((Path(self.tmp) / "beceri-adaylari").glob("*.md"))
        run2 = self._kos("v8b")
        yeni = list((Path(self.tmp) / "beceri-adaylari").glob("*.md"))
        self.assertEqual(len(ilk), len(yeni))  # dosya sayısı artmadı
        rapor = (run2 / "sabah-raporu.md").read_text(encoding="utf-8")
        self.assertIn("Zaten adaydı", rapor)

    def test_url_kaynak_kuru_modda_atlanir(self):
        run = self._kos("v4")
        rapor = (run / "sabah-raporu.md").read_text(encoding="utf-8")
        self.assertIn("model gerekli", rapor)
        self.assertIn("metr.org", rapor)

    def test_kirmizi_takim_canli_profil_kirilmasini_bulur(self):
        run = self._kos("v5")
        kirilma = (run / "kirilma.md").read_text(encoding="utf-8")
        self.assertIn("tasarim_hatasi", kirilma)

    def test_adr_olcum_plani_zorunlu(self):
        run = self._kos("v6")
        oneri = (run / "oneri" / "ADR-taslagi.md").read_text(encoding="utf-8")
        self.assertIn("Ölçüm planı", oneri)
        self.assertIn("C3", oneri)

    def test_rapor_bes_bolumlu(self):
        run = self._kos("v7")
        rapor = (run / "sabah-raporu.md").read_text(encoding="utf-8")
        for baslik in ("Ne öğrenildi", "Ne üretildi", "Ne reddedildi", "Bugünün ilk üç işi", "Dürüstlük notu"):
            self.assertIn(baslik, rapor)

    def test_rotasyon_harcanan_atlanir(self):
        """Kısmi tüketim: okunmuş kaynak atlanır, okunmamış taranır."""
        kaynaklar = [
            {"tur": "dosya", "yol": "arastirma/01-karpathy.md", "konu": "eski"},
            {"tur": "dosya", "yol": "arastirma/03-superpowers.md", "konu": "yeni"},
        ]
        harcanan = frozenset(
            {str((vardiya.KOK / "arastirma/01-karpathy.md").resolve())}
        )
        okunan, atlanan = vardiya.kaynak_tara(kaynaklar, harcanan)

        atlanan_yollar = {
            a.get("yol") for a in atlanan if a.get("neden") == "önceden okundu (rotasyon)"
        }
        self.assertIn("arastirma/01-karpathy.md", atlanan_yollar)
        okunan_kaynaklar = {n["kaynak_dosya"] for n in okunan}
        self.assertTrue(all("03-superpowers" in k for k in okunan_kaynaklar))

    def test_tumu_tukendiyse_tekrar_isaretli(self):
        yol = str((vardiya.KOK / "arastirma/01-karpathy.md").resolve())
        kaynaklar = [{"tur": "dosya", "yol": "arastirma/01-karpathy.md", "konu": "k"}]
        okunan, atlanan = vardiya.kaynak_tara(kaynaklar, frozenset({yol}))
        self.assertGreater(len(okunan), 0)
        self.assertTrue(okunan[0]["tekrar_tarama"])
        self.assertEqual(atlanan, [])

    def test_kok_disi_kaynak_reddedilir(self):
        okunan, atlanan = vardiya.kaynak_tara(
            [{"tur": "dosya", "yol": "C:/Windows/win.ini", "konu": "disari"}]
        )
        self.assertEqual(okunan, [])
        self.assertIn("izinli", atlanan[0]["neden"])


if __name__ == "__main__":
    unittest.main(verbosity=2)