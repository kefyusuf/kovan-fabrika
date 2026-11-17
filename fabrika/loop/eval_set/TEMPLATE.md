# Eval Set Template — how to build a frozen case set for your own target repo

> The eval set is the factory's most valuable asset: **the ceiling is this
> set, not the model.** This template is the rulebook for building the
> `eval_set/<repo>-v1.jsonl` file for your own repo. A rule violation = the
> set "burns" = the measurement becomes worthless.

---

## 1. The case schema (JSONL — one case per line)

```json
{"modul": "sicaklik", "fonksiyon": "celsius_fahrenheit", "args": [0], "beklenen": 32.0, "tol": 1e-6, "etiket": "C0->F"}
{"modul": "sicaklik", "fonksiyon": "ortalama", "args": [[]], "beklenen": "ValueError", "etiket": "ort-bos-hata"}
```

| Field | Required | Rule |
|---|---|---|
| `modul` | ✓ | An importable module inside the repo (the `.py` file name) |
| `fonksiyon` | ✓ | The function name in the module |
| `args` | ✓ | A **list** of positional arguments — a single list argument is written as `[list]` |
| `beklenen` | ✓ | A value (compared with `tol`) or `"XxxError"` (the exception name) |
| `tol` | — | Absolute tolerance; the default is 1e-6 |
| `etiket` | ✓ | A short, unique label — this is what shows up in the error lists |

**The common error:** if the function takes a list, writing
`args: [a, b, c]` — that is argument unpacking. For a list argument write
`args: [[a, b, c]]`. (Exactly this error produced 7 inconsistencies in our
first set and dropped the score to 0.922 — the set was fixed.)

---

## 2. Where the golden values come from — the honesty rule

**Right:** generate them from an existing, WORKING reference behavior
("golden"). The set catches a **change** in behavior; it does not prove
mathematical correctness.

**Wrong:** generating values from the output of broken code, or looking at
production and writing the eval set backwards so it passes. The latter is
circularity.

The set itself must also produce evidence: **after writing the set, inject
a broken diff** (`mutasyon.py` or by hand) and watch the score drop — if it
does not drop, the set is dead.

---

## 3. Size and distribution discipline

| Rule | Value |
|---|---|
| Minimum cases | 50 (the PRD FR criterion; our first set was 90) |
| Boundary cases | ≥ 20% (zero, negative, empty list, maximum) |
| Error cases | ≥ 10% (`"ValueError"`-style expected exceptions) |
| Label distribution | No single label may exceed 60% of the total |
| Freezing | A version in the file name: `sicaklik-v1.jsonl`; a change = a new version file |

**The life of a frozen set:** adding is free, **removing is forbidden**,
and changing an expectation is forbidden. When new behavior arrives, a
**v2** file is opened; v1 is moved under `retired/` and stays there with a
note of "why it retired".

---

## 4. Running it

```bash
cd fabrika/loop
python eval_kos.py --repo /path/to/your-repo --set eval_set/your-v1.jsonl
# with a diff (to measure the model's patch):
python eval_kos.py --repo ... --set ... --diff-dosya yama.diff
```

`kovan.py run --adapter http --eval-set eval_set/your-v1.jsonl ...` makes
the **eval gate blocking**: a score < 0.90 → the patch is rejected.

---

## 5. Anti-patterns (habits that kill the set)

1. **Loosening the set after writing code that passes it** — the
   improving-the-measurement ban (constitution art. 2).
2. **Showing the set to the agent that produces** — circularity; a
   holdout-discipline violation.
3. **Padding with a single label** — without distribution it is not a
   regression set.
4. **Editing the set without opening a version file** — comparison with old
   scores becomes a lie.
5. **Making the score the single success metric** — read it together with
   the mutation score (`mutasyon.py`) and a real test run.
