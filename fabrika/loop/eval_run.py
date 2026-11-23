"""KOVAN — eval v1 kosucusu: dondurulmus seti diff'li depoda calistirir.

Sozlesme:
- skor = gecen / toplam (0..1). Eşik gates-live.yaml'da (0.90).
- diff uygulanamazsa skor 0 (fail-closed).
- Depo her durumda basa dondurulur.

Kullanim:
    python eval_run.py --repo ornek-repo --set eval_set/sicaklik-v1.jsonl \
        [--diff-file yama.diff]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import console

console.hazirla()

from verify import reset_repo, repo_is_valid, apply_patch  # noqa: E402

COMMAND_TIMEOUT = 180
RESULT_PREFIX = "KOSONUC="
BURASI = Path(__file__).resolve().parent


def run_eval(repo: str | Path, set_dosyasi: str | Path, diff: str | None = None) -> dict:
    repo_p = Path(repo)
    set_p = Path(set_dosyasi)
    if not repo_is_valid(repo_p):
        return {"skor": 0.0, "gecen": 0, "toplam": 0, "hata": "repo geçersiz veya git deposu değil"}

    lines = [
        s for s in set_p.read_text(encoding="utf-8").splitlines() if s.strip()
    ]
    total = len(lines)
    if total == 0:
        return {"skor": 0.0, "gecen": 0, "toplam": 0, "hata": "set boş"}

    if diff is not None:
        ok, note = apply_patch(repo_p, diff)
        if not ok:
            reset_repo(repo_p)
            return {"skor": 0.0, "gecen": 0, "toplam": total, "hata": f"diff uygulanamadı: {note}"}

    try:
        proc = subprocess.run(
            [sys.executable, str(BURASI / "eval_set" / "runner.py"), str(set_p.resolve())],
            cwd=str(repo_p),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"skor": 0.0, "gecen": 0, "toplam": total, "hata": "eval zaman aşımı"}

    data = None
    for line in reversed((proc.stdout or "").splitlines()):
        if line.startswith(RESULT_PREFIX):
            try:
                data = json.loads(line[len(RESULT_PREFIX):])
            except json.JSONDecodeError:
                data = None
            break
    if data is None:
        return {"skor": 0.0, "gecen": 0, "toplam": total, "hata": "koşucu çıktı vermedi"}

    passed = int(data.get("gecen", 0))
    total_set = int(data.get("toplam", total))
    skor = round(passed / total_set, 4) if total_set else 0.0
    return {
        "skor": skor,
        "gecen": passed,
        "toplam": total_set,
        "hatalar": data.get("hatalar", []),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN eval v1 koşucusu")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--set", required=True)
    parser.add_argument("--diff-file", default="")
    args = parser.parse_args(argv)

    diff = Path(args.diff_file).read_text(encoding="utf-8") if args.diff_file else None
    sonuc = run_eval(args.repo, args.set, diff)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0 if sonuc.get("skor", 0.0) >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())