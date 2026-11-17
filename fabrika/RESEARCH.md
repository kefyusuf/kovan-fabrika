# KOVAN — Research Notes

> This document records which external ideas the concept rests on and
> **which claims were not verified**. The aim is not a literature survey;
> it shows how each finding turned into design.

**Evidence levels:** **[A]** measured in this system · **[B]** a primary
external source (official document, repo, arXiv) · **[C]** second-hand /
agent research; the source exists but was not independently verified ·
**[D]** could not be verified.

**Method.** Seven parallel research lines: (1) Karpathy, (2) Matt Pocock,
(3) Superpowers + the skill/subagent architecture, (4) GSD + the
spec-driven movement, (5) commercial/open-source factories, (6) the
self-improvement literature, (7) governance/compliance. Three lines' full
notes live under `arastirma/`; the other four stayed at summary level (they
could not be filed due to the tool budget) and are marked **[C]** here.

---

## 1. Andrej Karpathy — the constraint is not intelligence, it is verifiability

**Finding.** In Karpathy's framing, "Software 3.0" is programming with
context/prompt/tools; but in production, verification, testing, security,
and human understanding remain mandatory. The distinctive sentence:
*"Software 1.0 specifies, Software 2.0 verifies"* — a job automates to the
extent it can be re-run and measured. **[C]** (the primary texts are listed
in `arastirma/01-karpathy.md` §3.4)

**Second finding: autonomy is graded.** Karpathy's "autonomy slider"
(Tab → Cmd+K → Cmd+L → Cmd+I) is a product control surface; not unleashing
the agent, but running it in verifiable slices. **[C]**

**Third finding: minimal, single-repo, end-to-end artifacts increase
reliability.** micrograd (~150 lines), llm.c (~1,000), nanochat (one dial,
one metric), autoresearch (3 files, the single metric `val_bpb`). A small
and understandable system is an auditable system. **[C]**

**Carried into design (→ ADR):**
- Classify tasks on the **verifiability axis** (F05, F08).
- Grade autonomy; make the "slider" a product surface (F08).
- A single-metric, fixed-budget experiment loop (F09, QUALITY §4).
- One repo, small artifacts, few dependencies (F10).

**Not carried:** "vibe coding" practices do not enter the production line;
prototype speed and production acceptance are not the same thing.

---

## 2. Matt Pocock — the spec is a decision record, not plan mode

**Finding.** Pocock abandoned the "plan mode" approach and moved to
documents + **seam contracts**: the spec is not a long plan but the
contract of the decisions taken and of the vertical slice (the seam). The
ideal seam count is 1; the spec is written only for multi-session work. **[C]**

**Verification discipline.** Deterministic tools (`tsc`, Vitest, lint,
pre-commit/CI) act as gates; the retrospective produces a **mechanical
check**, not "let's be more careful". **[C]**

**Review.** On two axes, in a separate context: *Standards* and *Spec*.
Every finding demands a location (file + line). Sub-agent output counts as
a **hypothesis**, not evidence. **[C]**

**The skill/subagent/script separation.** Skill = procedure; subagent =
context isolation (single level); script/CI = deterministic, human-free
enforcement. **[C]**

**Carried into design:** F05 (the command-bearing acceptance criterion),
F06 (deterministic > judgment), QUALITY §2.2 (review with rationale),
ORGANIZATION §5 (artifacts at the handoff).

---

## 3. Superpowers — a process engine, not a prompt collection

**Finding.** `obra/superpowers` (MIT, Jesse Vincent / Prime Radiant), as of
**v7.0.0 (2026-10-10)**, is a process engine made of 15 model-calling
skills; the slash commands are only three thin shells. Its value is not in
scope but in **rule hardness**: "no production code without a test", "no
'done' without fresh verification evidence", "a breaker after 5 rounds",
and the "rationalization" tables listing the model's own excuses. **[B]**
(repo + release notes; `arastirma/03-superpowers.md`)

**The cost finding.** ~22k tokens loaded at startup, a controller context
reaching 603k within a single session, 18 fix rounds caused by a skill
truncated at 20,000 characters after compaction — all documented as issues. **[C]**

**The official Claude Code side.** Skill = a directory whose body loads
when used; subagent = a separate context with its own toolset; hook = a
deterministic gate running ahead of the permission system. Together the
three separate "process" from "enforcement". **[C]**

