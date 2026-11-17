# KOVAN — Roadmap, Risks, Kill Criteria

> 12 weeks. Each week one output and one gate. A "weekly goal" sentence that
> is not measurable was not written.

---

## 1. Milestones

| # | Week | Name | Exit criterion (evidence) |
|---|---|---|---|
| **M0** | 0 | Concept + core | This document set + `runner.py` 22 tests |
| **M1** | 1–2 | Single line, real model | 1 adapter, a 20-task queue, policy integrated |
| **M2** | 3–4 | Real measurement | Eval set v1 (≥50), 20 tasks end-to-end, GPK/MBB measured |
| **M3** | 5–6 | Night shift | 5 consecutive morning reports |
| **M4** | 7–8 | Skills | 3 candidates → 1 active skill, having passed shadow mode |
| **M5** | 9–10 | Self-improvement | 1 C1 change through canary + the rollback test |
| **M6** | 11–12 | Hardening | Sandbox, SBOM, 2 weeks uninterrupted |

---

## 2. Weekly plan

### Week 1 — Connect the model
- **Work:** the `Adapter` implementation (one provider, one model); 3 tools:
  file read/write, shell, search. Wire the `policy` gate to the Airlock CLI.
- **Output:** 5 real tasks, no dry run.
- **Gate:** 3 of the 5 tasks pass the gates (GPK ≥ 60%, "indicative" at small n).
- **Risk:** the model output is far noisier than the scenario → a high
  rejection rate.

### Week 2 — Queue and cost
- **Work:** `backlog.yaml` (priority, dependency, class), token accounting,
  the cost manifest, the `butce-bekcisi` rules.
- **Output:** a real 20-task queue; the first cost report.
- **Gate:** MBB measured (a single number + n).
- **Risk:** the cost diverges 3–5× in the first week; do not continue
  without a ceiling.

### Week 3 — Eval set v1
- **Work:** a regression set from the past 50 errors; 30 adversarial cases;
  the set-ownership separation; the manifest.
- **Output:** `olcum/sets/regression-v1/`, the `eval` gate becomes real.
- **Gate:** the set catches the 5 known errors (kappa > 0.6 between two
  labelers).
- **Risk:** if the set is seen by the agent writing the rules, it burns →
  access separation.

### Week 4 — The first real measurement
- **Work:** 20 tasks end-to-end; GPK, BMP, MBB, DSP (sampled); the first
  retrospective.
- **Output:** `rapor/olcum-hafta-4.md` — the numbers + the error list.
- **Gate:** the measurement is reproducible (the same set, two runs, ±5%).
- **Risk:** the sample is small; learn to say "indicative", not "result".

### Week 5 — The night shift skeleton
- **Work:** the R2 loop: agenda, time boxes, the source allowlist, raw
  note → claim.
- **Output:** 1 night, a partial report.
- **Gate:** the report is on file by 06:00 (the content may be weak).
- **Risk:** the agent falls into a rabbit hole; the time box must be hard.

### Week 6 — Five nights
- **Work:** 5 nights in a row; each night 2–4 notes, 0–2 skill candidates.
- **Output:** 5 morning reports + an accumulation of `lessons`.
- **Gate:** 5/5 reports; at least 3 sourced notes per night.
- **Risk:** repeating content; the arsivci's duplicate merging must kick in.

### Week 7 — Distillation
- **Work:** the `SKILL.md` schema, the 5-step distillation, the test
  requirement, shadow mode.
- **Output:** 3 skill candidates, each with a test.
- **Gate:** one of the candidates measured in shadow on 20 tasks.
- **Risk:** slogan skills; the "behavior change" test must cut those.

### Week 8 — The first active skill
- **Work:** activate 1 skill; the before/after measurement (same task class).
- **Output:** `skills/*/SKILL.md` + the measurement record.
- **Gate:** ≥ 10% improvement on the target metric or ≥ 15% cost reduction.
- **Risk:** the improvement is indistinguishable from noise → repeat for
  2 weeks.

### Week 9 — The C1 proposal and canary
- **Work:** a prompt/roster change proposal (an ADR draft), shadow → canary
  → full.
- **Output:** 1 canary release, a rollback drill.
- **Gate:** the rollback works within 60 seconds.
- **Risk:** if the rollback is not tested, it will not work in the first
  real incident.

### Week 10 — The structure proposal
- **Work:** R4: 1 ADR draft from the ledger ("which role is redundant",
  "which gate is slow").
- **Output:** `oneri/ADR-F13-*.md`, with a measurement plan.
- **Gate:** the proposal enters the 14-day wait (it is not applied).
- **Risk:** the proposal count bloats; the ≤ 2/week limit.

### Week 11 — Hardening
- **Work:** the sandbox (container + allowlist), SBOM, the egress log, the
  S1 runbook drill.
