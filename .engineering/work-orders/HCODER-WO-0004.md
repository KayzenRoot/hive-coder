# Work Order — HCODER-WO-0004

## OBJECTIVE
Implement the Hive-owned Permission & Control Plane as the HIGH_ASSURANCE prerequisite for any future computer-use action.

## CONTEXT
Base `f05154b3494c9ed67c93a0ae6374a49713d343c3`; Issue #8; branch `feat/HCODER-WO-0004-control-plane`. Checkpoint HCODER-CP-0003 explicitly requires this increment before any Cua `tools/call`.

## CLASSIFICATION
NECESSARY · T3 · C4 · HIGH_ASSURANCE.

## SCOPE
Capability/risk taxonomy; default-deny policy rules; action/application/window/workspace/resource allowlists and explicit-deny precedence; bounded control sessions; policy epochs; emergency stop; user takeover; cancellation propagation callbacks; HMAC-signed request-bound single-use approvals and execution permits; tamper/replay/expiry checks; append-only hash-chained redacted in-memory audit; adversarial tests; Ubuntu + Windows validation.

## OUT OF SCOPE
Cua `tools/call`; Open Interpreter prompt execution; real mouse/keyboard/clipboard/screen/window/browser mutation; provider credentials; desktop UI; OS-global hotkey; durable audit storage; production desktop deployment.

## FILES/SOURCES TO READ
Checkpoint, Decisions Ledger, Scope, DoD, Architecture, Security, Test Plan, Requirements, Integration Contracts, existing runtime bridge.

## ARCHITECTURE RULES
The control plane sits between Hive orchestration and every future privileged adapter call. Unknown capability/target/session/approval state fails closed. Model text is untrusted context and never grants capability. Explicit deny wins. Mandatory-approval capability classes cannot downgrade approval by policy. Tokens are scoped to request fingerprint + session + policy epoch + global emergency epoch + expiry and are single-use.

## ACCEPTANCE CRITERIA
Denied requests cannot obtain execution permits; approvals and permits reject tamper/replay/target or argument swap/stale policy/expiry; wrong app/window/workspace/resource fail closed; emergency stop and user takeover invalidate ephemeral authorization and invoke cancellation callbacks; audit redacts sensitive material and verifies its digest chain; broad regression and Windows control-plane tests pass; no Cua action surface is added; HEDS has no unresolved HIGH/CRITICAL finding.

## TESTS
`python -m compileall -q hive_runtime tools`; `PYTHONWARNINGS=error::ResourceWarning python -m unittest discover -s tests -p "test_*.py"`; Windows targeted control-plane suite through Governance; HEDS adversarial review.

## DELIVERABLES
`hive_runtime` control-plane modules; control-plane docs; tests; Governance platform job; Context Lock; Evidence Bundle; proposed Checkpoint Delta.

## REVIEW FORMAT
HEDS delta-first on exact head. Focus authorization forgery, replay, confused deputy/target swap, stale policy, prompt injection, secret leakage, stop/takeover races, platform behavior and accidental privileged surfaces.

## STOP CONDITION
APPROVED + HCODER-CP-0004 promotion + squash merge, or CORRECTION REQUIRED/BLOCKED. Real computer mutation remains forbidden after this Work Order.
