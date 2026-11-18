# Evidence Update — Concept Corrections After Deep Research

**Date:** October 22, 2026
**Source:** [`../arastirma/KOVAN-DERIN-ARASTIRMA-2026-10-22.md`](../arastirma/KOVAN-DERIN-ARASTIRMA-2026-10-22.md)
**Purpose:** The research validated some of the concept's sentences and turned
others into ones that need fixing. This file keeps, in one place, what changes
in which document.

---

## 1. Three corrections (claim → evidence)

### D1 — "The self-learning factory" phrase must be narrowed

**Old sentence:** "KOVAN is a factory that learns overnight and improves its
own structure."
**Problem:** Systems in the literature (DGM, SICA) do not change model
weights; they change the **skeleton** (agent code, tools, control flow,
prompts). DGM says "frozen pretrained FMs" in its own text; `DGM_outer.py` is
fixed, i.e. the search procedure does not evolve.
**New sentence:** "KOVAN is a factory that evolves **its skeleton, its
skills, and its gate set** under a frozen model. Weight learning is out of
scope."
**Impact:** README §3 (İ4), LEARNING §1 and §6.4, ADR-F03.

### D2 — Not "the spec requirement is fading" but "the approval gates are being lifted"

**Old sentence:** "Spec-driven tools reduce the spec requirement; it turns
into a spec-maintenance burden."
**Problem:** Primary documents show the artifact is preserved: Kiro "all
three artifacts without approval gates"; Spec Kit "independent entry points,
not mandatory phases"; GSD quick "skips research, discussion, plan-checker,
verifier" but produces `PLAN.md`+`SUMMARY.md`. The "maintenance burden"
rationale does not exist in the official documents. The single exception is
BMAD: "small changes go straight to build".
**New sentence:** "In 2026, tools made the **approval gates** conditional;
the spec artifact is mostly preserved. What was removed, if it was a gate,
was evidence."
**Impact:** PRD FR-02/FR-05, ADR-F05, LEARNING §3 (the funnel), QUALITY §2.

### D3 — The "night shift" is not a calendar gain, it is a WIP increase

**Old sentence:** "7 hours of night production, a morning report."
**Problem:** As production capacity grows, acceptance capacity stays fixed:
PR volume ×2, median review time +441.5%. Night production grows the morning
queue; the flow does not speed up.
**New sentence:** "The night shift takes on **as much work as the morning
review capacity**. Production above capacity grows debt, not quality."
**Impact:** README §3 (İ6), ORGANIZATION §6, ROADMAP H5–H6, `loop/goal.yaml`
(max_parallel_workers).

---

## 2. Four additions (not in the concept)

### E1 — The review budget formula

```
Weekly review load (hours)  = Σ_PR ( LOC_PR / 500 ) + 0.25 × PR_count
Queue delay (M/M/1)         = (ρ / (1-ρ)) × (1/μ)
WIP limit (Little)          = target cycle time × daily PR count
```

Calibration: 400 LOC ≈ 0.8–1.0 h (Cisco/SmartBear); with μ=10 PR/day,
ρ=0.625 → ~4 h (Google <4 h), ρ=0.80 → 9.6 h, ρ=0.89 → ~19 h (Faros 441%),
ρ=0.95 → 45.6 h. Queue *length* and queue *time* must not be confused.
**Where:** PRD §9 ("review-hours/PR" instead of BMP), QUALITY §4,
ORGANIZATION §8.

### E2 — The seeded error set

