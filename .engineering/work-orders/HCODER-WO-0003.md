# Work Order — HCODER-WO-0003

## OBJECTIVE
Implement the smallest Hive-owned runtime bridge for the pinned Open Interpreter ACP and Cua Driver MCP processes without enabling real desktop actions.

## CONTEXT
Base `1591e3bca88096f51c87131a2b4f9cef0998e7c8`; Issue #5; branch `feat/HCODER-WO-0003-runtime-bridge`. Checkpoint HCODER-CP-0002 authorizes a mocked/contract-tested transport bridge before privileged desktop execution.

## CLASSIFICATION
NECESSARY · T3 · C3 · ELEVATED. Real computer actions remain HIGH_ASSURANCE.

## SCOPE
Shell-free stdio process lifecycle; strict NDJSON JSON-RPC 2.0 peer; ACP v1 initialize/session lifecycle/cancel/update collection; modern Cua MCP `2026-07-28` discovery only; exact binary-version preflight; deterministic mock-process tests; affected governance/documentation.

## OUT OF SCOPE
Open Interpreter prompt/model execution; provider credentials; Cua `tools/call`; mouse/keyboard/clipboard/screen/window/browser actions; desktop UI; automatic foundation installation; permission engine.

## FILES/SOURCES TO READ
Checkpoint, Decisions Ledger, Scope, DoD, Architecture, Security, Test Plan, Integration Contracts, foundation lock, pinned Open Interpreter ACP test, pinned Cua MCP protocol documentation.

## ARCHITECTURE RULES
Hive owns the process/transport/adapters. No shell invocation. Unknown version/protocol/result shape fails closed. Inbound agent requests are denied unless an explicit Hive handler exists. Cua adapter exposes discovery only and contains no `tools/call` method.

## ACCEPTANCE CRITERIA
Exact-version preflight gates production constructors; process lifecycle is bounded; malformed/unknown protocol fails closed; ACP v1 handshake/session create/cancel/close works under mock; Cua modern discovery works under mock; no privileged action API exists; deterministic tests and Governance pass; HEDS approves exact head.

## TESTS
`python -m compileall -q hive_runtime tools`; `PYTHONWARNINGS=error::ResourceWarning python -m unittest discover -s tests -p "test_*.py"`; existing foundation verifier and inventory doctor through Governance.

## DELIVERABLES
`hive_runtime` bridge package; runtime docs; tests; shared exact-version helper; Work Order/Context Lock; proposed Checkpoint Delta; Evidence Bundle/PR review.

## REVIEW FORMAT
HEDS delta-first on exact head; focus process lifecycle, protocol strictness, fail-closed behavior, capability leakage and forbidden privileged surfaces.

## STOP CONDITION
APPROVED + checkpoint promotion + merge, or CORRECTION REQUIRED/BLOCKED. No real desktop action is permitted in this Work Order.
