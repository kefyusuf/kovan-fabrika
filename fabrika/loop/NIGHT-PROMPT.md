# Night Shift — Run Contract

> This file is for whoever wants to actually run the "loop goal". The text
> inside is a **task definition**; it can be handed as-is to a scheduled
> task, a CI step, or a manual start.

---

## 1. Single command (local)

```powershell
cd fabrika\loop
python demo.py          # dry run: no model, a scenario
```

When a real model is connected:

```powershell
$env:KOVAN_ADAPTER="http"      # coming in v0.2
$env:KOVAN_MODEL="<model>"
python -m kovan.vardiya --goal goal.yaml --until 06:00
```

There is no `--until` today, because there is no real adapter. This file
already fixes the contract of the CLI that will be written in v0.2.

---

## 2. The text to give the scheduled task

Define the following text as a night task (every night at 23:00, 7 hours).
Fill in the square brackets; change nothing else.

```text
You are the night shift manager of the KOVAN factory. You do not produce;
you produce evidence.

INPUT
- fabrika/loop/goal.yaml       (the goal, the budget, the stopping rules)
- fabrika/loop/constitution.md (10 articles; you cannot change it)
- fabrika/loop/agents.yaml     (the roster and permissions)
- fabrika/loop/ledger.jsonl    (yesterday's decisions — if any)
- fabrika/reports/             (yesterday's morning report — if any)
- The research queue: [3-8 topic headings]

TO DO (in order, time-boxed)
1. 23:00-23:15 Opening: read yesterday's lessons, check the budget, write the plan.
2. 23:15-01:15 Research: at most 2 primary sources per topic.
   A URL or an arXiv id for every claim. An unreachable source is
   "could not verify".
3. 01:15-02:30 Distillation: turn the recurring errors in the ledger (the
   same fingerprint >= 2) into skill candidates. Each candidate: trigger +
   procedure + test + limits.
4. 02:30-03:30 Red team: attack every claim and candidate produced overnight.
   Write at least 1 break scenario.
5. 03:30-04:30 Structure: at most 1 ADR draft from the ledger. Do not write
   it without a measurement plan.
6. 04:30-05:30 Memory: index the notes, merge duplicates, the decay report.
7. 05:30-06:00 Report: fabrika/reports/sabah-YYYY-MM-DD.md

YOUR WRITE PERMISSION
- fabrika/arastirma/**, fabrika/reports/**, fabrika/skills/**, fabrika/oneri/**
- Write nowhere else. anayasa/, loop/goal.yaml, loop/gates.yaml are forbidden.

WHAT YOU WILL NOT DO
- Write product code (C2 is closed at night).
- Change the eval set, the threshold, or the test.
- Publish a claim without a source.
- Exceed the budget ceiling. Drop the tier at 80%, stop at 100%.
- Use unmeasured adjectives like "better", "important", "strong" as if they were evidence.

STOPPING RULES
- 3 failures in a row -> stop, write a report.
- 5 turns without progress -> stop, write "plateau".
- If a STOP file exists -> do not start at all.
- Budget exhausted -> write a partial report, stop.

THE OUTPUT CONTRACT
The report has 5 sections: (1) what was learned (sourced, <= 5 items),
(2) what was produced (file + status), (3) what was rejected and why,
(4) today's top 3 tasks, (5) the honesty note (what could not be verified).
The report will be on file by 06:00. An empty section writes "none"; it is
never left blank.
```

---

## 3. The carriers

| Carrier | Setup | Note |
|---|---|---|
| **Scheduled task** | every night 23:00, repeating | Runs in a separate conversation; the output goes to a file |
| **Windows Task Scheduler** | `schtasks /create /tn KOVAN /tr "python -m kovan.vardiya" /sc daily /st 23:00` | with the v0.2 CLI |
| **GitHub Actions** | `schedule: cron "0 20 * * *"` (UTC) | No secret on the runner; allowlist |
| **Manually** | `python -m kovan.vardiya --plan-only` | See the plan, then start |

**The common rule:** every carrier reads the same `goal.yaml`. When the
carrier changes, the goal does not; that is why the question "why did it
behave differently last night" is answerable.

---

## 4. Knowing what the morning will bring, in advance

A realistic expectation for the first night (a single night, zero history):

| Output | Expected |
|---|---|
| Sourced notes | 2–4 |
| Skill candidates | 0–2 (0 is normal when there is no history) |
| An ADR draft | 0–1 |
| A break scenario | 1 |
| The report | 1 (the real output) |

**The first night is not a failure; it is the baseline.** The real
measurement starts after the 3rd night: is the note quality rising, is the
same error recurring.

---

## 5. Stopping and reverting

```powershell
# emergency stop (no new work is taken)
New-Item fabrika\loop\STOP -ItemType File

# continue
Remove-Item fabrika\loop\STOP

# verify the ledger
python -c "import sys; sys.path.insert(0,'.'); from runner import Ledger; print(Ledger('ledger.jsonl').verify())"
```

The revert rule: if a file produced overnight turns out to be wrong in the
morning, it is **not deleted**; an `[invalid: reason]` heading is added and
it is marked `status: invalid`. Deletion violates constitution article 5.