The only method that measures whether the gates really catch: inject known
errors into a PR and measure the gate's catch rate. The defect-catch rate of
agent-to-agent review is **unmeasured** today; the nearest data is
observational (73.8% of comments change code, but that is not "caught an
error").
**Where:** QUALITY §3.1 (a new set type: `seeded`), ROADMAP H3.

### E3 — Judge calibration

In LLM-as-judge, raw agreement inflates chance-corrected κ by 33.8–41.3
points; "85% agreement" ≈ κ 0.48. Therefore:
- The gate report gives **κ**, not raw agreement.
- Position/length bias is tested.
- The judge is never a single gate.
**Where:** QUALITY §2.2 and §7.

### E4 — Identity, isolation, rollback

- No secret goes into the agent environment; short-lived identity via OIDC,
  scoped to the repo/branch.
- File and network isolation go **together**; if one is missing, the other
  is useless.
- `soft-delete` + backup isolation + a rollback drill.
- The reference incident: a database deleted in 9 seconds; the root cause
  was backups reachable with the same token.
**Where:** GOVERNANCE §2, §4, §8; `loop/goal.yaml sandbox`.

---

## 3. The six principles validated

| Principle | Evidence status |
|---|---|
| İ1 No evidence, no work | **Validated** — benchmark retirement, κ inflation, test hacking |
| İ2 Two gears | **Validated** — the production/acceptance separation |
| İ3 The immutable core | **Validated** — DGM keeps the search procedure fixed |
| İ4 Learning = file | **Validated** — memory is literally files; the alternative is not pursued |
| İ5 The evaluator can game it | **Validated** — three independent evidence lines |
| İ6 Production = review capacity | **Validated and quantified** — the formula was added |

---

## 4. Document mapping (the corrections to be applied)

| Document | Section | Change |
|---|---|---|
| `README.md` | §3 İ4, İ6 | The D1 and D3 sentences |
| `PRD.md` | §7 FR-02, FR-05; §9 | D2; the review-hours metric |
| `ARCHITECTURE.md` | §8 | The WIP limit formula |
| `ORGANIZATION.md` | §6, §8 | Night capacity; the review-hour scorecard |
| `LEARNING.md` | §1, §6.4 | D1; the "skeleton evolution" definition |
| `QUALITY.md` | §2, §3, §4, §7 | E2, E3, review-hours |
| `GOVERNANCE.md` | §2, §4, §8 | E4 |
| `ROADMAP.md` | H3, H5–H6 | The seeded set; night capacity |

These corrections have **not yet been applied**; this file is the auditable
list of the changes to be applied. Application is a separate work item
(v0.2).

---

## 5. New open questions

1. **How is the seeded error set built?** From error injection over the past
   100 PRs, or synthetic?
2. **How is review time measured?** Can session time be extracted from
   GitHub event logs?
3. **Where does the human label for κ calibration come from?** Who is the
   labeler in a one-person setup?
4. **How is night capacity capped?** How many PRs can you review in the
   morning; has that number been measured?
5. **In which files is "skeleton evolution" allowed?** `skills/`, `kadro/`,
   `loop/` — which is C1, which C3?

---

## 6. The single decision proposal

Two items should be added to the v0.2 scope:
1. **The review budget + the review-hours metric** (caps the night capacity).
2. **The seeded error set** (measures whether the gates really catch).

Both can be added to the existing architecture; they need no new component.
And both establish the only measurable ground of the "factory" claim.

---

## 7. The live-profile deviation (S2 · November 4, 2026)

The real model connection (adapter_http.py) and the real verification layer
(verify.py) went live. Two records:

1. **The runner boolean-signal bug was fixed.** On a gate carrying a
   `signal` field, a boolean `False` was counted as the numeric `0.0` and
   passed the gate. Now a boolean signal is treated as boolean under all
   conditions; a regression test was added (test_runner:
   `test_bool_signal_with_signal_field_is_boolean`).
2. **The live profile (gates-live.yaml):** the review and eval gates are
   temporarily *advisory*. Rationale: in S2 these gates produce no signal.
   This is not a loosening but a deferral: every line carries a dated
   rationale and, in S3 (eval v1 ≥50 cases + an independent reviewer), they
   return to blocking. The gate was **not removed**; a gate producing no
   signal already fails closed.

---

## 8. The S3 update (November 4, 2026)

1. **Eval v1 is live and blocking.** `eval_set/sicaklik-v1.jsonl` — a frozen
   90-case set (the golden values come from the existing reference behavior;
   the set catches behavior change, it does not prove mathematical
   correctness). `eval_run.py` applies the diff to the repo and runs the
   set, blocking at a 0.90 threshold. The broken-formula diff dropped the
   score below 0.90 (verified in a test). In the live profile, eval is now
   `blocking: true`.
2. **The set-writer error was also caught:** in the first set the `ortalama`
   cases produced 7 inconsistencies because of argument unpacking; the score
   dropped to 0.922. The set was fixed → 90/90. Lesson: the eval set must
   also pass the gate.
3. **The independent reviewer contract:** `reviewer.py` — a second model
   endpoint, a structured decision JSON, approval without a rationale
   auto-rejected. When `--inceleme-url` is given, the review gate escalates
   to programmatic blocking and the decisions land in the report; without
   it, it stays advisory.
4. **The night line runs (dry mode).** `shift.py`: sourced notes from
   local sources (15 claims), skill candidates from recurring lessons
   (seen ≥ 2), a seedtest-based break report (the type the live profile
   missed: a design error), a measurement-planned ADR draft from ledger
   statistics, and a 5-section morning report. C2 is closed at night; when
   a model connects, the same line switches to the adapter, the file
   contract does not change.
5. **The loop goal went live (November 4, 2026).** `kovan.py durum` — the
   cross-metrics of all runs (accept/block/reject, revisions, average
   occupancy, the most-falling gates, recurring lessons, the shift count).
   A **KOVAN-Gece** task was installed into Windows Task Scheduler: every
   night at 23:00 local python, dry mode (zero tokens); outputs go under
   `runs/` and `vardiya-runs/` + a log side file. Removal: `task-remove.ps1`.
   When the model key arrives, an `--adapter http` line is added inside
   `night-run.ps1`; the line stays the same. The task was verified by running
   it once by hand (gece-20261104-2026 / vardiya-20261104-2026; both ledgers
   sound).
7. **The provenance signal was tied to a real measurement.** `compliance.py`:
   extracts the new import roots from the diff; stdlib is free, third-party
   is free only if it is on the `compliance-allowlist.yaml` list, and a
   dependency-file change is REJECT (C3). This way all four blocking gates
   in the live profile (policy, tests, provenance, eval) run on real
   measurement; review is conditional (the reviewer), cost warns. SBOM
   (SPDX) and copy-code detection are in S4.

---

## 9. S4 first step — the "careful turn" (November 4, 2026)

No existing test broke (93 → 103, all green); the ornek-repo working tree is
clean; the previous two ledgers unchanged.

1. **The SBOM seed (`sbom.py`):** the repo's .py files are scanned with
   `ast` (no exec); stdlib and local modules do not enter the SBOM,
   third parties become SPDX 2.3 Packages (version if installed, otherwise
   NOASSERTION). ornek-repo: packages = 0 (only stdlib + local).
2. **Copy suspicion (compliance.py):** a Copyright/SPDX header in the added lines
   → provenance False, rationale "human decision". seedtest's `kopya_kod`
   error type is now tied to a measurable signal.
3. **`verify.py --geri-al`:** turns the repo back to HEAD and reports
   cleanliness.
4. **`kovan.py --kanarya N`:** only the first N of the accepted tasks run;
   the rest are counted as having spent capacity (honest accounting) and the
   report heading gets a CANARY stamp.
5. **Reading versions from the lock file:** `sbom.py` prioritizes the pinned
   versions in requirements/pyproject; the module→distribution mapping is
   resolved with `packages_distributions()` (yaml → PyYAML).
6. **Duplicate function detection (uyum):** if the function names added by
   the diff intersect with those in the repo, it lands in `uyum_not` — not
   blocking, a review signal. Not fail-closed: the information layer.
7. **The egress record (adapter_http):** if `--egress-log` is given, every
   external call is written to JSONL (ts, host, model, result) — the first
   concrete piece of the GOVERNANCE §4 audit item.

---

## 10. The first autonomous night + the first system-caught defect (November 5, 2026)

**KOVAN-Gece ran by itself at 04.11.2026 23:00** (LastTaskResult 0):
- kovan: 4 accepted / 1 block (K-107, policy) / 1 revision; ledger 6 records
  sound;
- vardiya: 15 sourced claims, a skill candidate, a break report, an ADR
  draft, a morning report;
- No C2 was written (compliant with constitution art. 3).

**The defect the system caught itself:** the skill candidate was being
regenerated every night (3 copies had accumulated). A recurring lesson is
not recurring "new learning" — distillation was made idempotent: candidates
are written to a shared directory, not written if present, and
`beceri_adayi_zaten_var` lands in the ledger. Regression test: over two runs
the file count does not grow, and the report writes "Zaten adaydı".

---

## 13. The release package (November 10, 2026)

1. **Security: dirty-tree protection.** `verify.uygula` now REFUSES to
   apply if `git status --porcelain` is dirty — in live mode it cannot wipe
   the user's uncommitted work with `reset --hard` (fail-closed, tested).
2. **Installation:** `fabrika/pyproject.toml` + entry points
   (`kovan/vardiya/tatbikat/beceri`). Evidence: after
   `pip install -e fabrika --no-build-isolation`, `kovan plan` ran from the
   repo root; the capacity valve correctly deferred K-103 at hour=2. Note:
   since py-modules live under `loop/`, the `package-dir` mapping was
   needed.
3. **Configuration:** `loop/user.yaml` — user defaults apply to all
   subcommands, CLI overrides. The argparse trap (the subparser default
   overriding the main default) was documented with a test.
4. **README.en.md** (an English quick start + security warnings) and **CI**
   (`.github/workflows/tests.yml`: 15 test files + the drill).
5. **.gitignore:** run evidence, logs, and key files excluded.

**The public-use target:** a self-hosted, bring-your-own-key developer.
A hosted service (SaaS) is the X2 non-goal (GOVERNANCE).

---

## 12. The S4 closing pieces (November 10, 2026)

1. **Copy-code block detection (level 2):** `uyum.kopya_blok_tara` — the
   diff is applied to a temporary clone; the new function bodies are
   compared against the repo's functions using a **structure signature**
   (an identifier/number/text-masked token sequence). Threshold: ≥12 lines,
   similarity ≥0.90; excluding its own former self. Evidence demo: a copy of
   the `istatistik` function with renamed variables scored 1.0 → provenance
   False. Live profile: copy suspicion makes provenance False (fail-closed,
   a human decision is required).
2. **The S1 runbook drill (`drill.py`):** a normal run, ledger
   verification, stopping with STOP, rollback on a dirty clone — 4/4 PASS.
   The CRLF comparison bug in A4's first version was fixed with the
   `git status --porcelain` criterion.
3. **Canary accounting:** `--kanarya N` reduces the running tasks to N; the
   remaining tasks are counted as having spent capacity (they enter the
   ledger as deferred).
4. **The weekly retro automation (`retro.py`):** computes the GPK proxy from
   the ledger (the first decision counts as the first pass if it is
   accepted), extracts the gate trend, and produces **runnable mechanical
   checks** (the ORGANIZATION §6 rule). Known limit: the GPK proxy mixes all
   runs — run-based separation is S3b.
5. **An A5 chaos step for the drill:** interruption → resume; the runner
   does not repeat an accepted task and retries the dropped one in the next
   shift (the fail-closed behavior was proven with the drill — 5/5 PASS).

**Remaining:** input only — the API key (live measurement) and a real
backlog (GPK/MBB). Also, mutation testing is live: **all** of the first
6 mutants were killed by eval and the real test run — the "gates catch"
claim is now enforcement-proven (a continuation of §12, November 10, 2026).

---

## 11. The first skill was activated (November 5, 2026)

**First the system twice REFUSED to approve itself** (art. 2 working):
`AKTİFLEŞTİRME RED: insan onay notu yok`. Then the founder was asked for the
decision (ask_user) and the approval was recorded.

- **The skill:** `tests-kapisi-tekrar-dusmesi` v0.2.0 — the procedure was
  turned into real code: `skill.test_zayiflatma_tespiti(diff)` (5 test
  cases: deletion, `assert True` weakening, a legitimate swap, outside
  tests/, file deletion).
- **Conditional execution:** the runner applies the skill only while
  `status: active`; a proposed skill cannot affect the pipeline (the code
  counterpart of art. 6).
- **Live simulation evidence:** the patch passing with `assert True` →
  `tests=False`, note: "beceri taraması: assertion zayıflatıldı", a usage
  record landed in `kullanim.jsonl` (ÖVD is now measurable).
- **The life cycle:** proposed → active → stale (90 days) → archived;
  activation criteria: the skill's test passes + evidence ≥ 2 tasks + human
  approval. The decay report: `skill.py rapor`.

**The learning loop closed end-to-end for the first time:** error → lesson →
skill candidate → human approval → active skill → enforcement in the
pipeline → the usage counter. No weight learning; **file learning** (İ4).

---

## 14. Queue progress live (November 10–16, 2026)

**Real autonomous-operation data:** between November 4–15, **10 night runs**
(Scheduler, LastTaskResult always 0) + **the first weekly retro (W46)** +
the first drill run. Total: 34 accepted / 8 blocked, all ledgers sound.

This week's three fixes:
1. **The drill log encoding bug:** Windows redirection produced a
   UnicodeEncodeError on a Turkish character; the task looked "successful"
   but the log was cut short. Fixed with `PYTHONIOENCODING=utf-8` +
   `Out-File -Encoding utf8`; verified with a manual run (5/5 PASS, the log
   is readable).
2. **Source rotation for the night line:** instead of the same 15 sources
   every night, the read ones are written to history
   (kaynak-gecmisi.jsonl) and the unread ones are scanned; when all are
   exhausted, they are re-read with an explicit "TEKRAR TARAMA" (rescan)
   mark. In the first turn, a resolved-path bug in the rotation code
   silently led to 0 sources being read — caught from the board, fixed,
   tested.
3. **The completion-aware queue:** with `--tamamlanan`, accepted tasks are
   recorded and skipped the next night — the queue advances. The fix:
   blocked tasks were also being recorded (the recurring-violation trend
   would have been lost); only accepted tasks are recorded, blocked ones
   are retried the next night (fixed with a test).

**ÖVD's first real data:** a single active skill (tests-kapisi-tekrar-
dusmesi), the usage counter in kullanim.jsonl. The number is still singular;
at the end of the 30-day window, ÖVD = usage / 30 will be measurable.

