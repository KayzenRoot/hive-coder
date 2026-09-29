# HCODER-SEC-0001 — Bounded source/context lock

**Stage:** ANALYSIS-ONLY PREBUILD / PROPOSED; **Issue:** #97.
**Branch:** `security/HCODER-SEC-0001-glib-reachability-prebuild`.
**Source base:** `main 4ee0894ad79bd869b1ed4668ea33e151f0ef18ff`.
**Source checkpoint:** CP-0027 / DEC-031 EFFECTIVE by PR #98 stage A+B+C, with historically canonical CP-0026/DEC-030 retained; evidence in Issues #30/#89, PR #98.
**Scope:** three exact prebuild documentation files; no runtime/manifest/workflow/security code changes.
**External HIVE:** NOT REQUIRED; all source lives in Git, GitHub and internal repos.
**Reviewer:** owner-only KayzenRoot, always `OWNER_SELF_AUDIT / NOT_INDEPENDENT` with objective CI.

## Locked base Git blobs
- `apps/desktop/src-tauri/Cargo.lock`: `517f181e3c0e1e281e12e270ae2b5e23922c5f35`.
- `apps/desktop/src-tauri/Cargo.toml`: `2ab3c506dff4ff9c546a523941536678632fb2f9`.
- `docs/project-brain/11-CHECKPOINT.md`: `1f7f8323ae08687ab727fdbb84ae9849c3b889d1`.
- `docs/project-brain/05-SECURITY.md`: `1cede4091b2f27523eccca4e3febe1eb3c1bc248`.
- `docs/project-brain/08-BACKLOG.md`: `6577b7636a6b6440d4c8aeb4fc99217204300f3b`.
- `docs/project-brain/09-DEFINITION-OF-DONE.md`: `ab4f81b4c1fdc70b0ab4c69e2026f14bd46e11d1`.
- `docs/project-brain/10-DECISIONS-LEDGER.md`: `399dd2278ec9439a2d2ace466bd6b61cd91a76b2`.
- `apps/desktop/src-tauri/tauri.conf.json`: `3cc63516a5065bcc115e3274a66eed74f15f0cab`.
- `apps/desktop/src-tauri/src/update_admission.rs`: `234e40fdd5d805e30d44f824a3cea416d348b7c9`.

## Observed risk and unknowns
Git lock graph includes `glib=0.18.5`, `gtk=0.18.2`, `webkit2gtk=2.0.2`, `tauri=2.11.5`. RustSec RUSTSEC-2024-0429 fixed in glib>=0.20.0. Optional Dependabot patch run 36579704036 reported `security_update_not_possible`. First-party/transitive GTK `VariantStrIter` call reachability is UNKNOWN. Hosted CI for the merged inert updater, including Rust and package builds, has passed, but this does NOT prove that the vulnerable iterator is unreachable or that Linux release security is clean.

## Frozen/security boundaries
Entire product tree, manifests/lock, source/checkpoint historical receipts, approved trust, protected CI configuration and security gates. No production distribution, external HIVE preflight or collaborator approval. Owners may inspect; no code/lock modifications without an accepted scoped correction and compatible supported remediation. Treat alternate Tauri/GTK branches as unverified until objectively probed, never as already compatible.

## STALE / RECOMPILE
If actual `main`, advisory/upstream fix, dependency graph, ruleset, package semantics or accepted CP changes materially, refresh the fingerprints and re-evaluate the bounded Work Order before any edit. Only current proof on exact HEAD carries. The issue remains OPEN until the actual security risk is remediated or a separately governed bounded disposition is proven. GitHub automation or signed artifact credentials must never be enabled to make this prebuild pass.

## Context Lock Delta 001 — PR-only diagnostic evidence (accepted main 93f0cc3)

**Source refresh:** analysis-only prebuild PR #99 reviewed at `2f682855ab003757f6220e8d822bd670bf5dd46d`, protected-squash-merged to exact `main 93f0cc314699788e7e405d46de62f8d8bab3c759` with matching tree `f083a587fa5964b5437100eb9af5a81c2070c1db`, then exact-main 13 required contexts SUCCESS: Governance `36584730342`, Desktop Shell `36584730312`, Native Package Matrix `36584730464`, Protected Release `36584730326`. Six release credential stages SKIPPED. CP-0027 remains canonical; issue #97's actual security risk remains OPEN.

**Temporary diagnostic-only allowed paths:** this locked Context Lock (append only), the Work Order (append only), evidence `.engineering/evidence/HCODER-SEC-0001-PREBUILD.md` (append only), and NEW PR-only `.github/workflows/hcoder-glib-diagnostic.yml`. No other files. The workflow must NOT be merged to main and must never change existing workflows or turn a diagnostic observation into approval to ship Linux. No collaborator, external HIVE, production signing credentials, release permissions or local Docker used. Review source against actual default branch again before running.

**STOP:** if current `main` or product Cargo.lock blob changes, a new workflow requires privileged permissions to run, the diagnostic cannot execute in PR without admin actions, or actual Linux tree contradicts the static lock graph, STOP and document the discrepancy. Source snapshots, signed/trust updater and all runtime code remain frozen. Audit this diagnostic PR as owner SELF_AUDIT / NOT_INDEPENDENT; no extra GitHub reviewer is needed.
