"""KOVAN CLI uçtan uca testleri."""

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
from runner import Ledger  # noqa: E402

BACKLOG = Path(__file__).resolve().parent.parent / "sample-backlog.yaml"


def calistir(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        kod = kovan.main(list(argv))
    return kod, buf.getvalue()


class PlanTest(unittest.TestCase):
    def test_kapasiteye_gore_kabul(self):
        kod, cikti = calistir("plan", "--backlog", str(BACKLOG), "--saat", "3")
        self.assertEqual(kod, 0)
        self.assertIn("K-101", cikti)
        self.assertIn("K-104", cikti)  # ertelenen
        self.assertIn("K-108", cikti)  # insan kuyruğu
        self.assertIn("ertelenen", cikti.lower())

    def test_dusuk_kapasite_az_is_alir(self):
        _, tam = calistir("plan", "--backlog", str(BACKLOG), "--saat", "3")
        _, az = calistir("plan", "--backlog", str(BACKLOG), "--saat", "0.5")
        self.assertNotEqual(tam, az)


class RunTest(unittest.TestCase):
    def _run(self, tmp: str, run_id: str) -> Path:
        kod, _ = calistir("run", "--backlog", str(BACKLOG), "--out", tmp, "--run-id", run_id)
        self.assertEqual(kod, 0)
        return Path(tmp) / run_id

    def test_uctan_uca_kanit_uretir(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._run(tmp, "t1")
            for ad in ("ledger.jsonl", "ozet.json", "rapor.md", "state.json"):
                self.assertTrue((run / ad).exists(), ad)

            ok, kayit, neden = Ledger(run / "ledger.jsonl").verify()
            self.assertTrue(ok, neden)
            self.assertGreater(kayit, 0)

            ozet = json.loads((run / "ozet.json").read_text(encoding="utf-8"))
            self.assertEqual(ozet["insan_kuyrugu"], ["K-108"])
            self.assertNotIn("K-108", ozet["kabul"])
            self.assertGreaterEqual(len(ozet["kabul"]), 3)
            self.assertTrue(ozet["defter"]["ok"])

    def test_kanarya_yalnizca_n_is_kosturur(self):
        with tempfile.TemporaryDirectory() as tmp:
            kod, _ = calistir(
                "run", "--backlog", str(BACKLOG), "--out", tmp, "--run-id", "k1", "--kanarya", "2"
            )
            self.assertEqual(kod, 0)
            ozet = json.loads((Path(tmp) / "k1" / "ozet.json").read_text(encoding="utf-8"))
            self.assertEqual(len(ozet["kabul"]), 2)
            self.assertLessEqual(ozet["accepted"], 2)
            rapor = (Path(tmp) / "k1" / "rapor.md").read_text(encoding="utf-8")
            self.assertIn("KANARYA", rapor)

    def test_yapilandirma_saat_uygulanir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yol = Path(tmp) / "user.yaml"
            yol.write_text("saat: 1.5\n", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                kod = kovan.main(
                    ["--yapilandirma", str(yol), "plan", "--backlog", str(BACKLOG)]
                )
            self.assertEqual(kod, 0)
            self.assertIn("1.5 saat", buf.getvalue())

    def test_cli_yapilandirmayi_ezer(self):
        with tempfile.TemporaryDirectory() as tmp:
            yol = Path(tmp) / "user.yaml"
            yol.write_text("saat: 1.5\n", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                kovan.main(
                    [
                        "--yapilandirma", str(yol), "plan",
                        "--backlog", str(BACKLOG), "--saat", "3.0",
                    ]
                )
            self.assertIn("3.0 saat", buf.getvalue())

    def test_bozuk_yapilandirma_uyari_verir_ve_devam_eder(self):
        with tempfile.TemporaryDirectory() as tmp:
            yol = Path(tmp) / "user.yaml"
            yol.write_text("saat: [bozuk", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                kod = kovan.main(
                    ["--yapilandirma", str(yol), "plan", "--backlog", str(BACKLOG)]
                )
            self.assertEqual(kod, 0)
            self.assertIn("UYARI", buf.getvalue())
            self.assertIn("3.0 saat", buf.getvalue())

    def test_tamamlanan_atlanir_ve_yazilir(self):
        with tempfile.TemporaryDirectory() as tmp:
            durum = Path(tmp) / "tamamlanan.jsonl"
            durum.write_text(json.dumps({"id": "K-101"}) + "\n", encoding="utf-8")
            kod, _ = calistir(
                "run", "--backlog", str(BACKLOG), "--out", tmp,
                "--run-id", "t1", "--tamamlanan", str(durum),
            )
            self.assertEqual(kod, 0)
            ozet = json.loads((Path(tmp) / "t1" / "ozet.json").read_text(encoding="utf-8"))
            self.assertNotIn("K-101", ozet["kabul"])
            self.assertEqual(ozet["tamamlanan_atlandi"], 1)
            kayitlar = {json.loads(s)["id"] for s in durum.read_text(encoding="utf-8").splitlines() if s}
            self.assertIn("K-102", kayitlar)  # kabul edilenler kayda geçti

    def test_bloklanan_tamamlanmaz(self):
        """Politika ihlali 'tamamlandı' sayılmaz: tekrar eden ihlal trendi korunur."""
        with tempfile.TemporaryDirectory() as tmp:
            durum = Path(tmp) / "tamamlanan.jsonl"
            kod, _ = calistir(
                "run", "--backlog", str(BACKLOG), "--out", tmp,
                "--run-id", "t2", "--tamamlanan", str(durum),
            )
            self.assertEqual(kod, 0)
            kayitlar = {json.loads(s)["id"] for s in durum.read_text(encoding="utf-8").splitlines() if s}
            self.assertNotIn("K-107", kayitlar)  # sır okuma isteği bloklandı → kayda girmez
            self.assertIn("K-102", kayitlar)     # kabul edilenler girer

    def test_hepsi_tamamlanmis_is_kalmadi(self):
        with tempfile.TemporaryDirectory() as tmp:
            durum = Path(tmp) / "tamamlanan.jsonl"
            tum_idler = ["K-101", "K-102", "K-103", "K-104", "K-105", "K-106", "K-107", "K-108"]
            durum.write_text(
                "\n".join(json.dumps({"id": i}) for i in tum_idler) + "\n",
                encoding="utf-8",
            )
            kod, _ = calistir(
                "run", "--backlog", str(BACKLOG), "--out", tmp,
                "--run-id", "t3", "--tamamlanan", str(durum),
            )
            self.assertEqual(kod, 0)
            ozet = json.loads((Path(tmp) / "t3" / "ozet.json").read_text(encoding="utf-8"))
            self.assertEqual(ozet["accepted"], 0)

    def test_politika_ihlali_bloklanir(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._run(tmp, "t2")
            rapor = (run / "rapor.md").read_text(encoding="utf-8")
            self.assertIn("politika ihlali", rapor)
            self.assertIn(".secrets/", rapor)

    def test_ayni_girdi_ayni_karar(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self._run(tmp, "a")
            b = self._run(tmp, "b")
            oa = json.loads((a / "ozet.json").read_text(encoding="utf-8"))
            ob = json.loads((b / "ozet.json").read_text(encoding="utf-8"))
            self.assertEqual(oa["accepted"], ob["accepted"])
            self.assertEqual(oa["blocked"], ob["blocked"])

    def test_defter_dogrulama_komutu(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._run(tmp, "t3")
            kod, cikti = calistir("verify", "--run", str(run))
            self.assertEqual(kod, 0)
            self.assertIn("OK", cikti)


if __name__ == "__main__":
    unittest.main(verbosity=2)