**Carried into design:** F02 (a testable skeleton), F04 (the SKILL.md
unit), F06 (evidence > claim), QUALITY §2.1 (the test-weakening ban), the
`loop/agents.yaml` handoff rules.

**Not carried:** moving all 15 skills. KOVAN starts with 14 roles + 5–8
skills; the skill count is not a success indicator (LEARNING §7).

---

## 4. GSD and the spec-driven movement — the limit of the spec

**Finding (GSD).** `gsd-build/get-shit-done` was archived; development
continues under `open-gsd/gsd-core` (v1.18.0, MIT) **[C]**. The critical
detail: in GSD, `SPEC.md` is **optional**; that is, the movement's
"spec = single source of truth" slogan is not absolute in the tool's own
implementation **[C]**. GSD's real contribution is not the spec but **phase
management**: `STATE.md`, `ROADMAP.md`, phase transitions, goal-backward
validation.

**Finding (the movement).** Spec Kit (`/specify` → `/plan` → `/tasks`),
Kiro (spec → design → tasks), BMAD (a role-based agent team) are different
solutions to the same need. The shared claim: code is derivative, the spec
is the source. The shared failure: **spec drift** — the spec is not
updated, nobody reads it, and the code becomes the only truth. **[C]**

**Carried into design:** F05 (spec = executable criterion + the drift
audit), ARCHITECTURE §6 (phase/state files), the ROADMAP's weekly output
discipline.

**Lesson.** "Write a spec" is not the solution; **measuring the spec** is.
That is why in KOVAN the spec does not accept sentences without commands.

---

## 5. Software factories — the market consolidated, the architecture converged

**Finding 1: eight common patterns.** An isolated VM/container per task;
plan → implement → test → review; a review agent; multi-agent roles; human
approval gates; fleet management; model steering; a persistent environment.
Every pattern was verified first-hand in at least two products. **[C]**
(`arastirma/05-fabrikalar.md` §7)

**Finding 2: the benchmark diverged.** The same model is shown between 58.0
and 69.9 across different harnesses; the gap between leaderboards is 20+
points. A single number is no longer meaningful. **[C]**

**Finding 3: production metrics contradict each other.** To the same
question ("how many agent PRs merge") four different answers: the vendor
report 67%, the peer-reviewed comparison 61.6%, a secondary analysis 32.7%
— different populations are being measured. **[C]**

**Finding 4: the real cost is coordination.** Independent measurements show
developers can slow down with AI (the METR RCT, 19%; its data was later
declared unreliable), DORA 2026 found a −1.5% association in delivery speed
and −7.2% in stability; 79.4% of agent PRs sit open concurrently in the
same repo. **[C]**

**Finding 5: five structural failures.** The ambiguity wall; the review
bottleneck; coordination collision; measurement inflation; the loss of
audit. **[C]**

**Carried into design:** İ6 (the review budget), ARCHITECTURE §8 (single
writer, worktrees, the file lock), QUALITY §3.2 (set identity, harness
pinning), ADR-F07 (Airlock).

**Not carried into design:** "fleet" scale. A 20-agent roster is an
unmeasured review queue; KOVAN starts with 3–5 concurrent workers.

---

## 6. Self-improvement — the agent produces the proposal, the gate grants acceptance

**Finding 1: the literature is real but narrow.** Darwin Gödel Machine
(arXiv:2505.22954) went 20% → 50% on SWE-bench; SICA (arXiv:2504.15228)
17% → 53%; AlphaEvolve (arXiv:2506.13131) reduced 4×4 matrix
multiplication to 48 multiplications. **[C]** (the arXiv ids come from an
agent report; the full texts must be verified)

**Finding 2: the real bottleneck is evaluator fidelity.** The DGM's
test-hacking is documented; while SWE-bench Verified was being produced, a
significant share of the samples was discarded as flawed. **[C]**

**Finding 3 — our own measurement [A].** On this project the rule set
scored **F1 1.000** on the 30 cases it had written itself and **0.394** on
a realistic holdout; the holdout was then declared "burned" (see
`../STATUS.md` §4). This is the most concrete justification of the whole
concept: **circular measurement is not measurement.**

**Carried into design:** F06 (D1 > D2 > D3), QUALITY §3.2 (holdout
discipline), LEARNING §6.3 (a candidate that changes eval is
auto-rejected), F03 (the immutable core).