- **Output:** isolation evidence (running with the network cut),
  `uyum/sbom.json`.
- **Gate:** a write attempt outside the sandbox is blocked.
- **Risk:** the sandbox slows things down by 30%; that must be accepted.

### Week 12 — Closure
- **Work:** 2 weeks of uninterrupted running; all metrics; an honest
  closing report.
- **Output:** `rapor/v1-kapanis.md` — what happened, what did not.
- **Gate:** none of the kill criteria triggered.
- **Risk:** the pressure toward a "success" narrative; the report writes
  the bad news first.

---

## 3. Risk register

| # | Risk | Likelihood | Impact | Countermeasure | Trigger |
|---|---|---|---|---|---|
| R1 | Agent output unreliable, high rejection rate | High | Medium | Small tasks + a strong spec | GPK < 25% (week 4) |
| R2 | The eval set burns / becomes circular | High | High | Ownership separation + set identity | A second improvement on the same set |
| R3 | The cost ceiling is exceeded | Medium | High | Reservation + tier dropping | MBB > 10 USD (2 weeks) |
| R4 | The night report hollows out | Medium | Medium | Time box + the "empty" label | < 2 notes 3 nights in a row |
| R5 | The review bottleneck | High | Medium | İ6: the review budget | Queue > 2 days |
| R6 | Skill inflation | Medium | Medium | Usage counter + decay | 10 skills, < 3 used |
| R7 | Prompt injection | Medium | High | Isolation + the measured trifecta ban | Any S1 incident |
| R8 | A secret leak | Low | Very high | No secrets + forbidden paths | `.env` in a diff |
| R9 | A license violation | Low | High | Provenance + the allowlist | A new dependency |
| R10 | Self-authorization | Low | Very high | C3 + forbidden paths + the ledger | A constitution diff |
| R11 | Dependence on a single person | High | Medium | Every decision in a file | The founder absent for 7 days |
| R12 | The "factory" metaphor not selling | Medium | Low | The product name: gates + memory | 3 customer conversations |

---

## 4. Kill criteria

These are not a "things are going badly" feeling; they are **stop**
conditions. When one triggers, the project stops, is redesigned, or closes.

| # | Criterion | Threshold | Decision |
|---|---|---|---|
| **Ö1** | Gate pass rate | GPK < 25% at week 6 (n ≥ 20) | Change the approach: shrink the tasks, harden the spec |
| **Ö2** | Unit cost | MBB > 10 USD for 2 weeks | Stop: the economics do not work |
| **Ö3** | Night reliability | Reports on < 5 of 10 nights | Close R2: the night shift is not ready |
| **Ö4** | Regression | KKA > 5 / 100 PRs | Stop: speed is eating quality |
| **Ö5** | Learning | 0 skills activated in 3 months | Drop the "learning factory" claim; continue as a production line |
| **Ö6** | Audit | The ledger cannot be verified (once) | Stop immediately: every claim is invalid |

**Ö6 is special:** a single verification failure makes every other metric
meaningless.

---

## 5. What can be done tonight (realistically)

This deliverable was produced in a single night; the following is the
**generalizable** plan of that same night:

| Time | Work | Output | Status |
|---|---|---|---|
| 21:00–22:00 | Goal contract + scope | `goal.yaml` | ✅ done |
| 22:00–23:30 | Parallel research (7 lines) | `arastirma/*.md` | ✅ 3 files + summaries |
| 23:30–01:00 | Concept + PRD | `README.md`, `PRD.md` | ✅ |
| 01:00–02:00 | Architecture + org | `ARCHITECTURE.md`, `ORGANIZATION.md` | ✅ |
| 02:00–03:00 | Core code + tests | `loop/runner.py`, 22 tests | ✅ |
| 03:00–04:00 | Learning + quality + governance | 3 documents | ✅ |
| 04:00–05:00 | ADR + roadmap | `ADR.md`, this file | ✅ |
| 05:00–06:00 | Self-audit + morning report | `SELF-REVIEW.md` | ✅ |

**What could not be done (honestly):** a real model connection, a real eval
set, real cost, market conversations, legal review. These cannot be shown
as "done" in a single night; they are listed as gaps in `SELF-REVIEW.md`.

---

## 6. The morning checklist (5 minutes)

1. `fabrika/loop/ornek-cikti/sabah-raporu-ornek.md` — is the report readable?
2. `fabrika/loop/tests/` — do the 22 tests pass? (`python tests\test_runner.py`)
3. `fabrika/ADR.md` — are all 12 decisions understandable on one page?
4. `fabrika/SELF-REVIEW.md` — are the three weakest assumptions acceptable?
5. Decision: proceed to M1, or narrow the scope?

The fifth item is the only real decision; the other four feed it.
