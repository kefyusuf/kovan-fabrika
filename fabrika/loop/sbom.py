"""KOVAN — SBOM tohumu (SPDX 2.3 JSON).

Ölçülen şey: hedef depodaki .py dosyalarının import kökleri.
- stdlib → SBOM'a girmez (Python çalışma zamanının parçası olarak not edilir);
- depo-içi yerel modül → SBOM'a girmez;
- üçüncü taraf → SPDX Package (kuruluysa sürümü, değilse NOASSERTION).

Sınır: sürüm dosyadan değil, kurulu ortamdan okunur. S4'te lock dosyası
(requirements/pyproject lock) bağlanacak.

Kullanim:
    python sbom.py --repo ornek-repo [--cikti sbom.json]
"""

from __future__ import annotations

import argparse
import ast
import importlib.metadata as im
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import konsol

konsol.hazirla()

ATLANAN_DIZINLER = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", "target",
    "runs", "vardiya-runs", ".secrets",
}


def _kok(modul: str) -> str:
    return modul.split(".")[0]


def _import_kokleri(dosya: Path) -> set[str]:
    try:
        agac = ast.parse(dosya.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, ValueError):
        return set()
    kokler: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Import):
            kokler |= {_kok(a.name) for a in dugum.names}
        elif isinstance(dugum, ast.ImportFrom) and dugum.module and dugum.level == 0:
            kokler.add(_kok(dugum.module))
    return kokler


def repo_tara(repo: Path) -> dict:
    """Depoyu tarar: (üçüncü taraf importlar, yerel modüller)."""
    if not repo.is_dir():
        raise ValueError(f"repo yok: {repo}")
    kokler: set[str] = set()
    yerel: set[str] = set()
    for dosya in repo.rglob("*.py"):
        if any(par in ATLANAN_DIZINLER for par in dosya.parts):
            continue
        yerel.add(dosya.stem)
        if (dosya.parent / "__init__.py").exists():
            yerel.add(dosya.parent.name)
        kokler |= _import_kokleri(dosya)
    ucuncu = sorted(m for m in kokler if m not in sys.stdlib_module_names and m not in yerel)
    return {"ucuncu_taraf": ucuncu, "yerel": sorted(yerel), "tumu": sorted(kokler)}


def _dagitim_adlari(modul: str) -> list[str]:
    try:
        return im.packages_distributions().get(modul, [])
    except Exception:  # noqa: BLE001
        return []


def _surum(modul: str, kilit: dict[str, str] | None = None) -> str:
    kilit = kilit or {}
    anahtar = modul.lower().replace("_", "-")
    if anahtar in kilit:
        return kilit[anahtar]
    for dist in _dagitim_adlari(modul):
        k = dist.lower().replace("_", "-")
        if k in kilit:
            return kilit[k]
    try:
        return im.version(modul)
    except Exception:  # noqa: BLE001 — kurulmamış paket
        for dist in _dagitim_adlari(modul):
            try:
                return im.version(dist)
            except Exception:  # noqa: BLE001
                pass
        return "NOASSERTION"


def lock_sürümleri(repo: Path) -> dict[str, str]:
    """requirements.txt / pyproject.toml'dan sabitlenmiş sürümleri okur."""
    sürüm: dict[str, str] = {}
    req = repo / "requirements.txt"
    if req.exists():
        for satir in req.read_text(encoding="utf-8", errors="replace").splitlines():
            satir = satir.strip()
            if not satir or satir.startswith(("#", "-")) or "==" not in satir:
                continue
            ad, ver = satir.split("==", 1)
            sürüm[ad.strip().lower().replace("_", "-")] = ver.strip()
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib

            veri = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            for dep in (veri.get("project", {}) or {}).get("dependencies", []) or []:
                dep = dep.strip()
                if "==" in dep:
                    ad, ver = dep.split("==", 1)
                    sürüm[ad.strip().lower().replace("_", "-")] = ver.strip()
        except Exception:  # noqa: BLE001 — bozuk pyproject SBOM'u düşürmez
            pass
    return sürüm


def _proje_kimligi(repo: Path) -> dict:
    """Hedef projenin adı/sürümü — pyproject yoksa NOASSERTION."""
    ad, surum = repo.name, "NOASSERTION"
    try:
        metin = (repo / "pyproject.toml").read_text(encoding="utf-8")
        m_ad = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"', metin)
        m_sur = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', metin)
        if m_ad:
            ad = m_ad.group(1)
        if m_sur:
            surum = m_sur.group(1)
    except OSError:
        pass
    return {"ad": ad, "surum": surum}


def spdx_uret(repo: Path) -> dict:
    tarama = repo_tara(repo)
    kilit = lock_sürümleri(repo)
    simdi = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    kimlik = _proje_kimligi(repo)
    kovan_mi = kimlik["ad"] == "kovan-fabrika"
    kok_paket = {
        "name": kimlik["ad"],
        "SPDXID": "SPDXRef-Package-hedef-proje",
        "versionInfo": kimlik["surum"],
        "supplier": "Organization: KOVAN projesi" if kovan_mi else "NOASSERTION",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "licenseConcluded": "Apache-2.0" if kovan_mi else "NOASSERTION",
        "licenseDeclared": "Apache-2.0" if kovan_mi else "NOASSERTION",
        "copyrightText": "NOASSERTION",
    }
    paketler = [
        {
            "name": m,
            "SPDXID": f"SPDXRef-Package-{m}",
            "versionInfo": _surum(m, kilit),
            "supplier": "NOASSERTION",
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
        }
        for m in tarama["ucuncu_taraf"]
    ]
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": repo.name,
        "documentNamespace": f"https://kovan.local/spdx/{repo.name}",
        "creationInfo": {"created": simdi, "creators": ["Tool: KOVAN-0.2"]},
        "packages": [kok_paket] + paketler,
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": kok_paket["SPDXID"],
            },
        ]
        + [
            {
                "spdxElementId": kok_paket["SPDXID"],
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": p["SPDXID"],
            }
            for p in paketler
        ],
        "notlar": {
            "stdlib_importlar": sorted(
                m for m in tarama["tumu"] if m in sys.stdlib_module_names
            ),
            "yerel_moduller": tarama["yerel"],
        },
    }


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN SBOM tohumu (SPDX 2.3)")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--cikti", default="")
    args = parser.parse_args(argv)

    dokuman = spdx_uret(Path(args.repo))
    cikti = json.dumps(dokuman, ensure_ascii=False, indent=2)
    if args.cikti:
        Path(args.cikti).write_text(cikti, encoding="utf-8")
        print(f"SBOM yazıldı: {args.cikti} ({len(dokuman['packages'])} paket)")
    else:
        print(cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())