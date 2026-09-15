# HCODER-WO-0020 — Checkpoint Delta

**Source checkpoint:** `HCODER-CP-0019` — APPROVED / CANONICAL  
**Target candidate:** `HCODER-CP-0020` — CANDIDATE / NOT CANONICAL  
**Technical head:** `86c6e956985e0b51e0f56b3568a3fe9db61fef90`  
**Technical HEDS:** `5216871217` — APPROVED FOR PROMOTION CANDIDATE

## Product delta
CP-0020 candidate adds a single fixed desktop runtime-status supervisor boundary and a read-only System Truth presentation surface. It consumes the already-canonical CP-0019 helper and CP-0018 wire without widening either.

New governed path:

`React System Truth -> argument-free Tauri read command -> fixed Rust supervisor -> fixed CP-0019 sidecar -> CP-0018 canonical wire -> strict raw TypeScript decoder -> presentation only`

## Preserved laws
- generic process/shell execution remains forbidden;
- no caller/model-selected executable/path/args/env;
- child environment is cleared;
- only fixed `--stdio-status-v1` is used;
- response ceiling remains 33,024 bytes;
- runtime status is presentation, never authorization;
- safety/task/file/Git/computer mutation remains unavailable;
- Permission & Control Plane remains the only mutation authority choke point.

## Corrections closed in candidate
- CR-001 MEDIUM: no fabricated zero permission counters; canonical subsystem provenance preserved.
- CR-002 MEDIUM: fixed-supervisor invariants promoted into executable security-gate enforcement.

## Evidence
Exact technical head passed Governance #263 (**288/288 Ubuntu + 61/61 Windows HIGH_ASSURANCE**), Desktop Shell #99 (**26/26 frontend + 13/13 Rust + locked checks/audits + Windows release build/smoke**) and HEDS `5216871217` with unresolved HIGH/CRITICAL `0`.

## Residuals
Packaging/signing/attestation of the sidecar, a packaged live sidecar E2E, restart/health supervision, release process containment, provider reachability/authentication, VERIFIED capability, privileged mutations and installer/updater remain outside this candidate.

## Promotion condition
This delta does not itself approve CP-0020. Candidate status requires documentation/evidence-only promotion gates and HEDS. Canonical status requires final gates, squash product merge, product post-merge validation and documentation-only canonical closeout with its own gates/HEDS/push validation.