---

## 15. The print crash of the night runs — root cause and closure (November 16, 2026)

**Symptom:** 10 nights with sound ledgers, the summaries and reports
written; but every night's log had
`UnicodeEncodeError: 'charmap' codec can't encode 'ş'` and
`state/tamamlanan.jsonl` had never been created (the queue was not
advancing).

**Root cause:** when stdout is attached to a PIPE, Python uses the legacy
encoding (cp1252); a Turkish-character `print` kills the process on the last
line. Since all artifacts were written BEFORE the print, the run looked
"successful" — but the exit code was broken and the next step/log was cut
short. Also, `--tamamlanan` was never passed in the old gece-kos version;
that is why the record file did not exist.

**The fix:**
1. `console.py` + 11 CLI entries get `console.hazirla()`: stdout/stderr
   `encoding="utf-8", errors="replace"`. Output is not lost, the process
   does not die.
2. `night-run.ps1` / `week-run.ps1`: `PYTHONIOENCODING=utf-8` +
   `Out-File -Encoding utf8` (the Turkish log is now readable).
3. The `--tamamlanan` path is first taken into a variable and passed
   explicitly.
4. `console` was added to pyproject.toml py-modules (so it is not missing
   from the install).

**Evidence (end-to-end, with the entry the Scheduler uses):**
`night-run.ps1` was run by hand → `runs/gece-20261116-0941`: 5 accepted / 8,
4 accepted + 1 block, ledger OK; `state/tamamlanan.jsonl` was created
(236 bytes, only the accepted ones); the log is **clean** (no Traceback,
Turkish readable). From 23:00 tonight, the queue will advance.

