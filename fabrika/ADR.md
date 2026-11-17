# KOVAN — Architecture Decision Records (ADR)

> Each ADR defends a single decision: **context → decision → consequences →
> rejected alternatives**. Decisions can be reversed; but reversing one also
> requires an ADR. The ordinals carry the `F` prefix because this is a separate
> product line (it must not be confused with the Airlock ADRs 0001–0010).

| # | Decision | Status |
|---|---|---|
| [F01](#adr-f01) | The product's output is evidence-backed change | Accepted |
| [F02](#adr-f02) | Skeleton first, model later | Accepted |
| [F03](#adr-f03) | Immutable core / mutable shell | Accepted |
| [F04](#adr-f04) | The unit of learning is the skill, not code | Accepted |
| [F05](#adr-f05) | Spec = executable acceptance criterion | Accepted |
| [F06](#adr-f06) | Verification hierarchy: D1 > D2 > D3 | Accepted |
| [F07](#adr-f07) | Tool policy goes through Airlock | Accepted |
| [F08](#adr-f08) | Change classes C0–C3 | Accepted |
| [F09](#adr-f09) | Model tiering + budget ceiling | Accepted |
| [F10](#adr-f10) | Files + git + SQLite; no workflow engine | Accepted |
| [F11](#adr-f11) | Memory is append-only; no deletion | Accepted |
| [F12](#adr-f12) | Borrow patterns, not a framework | Accepted |
| [F13](#adr-f13) | Project identity: KOVAN brand + kovan-fabrika namespace | Accepted |

---

## ADR-F01
### The product's output is evidence-backed change

**Status:** Accepted · **Date:** 2026-10-21

**Context.** Market products are measured by "code generation": lines, PR
counts, benchmark scores. But getting generated code accepted is a separate
job; and measurements show the review load rising as the PR count rises
([C], see `arastirma/05-fabrikalar.md` [K30]).

**Decision.** KOVAN's output is not "code" but **evidence-backed change**:
a PR + the tests that verify it + gate results + a ledger record. Without
its evidence a PR does not count as "work"; a day does not count as
"productive".

**Consequences.**
- (+) The success metric aligns with acceptance, not with production.
- (+) Audit becomes a by-product of production rather than an add-on.
- (−) The first weeks look "slow": producing evidence costs more than writing code.
- (−) If evidence quality drops, the product loses its value; hence
  QUALITY.md is a separate document.

**Rejected.** "Lines written" and "PR count" metrics — both are easy to
game and can show an inverse correlation with quality.

---

## ADR-F02
### Skeleton first, model later

**Status:** Accepted · **Date:** 2026-10-21

**Context.** Agent systems usually start from the model: a prompt is written,
the model is connected, behavior is observed. The result: nobody knows whether
a failure is in the model, the flow, or a gate. And every model change
re-tests the whole system.

**Decision.** The loop is written first as a **deterministic state machine**
(`runner.py`): gate order, budget, circuit breaker, ledger. The model is
plugged in last, behind the `Adapter` interface. Tests run model-free with
`ScriptedAdapter`.

**Consequences.**
- (+) 22 tests pass without a model; regressions are caught independently of it.
- (+) A model swap happens in one file; the flow does not change.
- (−) It looks "artificial" at first: the scenario signals are not real.
- (−) If the adapter design is wrong, the real model brings surprises (v0.2 risk).

**Rejected.** "Try the prompt first, derive the architecture later" — buys
prototype speed, loses measurement and regression capability.

---

## ADR-F03
### Immutable core / mutable shell

**Status:** Accepted · **Date:** 2026-10-21

**Context.** The definition of a "self-improving system" is meaningless until
what the system may change is defined. A system that can change everything
cannot reliably change anything.

**Decision.** Two layers:
- **Core (immutable):** constitution, gate order, thresholds, model selection,
  forbidden paths, budget ceiling. Humans only (C3).
- **Shell (mutable):** skills, prompts, code, tests, roster proposals. The
  system proposes; the gates accept.

**Consequences.**
- (+) "Self-improvement" is confined to a measurable area.
- (+) Audit is possible because the core is small.
- (−) Some improvements (e.g. gate order) move slowly: a 14-day wait.
- (−) If the core is misdesigned, the system becomes "safe" in the wrong direction.

**Rejected.** Unbounded, fully autonomous self-modification (DGM-style) —
test-hacking cases are documented in the literature; unacceptable in production.

---

## ADR-F04
### The unit of learning is the skill, not code

**Status:** Accepted · **Date:** 2026-10-21

**Context.** "Self-improvement" can happen in two ways: (a) the system changes
its own code, (b) the system changes its procedures. (a) is powerful, but
every change affects the whole system and is hard to revert; and testing it is
as complex as the change itself.

**Decision.** The unit of learning is the **skill**: `skills/<name>/SKILL.md`
+ its test + its evidence. A lesson is born from a failure that has recurred
at least twice; without a test it does not count as a skill. Code change (C2)
is a separate channel, not the learning channel.

**Consequences.**
- (+) Reverting is easy: flip the file to `status: archived`.
- (+) The skill is portable across harnesses (the SKILL.md standard).
- (−) Some improvements cannot be expressed as a procedure (e.g. performance).
- (−) The skill count can bloat; a decay mechanism is mandatory.

**Rejected.** "Let the agent write its own code" (self-coding) as the primary
learning path — appealing, but it makes audit and revert harder.

---

## ADR-F05
### Spec = executable acceptance criterion

**Status:** Accepted · **Date:** 2026-10-21

**Context.** Spec-driven development rests on a correct intuition: code is
the derivative, the spec is the source. In practice the spec document falls
behind the code; you get "spec drift" — a stack of documents nobody reads.

**Decision.** The spec consists of acceptance criteria that **contain
commands**. A criterion without a command is rejected. The gap between spec
and code is measured by a weekly "drift audit": behaviors that are in the spec
but not the code, and in the code but not the spec.

**Consequences.**
- (+) The spec is automatically verifiable; it is not "commentary".
- (+) Drift becomes a measurable number.
- (−) Converting every criterion into a command is slow; some qualitative
  criteria (UX) are forced.
- (−) Writing commands is nearly the same work as writing tests; some teams
  will call it "double work".

**Rejected.** A long prose spec + "plan mode" — unread, unmeasured.
(Pocock's move away from plan mode toward documents + seam contracts supports
this direction [C].)

---

## ADR-F06
### Verification hierarchy: D1 > D2 > D3

**Status:** Accepted · **Date:** 2026-10-21

**Context.** "LLM-as-judge" is widespread in agent systems because it is cheap
and flexible. But a judgment is not a measurement; uncalibrated, it produces
noise. And as the sole gate, the system approves itself.

**Decision.** Three layers: deterministic (D1) > statistical (D2) >
judgment (D3). **Authority** follows this order; **workflow** does not: the
gates run in the order D1 → review (D3) → eval (D2), because eval must
measure only candidates that have already passed review. D3 alone cannot be
the gate; it is backed by D2. Human review is also D3 — which is why it is
audited by random sampling.

**Consequences.**
- (+) The cheap and exact runs first; the expensive judgment comes last.
- (+) The "no signal = pass" assumption is closed off.
- (−) Quality that cannot be expressed in D1 (readability, design) stays unmeasured.
- (−) The D2 set is continuous upkeep; neglected, it rots.

**Rejected.** "Evaluate everything with an LLM judge" — quick to set up, but
it has neither calibration nor tamper resistance.

---

## ADR-F07
### Tool policy goes through Airlock

**Status:** Accepted · **Date:** 2026-10-21

**Context.** Every agent in the factory uses file, shell, and network tools.
Auditing these calls separately inside each agent means N different policies
and N different failure modes. There is already a tool-level policy engine
working on the same project (Airlock): a rule base, a decision judge, a
hash-chained ledger.

**Decision.** Tool calls go through Airlock; the factory does not write its
own policy engine. The factory's `policy` gate completes Airlock's decision at
the **change level** (file paths, scope). The two ledgers stay separate: the
tool-call ledger (Airlock) and the decision ledger (KOVAN).

**Consequences.**
- (+) One policy language, one audit format.
- (+) The factory benefits directly from Airlock's maturation.
- (−) Airlock's known gaps are inherited by the factory (no command AST,
  serial proxy, weak platform coverage).
- (−) Correlating the two ledgers is separate work (the same `trace_id` is required).

**Rejected.** A second policy engine inside the factory — two sources of
truth, two escape routes.

---

## ADR-F08
### Change classes C0–C3

**Status:** Accepted · **Date:** 2026-10-21

**Context.** Not every change carries the same risk: a typo fix and a
constitutional amendment cannot pass through the same gate. But if
classification is left to the agent, the agent declares its own work "small".

**Decision.** Four classes: C0 (typos/formatting), C1 (skills/prompts/docs),
C2 (product code), C3 (constitution/gates/thresholds/model/roster). The class
is assigned in the spec; the agent cannot lower it. C3 never passes
automatically under any condition. C2 is closed at night.

**Consequences.**
- (+) Process matches risk; C0 is fast, C3 is slow.
- (+) The night/day split becomes enforceable with these classes.
- (−) Class assignment can be contested (a "small" refactor is C2).
- (−) A wrong class produces either needless friction or an audit gap.

**Rejected.** A single class ("every change is the same") — either far too
slow or far too risky.

---

## ADR-F09
### Model tiering + budget ceiling

**Status:** Accepted · **Date:** 2026-10-21

**Context.** The most capable model is overkill for every task; the cheapest
model is insufficient for every task. And an unbounded budget optimizes
spending, not learning.

**Decision.** Four tiers: T0 (no model), T1, T2, T3. The role contract sets
the tier; when the budget reaches 80% the tier drops. Every shift has
token/USD ceilings; on breach the loop stops — there is no "a little more".

**Consequences.**
- (+) Cost is predictable; the invoice holds no surprises.
- (+) Cheap work stays on cheap models.
- (−) A tier drop can lower quality; this must be watched via evals.
- (−) Model prices change and the table goes stale; a monthly update is needed.

**Rejected.** "One strong model, everywhere" — simple, but unsustainable in
cost and latency.

---

## ADR-F10
### Files + git + SQLite; no workflow engine

**Status:** Accepted · **Date:** 2026-10-21

**Context.** Temporal, Airflow and the like exist for durable workflows. But
the first version has one repo, one user, and low concurrency. Adding an
engine would hide an unsolved problem (gate quality) behind infrastructure.

**Decision.** State files + git + a SQLite index. Every turn is restartable;
`resume` from `state.json`. Concurrency is at most 5 workers, with a
single-writer rule.

**Consequences.**
- (+) Understandable, portable, easy to debug.
- (+) Git is ready-made for audit and revert.
- (−) Past 10k+ tasks the file-based ledger slows down (O(n²), a known debt).
- (−) No multi-machine distribution; scaling requires a redesign.

**Rejected.** Starting with Temporal/Kubernetes — premature optimization; the
real bottleneck is not orchestration but the gate.

---

## ADR-F11
### Memory is append-only; no deletion

**Status:** Accepted · **Date:** 2026-10-21

**Context.** The most dangerous move of a self-improving system is rewriting
its own past. The question "did it learn, or did it only think it learned"
becomes unanswerable.

**Decision.** `ledger.jsonl`, `lessons.jsonl`, `skills.proposed.jsonl` are
append-only. A wrong record is not deleted; a `supersedes` entry or an
`[invalid]` note is added. A skill may become `archived`; its file remains.
The hash chain enforces this technically.

**Consequences.**
- (+) The audit trail is whole; retrospective analysis is possible.
- (+) Wrong learning can be flagged later.
- (−) The store grows; indexing and archiving become necessary.
- (−) A record containing personal data cannot be deleted → it must be masked
  from the start (v0.2 rule).

**Rejected.** "Delete the wrong record, keep it clean" — breaks the audit.

---

## ADR-F12
### Borrow patterns, not a framework

**Status:** Accepted · **Date:** 2026-10-21

**Context.** Mature skeletons exist: Superpowers, GSD, Spec Kit, BMAD.
Installing them is the fast road; but none of them meets the factory's three
needs together: (1) the night/day split, (2) self-improvement classes,
(3) an evidence ledger + budget accounting.

**Decision.** Patterns are borrowed; the engine is written. Specifically
borrowed:

| Source | Pattern borrowed | Why |
|---|---|---|
| Superpowers | "no production code without a test", fresh verification evidence, a 5-round breaker, SKILL.md | Rule hardness, portability |
| Superpowers | Skill = procedure, subagent = context isolation, hook = enforcement | Three mechanisms, three jobs |
| GSD | Phase/phase transitions, `STATE.md`/`ROADMAP.md` state files, goal-backward validation | Context management on long tasks |
| Spec Kit / Kiro | the spec → plan → tasks separation | Keeping the spec derivable |
| Pocock | Spec = decision record + seam contracts; deterministic verification (tsc/vitest) | A measurable artifact instead of "plan mode" |
| Karpathy | The verifiability axis, the autonomy slider, the single-metric experiment loop | Task classification and measurement |

**Not borrowed:** heavy multi-agent ceremonies (MetaGPT/ChatDev-style role
theater), "plan mode" (unmeasurable), unbounded autonomy, framework lock-in.

**Consequences.**
- (+) The engine is small (300 lines) and fits its own need.
- (+) The patterns are tested; we are not reinventing the wheel.
- (−) We cannot use the frameworks' ready-made integrations (IDE, CI).
- (−) Pattern upkeep is ours; upstream fixes do not arrive.

**Rejected.** Installing Superpowers/GSD directly — 2 of the 3 needs go
unmet and the self-improvement classes are left out.

---

## ADR-F13
### Project identity: KOVAN brand + kovan-fabrika namespace

**Status:** Accepted · **Date:** 2026-11-17

**Context.** Before the public release, a repo/PyPI name had to be chosen.
Candidates: bare "kovan", "kovan-fabric", "kovan-fabrika". Search validation
(November 17): bare "kovan" is taken on GitHub — vertexclique/kovan (a Rust
wait-free library) and boratanrikulu/kovan ("engineering methodology →
infrastructure; agent + gates" — high conceptual collision); Ethereum Kovan
testnet results bury "kovan" searches. "fabric" as a head word is polluted in
the AI/framework space (danielmiessler/Fabric, Microsoft Fabric, Hyperledger
Fabric, Python Fabric); the system is in fact a capacity-bounded production
line — the code and docs metaphor is already the factory (shift, line, gate,
production).

**Decision.** Brand: **KOVAN**; repo and PyPI package: **`kovan-fabrika`**;
CLI command: `kovan`; the English framing lives in README.md: "a
capacity-bounded, evidence-first software factory". pyproject is already
compliant — migration cost is zero. `project.urls` is added in a single line
once the real repo address exists.

**Consequences.**
- (+) Discoverability: a full-string search for "kovan-fabrika" returns only us.
- (+) Metaphor integrity: no conflict with the document set; migration cost is zero.
- (−) "kovan"-prefixed searches compete with the testnet; the full-string
  search is the norm.
- (−) The Turkish namespace weakens the international feel; README.en and the
  cognate ("fabrika" ≈ factory) compensate for it.

**Rejected.** bare "kovan" (taken + conceptual collision);
"kovan-fabric" (polluted head word + metaphor mismatch + migration
cost); "kovan-os" (overclaiming); Anglicization ("hivecraft"-like —
a collapsed space: TheHive etc.).

---

## Decision log

| Date | Event |
|---|---|
| 2026-10-21 | F01–F12 accepted (concept version) |
| 2026-11-17 | F13 accepted — project identity: KOVAN / kovan-fabrika |
| 2026-11-18 | F13 revision note — README.en.md was folded into README.md; the English framing lives in README.md |
| — | F07 is counted "partial" until Airlock's T1 model is measured |
| — | F09's price table will be updated monthly |
| — | F12 will be revisited on the first real task (v0.2) |
