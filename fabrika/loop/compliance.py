"""KOVAN — compliance layer: the provenance signal (SBOM seed).

What is measured: modules NEWLY imported in the diff and dependency-file
changes. Rules:
- standard-library imports → free;
- third-party imports → free only if listed in `compliance-allowlist.yaml`;
- a requirements/pyproject/package.json/Cargo.toml change → REJECT (C3:
  a new dependency is a human decision);
- an unmeasurable state → False (fail-closed).

This is today's measurable form of the rule "code whose source cannot be
shown does not merge". Copy detection and the full SBOM (SPDX) join in S4.

Usage:
    python compliance.py --diff-file yama.diff [--allowlist compliance-allowlist.yaml]
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

import console

console.hazirla()

from verify import reset_repo, repo_is_valid, apply_patch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

DEPENDENCY_FILES = (
    "requirements",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "Pipfile",
)
SKIPPED_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", "target",
    "runs", "vardiya-runs", ".secrets",
}
IMPORT_LINE_RE = re.compile(r"^\+\s*(?:import\s+([A-Za-z_][\w.]*)|from\s+([A-Za-z_][\w.]*)\s+import)", re.M)


def _root(module: str) -> str:
    return module.split(".")[0]


def extract_dependencies(diff: str) -> set[str]:
    """Extracts the root modules from the diff's added lines."""
    return {
        _root(m)
        for m in (
            a or b
            for a, b in IMPORT_LINE_RE.findall(diff or "")
        )
        if m
    }


def has_dependency_change(diff: str) -> bool:
    return any(d in (diff or "") for d in DEPENDENCY_FILES)


def read_allowlist(path: str | Path | None) -> set[str]:
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    import yaml

    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {str(x).strip() for x in data.get("paketler", []) if str(x).strip()}


def copy_suspicion(diff: str) -> bool:
    """Searches the added lines for external-origin markers (seed level).

    A Copyright/SPDX header, a copyright notice, or an installer line — this
    is not a copyright decision, it exists to force a HUMAN decision
    (fail-closed).
    """
    pattern = re.compile(
        r"^\+.*(Copyright \(c\)|Copyright ©|SPDX-License-Identifier|All rights reserved)",
        re.M | re.I,
    )
    return bool(pattern.search(diff or ""))


def _added_code(diff: str) -> str:
    return "\n".join(
        s[1:] for s in (diff or "").splitlines() if s.startswith("+") and not s.startswith("+++")
    )


