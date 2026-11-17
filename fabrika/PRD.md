# KOVAN — Product Requirements Document (PRD)

| Field | Value |
|---|---|
| Version | 1.0 (concept) |
| Date | October 21, 2026 |
| Owner | founder |
| Status | **the v2 redirection is in effect** — system definition: [`SYSTEM.md`](SYSTEM.md) |
| Related | [`README.md`](README.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md) · [`ADR.md`](ADR.md) · [`loop/goal.yaml`](loop/goal.yaml) |

---

## 1. Summary

KOVAN is a production line that processes a software team's accumulated
backlog **through the night** and leaves, by morning, (a) merge-ready PRs,
(b) a sourced learning report, and (c) measured proposals about its own
structure.

The product is not a model. The product is three things:

1. **A gate set** — immutable, measurable rules that decide what is accepted.
2. **Memory** — the skill library and evaluation set it distilled from its own mistakes.
3. **A report** — a one-page status a human can read and act on in 5 minutes.

Sales sentence (not yet validated; see §11):

> "We do not change your model. We turn your backlog into a readable morning
> report and merge-ready PRs — and every decision is auditable."

---

## 2. Problem

**P1 — Production rose; acceptance did not.**
Agents accelerated code production; the bottleneck moved from production to
review. With high AI adoption, PR counts rise ~98% while review time rises
~91% and PR size ~154% (secondary analysis; see `arastirma/05-fabrikalar.md`
[K30]). The result is not "more code" but "more unread code".

**P2 — Learning does not accumulate.**
Every session starts from zero. The agent makes the same mistake a third
time; the error is not recorded, not distilled, not made reusable. What the
organization knows is not what the agent knows.

**P3 — Loss of audit.**
As autonomy grows, the human gate slides downward: from plan to code, from
code to "agent review". This is the least measured area. Who approved what,
and why, is recorded nowhere in most systems.

**P4 — Measurement inflation.**
The same model looks 10+ points apart across different harnesses. Teams pick
tools by benchmark counts without measuring what happens in their own work.

---

## 3. Vision and positioning

**Vision:** To be a software team's "second shift" — one that can account for
itself in the morning.

| KOVAN is | KOVAN is not |
|---|---|
| A repo-native production line (files + git + CLI) | A hosted multi-tenant SaaS |
| A gates-and-memory product | A model or IDE product |
| A system that makes the human gate **meaningful**, not smaller | A "removes the human" autonomy claim |
| Something that starts with one repo, one line | Fleet management from day one |
| A measurable claim | A leaderboard claim |

---

## 4. Users

| Persona | State | Pain | Expects from KOVAN |
|---|---|---|---|
| **Solo technical founder** | 1 person, 3 products, unbounded backlog | Cannot work at night; forgets by morning what to do | One page in the morning: what happened, what is waiting |
| **Small product team** | 3–8 people, one repo | Review queue; unreliable agent output | PRs that passed the gates, small PRs |
| **Platform team** | 20+ people, many repos | No standard; everyone with their own prompt | Policy + audit + measurement |

Primary persona: **the solo technical founder**. Reason: the decision-maker
and the user are the same person; the feedback loop is shortest; C3 approval
is a single signature.

---

## 5. Goals and non-goals

### Goals (12 weeks)

| # | Goal | Measure |
|---|---|---|
| O1 | The night shift runs reliably | Morning report ready by 06:00 on ≥ 8 of 10 nights |
| O2 | The gates do their job | First-pass gate rate on C2 tasks ≥ 50% (week 8), ≥ 65% (week 12) |
| O3 | Learning accumulates | ≥ 30% of the produced skill candidates get used at least once within the following 2 weeks |
| O4 | Audit is proven | Every decision verifiable through the hash chain; the tamper test passes |
| O5 | Cost is predictable | Cost per merged PR ≤ 6 USD (12-week average) |

### Non-goals (deliberately out of scope)

