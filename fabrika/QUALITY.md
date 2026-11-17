# KOVAN — Quality, Gates, and Measurement

> **v2 note (November 4, 2026):** The current system definition is
> [`SYSTEM.md`](SYSTEM.md). Eval v1 is live (a frozen 90-case set, blocking);
> seeded error measurement is `seedtest.py`; for the LLM judge, κ will be
> reported rather than raw agreement.

> The factory's product is evidence; this document describes how that
> evidence is produced and how it is falsified. The rule: **do not claim
> what you have not measured; write the set for what you do claim.**

---

## 1. The three-layer verification

| Layer | What | Example | Reliability | Can it be a gate alone |
|---|---|---|---|---|
| **D1 Deterministic** | Same input → same result | compiler, type check, test, rule | High | **Yes** |
| **D2 Statistical** | A rate over a sample | eval set, regression set | Medium (depends on n) | Yes, but n and CI are reported |
| **D3 Judgment** | Model/human evaluation | code review, rubric | Low–medium | **No**, not alone |

**The gate order and the layer hierarchy are not the same thing.** The
order is the workflow: first the D1 gates (policy, lint, types, test,
provenance), then review (D3), and eval (D2) last. Eval coming last is
deliberate: only a candidate that has already passed review is measured —
otherwise the team writes code for the eval and the measurement replaces
the goal.

**The authority hierarchy**, however, is D1 > D2 > D3: if two gates
conflict, the deterministic one wins, then the statistical one, and
judgment last. The order is a matter of cost/flow; the hierarchy is a
matter of trust; the two must not be confused.

---

## 2. Gates

| # | Gate | Layer | Owner | Cost | On failure |
|---|---|---|---|---|---|
| 1 | `policy` | D1 | Airlock | < 1 ms | block + human |
| 2 | `lint` | D1 | static | ~1 s | revision |
| 3 | `types` | D1 | static | ~5 s | revision |
| 4 | `tests` | D1 | test | ~30 s | revision |
| 5 | `provenance` | D1 | compliance | ~2 s | block + human |
| 6 | `review` | D3 | incelemeci | ~15 min | revision |
| 7 | `eval` | D2 | measurement | ~5 min | reject + rollback |
| 8 | `cost` | accounting | finance | ~0 | warn + throttle |

**Fail-fast:** stops at the first blocking failure. `cost` does not block;
it warns.

**The "no signal" rule:** if no measurement has been produced for a gate,
the gate **does not pass**. This closes the "unmeasured = passed" assumption
(`test_missing_eval_signal_is_not_a_pass`).

### 2.1 The test gate's special rule

The candidate may bring its own test; but:

1. The test must be red **before** the code (the record is mandatory).
2. The test cannot be deleted; assertions cannot be weakened.
3. The new test must cover the behavior the old test covered.
4. The legitimate-refactor exception: if coverage grows, the test count may
   shrink — with a rationale.

Without this rule the `tests` gate turns into theater: the agent fits the
test to the code, the gate goes green, the behavior breaks.

### 2.2 The review gate

- The reviewer runs in a **different context** from the code writer.
- A rationale is mandatory; "LGTM" is invalid.
- The reviewer does not fix the code; it rejects and writes why.
- A random 10% sample goes to human audit (rubber-stamp detection).

---

## 3. The eval harness

### 3.1 Set types

| Type | Purpose | Size (v1) | Use | Frozen? |
|---|---|---|---|---|
| **Unit** | A single behavior | 200+ | Every PR | No (grows with the code) |
| **Regression** | Past errors | 50+ | Every PR | Yes (appended, never removed) |
| **Adversarial** | Break scenarios | 30+ | Daily | Yes |
| **Holdout** | True performance | 30+ | **Release only** | Yes, blind |
| **Transfer** | Generalization | 20+ | Monthly | Yes |

### 3.2 Holdout discipline (a lesson from our own burned holdout)

A concrete incident on this project: the rule set scored **F1 1.000** on the
30 cases it had written itself; on a realistic holdout it scored **0.394**.
Then the missed holdout cases were used in rule writing and that holdout
**burned too** — it no longer produces a publishable number (see
`../STATUS.md` §4).

Therefore:

1. **The holdout is never seen by the agent that produces.** A separate
   directory, a separate owner.
2. **If rules were written while looking at the holdout, that set is dead.**
   A new set is required.
3. **Every report carries the set identity:**
   `{set, n, date, harness, model, seed}`.
4. A **burned set** is moved under `olcum/sets/retired/`; it is not deleted;
   it stays with the "retired" tag (with the reason it burned on record).

### 3.3 Release and canary

```
new release ──▶ shadow (past 50 tasks) ──▶ canary (10%) ──▶ full
                    │                          │
                    └─ agreement < 70% → reject └─ regression → automatic rollback
```