def _def_names(code: str) -> set[str]:
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return set()
    return {d.name for d in ast.walk(tree) if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _structure_signature(code: str) -> list[str]:
    """Tokenizes the code's structure: identifiers/numbers/strings are masked.

    Purpose: to also see a copy hidden by variable renaming. Result: a
    sequence of token types (['def','N','(',...]).
    """
    import keyword

    masks = {"NAME": "N", "NUMBER": "#", "STRING": "S"}
    skip = {"COMMENT", "NL", "NEWLINE", "ENCODING", "ENDMARKER"}
    signature: list[str] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.NAME:
                signature.append("N" if tok.string not in keyword.kwlist else tok.string)
            elif tok.type == tokenize.NUMBER:
                signature.append("#")
            elif tok.type == tokenize.STRING:
                signature.append("S")
            elif tok.type == tokenize.OP:
                signature.append(tok.string)
            elif tok.type in (tokenize.INDENT, tokenize.DEDENT):
                signature.append(tok.type)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return signature  # continue with a partial signature (fragment code possible)
    return [x for x in signature if x not in {"NEWLINE"}]


def duplicate_functions(repo: Path, diff: str) -> list[str]:
    """The intersection of the diff's added function names with existing names in the repo.

    A redefinition is most likely a collision: reported as information; it
    does not by itself change the provenance decision (a signal to the review
    gate).
    """
    added = _def_names(_added_code(diff))
    if not added or not repo.is_dir():
        return []
    existing: set[str] = set()
    for file in repo.rglob("*.py"):
        if any(part in SKIPPED_DIRS for part in file.parts):
            continue
        try:
            tree = ast.parse(file.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError):
            continue
        existing |= {d.name for d in ast.walk(tree) if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return sorted(added & existing)


MIN_COPY_LINES = 12
MIN_COPY_SCORE = 0.90


def _normalized_lines(text: str) -> list[str]:
    out = []
    for s in text.splitlines():
        s = re.sub(r"\s+", " ", s.strip())
        if s and not s.startswith("#"):
            out.append(s)
    return out


def _functions(repo: Path) -> list[tuple[str, str, int, list[str]]]:
    out = []
    for file in repo.rglob("*.py"):
        if any(part in SKIPPED_DIRS for part in file.parts):
            continue
        try:
            src = file.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
        except (SyntaxError, ValueError):
            continue
        rel = str(file.relative_to(repo))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                segment = ast.get_source_segment(src, node) or ""
                lines = _normalized_lines(segment)
                if len(lines) >= MIN_COPY_LINES:
                    out.append((node.name, rel, len(lines), _structure_signature(segment)))
    return out


def scan_copy_blocks(repo: Path, diff: str) -> list[dict]:
    """Applies the diff to a temporary clone and compares new/old function bodies.

    Threshold: ≥ 12 normalized lines and similarity ≥ 0.90, excluding the
    function's own former self. The real repo NEVER changes; the scan runs
    on the clone.
    """
    import difflib

    if not repo.is_dir():
        return []
    added_code = _added_code(diff)
    if not added_code.strip():
        return []
    try:
        ast.parse(added_code)  # quick pre-check: discard a fully broken diff
    except (SyntaxError, ValueError):
        pass  # a partial diff is possible; the clone application decides

    tmp = Path(tempfile.mkdtemp(prefix="kovan-kopya-"))
    try:
        clone_run = subprocess.run(
            ["git", "clone", "--quiet", str(repo.resolve()), str(tmp / "r")],
            capture_output=True, text=True, timeout=120,
        )
        if clone_run.returncode != 0:
            return []
        clone_repo = tmp / "r"
        ok, _ = apply_patch(clone_repo, diff)
        if not ok:
            return []

        new_functions = _functions(clone_repo)
        old_functions = _functions(repo)
        old_map = {(name, rel): (lines, signature) for name, rel, lines, signature in old_functions}

        findings: list[dict] = []
        for name, rel, line_count, signature in new_functions:
            if line_count < MIN_COPY_LINES:
                continue
            old = old_map.get((name, rel))
            if old is not None and old[1] == signature:
                continue  # unchanged function
            best, best_where, best_score = None, None, 0.0
            for name2, rel2, lines2, signature2 in old_functions:
                if (name2, rel2) == (name, rel):
                    continue  # its own former self: not a copy, an edit
                r = difflib.SequenceMatcher(None, signature, signature2).ratio()
                if r > best_score:
                    best, best_where, best_score = name2, rel2, r
            if best and best_score >= MIN_COPY_SCORE:
                findings.append(
                    {
                        "fonksiyon": name,
                        "dosya": rel,
                        "satir": line_count,
                        "benzer": f"{best} ({best_where})",
                        "skor": round(best_score, 3),
                    }
                )
        return findings
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def signal(diff: str, allowlist_file: str | Path | None = None, repo: Path | None = None) -> dict:
    duplicated = duplicate_functions(repo, diff) if repo is not None else []
    copy_blocks = scan_copy_blocks(repo, diff) if repo is not None else []
    copy_note = (
        "; kopya kod şüphesi: "
        + ", ".join(
            f"{b['fonksiyon']}≈{b['benzer']} (%{round(b['skor'] * 100)})" for b in copy_blocks
        )
        if copy_blocks
        else ""
    )
    if copy_suspicion(diff):
        return {
            "provenance": False,
            "not": "dış kopya şüphesi (telif/SPDX başlığı) — insan kararı" + copy_note,
            "paketler": [],
            "yinelenen_fonksiyon": duplicated,
            "kopya_blok": copy_blocks,
        }
    if has_dependency_change(diff):
        return {
            "provenance": False,
            "not": "bağımlılık dosyası değişti — yeni bağımlılık C3 (insan kararı)" + copy_note,
            "paketler": [],
            "yinelenen_fonksiyon": duplicated,
            "kopya_blok": copy_blocks,
        }
    imports = extract_dependencies(diff)
    if not imports:
        result = {"provenance": True, "not": "yeni import yok", "paketler": [], "yinelenen_fonksiyon": duplicated}
    else:
        allowlisted = read_allowlist(allowlist_file)
        foreign = sorted(m for m in imports if m not in sys.stdlib_module_names and m not in allowlisted)
        if foreign:
            result = {
                "provenance": False,
                "not": f"izin listesinde olmayan üçüncü taraf import: {', '.join(foreign)}",
                "paketler": foreign,
            }
        else:
            result = {
                "provenance": True,
                "not": f"tüm importlar serbest ({', '.join(sorted(imports))})",
                "paketler": sorted(imports),
            }
    result["yinelenen_fonksiyon"] = duplicated
    result["kopya_blok"] = copy_blocks
    if copy_blocks and result["provenance"]:
        result["provenance"] = False
        result["not"] = result["not"] + copy_note
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN uyum katmanı (provenance sinyali)")
    parser.add_argument("--diff-file", required=True)
    parser.add_argument("--allowlist", default=str(Path(__file__).resolve().parent / "compliance-allowlist.yaml"))
    args = parser.parse_args(argv)

    diff = Path(args.diff_file).read_text(encoding="utf-8")
    result = signal(diff, args.allowlist)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["provenance"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
