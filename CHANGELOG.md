# Changelog — KOVAN

Format: [Keep a Changelog](https://keepachangelog.com/) · Versioning: [SemVer](https://semver.org/).
All dates UTC. This log tracks the `fabrika/` package (kovan-fabrika).

## [0.2.1] — 2026-11-16

### Fixed
- **Windows console trap (cp1252):** with stdout/stderr attached to a pipe,
  Turkish `print` output killed the process with `UnicodeEncodeError`; ten
  night runs crashed *after* artifacts were written. `konsol.hazirla()` is
  now bound at 11 CLI entry points (UTF-8 + `errors="replace"`).
- `gece-kos.ps1` / `hafta-kos.ps1`: `PYTHONIOENCODING=utf-8`, UTF-8 logs,
  the `--tamamlanan` path is passed via a variable.
- Queue progression proven: `state/tamamlanan.jsonl` grew 5→6 records
  (K-106); blocked/deferred tasks still never count as done (m.4 rule).

### Added
- `retro.py --log-saglik`: scans run logs for crash signatures
  (Traceback/UnicodeEncodeError; UTF-16 BOM detection included). Exits 1
  when a broken log exists — the weekly retro emits this as a mechanical
  check.
- `state/gece-durum.log`: nightly record of both runs' exit codes + log
  cleanliness.
- CI: `test_kuyruk_uret.py` + `test_konsol.py` joined the list; a "log
  integrity scan" step was added.
- Sector-norm files: CHANGELOG, SECURITY, CONTRIBUTING, CoC, PR/issue
  templates; pyproject PEP 639 license + classifiers.

### Package
- The `konsol` module joined py-modules (never missing after install).
- Version 0.2.0 → 0.2.1.

## [0.2.0] — 2026-11-08 (v2 system)

### Added
- 3-line architecture: **vardiya** (night source scan), **gece** (gated
  run), **hafta** (retro + drill); roles reduced 14→6.
- Queue progression: accepted tasks are recorded via `--tamamlanan`;
  blocked ones never are.
- `dogrula.py`: git apply + real test execution; dirty-tree protection
  (fail-closed) and a `--geri-al` CLI.
- `uyum.py`: duplicate-block detection (structural signature, 6-variant
  robustness-tested), duplicate functions, allowlist.
- `adapter_http.py`: OpenAI-compatible adapter, egress logging; produces
  no gate signals.
- `sbom.py`: SPDX 2.3 JSON (toward NTIA minimum elements).
- `mutasyon.py`: AST mutations + kill score (6/6 mutants killed).
- `tatbikat.py`: S1 runbook, 5 steps (5/5 PASS); `simulasyon.py` N-day
  operation simulation; `kuyruk_uret.py` evidence-based task proposals.
- Live gate order: policy→tests→provenance→lint→types→review→eval
  (blocking, 0.90)→cost.

## [0.1.0] — 2026-11-04 (first line)

### Added
- `kovan.py` core: capacity-bounded plan/run/verify/status; ledger (JSONL),
  budget, circuit breaker, plateau, resume.
- `kapasite.py`: LOC→hours, M/M/1 queue, acceptance decision; `seedtest.py`
  deterministic scenarios.
- Scheduler installations: KOVAN-Gece (23:00), KOVAN-Hafta (Fri 18:00).
