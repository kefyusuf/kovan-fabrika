"""KOVAN — uyum katmanı: provenance sinyali (SBOM tohumu).

Ölçülen şey: diff'te YENİ import edilen modüller ve bağımlılık dosyası
değişimi. Kural:
- standart kütüphane import'u → serbest;
- üçüncü taraf import → yalnızca `compliance-allowlist.yaml` listesindeyse serbest;
- requirements/pyproject/package.json/Cargo.toml değişimi → REDDET (C3:
  yeni bağımlılık insan kararıdır);
- ölçülemeyen durum → False (fail-closed).

Bu, "kaynağı gösterilemeyen kod birleşmez" kuralının bugünkü ölçülebilir
hâlidir. Kopya kod tespiti ve tam SBOM (SPDX) S4'te eklenir.

Kullanim:
    python uyum.py --diff-dosya yama.diff [--izinli compliance-allowlist.yaml]
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import konsol

konsol.hazirla()

from dogrula import geri_al, repo_gecerli_mi, uygula  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

BAGIMLILIK_DOSYALARI = (
    "requirements",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "Pipfile",
)
ATLANAN_DIZINLER = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", "target",
    "runs", "vardiya-runs", ".secrets",
}
IMPORT_SATIRI = re.compile(r"^\+\s*(?:import\s+([A-Za-z_][\w.]*)|from\s+([A-Za-z_][\w.]*)\s+import)", re.M)


def _kok(modul: str) -> str:
    return modul.split(".")[0]


def bagimlilik_cikar(diff: str) -> set[str]:
    """Diff'in eklenen satırlarındaki kök modülleri çıkarır."""
    return {
        _kok(m)
        for m in (
            a or b
            for a, b in IMPORT_SATIRI.findall(diff or "")
        )
        if m
    }


def dosya_degisimi_var(diff: str) -> bool:
    return any(d in (diff or "") for d in BAGIMLILIK_DOSYALARI)


def izinli_oku(path: str | Path | None) -> set[str]:
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    import yaml

    veri = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {str(x).strip() for x in veri.get("paketler", []) if str(x).strip()}


def kopya_suphesi(diff: str) -> bool:
    """Eklenen satırlarda dış kaynak göstergesi arar (tohum düzeyi).

    Copyright/SPDX başlığı, telif notu veya yükleyici satırı — bu bir
    telif kararı değildir, İNSAN KARARI içindir (fail-closed).
    """
    desen = re.compile(
        r"^\+.*(Copyright \(c\)|Copyright ©|SPDX-License-Identifier|All rights reserved)",
        re.M | re.I,
    )
    return bool(desen.search(diff or ""))


def _eklenen_kod(diff: str) -> str:
    return "\n".join(
        s[1:] for s in (diff or "").splitlines() if s.startswith("+") and not s.startswith("+++")
    )


def _def_isimleri(kod: str) -> set[str]:
    try:
        agac = ast.parse(kod)
    except (SyntaxError, ValueError):
        return set()
    return {d.name for d in ast.walk(agac) if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _yapi_imzasi(kod: str) -> list[str]:
    """Kodun yapısını tokenize eder: tanımlayıcı/sayı/metin değerleri maskelenir.

    Amaç: değişken yeniden adlandırma ile gizlenen kopyayı da görmek.
    Sonuç: token tipi dizisi (['def','N','(',...]).
    """
    import keyword

    maskeler = {"NAME": "N", "NUMBER": "#", "STRING": "S"}
    atla = {"COMMENT", "NL", "NEWLINE", "ENCODING", "ENDMARKER"}
    imza: list[str] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(kod).readline):
            if tok.type == tokenize.NAME:
                imza.append("N" if tok.string not in keyword.kwlist else tok.string)
            elif tok.type == tokenize.NUMBER:
                imza.append("#")
            elif tok.type == tokenize.STRING:
                imza.append("S")
            elif tok.type == tokenize.OP:
                imza.append(tok.string)
            elif tok.type in (tokenize.INDENT, tokenize.DEDENT):
                imza.append(tok.type)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return imza  # kısmi imza ile devam (parça kod olabilir)
    return [x for x in imza if x not in {"NEWLINE"}]


def yinelenen_fonksiyon(repo: Path, diff: str) -> list[str]:
    """Diff'in eklediği fonksiyon adları ile depodaki mevcut adların kesişimi.

    Yeniden tanımlama, büyük olasılıkla çakışmadır: bilgi olarak raporlanır,
    provenance kararını tek başına değiştirmez (review kapısına sinyal).
    """
    yeni = _def_isimleri(_eklenen_kod(diff))
    if not yeni or not repo.is_dir():
        return []
    mevcut: set[str] = set()
    for dosya in repo.rglob("*.py"):
        if any(par in ATLANAN_DIZINLER for par in dosya.parts):
            continue
        try:
            agac = ast.parse(dosya.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError):
            continue
        mevcut |= {d.name for d in ast.walk(agac) if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return sorted(yeni & mevcut)


MIN_KOPYA_SATIR = 12
MIN_KOPYA_SKOR = 0.90


def _norm_satirlar(metin: str) -> list[str]:
    cikti = []
    for s in metin.splitlines():
        s = re.sub(r"\s+", " ", s.strip())
        if s and not s.startswith("#"):
            cikti.append(s)
    return cikti


def _fonksiyonlar(repo: Path) -> list[tuple[str, str, int, list[str]]]:
    cikti = []
    for dosya in repo.rglob("*.py"):
        if any(par in ATLANAN_DIZINLER for par in dosya.parts):
            continue
        try:
            src = dosya.read_text(encoding="utf-8", errors="replace")
            agac = ast.parse(src)
        except (SyntaxError, ValueError):
            continue
        rel = str(dosya.relative_to(repo))
        for dugum in ast.walk(agac):
            if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef)):
                parca = ast.get_source_segment(src, dugum) or ""
                satirlar = _norm_satirlar(parca)
                if len(satirlar) >= MIN_KOPYA_SATIR:
                    cikti.append((dugum.name, rel, len(satirlar), _yapi_imzasi(parca)))
    return cikti


