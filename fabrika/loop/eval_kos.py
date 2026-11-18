"""KOVAN — eval v1 kosucusu: dondurulmus seti diff'li depoda calistirir.

Sozlesme:
- skor = gecen / toplam (0..1). Eşik gates-live.yaml'da (0.90).
- diff uygulanamazsa skor 0 (fail-closed).
- Depo her durumda basa dondurulur.

Kullanim:
    python eval_kos.py --repo ornek-repo --set eval_set/sicaklik-v1.jsonl \
        [--diff-dosya yama.diff]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import konsol

konsol.hazirla()

from verify import geri_al, repo_gecerli_mi, uygula  # noqa: E402

KOMUT_TIMEOUT = 180
KOSONUC_ONEK = "KOSONUC="
BURASI = Path(__file__).resolve().parent


def kos(repo: str | Path, set_dosyasi: str | Path, diff: str | None = None) -> dict:
    repo_p = Path(repo)
    set_p = Path(set_dosyasi)
    if not repo_gecerli_mi(repo_p):
        return {"skor": 0.0, "gecen": 0, "toplam": 0, "hata": "repo geçersiz veya git deposu değil"}

    satirlar = [
        s for s in set_p.read_text(encoding="utf-8").splitlines() if s.strip()
    ]
    toplam = len(satirlar)
    if toplam == 0:
        return {"skor": 0.0, "gecen": 0, "toplam": 0, "hata": "set boş"}

    if diff is not None:
        ok, not_ = uygula(repo_p, diff)
        if not ok:
            geri_al(repo_p)
            return {"skor": 0.0, "gecen": 0, "toplam": toplam, "hata": f"diff uygulanamadı: {not_}"}

    try:
        son = subprocess.run(
            [sys.executable, str(BURASI / "eval_set" / "kosucu.py"), str(set_p.resolve())],
            cwd=str(repo_p),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=KOMUT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"skor": 0.0, "gecen": 0, "toplam": toplam, "hata": "eval zaman aşımı"}

    veri = None
    for satir in reversed((son.stdout or "").splitlines()):
        if satir.startswith(KOSONUC_ONEK):
            try:
                veri = json.loads(satir[len(KOSONUC_ONEK):])
            except json.JSONDecodeError:
                veri = None
            break
    if veri is None:
        return {"skor": 0.0, "gecen": 0, "toplam": toplam, "hata": "koşucu çıktı vermedi"}

    gecen = int(veri.get("gecen", 0))
    toplam_set = int(veri.get("toplam", toplam))
    skor = round(gecen / toplam_set, 4) if toplam_set else 0.0
    return {
        "skor": skor,
        "gecen": gecen,
        "toplam": toplam_set,
        "hatalar": veri.get("hatalar", []),
    }


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN eval v1 koşucusu")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--set", required=True)
    parser.add_argument("--diff-dosya", default="")
    args = parser.parse_args(argv)

    diff = Path(args.diff_dosya).read_text(encoding="utf-8") if args.diff_dosya else None
    sonuc = kos(args.repo, args.set, diff)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0 if sonuc.get("skor", 0.0) >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(ana())