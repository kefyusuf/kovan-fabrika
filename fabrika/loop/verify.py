"""KOVAN — the real verification layer.

The model never declares the signal; the computer measures it. This module:
1. applies the model-produced diff to a real git repository (--check first),
2. runs the real test command inside the repo,
3. returns the outcome as the `tests` signal and resets the repo.

Contract:
- an inapplicable diff = tests: False (fail-closed).
- if the signal dict has no "tests" key, the gate does not pass (the runner
  already behaves this way).

Usage:
    python verify.py --repo ornek-repo --diff-file yama.diff \
        --command "python -m unittest discover -s tests -t ."
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import console

console.hazirla()

COMMAND_TIMEOUT = 180


class VerifyError(RuntimeError):
    pass


def _git(repo: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def repo_is_valid(repo: Path) -> bool:
    if not repo.is_dir():
        return False
    code, _ = _git(repo, "rev-parse", "--is-inside-work-tree")
    return code == 0


def apply_patch(repo: Path, diff: str) -> tuple[bool, str]:
    """Applies the diff to the repo. On failure the repo is untouched (--check).

    Safety: if the working tree is DIRTY, applying is REFUSED — a later
    `reset_repo` (reset --hard) could wipe the user's uncommitted work.
    Rule: a patch is only tried on a clean tree (fail-closed).
    """
    if not diff.strip():
        return False, "diff boş"
    code, status = _git(repo, "status", "--porcelain")
    if code != 0:
        return False, f"git durumu okunamadı: {status[:200]}"
    if status:
        return False, (
            "çalışma ağacı kirli — commit/stash edin; yama yalnızca temiz "
            "ağaçta denenir (reset --hard koruması)"
        )
    with tempfile.NamedTemporaryFile(
        "w", suffix=".diff", delete=False, encoding="utf-8", newline="\n"
    ) as fh:
        fh.write(diff if diff.endswith("\n") else diff + "\n")
        patch_file = fh.name
    code, output = _git(repo, "apply", "--check", patch_file)
    if code != 0:
        return False, f"uygulanamaz: {output[:300]}"
    code, output = _git(repo, "apply", patch_file)
    return (code == 0), output[:300]


def reset_repo(repo: Path) -> None:
    """Resets tracked changes back to HEAD; removes untracked files."""
    _git(repo, "reset", "--hard", "HEAD")
    _git(repo, "clean", "-fd")


def run_test_command(repo: Path, command: str, timeout: int = COMMAND_TIMEOUT) -> tuple[bool, str]:
    result = subprocess.run(
        command,
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=True,
    )
    output = (result.stdout + result.stderr).strip()
    tail = output[-400:] if output else ""
    return result.returncode == 0, tail


def measure_tests(repo: Path, diff: str, test_command: str) -> dict:
    """Measures the tests signal; resets the repo in every case."""
    if not repo_is_valid(repo):
        return {"tests": False, "not": "repo geçersiz veya git deposu değil"}
    ok, note = apply_patch(repo, diff)
    if not ok:
        reset_repo(repo)
        return {"tests": False, "not": note}
    try:
        passed, output = run_test_command(repo, test_command)
    except subprocess.TimeoutExpired:
        passed, output = False, "test komutu zaman aşımına uğradı"
    finally:
        reset_repo(repo)
    return {"tests": passed, "not": output}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN doğrulama katmanı")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--rollback", action="store_true", help="depoyu HEAD'e döndürür (diff koşmaz)")
    parser.add_argument("--diff-file", default="")
    parser.add_argument("--command", default="")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    if args.rollback:
        reset_repo(repo)
        clean = not repo_is_valid(repo) or not _git(repo, "status", "--porcelain")[1]
        print("depo başa döndürüldü; çalışma ağacı " + ("temiz" if clean else "HÂLÂ kirli"))
        return 0 if clean else 1

    if not args.diff_file or not args.command:
        parser.error("--diff-file ve --command gerekli (ya da --rollback)")
    diff = Path(args.diff_file).read_text(encoding="utf-8")
    result = measure_tests(repo, diff, args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("tests") else 1


if __name__ == "__main__":
    raise SystemExit(main())