def kopya_blok_tara(repo: Path, diff: str) -> list[dict]:
    """Diff'i geçici klon'a uygulayıp yeni/eski fonksiyon gövdelerini karşılaştırır.

    Eşik: ≥ 12 normalize satır ve benzerlik ≥ 0.90, aynı fonksiyonun kendi
    eski hali hariç. Gerçek repo HİÇ değişmez; tarama klon üzerinde yapılır.
    """
    import difflib

    if not repo.is_dir():
        return []
    yeni_kod = _eklenen_kod(diff)
    if not yeni_kod.strip():
        return []
    try:
        ast.parse(yeni_kod)  # hızlı ön kontrol: tamamen bozuk diff'i eleme
    except (SyntaxError, ValueError):
        pass  # parçalı diff olabilir; klon uygulaması karar verir

    tmp = Path(tempfile.mkdtemp(prefix="kovan-kopya-"))
    try:
        klon = subprocess.run(
            ["git", "clone", "--quiet", str(repo.resolve()), str(tmp / "r")],
            capture_output=True, text=True, timeout=120,
        )
        if klon.returncode != 0:
            return []
        klon_repo = tmp / "r"
        ok, _ = uygula(klon_repo, diff)
        if not ok:
            return []

        yeni_fn = _fonksiyonlar(klon_repo)
        eski_fn = _fonksiyonlar(repo)
        eski_harita = {(ad, rel): (satir, imza) for ad, rel, satir, imza in eski_fn}

        bulgular: list[dict] = []
        for ad, rel, satir_sayisi, imza in yeni_fn:
            if satir_sayisi < MIN_KOPYA_SATIR:
                continue
            eski = eski_harita.get((ad, rel))
            if eski is not None and eski[1] == imza:
                continue  # değişmemiş fonksiyon
            en_iyi, en_iyi_yer, en_iyi_skor = None, None, 0.0
            for ad2, rel2, satir2, imza2 in eski_fn:
                if (ad2, rel2) == (ad, rel):
                    continue  # kendi eski hali: kopya değil, düzenleme
                r = difflib.SequenceMatcher(None, imza, imza2).ratio()
                if r > en_iyi_skor:
                    en_iyi, en_iyi_yer, en_iyi_skor = ad2, rel2, r
            if en_iyi and en_iyi_skor >= MIN_KOPYA_SKOR:
                bulgular.append(
                    {
                        "fonksiyon": ad,
                        "dosya": rel,
                        "satir": satir_sayisi,
                        "benzer": f"{en_iyi} ({en_iyi_yer})",
                        "skor": round(en_iyi_skor, 3),
                    }
                )
        return bulgular
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def sinyal(diff: str, izinli_dosya: str | Path | None = None, repo: Path | None = None) -> dict:
    yinelenen = yinelenen_fonksiyon(repo, diff) if repo is not None else []
    kopya = kopya_blok_tara(repo, diff) if repo is not None else []
    kopya_not = (
        "; kopya kod şüphesi: "
        + ", ".join(
            f"{b['fonksiyon']}≈{b['benzer']} (%{round(b['skor'] * 100)})" for b in kopya
        )
        if kopya
        else ""
    )
    if kopya_suphesi(diff):
        return {
            "provenance": False,
            "not": "dış kopya şüphesi (telif/SPDX başlığı) — insan kararı" + kopya_not,
            "paketler": [],
            "yinelenen_fonksiyon": yinelenen,
            "kopya_blok": kopya,
        }
    if dosya_degisimi_var(diff):
        return {
            "provenance": False,
            "not": "bağımlılık dosyası değişti — yeni bağımlılık C3 (insan kararı)" + kopya_not,
            "paketler": [],
            "yinelenen_fonksiyon": yinelenen,
            "kopya_blok": kopya,
        }
    importlar = bagimlilik_cikar(diff)
    if not importlar:
        sonuc = {"provenance": True, "not": "yeni import yok", "paketler": [], "yinelenen_fonksiyon": yinelenen}
    else:
        izinli = izinli_oku(izinli_dosya)
        yabanci = sorted(m for m in importlar if m not in sys.stdlib_module_names and m not in izinli)
        if yabanci:
            sonuc = {
                "provenance": False,
                "not": f"izin listesinde olmayan üçüncü taraf import: {', '.join(yabanci)}",
                "paketler": yabanci,
            }
        else:
            sonuc = {
                "provenance": True,
                "not": f"tüm importlar serbest ({', '.join(sorted(importlar))})",
                "paketler": sorted(importlar),
            }
    sonuc["yinelenen_fonksiyon"] = yinelenen
    sonuc["kopya_blok"] = kopya
    if kopya and sonuc["provenance"]:
        sonuc["provenance"] = False
        sonuc["not"] = sonuc["not"] + kopya_not
    return sonuc


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN uyum katmanı (provenance sinyali)")
    parser.add_argument("--diff-dosya", required=True)
    parser.add_argument("--izinli", default=str(Path(__file__).resolve().parent / "compliance-allowlist.yaml"))
    args = parser.parse_args(argv)

    diff = Path(args.diff_dosya).read_text(encoding="utf-8")
    sonuc = sinyal(diff, args.izinli)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0 if sonuc["provenance"] else 1


if __name__ == "__main__":
    raise SystemExit(ana())