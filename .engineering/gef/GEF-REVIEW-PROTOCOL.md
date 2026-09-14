# GEF V1 HEDS Delta Review Protocol — Hive Coder

## Review pipeline
`ANALYZE DELTA -> SOURCE CHECK -> INVALIDATED PROOFS -> SEMANTIC REVIEW -> GATE RECEIPTS -> EXACT-HEAD VERDICT`.

First candidate may receive broad review to establish baseline. Later candidates are delta-first: compare last reviewed head with current exact head, carry forward only compatible proofs, invalidate proofs whose inputs changed, and never reopen accepted findings without an invalidating delta.

## Audit targets
Scope, Architecture, Requirements, Acceptance Criteria, DoD, regression risk, security, computer-use permissions, data integrity, contracts, error handling, test adequacy, unnecessary complexity, and proposed checkpoint accuracy.

## Verdicts
- `APPROVED`: may advance.
- `CORRECTION REQUIRED`: only a Correction Delta in the same WO/PR when safe.
- `BLOCKED`: resolve blocker before advancing.

Final verdict waits for all mandatory exact-head gates. Evidence from another head is historical only.
