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

## Review deliverable law (canonical)
Every completed review must already deliver the next executable executor prompt as a generated PDF, in the same response as its verdict. A review is not complete without it.

- `APPROVED`: the delivered PDF is the next increment's executor prompt.
- `CORRECTION REQUIRED`: the delivered PDF is the bounded Correction Delta prompt for the **same** Work Order. No new Work Order and no new increment.
- `BLOCKED`: deliver a bounded unblock prompt when one can be stated objectively; otherwise state explicitly why no executable prompt can be issued yet.
- No new increment may begin before its predecessor's acceptance. A review never opens the successor increment while the current one is unresolved.

The PDF is the executable artifact; the chat/verdict text is the audit record. If no PDF is delivered, the review is incomplete regardless of its verdict.
