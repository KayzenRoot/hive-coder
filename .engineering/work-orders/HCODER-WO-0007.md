# HCODER-WO-0007 — Model Capability Registry + Skills Foundation

**Classification:** NECESSARY · T3 · C3 · ELEVATED  
**Base checkpoint:** HCODER-CP-0006  
**Base SHA:** `91e0265a215d4edb179d6fcdafbbf3a05409e244`

## OBJECTIVE
Create Hive-owned deterministic model capability negotiation and the governed foundation for reusable/learned skills.

## CONTEXT
CP-0006 proves the Cua integration harness but broad autonomy must know what a selected model can actually do and must treat skills as governed artifacts rather than instructions with ambient authority.

## SCOPE
Capability evidence/profile/registry/negotiation; skill manifest/store/ingestion/evaluation/activation/rollback; MCP skill content untrusted by construction; deterministic adversarial tests; canonical docs and checkpoint.

## OUT OF SCOPE
Provider credentials, remote control, automatic external installs, self-modifying production skills, new desktop mutation capabilities.

## FILES/SOURCES TO READ
CP-0006, Decisions Ledger, Scope, Architecture, Security, Test Plan, Integration Contracts, CP-0005 permission boundary.

## REQUIREMENTS
Fail closed on unknown/unverified model capability. Skill text cannot change capability evidence or policy. Skill activation cannot expand existing permission grants. Duplicate versions and digest mismatches fail closed.

## ARCHITECTURE RULES
Hive-owned interfaces; data-driven evidence; no capability inference from model names; MCP resources remain untrusted data; CP-0005/0006 remain authoritative for mutation.

## CONSTRAINTS
No network calls, provider secrets, automatic installs or desktop mutation in this increment.

## ACCEPTANCE CRITERIA
Deterministic negotiation and skill lifecycle tests pass; malicious skill text cannot activate itself or grant authority; broad regression remains green.

## TESTS
Unit tests + Governance exact-head. ResourceWarning remains fatal under CI.

## DELIVERABLES
Runtime intelligence package, tests, docs, decision/checkpoint updates, evidence bundle.

## REVIEW FORMAT
HEDS Delta review on exact PR head. UNKNOWN is never PASS.

## STOP CONDITION
Governance green on exact head, HEDS APPROVED, no unresolved HIGH/CRITICAL, CP-0007 promoted, squash merge to main.
