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


## Correction Delta 002 Context Lock — authenticated-backport candidate research, 2026-09-29

**No retroactive change to the initial prebuild or temporary diagnostic Delta 001.** This append-only Delta is documentation research, not product implementation. Same HCODER-SEC-0001 / Issue #97. Branch: `security/HCODER-SEC-0001-debian-backport-provenance`; immutable source `main 93f0cc314699788e7e405d46de62f8d8bab3c759` (postvalidated prebuild PR #99). CP-0027/DEC-031 effective, DEC-032/033 owner-only/no external HIVE effective. Temporary diagnostic PR #100 remains CLOSED/UNMERGED; its exact successful Linux runner run `36585888151` belongs to its candidate HEAD and is contextual evidence only, not this branch's CI.

**Critical immutable source Git blob SHA:**
- `apps/desktop/src-tauri/Cargo.lock`: `517f181e3c0e1e281e12e270ae2b5e23922c5f35`.
- `apps/desktop/src-tauri/Cargo.toml`: `2ab3c506dff4ff9c546a523941536678632fb2f9`.
- `docs/project-brain/11-CHECKPOINT.md`: `1f7f8323ae08687ab727fdbb84ae9849c3b889d1`.
- `docs/project-brain/10-DECISIONS-LEDGER.md`: `399dd2278ec9439a2d2ace466bd6b61cd91a76b2`.
- `docs/project-brain/03-SCOPE.md`: `5413f15135fc19ddebf9aa86e4be722cd9aa83df`.
- `docs/project-brain/09-DEFINITION-OF-DONE.md`: `ab4f81b4c1fdc70b0ab4c69e2026f14bd46e11d1`.
- `docs/project-brain/04-ARCHITECTURE.md`: `10ac18d2d187e8f13ca2a4071499a667fe13cc35`.
- `docs/project-brain/05-SECURITY.md`: `1cede4091b2f27523eccca4e3febe1eb3c1bc248`.

**Exact allowed tracked paths** on THIS draft candidate:
1. `.engineering/work-orders/HCODER-SEC-0001.md` — append Correction Delta 002.
2. `.engineering/context-locks/HCODER-SEC-0001.md` — append this lock.
3. `.engineering/evidence/HCODER-SEC-0001-PREBUILD.md` — append new externally sourced research, explicitly unexecuted.

All other tracked files are FROZEN. No source archive download/execution, `[patch.crates-io]`, glib vendoring, Cargo update, CI workflow, GTK transition, unconfigured trust or credential/provisioning mutation is permitted by this DOCS-ONLY Delta. Public upstream Debian metadata and upstream gtk-rs patch are research inputs, not approvals. Require a second separately bounded executable correction amendment before any local Cargo/security branch.

**STALE predicate:** compare actual `main` SHA and critical fingerprints before review/merge; if they drift, STOP and recompile. Never reuse exact-head protected CI, owner audit or postmerge evidence from prior candidate or PR #100 as this PR's proof. Linux production distribution remains blocked; real `VariantStrIter` transitive reachability remains UNKNOWN; six credential-bearing protected-release lanes remain SKIPPED. No new canonical checkpoint.


## Correction Delta 003 Context Lock — temporary Debian provenance runner (2026-09-29)

**Accepted predecessor proof:** existing HCODER-SEC-0001 Delta 002 PR #101 candidate `cc9663986e8e6ad194667389aaa9bbf0b84fd6e3` merged as `main f4f000ec03c3fd96f73b1c6370c57c286557cee5` with equal reviewed/merge tree `1b5b383b5e501ac56ae534e8b315de800c6c2314`; all four FRESH PUSH workflows SUCCESS on exactly that main, 13/13 required jobs SUCCESS, six credential jobs SKIPPED. CP-0027/DEC-031 canonical, no successor checkpoint. Same HCODER-SEC-0001 Issue #97 OPEN.

**New isolated branch/base:** `security/HCODER-SEC-0001-patch-provenance-diagnostic`, parent exact `f4f000ec03c3fd96f73b1c6370c57c286557cee5`. The original static product fingerprints retained unchanged by docs-only PR #101:
- `apps/desktop/src-tauri/Cargo.lock` `517f181e3c0e1e281e12e270ae2b5e23922c5f35`;
- `apps/desktop/src-tauri/Cargo.toml` `2ab3c506dff4ff9c546a523941536678632fb2f9`;
- `docs/project-brain/11-CHECKPOINT.md` `1f7f8323ae08687ab727fdbb84ae9849c3b889d1`;
- `docs/project-brain/10-DECISIONS-LEDGER.md` `399dd2278ec9439a2d2ace466bd6b61cd91a76b2`;
- `docs/project-brain/03-SCOPE.md` `5413f15135fc19ddebf9aa86e4be722cd9aa83df`;
- `docs/project-brain/09-DEFINITION-OF-DONE.md` `ab4f81b4c1fdc70b0ab4c69e2026f14bd46e11d1`;
- `docs/project-brain/04-ARCHITECTURE.md` `10ac18d2d187e8f13ca2a4071499a667fe13cc35`;
- `docs/project-brain/05-SECURITY.md` `1cede4091b2f27523eccca4e3febe1eb3c1bc248`.
**Delta 002 doc fingerprints at new base**: WO `298acad6fbefd50731e02c0d890e883900515d7b`, Context Lock `3746641337e6ebc2b812ab43c94f112f68bd2846`, Evidence `faa212ccda55baf3044984aa178f7602b1b604a6`.

**One-off mutation allowlist, all four exact paths only:**
1. append `.engineering/work-orders/HCODER-SEC-0001.md`,
2. append `.engineering/context-locks/HCODER-SEC-0001.md`,
3. append `.engineering/evidence/HCODER-SEC-0001-PREBUILD.md`,
4. new `.github/workflows/hcoder-glib-provenance-diagnostic.yml` (PR-only read-only, not to be merged).

**External provenance anchors (not yet independently signature-verified here):** Debian 2026-08-13 signed upload metadata https://www.mail-archive.com/debian-bugs-closed@lists.debian.org/msg848790.html lists `rust-glib-0.18_0.18.5-7.dsc` SHA256 `a5079dd1f0cdcdb82b512feab81fe9afab6d79918fe70523015224afa8de0221` size 3181 and `rust-glib-0.18_0.18.5-7.debian.tar.xz` SHA256 `9895cf4df3525224ee825477dc76c730566591528b9af9fc05c310706b61db5b` size 27712. Require a trusted verified .dsc for original tar SHA and signer identity. Original upstream gtk-rs exact verified commit: `b5a4071e439bef2b5eea76c3aa25e5ae84839e34`.

**Frozen/STOP:** Whole product tree and pinned Cargo graph, all protected CI and release workflows, trust settings, permissions, signing, updater, GitHub branch rules, OS packages on user PC, external HIVE. No production dependency mutation or release. This diagnostic PR must stay unmerged, collected evidence goes only to Issue #97. Source/branch drift, archive checksum or signature failure and unforeseen patch changes force STOP and honest UNPROVEN. No successor product Work Order before actual security disposition.
