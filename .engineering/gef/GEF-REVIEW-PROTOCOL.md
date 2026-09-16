# GEF V1 Universal Review Protocol — Hive Coder

## Review pipeline
`ANALYZE DELTA -> SOURCE CHECK -> INVALIDATED/CARRIED PROOFS -> SEMANTIC REVIEW -> GATE RECEIPTS -> EXACT-HEAD VERDICT -> NEXT EXECUTABLE PDF`.

First candidate may receive broad review to establish baseline. Later candidates are delta-first: compare last reviewed head with current exact head, carry forward only compatible proofs, invalidate proofs whose inputs changed, and never reopen accepted findings without an invalidating delta.

## Audit targets
Scope, source hierarchy, architecture, requirements, acceptance criteria, DoD, brownfield preservation, regression risk, security, authority/permissions, data integrity, contracts, error/recovery behavior, test adequacy, unnecessary complexity, evidence accuracy and checkpoint accuracy.

## Verdicts
- `APPROVED`: may advance.
- `CORRECTION_REQUIRED`: only a bounded Correction Delta in the same WO/PR when safe.
- `BLOCKED`: resolve the external/architectural/evidence blocker before advancing.

## APPROVED exact-head conditions
Candidate SHA identified; required checks complete; CRITICAL=0; HIGH=0; no unresolved scope/preservation violation; no evidence mismatch; no stale-head mismatch. If head changes, audit again.

## Review output contract
Every review states identity, source match, delta, invalidated/carried proofs, findings with severity/evidence/correction, gates, checkpoint audit, verdict and next legal action.

Every review must also deliver the next executable Codex prompt as a generated PDF. A correction verdict generates the correction prompt for the same Work Order, not a new increment.

Final verdict waits for all mandatory exact-head gates. Evidence from another head is historical only.

## Review deliverable law (canonical, detail)
This expands the review output contract above; where the two overlap they agree.

- `APPROVED`: the delivered PDF is the next increment's executor prompt.
- `CORRECTION REQUIRED`: the delivered PDF is the bounded Correction Delta prompt for the **same** Work Order. No new Work Order and no new increment.
- `BLOCKED`: deliver a bounded unblock prompt when one can be stated objectively; otherwise state explicitly why no executable prompt can be issued yet.
- No new increment may begin before its predecessor's acceptance. A review never opens the successor increment while the current one is unresolved.

The PDF is the executable artifact; the chat/verdict text is the audit record. If no PDF is delivered, the review is incomplete regardless of its verdict.
