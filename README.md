# KOVAN — kovan-fabrika

![tests](https://github.com/kefyusuf/kovan-fabrika/actions/workflows/tests.yml/badge.svg)

**A capacity-bounded, evidence-first software factory.**

KOVAN accepts software tasks under explicit capacity accounting, pushes every
change through a fixed gate sequence (policy → tests → provenance → lint →
types → review → eval → cost), separates the producer from the approver, and
records every decision with evidence in a tamper-checked ledger. Dry mode is
fully offline (zero tokens); live mode uses your own API key (BYOK).

## Quick start

```bash
pip install -e fabrika --no-build-isolation   # needed on embedded Python
cd fabrika/loop
kovan plan          # capacity plan (dry, deterministic)
kovan run           # gated run + ledger + SBOM
python retro.py     # weekly retro + mechanical checks
```

Full setup and the fresh-clone note: [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation map

| Document | Content |
|---|---|
| [fabrika/SISTEM.md](fabrika/SISTEM.md) | v2 system definition: 3 lines, component table, 167 tests |
| [fabrika/README.md](fabrika/README.md) | The 6 principles (İ1–İ6), file map, setup |
| [fabrika/ADR.md](fabrika/ADR.md) | Architecture decision records (F01–F13) |
| [fabrika/EVIDENCE-UPDATE.md](fabrika/EVIDENCE-UPDATE.md) | Evidence log (§1–§21) |
| [CHANGELOG.md](CHANGELOG.md) | Release history (SemVer) |

## Norms

- **Producer ≠ approver (m.2):** the system cannot accept its own approval.
- **Human gates (C1/C3):** skill activation and breakage remediation require a
  human decision.
- **Fail-closed:** gates block on doubt; verification never runs on a dirty
  git tree.
- **Evidence:** every run produces a ledger (JSONL), an SBOM (SPDX 2.3), and a
  night-status record.

Security disclosure: [SECURITY.md](SECURITY.md) — never use public issues.

## License

Apache-2.0 — see [LICENSE](LICENSE).
