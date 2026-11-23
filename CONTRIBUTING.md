# Contributing to KOVAN

The short version: **every round follows feature → test → full suite →
doc sync.** This order comes from the project's own constitution
(m.2: producer ≠ approver) and has no exceptions.

## Development setup

```bash
pip install -e fabrika --no-build-isolation   # needed on embedded Python
cd fabrika/loop
python tests/test_kovan_cli.py                # smoke test
python kovan.py plan                          # dry mode: zero tokens
```

Requirements: Python ≥ 3.11, `pyyaml>=6,<7`. Live mode is **optional** and
works with your own API key; no test ever calls a model.

**Fresh-clone note:** `fabrika/loop/ornek-repo` ships as files only (no git
history). Tests expect it to be a git repository — run once:

```bash
git -C fabrika/loop/ornek-repo init
git -C fabrika/loop/ornek-repo add -A
git -C fabrika/loop/ornek-repo commit -m "ornek-repo initial state"
```

## Testing norms

- **19 test files, full suite green before opening a PR.** If the count
  changes, update the total line in `SYSTEM.md`.
- New behavior → test first. Changes touching gate logic must keep the
  gate-sequence tests in `tests/test_runner.py` intact.
- Determinism: `kuru_senaryo(isler, seed)` — same seed → same decisions.
- The weekly retro runs `--log-health`; log cleanliness is a PR norm.

## Rules for touching the gate sequence

Order: policy → tests → provenance → lint → types → review → eval → cost.
- Changing the gate order requires an **ADR** record (`fabrika/ADR.md`).
- PRs that demote a blocking gate to a warning are rejected by default.
- The eval threshold (0.90) changes only with mutation-test evidence.

## PR norms

1. Fill in the template (test count + doc-sync checklist).
2. **You cannot approve your own PR** (m.2) — an independent reviewer or the
   founder must approve.
3. Doc language: repository prose is English; historical research notes stay
   in their original language.
4. Runtime evidence (`runs/`, `state/`, logs) never enters the repo —
   `.gitignore` is ready.

## Communication

- Bugs: issue template (log + reproduction steps required).
- Security: the SECURITY.md flow — never a public issue.
- Conduct: CODE_OF_CONDUCT.md.
