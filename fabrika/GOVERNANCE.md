# KOVAN — Governance, Security, and Cost

> **v2 note (November 4, 2026):** The current system definition is
> [`SYSTEM.md`](SYSTEM.md). The compliance layer `uyum.py` is live (import
> allowlist + dependency-file detection + copy suspicion + duplicate
> function = the provenance signal); the SBOM seed (`sbom.py`, SPDX 2.3,
> lock versions) and the **egress log** (`adapter_http --egress-log`) are
> live. Copy-block detection and full SPDX package versions are the
> remainder of S4.

> This document is not legal advice. Regulation items are marked **sourced
> but unverified** ([C]); before any public release they must be confirmed
> with a lawyer and current official texts.

---

## 1. The threat model

| # | Threat | Scenario | Impact | Control |
|---|---|---|---|---|
| T1 | **Prompt injection** | A read file/web page says "ignore the rules" | The agent does out-of-scope work | Isolation + policy + source separation |
| T2 | **Secret leak** | The agent reads `.env`, writes it into a report | Credential exposure | No secrets + forbidden paths + output scanning |
| T3 | **Poisoned dependency** | The agent adds an unknown package | Supply-chain attack | The `provenance` gate + the license list |
| T4 | **Budget escape** | The loop retries endlessly | An invoice explosion | Reservation + ceiling + circuit breaker |
| T5 | **Self-authorization** | The agent changes its own permission/threshold | The audit collapses | C3 + forbidden paths + a separate ledger |
| T6 | **Data leak** | Customer code goes to an external model | Privacy violation | Provider policy + a local-model option |
| T7 | **Coordination collision** | Two agents overwrite the same file | Data loss, a wrong merge | Worktrees + file locks + single writer |

### 1.1 The "lethal trifecta" ban

The following three cannot coexist **together** in one session:

1. private/rarely-known data,
2. untrusted content (external files, the web, issue text),
3. outbound communication (network, e-mail, opening a PR).

