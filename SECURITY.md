# Security Policy — KOVAN

## Supported versions

| Version | Support |
|---|---|
| 0.2.x | ✅ Active |
| 0.1.x | ❌ Upgrade to the latest release |

## Reporting a vulnerability

Please do **not** report security issues via public issues. Use GitHub's
*Security Advisories → Report a vulnerability* flow. We respond within
48 hours with validation and a remediation plan; fixes ship as a SemVer
patch release.

## Security decisions baked into the design

1. **BYOK (bring-your-own-key):** the API key stays on your machine only
   (`.anahtar*` files are gitignored). The key is never embedded in KOVAN
   code, written to the repo, or sent with telemetry.
2. **Egress logging:** the live adapter records every model call in
   `egress*.jsonl` (gitignored). The adapter produces no gate signals; gate
   decisions stay independent of the model.
3. **Fail-closed gates:** test/provenance/eval gates *block* on doubt. No
   verification runs on a dirty git tree.
4. **Human gates (C1/C3):** skill activation and breakage remediation require
   human approval; the system cannot accept its own approval (m.2).
5. **SBOM:** every run emits SPDX 2.3 output listing third-party components
   with versions.

## Out of scope

- **Provider-side** security of live model calls (OpenAI-compatible
  services): when you use your own key, the provider's data policy is your
  responsibility. Dry mode (the default) is fully offline and makes no model
  calls.
- Vulnerabilities in third-party code inside the target repo (track them
  with the SBOM and your own SCA process).
