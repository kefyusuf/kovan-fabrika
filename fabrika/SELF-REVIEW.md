# KOVAN — Self-Review

> This file is part of the deliverable, not an appendix. The aim: not "what
> I did" but **"what I verified, what I did not verify, where I strayed from
> the goal"**.

---

## 1. Request → deliverable mapping

| # | Requested | Delivered | Status |
|---|---|---|---|
| 1 | Research by morning | 7 parallel lines; 3 full notes + 4 summaries; the night agenda | Partial (see §4.2) |
| 2 | A structure that teaches itself | `LEARNING.md` + the skill distillation mechanism (tested) | Mechanism exists, no model |
| 3 | One that improves its own structure | The C0–C3 classes, the R4 ring, the constitution, the 14-day rule | Design complete |
| 4 | A company-style structure | `ORGANIZATION.md` (14 agents, 2 humans, handoff/SLA/escalation) + `loop/agents.yaml` | Complete |
| 5 | Karpathy, Pocock, Superpowers, GSD | `RESEARCH.md` §1–§4, sourced | Complete (C level) |
| 6 | Project files like ADR, PRD | 8 documents + 12 ADRs + 5 contract files + working code | Complete |
| 7 | Review yourself | This file | Complete |
| 8 | Stay on the goal | §4 the deviation audit | 2 deviations, with rationale |
| 9 | The "loop goal" method | `README.md` §8, `loop/goal.yaml`, `runner.py`, 22 tests | Working |

---

## 2. What I verified [A]

These are not claims; they are reproducible with a command.

| What | Command | Result |
|---|---|---|
| Test suite | `python tests\test_runner.py` | **22/22 passed**, 0.09 s |
| End-to-end dry run | `python demo.py` | 4 tasks → 2 accepted, 2 human gates, 1 revision |
| Ledger integrity | `Ledger(...).verify()` | `(True, 5, '')` — the chain is sound |
| Contract loading | `Spec.load('.')` | `kovan-gece-vardiyasi-v1`, 8 gates, a 2.4M token ceiling |
| Tamper detection | `test_tampering_is_detected` | The modified record was caught |
| Budget ceiling | `test_budget_exhaustion_stops` | The task exceeding the ceiling did not start |
| The C3 gate | `test_c3_change_requires_human` | Stopped on the first attempt, did not insist |
| Policy violation | `test_policy_violation_blocks_immediately` | A `.secrets/` diff was blocked instantly |
| Skill candidate | `test_repeated_failure_emits_skill_candidate` | A candidate was produced on the 2nd recurrence |

### 2.1 Three errors found and fixed by independent audit

The deliverable was audited by a second agent; three real errors were
found. All three were fixed, and a new test was written for each.

| # | Error | Why it is serious | Fix | Test |
|---|---|---|---|---|
| 1 | A boolean gate without a signal passed (`signals.get(name, True)`) | It would mean "unmeasured = passed"; a candidate carrying no lint/type/test signal would be accepted | The default became `False`; a missing signal rejects with "no signal" | `test_missing_boolean_signal_is_not_a_pass` |
| 2 | The constitution file was not protected | A C2-labeled patch could edit `loop/constitution.md` | constitution/gates/agents were added to `forbidden_paths`; the test loads the real contract | `test_constitution_file_is_protected` |
| 3 | The budget could be exceeded by actual spending | The estimate was 1,000 tokens, the reality 5,000 → accepted with a negative balance | If the balance goes negative after spending, the task is `blocked` and the loop gets `butce_bitti` | `test_budget_overflow_blocks_before_verification` |

The common root cause: the code was enforcing its own default, not the rule
in the document. This is concrete proof of the difference between "the
tests pass" and "the contract is enforced". A fourth finding (the gate
order ↔ the D1/D2/D3 hierarchy) was fixed with a document correction: the
authority hierarchy and the workflow order were written as separate things.

**Scope:** 20 files, 4,503 lines (code + documents; including the empty
`__init__.py`). `loop/runner.py` is 635 lines, the tests 322 lines.

**What was not proven:** these tests prove that the *mechanism* works; they
do not prove that the *product* is useful. The difference between the two
is the main subject of this document.

---

## 3. What I did not verify [C]/[D]

| # | Claim | Why it was not verified | How it can be verified |
|---|---|---|---|
| 1 | It works with a real model | The adapter is empty; no API key/budget | v0.2: one model, 20 tasks |
| 2 | The gates raise quality | No eval set | v0.2: a 50-case set + the GPK measurement |
| 3 | The cost is ≤ 6 USD per PR | No model call was ever made | v0.2: invoice + manifest |
| 4 | The night shift produces value | No real night run has happened | v0.3: 5 nights in a row |
| 5 | The 12-week plan is realistic | A plan is not evidence | The weekly gates |
| 6 | There is a market/customers | No conversations were held | 3 customer conversations |
| 7 | The research numbers (versions, dates, benchmarks) | Agent summaries; the full texts unverified | The `RESEARCH.md` §9 list |
| 8 | Legal compliance is sufficient | No lawyer reviewed it | An expert + the official texts |
| 9 | "Self-improvement" is safe | Only the C3 gate was tested; no real attack scenario | A red-team drill |
| 10 | The two-signature rule works | There is a single human | A second human or a process drill |

**The honest sentence:** this deliverable is a **concept + verified
skeleton**, not a working factory. The only things I can call "working" are
the loop core and the contracts.

---

## 4. Did I stray from the goal?

My own goal: *"research by morning, a self-learning, self-improving,
company-style structure; complete project files like ADR/PRD."* Against
that, three decisions were audited:

### 4.1 The ADRs in a single file (deviation: low)
**Decision:** 12 ADRs in a single file, `ADR.md`; not separate
`adr/ADR-F01.md` files.
**Rationale:** scannability on one page; seeing the whole of 12 decisions
is faster than opening them one by one. The `docs/adr/` separation already
exists in Airlock.
**A deviation?** Formally yes, in substance no. If separate files are
wanted, splitting is a 10-minute job; but the single file makes it easier
to see contradictions between decisions. **Decision: accepted.**

### 4.2 Four research notes could not be filed (deviation: medium)
**What happened:** 3 of the 7 research lines could write full notes
(`arastirma/`); 4 returned only summaries (the tool budget). The summaries
were entered into `RESEARCH.md` with the **[C]** tag; the sources were
preserved.
**A deviation?** Yes: part of the "fully sourced research" goal is missing.
**The compensation:** every claim is tagged [C], the verification list is
in §3, the sources are in `RESEARCH.md` §10. There is no fabrication; there
are gaps. **Decision: accepted, but incomplete.**

### 4.3 I did not wire the night shift to a scheduled task (deviation: deliberate)
**Decision:** the "loop goal" mechanism was described and coded; but a real
nightly 23:00 cron task was **not set up**.
**Rationale:** an irreversible spending commitment (tokens/USD every
night). That is the user's decision, not my assumption.
**A deviation?** No — it was left out of scope and said so explicitly. It
can be set up in a single step (README §8).

### 4.4 General verdict
There are two formal/measurement deviations, both documented; there is no
deviation from the goal's substance (an evidence-producing, learning,
company-like structure).

---

## 5. The three weakest assumptions

If these are falsified, it is not the concept that changes; it is the
**plan**.

**V1 — "The value of learning overnight exceeds its cost."**
7 hours × 40 USD per night = 40 USD a night; ~1,200 USD a month. In return,
1–2 active skills per month are expected. A skill is valuable if it
prevents a recurring error; if it does not, it is an expensive diary.
**Test:** in week 6, "cost per skill" must be measured. That number does
**not** exist yet.

**V2 — "The gates really stop the agent."**
What was tested is the runner enforcing the rule. What was not tested is
the model behaving *creatively* to slip past the gate (deleting tests,
shifting scope, changing thresholds). A rule engine written against a model
that does not know the rule is strong; written against a model that knows
it, fragile. **Test:** a red-team drill (v0.2, week 4).

**V3 — "In a one-person setup, the two-signature rule works."**
The founder both writes the proposal and approves it; producing two records
gives the *appearance* of audit, not the *function* of audit. **Test:**
until a second human (an advisor, a partner) is added, the C3 rule should
be counted as "technically working, socially not".

---

## 6. Internal tensions (not hidden)

1. **14 agents ↔ the review budget (İ6).** The roster has 14 roles, but
   concurrency is 3–5. The tension: the role count gives a "company"
   feeling; the capacity is small. The solution: most roles run serially;
   the roster is a "capability inventory", not a concurrency plan.
2. **"Learning at night" ↔ learning slows production.** When a skill
   activates, the gates tighten and first-pass rejections rise. In the
   short term GPK drops. The solution: measure GPK 2 weeks after skill
   activation; report the transition period separately.
3. **C3's 14 days ↔ the 12-week plan.** Structure changes are slow; the
   plan is fast. The solution: R4 proposals start at week 9, and
   application extends past week 12 — the plan accepts this.
4. **Honesty ↔ the "useful" feeling of the morning report.** When the bad
   news is written first, the report can demoralize. The solution: next to
   every piece of bad news, a single next step is written (report §5).
5. **"By itself" ↔ the human gate.** The more autonomous the system, the
   more critical the human gate becomes. This is not a contradiction but a
   proportion: as automation grows, the checkpoint gets fewer but heavier.

---

## 7. Checklist for the reviewer

Someone auditing this deliverable may ask these 8 questions:

1. Are the `PRD.md` requirements measurable? (an acceptance criterion per FR)
2. Do the `ADR.md` decisions contradict each other? (especially F03 ↔ F08)
3. Does `loop/goal.yaml` conflict with `constitution.md`? (forbidden paths,
   budget)
4. Is `runner.py` really fail-fast? (does `evaluate` exit early)
5. Is ledger tampering really caught? (run the test, then break it by hand)
6. Is the "2 recurrences" threshold in `LEARNING.md` the same as in
   `runner.py`? (`>= 2`)
7. Do the `QUALITY.md` metrics use the same definitions as `PRD.md`?
8. Is the `SELF-REVIEW.md` §3 list consistent with `RESEARCH.md` §9?

Six of these questions are answered with a command, two by reading. An
item whose answer is "no" is the item to fix.

---

## 8. The next three steps (in decision order)

1. **Decision:** the internal factory or an external service? (PRD §11) —
   this determines the SLA and the risk profile; everything else depends on
   it.
2. **v0.2:** a single-model adapter + a 50-case eval set + 20 tasks.
   Exit: two numbers, GPK and MBB, measured.
3. **v0.3:** the night shift; 5 consecutive nights of reports. Exit: is the
   morning report actually readable? (can the user decide in 5 minutes)

**Not to do:** increasing the agent count before v0.2 is done, adding new
skill types, getting into brand/name work.

---

## 9. The one-sentence verdict

> The concept has a verified skeleton and an honest list of gaps; it does
> not prove what it claims, it **makes it provable** — which is the most
> one can expect from a concept.