**Lesson:** "artifacts exist" ≠ "the run succeeded". Exit code and log
integrity must enter the board — with this fix, the night report now checks
those too.

---

## 16. Queue progress evidence + the log-integrity net + publish prep (November 16, 2026)

**Queue progress (§15's promise, now real):** `night-run.ps1` was run by hand
→ `state/tamamlanan.jsonl` grew from 5 to 6 records (K-106 accepted and
recorded); blocks/deferrals still do not enter the record (the art. 4 rule
is preserved). The system no longer lives the same night twice: completed
tasks are not selected again.

**The night status ledger (a new safety net):** `night-run.ps1` now checks
both runs' **exit codes** and whether their logs contain a **crash
signature**, writing to `state/gece-durum.log`. The first record:
`20261116-1353 | kovan-cikis: 0 temiz: EVET | vardiya-cikis: 0 temiz: EVET`.

**The retro mechanical check — `python retro.py --log-saglik`:** scans
runs\*.log; reports those containing Traceback/UnicodeEncodeError, exits 1
if anything is broken. Critical finding: the old PowerShell logs had been
written **UTF-16 (with BOM)** — UTF-8 reading could not see "Traceback"
(NULs land between the characters). BOM detection was added and tested
(including a UTF-16 test; retro 6→11 tests). The live scan caught 9 broken
logs; they were moved to `runs/arsiv/` as evidence (outside the scan scope,
kept on disk).

**Publish prep:**
1. `pip install -e fabrika --no-build-isolation` → kovan-fabrika 0.2.1
   installed (editable, loop/); `kovan --help` and `vardiya --help` exit 0.
   Note: the CLI files (backlog etc.) resolve relative to cwd — the entry
   point giving `plan` in an empty directory is expected behavior.
2. CI: `test_queue_build.py` + `test_console.py` added to the test list
   (19 files); the "Log integrity scan" step entered (`--log-saglik`).
3. `.gitignore`: `fabrika/loop/state/` and `fabrika/loop/reports/` added
   (runtime state does not enter the repo; the ledger/evidence stays
   local).
4. Version 0.2.0 → 0.2.1.

**Lesson:** the monitoring chain must be completed — even if artifacts
(summary/report) are written, the exit code + log integrity + queue progress
are separate signals; now all three are recorded (gece-durum.log →
retro --log-saglik → tamamlanan.jsonl).

---

## 17. The industry-norm closure (November 16, 2026)

The norm audit found five gaps; all were closed this turn:

1. **Norm files** (all under fabrika/, Turkish at the time): CHANGELOG.md
   (Keep a Changelog + SemVer; 0.1.0→0.2.1), SECURITY.md (disclosure +
   the BYOK/egress design decisions), CONTRIBUTING.md (the turn norm,
   gate-order immutability, the art. 2 PR rule), CODE_OF_CONDUCT.md (the
   Contributor Covenant 2.1 model). At the repo root,
   `.github/PULL_REQUEST_TEMPLATE.md` + `ISSUE_TEMPLATE/` (bug + feature,
   with norm checklists). LICENSE copied into the package directory as
   Apache-2.0.
2. **pyproject PEP 639:** `license = "Apache-2.0"` (SPDX expression) +
   `license-files = ["LICENSE"]`; 9 classifiers; the `pyyaml>=6,<7` range
   pin; build-system setuptools>=77. **Learned:** once the license
   expression is used, the License classifier is rejected as an *error* by
   setuptools 77+ — the classifier was removed. Evidence:
   `pip install -e fabrika` exit 0; metadata: License-Expression
   Apache-2.0, Requires-Dist pyyaml<7,>=6.
3. **SBOM NTIA hardening:** the root package (the target project's
   name/version from pyproject, else NOASSERTION), a `supplier` for every
   package, DOC→root DESCRIBES + root→package DEPENDS_ON relationships.
   sbom 6→8 tests.
4. **Versioning:** 0.2.1 entered into the changelog; the SemVer norm
   written down.

**Result:** the five gaps in the norm-audit table closed; 162/162 tests.
The only remaining one-line job: `project.urls` — added when the real
GitHub repo address is created (no invented URL was written).

---

## 18. The project-identity decision — ADR-F13 (November 17, 2026)

Name research was done and the decision was recorded as ADR-F13: the brand
**KOVAN**, repo/PyPI **`kovan-fabrika`**, CLI `kovan`. Evidence: bare
"kovan" is taken on GitHub (vertexclique/kovan; boratanrikulu/kovan —
conceptual collision) and the Kovan testnet buries the searches; "fabric"
is polluted in the AI space (danielmiessler/Fabric etc.); a full-string
search for "kovan-fabrika" is empty. pyproject was already compliant; the
only pending item was `project.urls` (once the GitHub repo address is
created). The decision was also written into workspace memory.

---

## 19. Release: the kovan-fabrika repo is on GitHub (November 17, 2026)

**The ADR-F13 decision went into effect.** With the git identity registered
on the machine (kefyusuf; the token used in memory, never printed), the
repo was created and pushed:

- **Repo:** https://github.com/kefyusuf/kovan-fabrika (public, main)
- **Structure:** the repo root = the root README + LICENSE +
  CHANGELOG/SECURITY/CONTRIBUTING/CoC + .github (CI, PR/issue templates);
  the package lives under `fabrika/` — all existing paths (the CI
  working-directory, pip install -e fabrika, .gitignore) stayed unchanged.
- **Excluded:** runtime evidence (runs/, state/, reports/, vardiya-runs/,
  logs, .anahtar*, egress, kullanim.jsonl) and the ornek-repo's git
  history.
- **The security scan:** a credential/token pattern scan across 157 files
  came back clean.
- **The fresh-clone solution:** the tests expect ornek-repo to be a git
  repo; a "Sample repo preparation" step (init+commit) entered CI, and a
  fresh-clone note was added to CONTRIBUTING.
- **§17's last gap closed:** `project.urls` (Homepage/Repository/Changelog)
  entered pyproject; the CI badge on the root README.
- **CI:** the tests workflow started after the push (run 44078529278).

---

## 20. The release CI: the portability fix (November 17, 2026)

The first CI run (run 44078596115) **failed with 3 tests** — all vardiya:
the tests and the night queue depended on non-published workspace files
(`arastirma/…`); inside a fresh clone those files do not exist.

**The fix (the intent preserved, the mechanical dependency removed):**
1. `source-queue.yaml`: the 6 file sources are now inside the repo —
   fabrika/README, SYSTEM, ADR, PRD, QUALITY, EVIDENCE-UPDATE (+ the same
   2 URLs). A fresh clone + CI + local behave the same.
2. The `test_vardiya` rotation tests were made hermetic: a temporary root +
   temporary markdown (with a URL line); the dependency on document
   content — beyond `kaynak_tara`'s "produces records only from URL-carrying
   lines" fact — was removed (the root monkeypatched, finally-restored).
3. `test_verify`/`test_eval_run` expect a real git repo: a "Sample repo
   preparation" step in CI (init+commit), a fresh-clone note in
   CONTRIBUTING.

**Known limitation (accepted):** the new queue's factory documents are
URL-poor (2 URL lines) — the night scan's "sourced claim" output is limited
to the links in EVIDENCE/SYSTEM. When a real backlog + live mode arrive,
the queue will be filled with real targets; feeding the scanner with
invented URLs would violate the evidence-first norm.

**Result:** 162/162 local. The CI re-run was being watched.

**Closure (same day):** a third run with two more fixes — `sys.path.insert`
in `test_console.py` (locally the pip install masked it; on CI
ModuleNotFoundError) and the missing `test_simulation.py` added to the CI
list. The CI result: **success** (run 44081160418) — 20 test files (167
tests) + the retro smoke + log integrity + the S1 drill, green on a fresh
Linux clone. The SYSTEM.md totals row was updated to 167.

---

## 21. The post-release careful audit + the release flow (November 17, 2026)

**CI double-green:** the docs push (a2b95f7) also succeeded — run
44081360845. The badge is active.

**Dependabot security alerts:** opened via the repo API (vulnerability
alerts). Branch protection was deliberately NOT enabled: the stored
credential token's admin scope is unknown; in the single-developer initial
period, a direct push to main is the norm (the art. 2 reviewer rule will be
evaluated once the PR flow starts).

**The night line — the first real evidence of queue progress:** the
November 16/17 runs gave `kabul 0 | blok 1 | dur is_kalmadi` — the
completed ones (K-101…K-106) are NOT SELECTED AGAIN; the only remaining
task waits at the human gate (C1/C3). `state/gece-durum.log` has two clean
records (exit 0, logs YES). The system does not fake work with empty tasks —
an honest standstill.

**The release flow was formalized:** source editing in `Default\fabrika`;
`sync-yayin.ps1` (the project root) mirrors only the tracked file set into
`kovan-fabrika\` (except the evidence directories; the norm files go to the
root, the copies inside fabrika/ are deleted). First-run evidence: with no
changes, git came back CLEAN. The flow: edit → sync → commit → push.

**Remaining thresholds:** the API key (the live line), a real backlog,
optional branch protection.