**The critical distinction.** "Prove" (the Gödel machine) versus "measure"
(experiment + gate). A weaker guarantee, but the only workable one.

---

## 7. Governance — architectural control, not policy prose

**Finding 1: the frameworks.** ISO/IEC 42001 (an AI management system),
NIST AI RMF (Govern–Map–Measure–Manage), the EU AI Act (risk classes +
technical documentation + human oversight) all look in the same direction:
**risk class, ownership, evidence, oversight**. **[C]**

**Finding 2: dates.** Annex III high-risk obligations were reported as
December 2, 2027, and Annex I as August 2, 2028; the "it starts in August
2026" information looks stale. **[C]** — confirmation from the official
text is mandatory before release.

**Finding 3: the lethal trifecta.** Private data + untrusted content +
outbound communication must not coexist in one session. Token passthrough
is banned in MCP; tool annotations are not trustworthy; a devcontainer is
not a security boundary. **[C]**

**Finding 4: the supply chain.** SBOM (SPDX/CycloneDX), SLSA levels, signed
artifacts. **[C]**

**Finding 5: the law.** In 2026 an appellate ruling (Doe v. GitHub, 9th
Cir.) reportedly narrowed the training-data claims; the copyright risk
remains. **[C]** — not legal advice.

**Carried into design:** GOVERNANCE §1–§9 (the threat model, isolation,
human gates, SBOM, the runbook), constitution articles 6 and 8.

---

## 8. Synthesis: from finding to decision

| Finding | Principle | Decision |
|---|---|---|
| Verifiability determines automation | İ1, İ5 | F05, F06 |
| Autonomy is graded | İ3 | F08 |
| Production is cheap, acceptance is expensive | İ6 | the review budget |
| The evaluator can game it | İ5 | F06, QUALITY §3 |
| Experiment > proof | İ4 | F02, LEARNING §6.4 |
| Memory accumulates in files | İ4 | F11 |
| The core must be immutable | İ3 | F03 |
| The coordination cost is real | — | ARCHITECTURE §8 |
| Policy must live at the tool level | — | F07 |
| Portability is harness-independent | — | F12 |

---

## 9. What cannot be verified (the honesty list)

Every number marked **[C]** in this document is the summary of an agent
research run; full-text or official-source verification was not done in
this round. In particular:

1. **Versions and dates** (Superpowers v7.0.0, GSD v1.18.0, the EU AI Act
   dates) — from autumn 2026; confirmation needed before release.
2. **Benchmark percentages** — they cannot be compared without stating the
   harness and date; deliberately not listed one by one in this document.
3. **The METR/DORA findings** — the RCT's own update declared the data
   "unreliable"; that is why we do not say "AI slows you down", we say
   "the measurement is contested".
4. **The Karpathy quotes** — the X posts' dates and full texts can change;
   the primary archive is in `arastirma/01-karpathy.md`.
5. **The Pocock practices** — one instructor's workflow; generalizability
   unproven.
6. **The legal situation** — no section is legal advice.

A claim marked **[D]** is not listed here, because it was not used in the
concept.

---

## 10. Bibliography (summary)

**Primary / official**
- `github.com/obra/superpowers` — README, `skills/`, release v7.0.0
- `github.com/open-gsd/gsd-core` — README, ADR-1820 (SPEC.md optional)
- `github.com/github/spec-kit` — `/specify`, `/plan`, `/tasks`
- `aihero.dev` — Matt Pocock, AI Hero content
- `karpathy.bearblog.dev`, `x.com/karpathy`, `github.com/karpathy/nanochat`
- `arxiv.org/abs/2505.22954` (DGM), `2504.15228` (SICA), `2506.13131` (AlphaEvolve)
- `iso.org/standard/81230.html` (ISO/IEC 42001), `nist.gov/itl/ai-risk-management-framework`
- `artificialintelligenceact.eu` — the implementation timeline
- `modelcontextprotocol.io` — security notes

**Secondary / analysis**
- `arastirma/01-karpathy.md`, `arastirma/03-superpowers.md`, `arastirma/05-fabrikalar.md`
- `LLM-Self-Improvement-Report.md` (this repo) — the self-improvement literature
- `STATUS.md` (this repo) — the circular measurement case

**Note:** the source list is a record of "accessed", not a claim of
"read". Each one's full text must be re-checked before release.
