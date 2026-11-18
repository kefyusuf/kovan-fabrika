"""KOVAN — mutasyon testi: kapılar gerçekten yakalıyor mu?

Yöntem: hedef repodaki sayısal/operatör düğümleri tek tek mutasyona uğratılır
(+=→-=, <→<=, sabit→sabit+1 ...), her mutant geçici KLON'a yazılır ve iki
kapıya sorulur:
- eval seti skoru düştü mü?  (davranış kapısı)
- gerçek test komutu düştü mü? (test kapısı)

Mutant "öldü" = en az bir kapı yakaladı. Mutasyon skoru = ölen / toplam.
Ölen yoksa ("survived"), bu bir kapsam boşluğudur — rapor açıkça yazar.

Kullanim:
    python mutasyon.py --repo ornek-repo --set eval_set/sicaklik-v1.jsonl \
        --test-komut "python -m unittest discover -s tests -t ." --maks 12
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import console

console.hazirla()

from verify import test_calistir  # noqa: E402
from eval_run import kos as eval_kos  # noqa: E402

BURASI = Path(__file__).resolve().parent
BINOP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult, ast.Mod: ast.Mult}
CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


def _adaylar(agac: ast.AST) -> list[tuple[int, int, str]]:
    """Mutasyon noktalarını deterministik sırada döndürür."""
    noktalar: list[tuple[int, int, str]] = []
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.BinOp) and type(dugum.op) in BINOP:
            noktalar.append((dugum.lineno, dugum.col_offset, "binop"))
        elif isinstance(dugum, ast.Compare) and dugum.ops and type(dugum.ops[0]) in CMP:
            noktalar.append((dugum.lineno, dugum.col_offset, "compare"))
        elif isinstance(dugum, ast.Constant) and isinstance(dugum.value, bool):
            noktalar.append((dugum.lineno, dugum.col_offset, "bool"))
        elif isinstance(dugum, ast.Constant) and isinstance(dugum.value, (int, float)):
            noktalar.append((dugum.lineno, dugum.col_offset, "sayi"))
    return sorted(set(noktalar))


def mutant_uret(kaynak: str, indeks: int) -> tuple[str, str] | None:
    """i. adayı mutasyona uğratıp (açıklama, yeni_kaynak) döndürür."""
    agac = ast.parse(kaynak)
    adaylar = _adaylar(agac)
    if indeks >= len(adaylar):
        return None
    satir, kolon, tur = adaylar[indeks]
    yeni_agac = copy.deepcopy(agac)
    for dugum in ast.walk(yeni_agac):
        if getattr(dugum, "lineno", None) != satir or getattr(dugum, "col_offset", None) != kolon:
            continue
        if tur == "binop" and isinstance(dugum, ast.BinOp):
            eski = type(dugum.op).__name__
            dugum.op = BINOP[type(dugum.op)]()
            return f"satır {satir}: {eski}→{type(dugum.op).__name__}", ast.unparse(yeni_agac) + "\n"
        if tur == "compare" and isinstance(dugum, ast.Compare):
            eski = type(dugum.ops[0]).__name__
            dugum.ops[0] = CMP[type(dugum.ops[0])]()
            return f"satır {satir}: {eski}→{type(dugum.ops[0]).__name__}", ast.unparse(yeni_agac) + "\n"
        if tur == "bool" and isinstance(dugum, ast.Constant):
            dugum.value = not dugum.value
            return f"satır {satir}: bool ters çevrildi", ast.unparse(yeni_agac) + "\n"
        if tur == "sayi" and isinstance(dugum, ast.Constant):
            dugum.value = dugum.value + 1
            return f"satır {satir}: sabit+1", ast.unparse(yeni_agac) + "\n"
    return None


def _klonla(kaynak_repo: Path, hedef: Path) -> bool:
    sonuc = subprocess.run(
        ["git", "clone", "--quiet", str(kaynak_repo.resolve()), str(hedef)],
        capture_output=True, text=True, timeout=120,
    )
    return sonuc.returncode == 0


def _commit(klon: Path) -> None:
    for komut in (["add", "-A"], ["-c", "user.name=k", "-c", "user.email=k@l", "commit", "-q", "-m", "mutant"]):
        subprocess.run(["git", *komut], cwd=str(klon), capture_output=True)


def kos(repo: Path, set_dosyasi: Path, test_komutu: str, maks: int = 12) -> dict:
    hedef_dosya = repo / "sicaklik.py"
    if not hedef_dosya.exists():
        return {"hata": "sicaklik.py yok", "mutantlar": [], "mutasyon_skoru": 0.0}
    kaynak = hedef_dosya.read_text(encoding="utf-8")
    toplam = len(_adaylar(ast.parse(kaynak)))
    kayitlar: list[dict] = []
    tmp = Path(tempfile.mkdtemp(prefix="kovan-mutasyon-"))
    try:
        for i in range(min(maks, toplam)):
            uretilen = mutant_uret(kaynak, i)
            if uretilen is None:
                continue
            aciklama, yeni_kaynak = uretilen
            klon = tmp / f"m{i}"
            if not _klonla(repo, klon):
                continue
            (klon / "sicaklik.py").write_text(yeni_kaynak, encoding="utf-8", newline="\n")
            _commit(klon)
            ev = eval_kos(klon, set_dosyasi)
            try:
                testler, _ = test_calistir(klon, test_komutu)
            except Exception:  # noqa: BLE001
                testler = False
            oldu = ev["skor"] < 1.0 or not testler
            kayitlar.append(
                {
                    "mutant": i,
                    "aciklama": aciklama,
                    "eval_skor": ev["skor"],
                    "testler_gecti": testler,
                    "olduren": "ikisi" if (ev["skor"] < 1.0 and not testler) else
                               ("eval" if ev["skor"] < 1.0 else ("tests" if not testler else "hayatta")),
                    "oldu": oldu,
                }
            )
            shutil.rmtree(klon, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    olen = sum(1 for k in kayitlar if k["oldu"])
    return {
        "aday_sayisi": toplam,
        "denenen": len(kayitlar),
        "olen": olen,
        "mutasyon_skoru": round(olen / len(kayitlar), 3) if kayitlar else 0.0,
        "hayatta_kalanlar": [k for k in kayitlar if not k["oldu"]],
        "mutantlar": kayitlar,
    }


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN mutasyon testi")
    parser.add_argument("--repo", default=str(BURASI / "ornek-repo"))
    parser.add_argument("--set", default=str(BURASI / "eval_set" / "sicaklik-v1.jsonl"))
    parser.add_argument("--test-komut", default="python -m unittest discover -s tests -t .")
    parser.add_argument("--maks", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    sonuc = kos(Path(args.repo), Path(args.set), args.test_komut, args.maks)
    if args.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    else:
        print(f"Aday: {sonuc['aday_sayisi']} · Denenen: {sonuc['denenen']} · Ölen: {sonuc['olen']} "
              f"· Mutasyon skoru: {sonuc['mutasyon_skoru']:.0%}")
        for k in sonuc["mutantlar"]:
            durum = "ÖLDÜ" if k["oldu"] else "HAYATTA"
            print(f"  m{k['mutant']:02} {k['aciklama']:34} eval={k['eval_skor']:.3f} "
                  f"tests={'OK' if k['testler_gecti'] else 'DUŞTU'} → {durum}")
    return 0 if sonuc.get("olen", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(ana())