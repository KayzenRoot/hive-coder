# Checkpoint Delta — HCODER-WO-0018

**Source checkpoint:** `HCODER-CP-0017`  
**Target checkpoint:** `HCODER-CP-0018`  
**Target state in this commit:** `CANDIDATE`  
**Technical head:** `9df7202835a47f2c18af77bbefa665afa5358b38`  
**PR:** `#45`  
**HEDS technical review:** `5215646309`

## Promotion boundary
Promote the first canonical cross-runtime runtime-status IPC contract without promoting a runtime process lifecycle. The delta freezes one bounded one-shot `status.snapshot` wire protocol shared by Python and desktop TypeScript, with deterministic canonical JSON and strict CP-0017 status semantics.

## Candidate effects
- `hive-runtime-status-ipc-v1` becomes the only approved WO-0018 status transport protocol if CP-0018 is finally promoted.
- The only operation is `status.snapshot`; no generic RPC namespace is approved.
- Request ceiling is 512 bytes; snapshot ceiling remains 32,768 bytes; total response envelope ceiling is 33,024 bytes.
- Raw response admission on desktop must pass `decodeRuntimeStatusEnvelope(raw)` before presentation.
- Canonical subsystem provenance, operational states, readiness rules and counter invariants are revalidated across the language boundary.
- The Python server primitive is one-shot and accepts a prebuilt presentation snapshot; it does not own runtime/provider/model/permission/task lifecycle.
- CP-0005 through CP-0017 authority boundaries remain unchanged.

## Evidence basis
Exact technical head `9df7202835a47f2c18af77bbefa665afa5358b38` passed:
- Governance #241: **283/283 Python PASS**, **56/56 Windows HIGH_ASSURANCE PASS**.
- Desktop Shell #77: security gate PASS, TypeScript PASS, **23/23 Vitest PASS**, Vite build PASS, npm vulnerabilities `0`, RustSec scan over 432 locked crates with 7 inherited warning-class advisories, **11/11 Rust PASS**, `cargo check --locked` PASS, Tauri release build PASS and `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS technical review: unresolved HIGH/CRITICAL **0**.

## Correction
`HCODER-WO-0018-CR-001` MEDIUM is resolved. The desktop public response-admission surface is raw-wire-only; semantic parser bypass is removed and Python/TypeScript Unicode canonical-wire parity is explicitly tested.

## Exclusions and residuals
- No runtime subprocess launch/supervision/restart/shutdown lifecycle.
- No Tauri process command or capability expansion.
- No provider/model/network call or credential path.
- No task/permission mutation or authorization semantics.
- No filesystem/Git/terminal/computer-use mutation.
- No remote control, billing/purchases or automatic skill activation.
- Seven RustSec warning-class transitive advisories remain dependency debt.
- Runtime sidecar process identity/authenticity and containment remain future governed work.

## Promotion rule
CP-0018 remains only `CANDIDATE` until this promotion delta itself passes fresh exact-head Governance + Desktop Shell, receives promotion HEDS with unresolved HIGH/CRITICAL = 0, is moved through the final approval mutation, squash-merged, and passes post-merge validation on canonical `main`.
