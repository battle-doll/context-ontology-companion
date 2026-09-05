# Test evidence — 2026-09-05

Executed on macOS, Python 3.12.14. `python scripts/check.py`: 38 product tests passed, independent vendored-contract digest check and demo/tools output parsing passed. [Raw product log](docs/agent/reports/2026-09-05-product-tests.txt).

The product tests include a fresh-process recovery, actual synthetic local HTTP login/review/apply, unauthorized and CSRF/Host/Origin cases, nonce/digest/expiry/replay, concurrent approval, Unicode budget, time boundary, scope separation, invalid inputs, deletion/restart, bounded export consumption, JSON Schema output checks, and malformed stdio process recovery.

An independent reviewer additionally exercised 106 malformed Context calls and 600 Contracts value mutations, read-only DB hash preservation and erasure/concurrent snapshots. [Independent report](docs/agent/reports/2026-09-05-security-review.md). The review reports are snapshots; final nested output schema and proposal-only metadata fixes were checked with additional focused tests.

Official local plugin manifest and Skill validators passed. `scripts/public_gate.py` checks local links, bounded secret patterns, required OSS files and exact runtime/submission metadata parity. It is not a comprehensive security audit.

The existing 32 design-package and 20 reference-experiment tests are separate from product tests. Required JSON Schema fixture validation uses pinned requirements-dev.txt. The original no-submission-file assertion was upgraded to require exact implemented descriptor parity and unpublished release state; integrity hashes were refreshed only after reviewing the intended new file set. Original input manifests and transitional failures are preserved at the containing workspace verification directory, outside these independent source packages.

Windows/Linux CI: configured but not_run. Windows ACL, actual ChatGPT/Codex host integration, OAuth/cloud tenancy, live E2E, model retrieval benchmark, token costs, submission and publication: not_run. No real user credentials or private conversations were used.

## Current-project application

[Local Codex trial](docs/LOCAL_CODEX_TRIAL.md): 160 lifecycle assertions, 46 schema-validated tool responses, 10 unique tools invoked through Codex 0.153.3 app-server. Explicit simulation approval; hosted ChatGPT and real human approval not verified.
