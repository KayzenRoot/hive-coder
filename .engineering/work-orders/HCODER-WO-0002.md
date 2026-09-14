# Work Order — HCODER-WO-0002

## OBJECTIVE
Establish a verified, replaceable foundation layer for Open Interpreter and Cua Driver before live computer-control or desktop UI implementation.

## CONTEXT
Base `9aedea9f9705cf3206ed17ca42b160d8eae91c7c`; Issue #3; branch `feat/HCODER-WO-0002-foundation-runtime`. Checkpoint HCODER-CP-0001 authorizes foundation license/provenance assessment and the smallest architecture spike.

## CLASSIFICATION
NECESSARY · T3 · C3 · ELEVATED. Any future privileged computer action is HIGH_ASSURANCE.

## SCOPE
Pin upstream releases/tags/commits/artifact hashes; provenance records; protocol-first boundary; fail-closed non-installing doctor; deterministic verifier/tests; affected governance.

## OUT OF SCOPE
Full upstream vendoring; GUI; live input automation; credentials/providers; automatic network install; OmniParser/Ultralytics; final product packaging.

## FILES/SOURCES TO READ
Checkpoint, Decisions Ledger, Scope, DoD, Architecture, Requirements, Integration Contracts, License/Provenance, upstream release/tag/license metadata.

## REQUIREMENTS
R2, R3, R5, R8, R9.

## ARCHITECTURE RULES
Hive-owned boundary only. ACP/stdio for Interpreter, JSON-RPC 2.0 for Cua Driver. Unknown version/capability fails closed. No UI dependency on upstream internals.

## ACCEPTANCE CRITERIA
Exact upstream identity and Windows x64 SHA256 recorded; optional copyleft components excluded; lock validates; doctor has no install/control side effects; unit tests pass; Governance exact-head success; HEDS approval.

## TESTS
`python tools/foundations/verify_lock.py`; `python tools/foundations/doctor.py --inventory-only`; `python -m unittest discover -s tests -p "test_*.py"`.

## DELIVERABLES
Foundation lock; provenance docs; doctor/verifier; tests; CI delta; Evidence Bundle; proposed Checkpoint Delta.

## REVIEW FORMAT
HEDS delta-first against exact head; security/license/architecture findings ranked CRITICAL/HIGH/MEDIUM/LOW.

## STOP CONDITION
APPROVED + checkpoint promotion + merge, or CORRECTION REQUIRED/BLOCKED. No live computer-control implementation in this WO.
