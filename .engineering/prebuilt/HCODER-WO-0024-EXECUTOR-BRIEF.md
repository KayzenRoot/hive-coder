# HCODER-WO-0024 — Executor Brief

**Status:** IMPLEMENTED / CORRECTION REVIEW PENDING  
**Base:** `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Issue:** `#77`  
**Review of the prebuild head:** `5236275753` — CORRECTION_REQUIRED (CRITICAL `0` / HIGH `4` / MEDIUM `2`) at `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`

## Start here
Read, in order:
1. `.engineering/work-orders/HCODER-WO-0024.md`
2. `.engineering/context-locks/HCODER-WO-0024.md`
3. `.engineering/prebuilt/HCODER-WO-0024-IMPLEMENTATION-PACK.md`
4. `.engineering/prebuilt/HCODER-WO-0024-ACCEPTANCE-SECURITY-MAP.md`
5. `.engineering/evidence/HCODER-WO-0024.md`
6. the existing contract modules under `apps/desktop/src/contracts/`.

## What already exists
The contract surfaces are materialised and tested. Complete them; do not redesign them:
- `apps/desktop/src/contracts/version.ts` — canonical source law, strict SemVer, drift evaluation.
- `apps/desktop/src/contracts/releaseChannel.ts` — channels, shape matching, eligibility, cross-channel refusal.
- `apps/desktop/src/contracts/updateState.ts` — state model, transition law, authenticity gate, bounded error metadata.
- `apps/desktop/src/contracts/aboutReadModel.ts` — bounded read-only Settings/About model.
- `apps/desktop/src/lib/updateService.ts` — boundary, inert adapter, forbidden-member guard.
- `tools/desktop/version_drift.py` — deterministic offline drift verifier.
- `tests/desktop/test_version_drift.py` — drift and SemVer contract tests.

## Mandatory order for any completion work
A. Keep the canonical version source fixed at `tauri.conf.json`. Do not switch it without a governed decision.
B. Keep strict SemVer. Never coerce, trim, default or partially accept a version.
C. Keep the channel vocabulary closed and stable the default. Never add an implicit cross-channel path.
D. Keep the transition table explicit. Every undeclared transition must fail closed.
E. Keep `ADMITTED_AUTHENTICITY_SCHEMES` empty until a governed cryptographic-verification slice admits a scheme. Never invent, fake or bypass verification.
F. Keep the production `UpdateService` inert. Any real updater integration is a later governed Work Order.
G. Keep diagnostic metadata bounded and redaction-safe. Never widen the charset or drop the credential-shape rule.
H. Keep `bundle.active=false`.

## Forbidden shortcuts
No updater plugin, endpoint, HTTP client, download, installer, restart, signing, notarization, release/tag publication, secret or key access, CI release workflow, dependency addition, `bundle.active=true`, generic process/shell execution, or weakening of an existing HIGH_ASSURANCE gate. No test-only stand-in may become reachable from production code. No widened error-detail charset.

## Definition of Done for execution
Contract tests pass; the drift gate reports `LOCKED` against live manifests; no updater/download/install/signing/release path exists; native Linux, Windows and macOS lanes are green at the exact head; the acceptance/security map has no unimplemented required proof; and HEDS reports HIGH/CRITICAL `0/0`. The decision stays PROPOSED and the PR stays Draft until its own promotion gate passes.

## STOP
If completing this slice requires any distribution authority, a dependency with update side effects, or a weakened security gate, STOP and create a same-Work-Order Correction Delta. Do not begin HCODER-DIST-001B.
