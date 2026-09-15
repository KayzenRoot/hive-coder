# HCODER-WO-0016 — Trusted Workspace & Git Read Surface

**Status:** COMPLETE / CANONICAL  
**Issue:** #34 — CLOSED / COMPLETED  
**Product PR:** #35 — SQUASH MERGED  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C4  
**Canonical checkpoint:** `HCODER-CP-0016`  
**Canonical product merge SHA:** `6483ed36393b02f45e286590e75bc9fb36d48727`  
**Final HEDS review:** `5214385916`

## OBJECTIVE
Turn the CP-0015 static Workspace shell into Hive Coder's first truthful live project surface: explicit user-mediated workspace selection plus bounded read-only workspace, Git and Hive evidence observations, while preserving all existing permission/control-plane boundaries and introducing no terminal execution, filesystem mutation, generic process execution or desktop-input authority.

## COMPLETION SUMMARY
The objective is complete and canonical under `HCODER-CP-0016`.

Delivered:
- named native `choose_workspace` with no frontend/model path payload;
- trusted Rust-side root validation/canonicalization and application-owned workspace identity;
- bounded read-only workspace metadata and project markers;
- direct bounded `.git` metadata observation for repository/branch/detached HEAD/HEAD identity without executing Git;
- bounded Hive checkpoint/evidence discovery;
- `DesktopSnapshot v2` with provenance and truthful READY/UNKNOWN/DISCONNECTED/DEGRADED states;
- Workspace/System Truth presentation updates with mutation controls still unavailable;
- hardened desktop security gate for no-write/no-generic-process/no-authority-expansion guarantees;
- exact dependency locking and Windows-native build/launch evidence.

## AUTHORITY BOUNDARY
No filesystem mutation, generic child process/shell, provider/model execution, credential path, Python-runtime spawn, Cua/computer-input mutation, remote control, automatic skill activation, billing/purchase authority or Permission & Control Plane expansion is part of CP-0016.

## CORRECTIONS
- `HCODER-WO-0016-CR-001` HIGH — RESOLVED: root containment/no-follow, dangling links, evidence link escape, malformed empty branch references.
- `HCODER-WO-0016-CR-002` MEDIUM — RESOLVED: physical byte-ceiling enforcement before UTF-8 decode.

## FINAL EXACT-HEAD EVIDENCE
Product head `f979d4776cf1eacff9e44dc4a8a5cacca2370fec`:
- Governance `35008893606` (#214): SUCCESS.
- Desktop Shell `35008894044` (#50): SUCCESS.
- HEDS `5214385916`: APPROVED FOR SQUASH MERGE; unresolved HIGH/CRITICAL 0.

## MERGE / POST-MERGE EVIDENCE
- Squash merge SHA `6483ed36393b02f45e286590e75bc9fb36d48727`, GitHub-signed.
- Governance `35009304333` (#215) on merge SHA: SUCCESS.
- Desktop Shell `35009304230` (#51) on merge SHA: SUCCESS, including Windows release build + `DESKTOP_LAUNCH_SMOKE=PASS`.

## RESIDUALS
- Native picker/full interaction E2E and direct Windows reparse fixture remain future work.
- Stronger handle-relative/no-follow capability I/O is required before privileged workspace/file mutation.
- Seven warning-class RustSec advisories remain tracked dependency debt.
- Linked worktree external gitdir remains intentionally DEGRADED.
- Live runtime/provider/permission integration and all mutation/execution surfaces remain separate governed increments.
- Packaging/signing/updater, full visual/accessibility E2E and final project-license decision remain open.

## STOP CONDITION
**SATISFIED.** Exact-head pre-merge Governance/Desktop + HEDS passed, PR #35 squash-merged, post-merge Governance/Desktop passed on canonical product SHA, and canonical closeout records CP-0016 truthfully.
