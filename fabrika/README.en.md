# KOVAN — capacity-bounded, evidence-first AI software factory

> **Turkish documentation is the source of truth** (`README.md`, `SISTEM.md`,
> `ADR.md`, …). This file is the English quickstart for public users.

**One-line thesis:** production is cheap, *acceptance* is expensive. KOVAN is
a production pipeline that refuses to accept more work than its **review
capacity**, runs every change through six deterministic/statistical gates,
writes every decision to a hash-chained ledger, and turns repeated failures
into tested skills — with **no weight learning**: only the scaffold, skills
and gate set evolve.

---

## What works today (offline, no API key)

```bash
cd fabrika/loop

python kovan.py plan        # capacity valve: which tasks fit today's review hours?
python kovan.py run         # spec → failing test → patch → gates → ledger → report
python vardiya.py run       # night shift: sources → distillation → red team → ADR → report
python mutasyon.py --maks 6 # gate kill-rate: are the gates real? (6/6 mutants killed)
python retro.py             # weekly retro: first-pass yield + mechanical checks
python kovan.py durum       # cross-run metrics (accept rate, gate failures, capacity)
python tatbikat.py          # S1 runbook drill: run, verify, STOP, chaos/resume, rollback
```

**107-line night shift included**: a scheduled task example writes a
morning report to `vardiya-runs/<id>/sabah-raporu.md` while you sleep
(dry mode = zero tokens).

Everything above runs **deterministically without any model**: the "coder"
is a scripted dry adapter. **120+ unit tests** prove the pipeline mechanics
(gate order, fail-closed, budget, circuit breaker, tamper detection).

## Live mode (bring your own key)

```bash
python kovan.py run --adapter http \
  --base-url https://api.openai.com/v1 --model gpt-4o-mini \
  --anahtar-dosya .anahtar \
  --repo /path/to/YOUR-git-repo \
  --test-komut "python -m unittest discover -s tests -t ." \
  --eval-set eval_set/sicaklik-v1.jsonl \
  --egress-log egress.jsonl
```

What the model gets: the task, the class, the allowed files.
What the model **never** gets to decide: test/eval/provenance signals —
those come from **real execution** on your repo (`git apply` in a temp
clone, real test run, rollback).

## SECURITY — read before live mode

1. **Clean tree required.** Patch application refuses on a dirty working
   tree, because rollback uses `git reset --hard`. Untracked files are
   removed by rollback's `git clean -fd` — use a **dedicated repo or
   worktree**, never your personal working copy.
2. **No secrets in the agent environment.** Put the API key in a file
   outside the repo; the adapter logs every call to `--egress-log`.
3. **Model output is never evidence.** Test/eval signals come from real
   execution; the reviewer is a *second, different* endpoint and its
   approve-without-reason is auto-rejected.
4. **Self-modification is gated.** Skills activate only after their own
   tests pass, evidence ≥ 2 tasks, and a recorded human approval
   (the system refuses to self-approve — m.2).

## Eval set — your moat

The frozen case set is the factory's most valuable asset. Template and
discipline: `eval_set/SABLON.md` (schema, golden-value honesty rules,
freezing/rotation, the 5 set-killing anti-patterns).

## Configuration

`fabrika/loop/kullanici.yaml` (see file for all keys):

```yaml
saat: 3.0          # your daily focused review hours — the system's ceiling
backlog: my-backlog.yaml
hedef_repo: /path/to/your-repo
base_url: https://api.openai.com/v1
model: gpt-4o-mini
anahtar_dosya: /secure/path/.anahtar
```

CLI flags override the config. Windows scheduler: `gorev-kur.ps1`.
Linux/macOS cron example:

```cron
0 23 * * * cd /path/to/repo/fabrika/loop && python vardiya.py run >> vardiya.log 2>&1
30 23 * * * cd /path/to/repo/fabrika/loop && python kovan.py run >> kovan.log 2>&1
```

## Tests

```bash
cd fabrika/loop
python tests/test_runner.py    # pipeline: 23
python tests/test_kapasite.py  # capacity valve: 18
python tests/test_uyum.py      # provenance + copy detection: 17
python tests/test_vardiya.py   # night shift + source rotation: 11
python tests/test_mutasyon.py  # gate kill-rate proof: 4
# … 17 files, 143 tests, no model calls required
```

## Documentation (Turkish, sourced)

- `SISTEM.md` — the concrete system (v2, supersedes)
- `PRD.md`, `MIMARI.md`, `ORGANIZASYON.md` — requirements, architecture, org
- `OGRENME.md` — how learning works (files, not weights)
- `KALITE.md` — gates, eval discipline, metric definitions
- `YONETISIM.md` — threat model, compliance, cost
- `EVIDENCE-UPDATE.md` — every correction research forced, with dates

## Status

Concept complete, pipeline skeleton proven (131 tests), live mode wired but
unmeasured: **no API-key runs have happened yet, so no accuracy/cost claims
are made.** Honest-limitations list: `EVIDENCE-UPDATE.md` §11.

License: Apache-2.0.
