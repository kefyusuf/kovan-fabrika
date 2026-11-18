"""KOVAN — gerçek doğrulama katmanı.

Sinyali model söylemez; bilgisayar ölçer. Bu modül:
1. modelin ürettiği diff'i gerçek bir git deposuna uygular (--check ile),
2. depoda gerçek test komutunu çalıştırır,
3. sonucu `tests` sinyali olarak döndürür ve depoyu geri alır.

Sözleşme:
- uygulanamayan diff = tests: False (fail-closed).
- sinyal sözlüğünde "tests" yoksa kapı geçmez (runner zaten böyle).

Kullanim:
    python verify.py --repo ornek-repo --diff-dosya yama.diff \
        --komut "python -m unittest discover -s tests -t ."
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import console

console.hazirla()

KOMUT_TIMEOUT = 180


class DogrulaError(RuntimeError):
    pass


def _git(repo: Path, *args: str) -> tuple[int, str]:
    sonuc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return sonuc.returncode, (sonuc.stdout + sonuc.stderr).strip()


def repo_gecerli_mi(repo: Path) -> bool:
    if not repo.is_dir():
        return False
    kod, _ = _git(repo, "rev-parse", "--is-inside-work-tree")
    return kod == 0


def uygula(repo: Path, diff: str) -> tuple[bool, str]:
    """Diff'i depoya uygular. Başarısızsa depo dokunulmaz (--check).

    Güvenlik: çalışma ağacı KİRLİ ise uygulama REDDEDİLİR — sonraki
    `geri_al` (reset --hard) kullanıcının commitlenmemiş işini silebilir.
    Kural: yama yalnızca temiz ağaçta denenir (fail-closed).
    """
    if not diff.strip():
        return False, "diff boş"
    kod, durum = _git(repo, "status", "--porcelain")
    if kod != 0:
        return False, f"git durumu okunamadı: {durum[:200]}"
    if durum:
        return False, (
            "çalışma ağacı kirli — commit/stash edin; yama yalnızca temiz "
            "ağaçta denenir (reset --hard koruması)"
        )
    with tempfile.NamedTemporaryFile(
        "w", suffix=".diff", delete=False, encoding="utf-8", newline="\n"
    ) as fh:
        fh.write(diff if diff.endswith("\n") else diff + "\n")
        yama = fh.name
    kod, cikti = _git(repo, "apply", "--check", yama)
    if kod != 0:
        return False, f"uygulanamaz: {cikti[:300]}"
    kod, cikti = _git(repo, "apply", yama)
    return (kod == 0), cikti[:300]


def geri_al(repo: Path) -> None:
    """Takip edilen değişiklikleri başa döndürür; yeni dosyaları temizler."""
    _git(repo, "reset", "--hard", "HEAD")
    _git(repo, "clean", "-fd")


def test_calistir(repo: Path, komut: str, timeout: int = KOMUT_TIMEOUT) -> tuple[bool, str]:
    sonuc = subprocess.run(
        komut,
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=True,
    )
    cikti = (sonuc.stdout + sonuc.stderr).strip()
    kuyruk = cikti[-400:] if cikti else ""
    return sonuc.returncode == 0, kuyruk


def sinyaller(repo: Path, diff: str, test_komutu: str) -> dict:
    """tests sinyalini ölçer; depoyu her durumda başa döndürür."""
    if not repo_gecerli_mi(repo):
        return {"tests": False, "not": "repo geçersiz veya git deposu değil"}
    ok, not_ = uygula(repo, diff)
    if not ok:
        geri_al(repo)
        return {"tests": False, "not": not_}
    try:
        gecti, cikti = test_calistir(repo, test_komutu)
    except subprocess.TimeoutExpired:
        gecti, cikti = False, "test komutu zaman aşımına uğradı"
    finally:
        geri_al(repo)
    return {"tests": gecti, "not": cikti}


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN doğrulama katmanı")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--geri-al", action="store_true", help="depoyu HEAD'e döndürür (diff koşmaz)")
    parser.add_argument("--diff-dosya", default="")
    parser.add_argument("--komut", default="")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    if args.geri_al:
        geri_al(repo)
        temiz = not repo_gecerli_mi(repo) or not _git(repo, "status", "--porcelain")[1]
        print("depo başa döndürüldü; çalışma ağacı " + ("temiz" if temiz else "HÂLÂ kirli"))
        return 0 if temiz else 1

    if not args.diff_dosya or not args.komut:
        parser.error("--diff-dosya ve --komut gerekli (ya da --geri-al)")
    diff = Path(args.diff_dosya).read_text(encoding="utf-8")
    sonuc = sinyaller(repo, diff, args.komut)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0 if sonuc.get("tests") else 1


if __name__ == "__main__":
    raise SystemExit(ana())
