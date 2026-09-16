# HCODER-WO-0021 — Checkpoint Delta

**Source checkpoint:** `HCODER-CP-0020` — APPROVED / CANONICAL  
**Target candidate:** `HCODER-CP-0021` — CANDIDATE / NOT CANONICAL  
**Technical head:** `12d86579335c8f553bf77457739a6f2a7d287f10`  
**Technical HEDS:** `5217411336` — APPROVED FOR PROMOTION CANDIDATE

## Product delta
CP-0021 candidate adds the first privileged Hive-owned workspace file mutation adapter behind the canonical Permission & Control Plane. Authority is deliberately restricted to atomic creation of a previously absent regular file inside the trusted workspace.

Governed path:

`Trusted host/orchestrator -> Permission & Control Plane -> request-bound single-use FILESYSTEM_WRITE permit -> WorkspaceFileCapability(create-only/no-clobber) -> OS handle/no-follow/no-clobber primitive -> new workspace file`

## Preserved laws
- Permission & Control Plane remains the sole authorization choke point;
- `FILESYSTEM_WRITE` remains HIGH and mandatory-approval gated;
- model/tool/task text cannot approve or mint permits;
- existing-file overwrite/edit/append/truncate/delete/rename-existing remains unavailable;
- Git mutation and `.git` internals remain outside this authority;
- no generic shell/process, Tauri/desktop write, provider/model execution, Cua/computer-use mutation, remote control, skill activation or billing/purchase authority is introduced;
- raw file content is not persisted in approval/audit metadata.

## HIGH_ASSURANCE invariants
- exact workspace, normalized target, parent identity, target absence, content SHA-256 and byte length are request-bound;
- workspace/parent/target/session state is revalidated before mutation;
- permit is consumed immediately before first mutation;
- traversed parents are no-follow/reparse-resistant;
- publication is atomic no-clobber on POSIX and Windows;
- concurrently appearing targets are preserved and cause fail-closed behavior;
- portable path contract rejects traversal/absolute/drive/UNC/device, `.git`, control/format/bidi and Windows-forbidden/reserved forms;
- payload ceiling is 1 MiB.

## Corrections closed in candidate
- Windows publication was corrected from incompatible `SetFileInformationByHandle` root-relative use to native NT handle-relative no-clobber rename without weakening the security contract.
- Real Windows junction/reparse and publication-race coverage was added.
- `.git` and approval-confusing Unicode/control path forms were closed after independent diff audit.

## Evidence
Exact technical head passed Governance #278 (**317 Ubuntu PASS + 89 Windows HIGH_ASSURANCE PASS**) and Desktop Shell #114 (web + Windows jobs fully green), then HEDS `5217411336` approved promotion with unresolved HIGH/CRITICAL `0`.

## Residuals
Existing-file compare-and-swap editing/replacement, Git mutation, desktop exposure of write authority and all broader privileged surfaces remain future separately governed increments. Existing desktop release-hardening/dependency residuals remain unchanged.

## Promotion condition
This delta does not itself approve CP-0021. Candidate status requires documentation/evidence-only promotion gates and HEDS. Canonical status requires final gates, squash product merge, product post-merge validation and documentation-only canonical closeout with its own gates/HEDS/push validation.