Rollback is automatic; it does not wait for human approval. Because letting
a worsening release sit "just for a look" defeats the purpose of measurement.

---

## 4. Metrics

For every metric three things are written: **formula**, **source**,
**how it can be gamed**.

| Acronym | Formula | Source | Gaming risk | Countermeasure |
|---|---|---|---|---|
| **BMP** | merged PRs / shift | git | Small, trivial PRs | ≥ 20 lines per PR + an issue link |
| **GPK** | first-pass / total tasks | ledger | Picking easy tasks | The task-class distribution is reported too |
| **DSP** | human diff lines after merge / PR | git | — | Measurement is expensive; by sampling |
| **MBB** | (model + CI + human) / merged PR | invoice + hours | Not counting human hours | The human minute is priced at $X |
| **ÖVD** | skills used / proposed | skills + triggers | Producing trivial skills | The 30-day use requirement |
| **TKH** | recurring fingerprints / total errors | lessons | Making the fingerprint too broad | Schema audit |
| **KKA** | errors in the next 2 weeks / 100 PRs | issues | Not labeling | The error label is mandatory |
| **GHS** | reports ready by 06:00 / nights | files | Counting an empty report as "ready" | The 5-sections-filled requirement |

**Reporting rule:** every number comes with `n` and, where possible, a
confidence interval. If `n < 20`, the number is labeled "indicative" and is
not presented as a "result".

---

## 5. Measurement protocol

Every run produces a **manifest**:

```json
{
  "run_id": "2026-10-21T23:00:00Z",
  "set": "regression-v3",
  "n": 57,
  "harness": "kovan/0.2.0",
  "model": {"provider": "x", "name": "y", "tier": "T2"},
  "seed": 0,
  "cost_usd": 3.12,
  "result": {"pass": 41, "fail": 16, "score": 0.719},
  "artifacts": ["ledger.jsonl", "diffs/"],
  "notes": "16 hatanın 9'u aynı sınıf: test zayıflatma"
}
```

**Forbidden:**
- Reporting "the best of 3 runs".
- Comparing different harnesses' results in the same table (harness
  differences reach 10+ points).
- Comparing against a previous number when the set changed (no comparison
  if the set identity differs).
- Giving a percentage without stating n.

**Mandatory:** the list of failing cases. A summary number is not published
without the failure list.

---

## 6. Evidence levels

Documents and reports tag every claim with a level:

| Level | Meaning | Example |
|---|---|---|
| **[A]** | Measured in this system; reproducible with a command/file | "22 tests pass" |
| **[B]** | A primary external source (official document, repo, paper) | with an arXiv id |
| **[C]** | Second-hand / agent research; the source exists, unverified | "X reduced Y by 30%" |
| **[D]** | Could not be verified | "Probably so" |

Report rule: [C] and [D] are not written side by side; [C]'s source is
given, and [D] items are collected under the "could not verify" heading.

---

## 7. The test pyramid (for agent output)

| Type | What it catches | Cost | Required |
|---|---|---|---|
| **Unit** | Function behavior | Low | Yes |
| **Contract** | The agent ↔ tool interface | Low | Yes |
| **Property-based** | Edge cases (properties) | Medium | Yes on C2 |
| **Snapshot** | Unexpected output change | Low | On C1 |
| **Adversarial** | Injection, secret leaks, scope escape | Medium | Weekly |
| **Chaos** | Interruption, partial failure | High | Monthly |

**Golden rule:** a test written by the agent is **not sufficient on its
own** to verify code written by the agent. An independent test writer or
property testing is required.

---

## 8. The quality council

When gates conflict (e.g. `review` approves, `eval` rejects), the decision
forum:

| Situation | Decision maker | Rule |
|---|---|---|
| Two D1 gates conflict | vardiya-müdürü | The deterministic one wins |
| D1 passed, D2 dropped | the eval owner | D2 wins (behavior > test) |
| D3 approves, D2 rejects | the quality council | D2 wins; the D3 rationale goes on record |
| A threshold-change proposal | founder (C3) | The 14-day wait |

Council members: incelemeci, the eval owner, the red team, the human. An
agent majority cannot decide — this is the "producer ≠ approver" rule at
council level.

---

## 9. Known measurement traps

1. **Circularity:** if the same person writes the rule set and the test
   set, the score inflates.
2. **Small n:** a 5% difference on 20 cases is meaningless; the confidence
   interval may be ±20%.
3. **Survivorship bias:** measuring only the successful PRs.
4. **Harness drift:** the same model, a different harness, 10+ points apart.
5. **Set drift:** the set is updated and compared against the old number.
6. **Optimizing the measurement:** the sneakiest one; the system loosens
   its own test.
7. **Invisible human labor:** not counting human corrections.

All seven are tied to a rule in this document; none is waved away with
"we'll be careful".