| # | Not doing | Why |
|---|---|---|
| X1 | Model training / fine-tuning | Separate budget, separate expertise; the gate problem comes first |
| X2 | Multi-tenant hosting | The security surface grows tenfold; not before validation with a single user |
| X3 | IDE / editor | The existing harnesses suffice; integration, not competition |
| X4 | A "human-free software" claim | The measurements say otherwise; the claim costs trust |
| X5 | Self-publishing (automatic deploy) | C3 class; a human gate is mandatory |

---

## 6. User stories

**US-01 — Morning report.** As a solo founder, while getting my coffee in the
morning, I want to see on a single page: what was learned overnight (with
sources), what was produced, what was rejected, and today's top three tasks.
*Acceptance:* the report reads in 5 minutes; every claim is tied to a file or
URL; the "could not verify" section may not be left empty (if empty, it says
"none").

**US-02 — A trustworthy PR.** As a small-team member, I want to see that the
morning PR passed its tests, that the reviewer wrote a rationale, and that no
forbidden file was touched. *Acceptance:* the PR description includes the gate
results as a table; the review rationale cannot be a one-word "LGTM".

**US-03 — The recurring error stops.** As a founder, I do not want the same
mistake a third time. *Acceptance:* the same gate + same cause seen twice
opens a candidate in `skills.proposed.jsonl`; the candidate is tested in the
next shift.

**US-04 — Stopping.** As a founder, when something goes wrong at 02:00 I want
to stop it with a single command. *Acceptance:* when the `STOP` file is in
place no new work is taken; a report is written within 60 seconds; unfinished
work is marked "partial".

**US-05 — Measurement honesty.** As a platform team, I want to see in which
set, with how many samples, and on which date the "eval 95%" sentence was
measured. *Acceptance:* every metric record carries
`{set, n, date, harness, model}`.

**US-06 — Structure proposal.** As a founder, I want the system's proposal to
change its own roster to come with a rationale and a measurement. *Acceptance:*
the proposal is an ADR draft; it contains "which metric, how much, how it will
be measured"; it is not applied without approval.

---

## 7. Functional requirements

Priority: **M**ust / **S**hould / **C**ould. Each requirement belongs to a
single ring.

### Ring 1 — Task loop (minutes)

| # | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-01 | The goal contract is read and validated | M | If `goal.yaml` is missing or `goal.id` is empty, the loop does not start |
| FR-02 | Issue → spec + executable acceptance criteria | M | Every criterion contains a command; a commandless criterion is rejected |
| FR-03 | Test-first: a red test before code | M | Without a record of the test failing first, the code does not enter the gate |
| FR-04 | Patch generation with bounded scope | M | The patch touches only the files listed in the spec |
| FR-05 | Independent review | M | The reviewer runs in a separate context; a rationale is mandatory |
| FR-06 | Ordered gate chain + fail-fast | M | On the first blocking failure, the later gates do not run |
| FR-07 | Change class and the human gate | M | C3 never passes automatically under any condition |
| FR-08 | Isolation: worktree + container | M | The agent cannot write to the main working tree; the network is allowlist-bound |

### Ring 2 — Shift loop (7 hours)

| # | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-09 | Night agenda and time box | M | Reserved duration and output defined for each block |
| FR-10 | Sourced research | M | Every claim carries a URL/arXiv id; unreachable means "could not verify" |
| FR-11 | Skill distillation | M | Skill candidate: trigger, procedure, verification, test |
| FR-12 | Morning report | M | 5 sections filled; on file by 06:00; one page |
| FR-13 | Lesson record and recurrence detection | S | A candidate opens the second time the same fingerprint appears |

### Ring 3 — Release loop (days)

| # | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-14 | Canary + automatic rollback | M | If eval falls below the threshold, the release is rolled back |
| FR-15 | Model/budget steering | S | At 80% budget the tier drops; at 100% it stops |
| FR-16 | Skill activation | S | A skill is not "active" until it has been measured on the task class it applies to |

### Ring 4 — Structure loop (weeks)

| # | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-17 | Structure proposal (ADR draft) | S | Proposal: context, decision, expected effect, measurement plan |
| FR-18 | Audit ledger | M | Append-only; hash chain; `verify` shows tampering |
| FR-19 | Memory upkeep | C | Decay report: a list of unused skills/notes; no deletion |

---

## 8. Non-functional requirements

| # | Requirement | Threshold / acceptance |
|---|---|---|
| NFR-01 | Cost | ≤ 6 USD per PR; ≤ 40 USD per shift; stops on breach |
| NFR-02 | Durability | Continues after interruption with `resume`; completed work is not repeated |
| NFR-03 | Isolation | Separate worktree + container per agent; no secrets |
| NFR-04 | Auditability | Every decision: what, why, which gate, which evidence |
| NFR-05 | Portability | Skill/roster definitions are harness-independent (SKILL.md + YAML) |
| NFR-06 | Observability | A span per turn: task, gate, model, tokens, duration |
| NFR-07 | Privacy | Code and secrets never leave; network by allowlist only |
| NFR-08 | Language | Reports in Turkish; code/commit messages in English; terms in the glossary |

---

## 9. Metrics

Definitions are in [`QUALITY.md`](QUALITY.md) §4. Only the target table is
here. **None of these has been measured yet**; that is why the "start" column
is empty.

| Acronym | Metric | 12-week target | Measurement |
|---|---|---|---|
| **BMP** | Merged PRs / shift | ≥ 1.5 | git log + merge record |
| **GPK** | First-pass gate rate | ≥ 65% | ledger |
| **DSP** | Human correction lines / PR | ≤ 25 lines | post-merge diff |
| **MBB** | Cost / merged PR | ≤ 6 USD | model invoice + ledger |
| **ÖVD** | Accepted skills / proposed | ≥ 30% | skills + usage record |
| **TKH** | Recurring error rate | ≤ 15% | lessons fingerprint |
| **KKA** | Escaped regressions / 100 PRs | ≤ 1 | errors within the following 2 weeks |
| **GHS** | On-time morning report rate | ≥ 80% | reports/ file count |

**Anti-metric:** "lines written". Not measured, because the line count can
show an inverse correlation with quality and is the easiest number to game.

---

## 10. Release scope

| Version | Scope | Exit criteria |
|---|---|---|
| **v0.1** (current) | Dry run: contracts, runner, gates, ledger, demo | 22 tests + a sample report |
| **v0.2** | Real adapter (one model), real eval set (≥ 50 cases), cost measurement | End-to-end on 20 tasks; GPK measured |
| **v0.3** | Night shift: research + distillation + morning report | 5 consecutive nightly reports |
| **v1.0** | Canary, rollback, C3 approval flow, multi-line (3 workers) | 2 weeks uninterrupted; KKA measured |

---

## 11. Open questions and dependencies

1. **Name/brand:** "KOVAN" is a working name; no screening has been done.
   (Open in Airlock too.)
2. **First customer:** the internal factory, or an external service? The
   pricing model depends on this.
3. **Model provider:** a single provider, or routing? A C3 decision.
4. **Where the eval set comes from:** our own past PRs, or synthetic? External
   data is a privacy risk.
5. **Turkish/English:** product language English, document language Turkish?
   For now, that is the state.
6. **Dependency:** until Airlock's tool-level policy matures, the factory
   cannot fully establish its security claim (see `../STATUS.md`).

---

## 12. Appendix: acceptance test matrix (for v0.2)

| Scenario | Input | Expected |
|---|---|---|
| Happy path | 1 C1 task | Gates pass, a PR opens, the ledger gets 1 record |
| Test weakening | The candidate deletes a test | The `tests` gate rejects; a lesson is written |
| Secret reading | The diff contains `.secrets/` | `policy` blocks; human gate; no revision |
| C3 | Constitutional change | Immediately `blocked`; stops on the first attempt |
| Budget | 99% of the ceiling | No new task is taken; a report is written |
| Interruption | The process dies mid-shift | `resume`; completed work is not repeated |
| Tampering | A ledger line is edited | `verify` gives the first break point |