Two of them may coexist; three may not. This rule architecturally blocks
injection from turning into exfiltration ([C] — Simon Willison's "lethal
trifecta" framework).

---

## 2. Isolation

| Layer | Implementation | Verification |
|---|---|---|
| Process | One task per container | the image tag is recorded |
| Files | git worktree; the main tree is read-only | a clean `git status` |
| Network | Allowlist proxy; off by default | the egress log |
| Secrets | Not in the environment; injected at the tool layer | the `env` scan |
| Resources | CPU/memory/time ceilings | the cgroup limit |
| Output | Only `diff` + artifacts leave | the output scan |

**Rule:** the agent runs in the state "may reach these 7 hosts", not "may
reach the internet". `goal.yaml → constraints.allowed_hosts` is the single
source for this.

---

## 3. Human gates

| Class | Example | Approval | Time |
|---|---|---|---|
| C1 | Skill activation | eval + human review | 1 day |
| C2 | Product code | gates (automatic) | — |
| C3 | Constitution, threshold, model, roster | founder + gate keeper | 14 days |
| Security | Network policy, sandbox loosening | gate keeper | immediate |
| Legal | License, external data | founder | 24 h |
| Release | Version, changes touching the customer | gate keeper | 24 h |

**Two-signature rule:** the writer of a proposal and its approver cannot be
the same person. Even in a one-person setup, two separate records are
produced (proposal + approval); this keeps the audit working when a second
human is added later.

**Timeout:** if a C3 approval does not arrive within 14 days, the proposal
becomes `expired` and must be reopened. Proposals do not pile up waiting
silently.

---

## 4. Audit and evidence

| Component | What it records | Retention | Verification |
|---|---|---|---|
| `ledger.jsonl` | Every decision + gate result | Indefinite | the `verify()` hash chain |
| `lessons.jsonl` | The rejection reason + fingerprint | Indefinite | schema |
| `skills/` | Skill + evidence + test | Versioned | test |
| `reports/` | The morning report | Indefinite | the 5-section check |
| Egress log | External calls | 90 days | allowlist comparison |
| Cost record | Tokens/USD | 24 months | invoice reconciliation |

**External anchor (v0.2):** the ledger's final hash is written daily to a
separate place (e.g. a signed commit tag). Purpose: to make a wholesale
rewrite of the whole ledger detectable.

---

## 5. Compliance frameworks

| Framework | What it asks for | Our counterpart | Status |
|---|---|---|---|
| **ISO/IEC 42001** | An AI management system: policy, roles, risk, continuous improvement | constitution + roster + the risk record | Partial |
| **NIST AI RMF** | The Govern–Map–Measure–Manage cycle | the R1–R4 rings | Partial |
| **EU AI Act** | Risk class, technical documentation, human oversight | the C classes + the ledger | Partial |
| **SBOM** (SPDX/CycloneDX) | A dependency inventory | `uyum/sbom.json` | Missing |
| **SLSA** | Supply-chain level | signed artifacts | Missing |

**EU AI Act timeline [C]:** Annex III obligations for high-risk categories
were reported as December 2, 2027, and Annex I as August 2, 2028. These
dates may change; they must be confirmed from the official text before
release. Also: which risk class a code-production tool falls into depends on
the **context of use** (e.g. it is not put in the same basket as a system
making hiring decisions). That assessment belongs to a lawyer, not an
engineer.

---

## 6. Licensing and provenance

Rules:

1. **Code whose source cannot be shown does not merge.** Every patch
   carries which spec + which files it derives from.
2. **Adding a dependency is C3.** The agent cannot add a package on its own.
3. **License allowlist:** MIT, Apache-2.0, BSD, ISC. GPL/AGPL and unknown
   licenses → a human decision.
4. **Copy-paste detection:** if the candidate diff contains 40+ lines of
   verbatim external code, the `provenance` gate flags it.
5. **The AI-production label:** the commit message carries
   `Co-authored-by: kovan` and the PR description carries the production
   record.

**Legal note [C]:** the copyright status of generated code varies by country
and case; in 2026 a US appellate ruling reportedly narrowed training-data
claims. This is not a legal opinion; consult before commercial use.

---

## 7. The cost model

### 7.1 Unit economics

```
PR cost = model + cache + CI + human review + infrastructure
```

| Item | Typical share | Way to reduce |
|---|---|---|
| Model (production) | 45% | Model steering, smaller T1/T2 |
| Model (review) | 20% | Cached context, a cheaper model |
| Retries | 15% | A better spec, better tests |
| CI | 10% | Immutable environment, layer caching |
| Human | 10% | Smaller PRs, clearer rationales |

**Levers [C]:** cached reads get markedly cheaper (~10% of the price,
depending on the provider), and batch processing gives ~50% off. Provider
prices change; the table is updated monthly by the butce-bekcisi.

### 7.2 Budget protection

| Threshold | Behavior |
|---|---|
| 50% | Report: a speed/cost comparison |
| 80% | The model tier drops (T3 → T2), parallelism 3 → 1 |
| 95% | Only ongoing tasks are completed |
| 100% | No new tasks are taken; a report is written; the loop stops |

**Reservation:** before every task starts, a budget of `estimate_tokens` is
reserved. This closes the "we'll notice along the way" possibility
(`test_budget_exhaustion_stops`).

### 7.3 The cost anti-pattern

"Spending 40 dollars on a PR and reporting it as 6 dollars" — by not
counting human review minutes. The `MBB` metric includes human time too;
otherwise the cost table turns into an advertisement banner.

---

## 8. Incident response

> **Drill (November 4, 2026):** the four steps of this section were audited
> as runnable via `tatbikat.py` (a normal run, ledger verification, stopping
> with STOP, rollback on a dirty clone) — 4/4 PASS. A4's first version fell
> wrongly on a line-ending (CRLF) comparison; the criterion was corrected to
> `git status --porcelain`.

| Level | Example | First response | Who |
|---|---|---|---|
| **S1** | A secret leak, unauthorized write | Stop + rotate the keys | gate keeper (immediate) |
| **S2** | A C3 that passed without policy, eval manipulation | Stop + roll back + record | founder (1 h) |
| **S3** | Budget overrun, a burst of recurring errors | Throttle + report | vardiya-müdürü (immediate) |
| **S4** | A single-task error | Lesson record + continue | damitici (same day) |
| **S5** | A quality drop (regression) | Automatic rollback | eval (immediate) |

**Runbook (S1):**
1. The `STOP` file → the loop stops.
2. The containers are stopped; the network is cut.
3. The ledger's last 24 hours are scanned: which call, which output.
4. The affected keys are rotated.
5. Report: what happened, what leaked, how long it took.
6. A policy update (C3) — a repeat of the same incident becomes impossible.

**Rule:** every S1/S2 incident must produce a **constitutional or gate
change**. Otherwise the incident is not counted as "closed"; it merely
becomes "forgotten".

---

## 9. Policy example (an Airlock rule)

```yaml
# policy/kovan.yaml (draft)
rules:
  - id: deny-secrets
    match: { path: [".secrets/**", "**/*.pem", "**/.env"] }
    decision: block
    reason: "Sır dosyası okunamaz."

  - id: deny-constitution
    match: { path: ["anayasa/**", "loop/goal.yaml", "loop/gates.yaml"] }
    decision: block
    reason: "Anayasa değişikliği yalnızca insan onayıyla."

  - id: ask-new-dependency
    match: { event: "file_write", file: ["package.json", "pyproject.toml", "Cargo.toml"] }
    decision: ask
    reason: "Yeni bağımlılık C3 sınıfıdır."

  - id: deny-network-default
    match: { event: "network" }
    decision: block
    unless: { host_in: "${allowed_hosts}" }
    reason: "Varsayılan ağ kapalı."

  - id: deny-prod-deploy
    match: { command_regex: "(kubectl|terraform|aws|gcloud).*(apply|deploy|destroy)" }
    decision: block
    reason: "Üretim erişimi ajanda yok."
```

These rules are compatible with Airlock's current format; the `policy` gate
uses the same engine (ADR-F07).

---

## 10. The compliance checklist

| # | Check | Evidence | Status |
|---|---|---|---|
| 1 | The constitution is written and write-forbidden | `loop/constitution.md` + policy | Present |
| 2 | Change classes defined | the C0–C3 table | Present |
| 3 | Human gates defined | the §3 table | Present |
| 4 | The audit record cannot be altered | hash chain + test | Present |
| 5 | Isolation defined | `goal.yaml` sandbox | Spec exists, no code |
| 6 | Budget ceiling and stopping | `goal.yaml` + test | Present |
| 7 | SBOM | `uyum/sbom.json` | **Missing** |
| 8 | License allowlist | §6 | Spec exists, no automation |
| 9 | The incident runbook | §8 | Present (on paper) |
| 10 | The data retention policy | §4 | Partial |
| 11 | The model provider contract | — | **Missing** |
| 12 | Employee/customer data separation | — | **Missing** |

The last three are real gaps that must close before productization.

---

## 11. What this document does not cover

- The model providers' terms of service and data-processing addenda.
- The "produced with AI" declaration in customer contracts.
- Labor law (the effect of agent output on employee performance).
- Insurance and liability.
- Tax/accounting.

These are not "we'll look later" items; they are parts of the
**productization gate**. Writing them down at the concept stage keeps them
from becoming surprises later.
