"""SBOM tohumu testleri (SPDX 2.3)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sbom import spdx_uret, repo_tara  # noqa: E402

REPO = Path(__file__).resolve().parent.parent / "ornek-repo"


class SbomTest(unittest.TestCase):
    def test_ornek_repo_gecerli_spdx(self):
        d = spdx_uret(REPO)
        self.assertEqual(d["spdxVersion"], "SPDX-2.3")
        self.assertEqual(d["dataLicense"], "CC0-1.0")
        self.assertEqual(d["SPDXID"], "SPDXRef-DOCUMENT")

    def test_stdlib_ve_yerel_paket_girmez(self):
        d = spdx_uret(REPO)
        # Yalnızca kök paket girer; stdlib/yerel modüller notlar'da.
        adlar = [p["name"] for p in d["packages"]]
        self.assertEqual(adlar, ["ornek-repo"])
        self.assertIn("sicaklik", d["notlar"]["yerel_moduller"])
        self.assertIn("unittest", d["notlar"]["stdlib_importlar"])

    def test_lock_sürümleri_öncelikli(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "mini"
            repo.mkdir()
            (repo / "app.py").write_text("import yaml\n", encoding="utf-8")
            (repo / "requirements.txt").write_text("pyyaml==9.9.9\n", encoding="utf-8")
            d = spdx_uret(repo)
            p = next(p for p in d["packages"] if p["name"] == "yaml")
            self.assertEqual(p["versionInfo"], "9.9.9")

    def test_ucuncu_taraf_paket_girer(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "mini"
            repo.mkdir()
            (repo / "app.py").write_text("import yaml\n", encoding="utf-8")
            d = spdx_uret(repo)
            adlar = [p["name"] for p in d["packages"]]
            self.assertIn("yaml", adlar)
            self.assertTrue(any(r["relatedSpdxElement"].endswith("yaml") for r in d["relationships"]))

    def test_local_modul_ucuncu_taraf_sayilmaz(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "mini"
            repo.mkdir()
            (repo / "yardimci.py").write_text("X = 1\n", encoding="utf-8")
            (repo / "app.py").write_text("import yardimci\n", encoding="utf-8")
            adlar = [p["name"] for p in spdx_uret(repo)["packages"]]
            self.assertEqual(adlar, ["mini"])  # yalnızca kök

    def test_kok_paket_supplier_dolu(self):
        """NTIA minimum öğeleri: kök bileşen + supplier + ilişkiler."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "kovan-fabrika"
            repo.mkdir()
            (repo / "app.py").write_text("import yaml\n", encoding="utf-8")
            (repo / "pyproject.toml").write_text(
                '[project]\nname = "kovan-fabrika"\nversion = "0.2.1"\n',
                encoding="utf-8",
            )
            d = spdx_uret(repo)
            kok = next(
                p for p in d["packages"] if p["SPDXID"] == "SPDXRef-Package-hedef-proje"
            )
            self.assertEqual(kok["name"], "kovan-fabrika")
            self.assertEqual(kok["versionInfo"], "0.2.1")
            self.assertEqual(kok["supplier"], "Organization: KOVAN projesi")
            self.assertEqual(kok["licenseDeclared"], "Apache-2.0")
            ucuncu = next(p for p in d["packages"] if p["name"] == "yaml")
            self.assertEqual(ucuncu["supplier"], "NOASSERTION")
            self.assertTrue(
                any(
                    r["relationshipType"] == "DESCRIBES"
                    and r["relatedSpdxElement"] == "SPDXRef-Package-hedef-proje"
                    for r in d["relationships"]
                )
            )
            self.assertTrue(
                any(
                    r["relationshipType"] == "DEPENDS_ON"
                    and r["relatedSpdxElement"].endswith("yaml")
                    for r in d["relationships"]
                )
            )

    def test_kok_paket_pyproject_yok_noassertion(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "orn"
            repo.mkdir()
            kok = next(
                p for p in spdx_uret(repo)["packages"]
                if p["SPDXID"] == "SPDXRef-Package-hedef-proje"
            )
            self.assertEqual(kok["name"], "orn")
            self.assertEqual(kok["versionInfo"], "NOASSERTION")
            self.assertEqual(kok["supplier"], "NOASSERTION")

    def test_cikti_dosyasi_yazar(self):
        with tempfile.TemporaryDirectory() as tmp:
            cikti = Path(tmp) / "sbom.json"
            kod_ana = sbom_ana(cikti)
            self.assertEqual(kod_ana, 0)
            veri = json.loads(cikti.read_text(encoding="utf-8"))
            self.assertEqual(veri["spdxVersion"], "SPDX-2.3")


def sbom_ana(cikti: Path) -> int:
    from sbom import ana

    return ana(["--repo", str(REPO), "--output", str(cikti)])


if __name__ == "__main__":
    unittest.main(verbosity=2)