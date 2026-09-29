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

## Prospective owner-only review identity: DEC-033 / HCODER-OPS-0001
After the owner-directed governance migration is accepted, the reviewer **role** remains mandatory but a separate reviewer **account/person** does not. `KayzenRoot` may execute a documented exact-head `OWNER_SELF_AUDIT / NOT_INDEPENDENT` and proceed without external approval only when the actual branch ruleset allows it, all applicable protected checks are SUCCESS, unresolved CRITICAL/HIGH = 0/0, all blocking review threads are resolved on evidence, and source/scope/security constraints are met. Never claim human independence from an owner self-review or optional reviewer agent/bot; do not request another account solely to satisfy a process label. Risk class HIGH_ASSURANCE additionally demands owner-recorded explicit risk acceptance, adversarial fail-closed/negative-test review and continued hard blocking of missing trust/credentials. Document exact current SHA, carried/invalidated proof, changed-file scope, findings, tests/gates, risk, STOP and post-merge check plan. Historical independent reviews stay immutable. A change of head invalidates current-head receipts. This section prospectively supersedes only incompatible *collaborator identity* expectations, not the severity/CI/evidence/preservation requirements. For reviews that can be completed safely via ChatGPT/GitHub, the chat-first routing in AGENTS takes precedence over the older unconditional Codex PDF sentence below; only issue a PDF when a real local executor is needed.

## Review deliverable law (canonical, detail)
This expands the review output contract above; where the two overlap they agree.

- `APPROVED`: the delivered PDF is the next increment's executor prompt.
- `CORRECTION REQUIRED`: the delivered PDF is the bounded Correction Delta prompt for the **same** Work Order. No new Work Order and no new increment.
- `BLOCKED`: deliver a bounded unblock prompt when one can be stated objectively; otherwise state explicitly why no executable prompt can be issued yet.
- No new increment may begin before its predecessor's acceptance. A review never opens the successor increment while the current one is unresolved.

The PDF is the executable artifact; the chat/verdict text is the audit record. If no PDF is delivered, the review is incomplete regardless of its verdict.
