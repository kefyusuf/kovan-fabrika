"""KOVAN — S1 runbook tatbikatı (GOVERNANCE §8 koşulabilir hali).

Dört adım:
  A1 Normal koşu: kuyruk → kapasite → kapılar → defter.
  A2 Defter doğrulama: hash zinciri sağlam, kayıt > 0.
  A3 Durdurma: STOP dosyası → döngü "insan_durdurdu" ile çıkar.
  A4 Geri alma: geçici klon kirletilir → depo başa döner, ağaç temiz.

Kullanim:
    python tatbikat.py            # PASS/FAIL tablosu
    python tatbikat.py --json
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import konsol

konsol.hazirla()

from runner import Ledger, Loop, ScriptedAdapter, Spec  # noqa: E402

BURASI = Path(__file__).resolve().parent
BACKLOG = BURASI / "sample-backlog.yaml"


def _adim(ad: str, gecti: bool, not_: str = "") -> dict:
    return {"ad": ad, "gecti": bool(gecti), "not": not_}


def _porcelain(repo: Path) -> str:
    sonuc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return sonuc.stdout.strip()


def tatbikat(repo: Path | None = None) -> dict:
    hedef = repo or (BURASI / "ornek-repo")
    adimlar: list[dict] = []
    tmp = Path(tempfile.mkdtemp(prefix="kovan-tatbikat-"))
    try:
        # A1 — normal koşu
        try:
            import kovan

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                kod = kovan.main(
                    ["run", "--backlog", str(BACKLOG), "--out", str(tmp), "--run-id", "a1"]
                )
            ozet = json.loads((tmp / "a1" / "ozet.json").read_text(encoding="utf-8"))
            adimlar.append(
                _adim(
                    "A1 normal koşu",
                    kod == 0 and len(ozet.get("kabul", [])) >= 1,
                    f"kabul={len(ozet.get('kabul', []))}",
                )
            )

            # A2 — defter doğrulama
            ok, kayit, neden = Ledger(tmp / "a1" / "ledger.jsonl").verify()
            adimlar.append(_adim("A2 defter doğrulama", ok and kayit > 0, f"{kayit} kayıt {neden}"))
        except Exception as e:  # noqa: BLE001 — tatbikat hatayı da raporlar
            adimlar.append(_adim("A1/A2 koşu", False, f"istisna: {e}"))

        # A3 — durdurma
        try:
            import kovan

            (tmp / "a3").mkdir(parents=True, exist_ok=True)
            (tmp / "a3" / "STOP").write_text("tatbikat", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                kod = kovan.main(
                    ["run", "--backlog", str(BACKLOG), "--out", str(tmp), "--run-id", "a3"]
                )
            ozet = json.loads((tmp / "a3" / "ozet.json").read_text(encoding="utf-8"))
            adimlar.append(
                _adim(
                    "A3 durdurma",
                    ozet.get("stopped") == "insan_durdurdu",
                    f"stopped={ozet.get('stopped')}",
                )
            )
            (tmp / "a3" / "STOP").unlink(missing_ok=True)
        except Exception as e:  # noqa: BLE001
            adimlar.append(_adim("A3 durdurma", False, f"istisna: {e}"))

        # A5 — kaos: kesinti → resume (koşucu kaldığı yerden döner)
        try:
            adaylar = [
                __import__("runner").Task("KA-1", "gorev bir", __import__("runner").ChangeClass.C1, estimate_tokens=1000),
                __import__("runner").Task("KA-2", "gorev iki", __import__("runner").ChangeClass.C1, estimate_tokens=1000),
            ]
            senaryo = {
                "KA-1": [__import__("runner").Candidate("KA-1", 1000, signals={
                    "lint": True, "types": True, "tests": True, "provenance": True,
                    "review": True, "eval": 0.95, "cost_usd": 1.0})],
                "KA-2": [__import__("runner").Candidate("KA-2", 1000, signals={
                    "lint": True, "types": True, "tests": True, "provenance": True,
                    "review": True, "eval": 0.95, "cost_usd": 1.0})],
            }
            a5 = tmp / "a5"
            ilk = Loop(
                spec=Spec.defaults(),
                adapter=ScriptedAdapter(senaryo),
                workdir=a5,
                backlog=adaylar,
            )
            ilk.run(max_rounds=1)  # kaos: ilk turda kesilir (KA-1 kabul edilmiş)
            ikinci = Loop(
                spec=Spec.defaults(),
                adapter=ScriptedAdapter(senaryo),
                workdir=a5,
                backlog=adaylar,
            )
            ikinci.run(max_rounds=10, resume=True)
            tamam = set(ikinci.report.accepted) == {"KA-1", "KA-2"}
            adimlar.append(
                _adim("A5 kaos/resume", tamam and ikinci.report.stopped == "is_kalmadi",
                      f"resume kabul={len(ikinci.report.accepted)}")
            )
        except Exception as e:  # noqa: BLE001
            adimlar.append(_adim("A5 kaos/resume", False, f"istisna: {e}"))

        # A4 — geri alma: geçici KLON kirletilir, gerçek depoya dokunulmaz
        try:
            import dogrula

            klon = tmp / "a4-klon"
            klonlama = subprocess.run(
                ["git", "clone", "--quiet", str(hedef.resolve()), str(klon)],
                capture_output=True, text=True, timeout=120,
            )
            if klonlama.returncode != 0:
                adimlar.append(_adim("A4 geri alma", False, "klon alınamadı"))
            else:
                sicaklik = klon / "sicaklik.py"
                sicaklik.write_text(
                    sicaklik.read_text(encoding="utf-8") + "\n# tatbikat kirliği\n",
                    encoding="utf-8",
                )
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    kod = dogrula.ana(["--repo", str(klon), "--geri-al"])
                temiz = _porcelain(klon) == ""
                kirlik_gitti = "# tatbikat kirliği" not in sicaklik.read_text(encoding="utf-8")
                adimlar.append(
                    _adim("A4 geri alma", kod == 0 and temiz and kirlik_gitti,
                          f"porcelain={'temiz' if temiz else 'kirli'}")
                )
        except Exception as e:  # noqa: BLE001
            adimlar.append(_adim("A4 geri alma", False, f"istisna: {e}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return {"adimlar": adimlar, "gecildi": all(a["gecti"] for a in adimlar)}


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN S1 runbook tatbikatı")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repo", default="")
    args = parser.parse_args(argv)

    sonuc = tatbikat(Path(args.repo) if args.repo else None)
    if args.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    else:
        for a in sonuc["adimlar"]:
            print(f"{'PASS' if a['gecti'] else 'FAIL'}  {a['ad']:24} {a['not']}")
        print("TATBİKAT:", "GEÇTİ" if sonuc["gecildi"] else "DÜŞTÜ")
    return 0 if sonuc["gecildi"] else 1


if __name__ == "__main__":
    raise SystemExit(ana())