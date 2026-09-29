# HCODER-CP-0027 — Promotion Evidence Bundle (proposal)

**Status:** PREPARED / source proof recorded / proposed conditional promotion, not a canonical checkpoint.  
**Source main:** `c25103bdfdfb74e12891fcdc13b0495d3fcf786d`  
**Product reviewed HEAD:** `281b719ab715eb94eeb9e193580c09adadced882`  
**Reviewed product tree = squash product merge tree:** `39b8f665a4e46341d10b378fb13f867a1a0ae209`  
**Source Work Order:** HCODER-WO-0027 / Issue #89 / PR #93, now MERGED and PRODUCT POSTVALIDATED.  
**Proposed conditional declaration:** `.engineering/checkpoint-deltas/HCODER-WO-0027.md`.  
**Proposed promotion PR:** link exact PR/head/review/checks in GitHub after this file's last commit, not self-referentially inside this immutable candidate.

## Source truth / unchanged product

The newest accepted main is the protected squash merge of existing updater PR #93. A recursive Git tree comparison proved that the reviewed branch and product merge both have tree `39b8f665a4e46341d10b378fb13f867a1a0ae209`. The previous standalone-development/owner-only governance main was `5b0948d92701c2721ee8a9dc67d5c73c04d287d2`. The product PR contains 14 admitted updater-specific tracked paths and no independent local HIVE dependency, production trust/endpoint, installer/signing permission or workflow edit. This promotion PR must change documentation/governance only; use direct Git blob/tree matching before authorizing any merge.

**Exact main technical source:** `apps/desktop/src-tauri/src/update_admission.rs` blob `234e40fdd5d805e30d44f824a3cea416d348b7c9`; `apps/desktop/src-tauri/src/lib.rs` blob `9252527bf5555278de91206ce54fe6d678e0b76c`; `apps/desktop/src/contracts/updateState.ts` blob `2b208f62ec920ce163c770da057ce9c4bd32cdfe`; `apps/desktop/src/lib/updateService.ts` blob `4b1bb5daf5a9d70925e8bb697e38f4d80563130a`; `apps/desktop/src-tauri/tauri.conf.json` blob `3cc63516a5065bcc115e3274a66eed74f15f0cab`; `tools/desktop/security_gate.py` is frozen along with Cargo/npm manifests and workflow YAML. The complete security map remains `.engineering/prebuilt/HCODER-WO-0027-ACCEPTANCE-SECURITY-MAP.md` and the candid staged evidence `.engineering/evidence/HCODER-WO-0027.md`. Preserve historical `PROVEN_LOCALLY` labels only at their recorded older heads; do not transfer those local labels to the newest merge without evidence.

## Product accepted evidence (not promotion evidence)

- Exact product HEAD `281b719...`, HIGH_ASSURANCE exact-head owner-account HEDS-style semantic/security audit, explicitly NOT INDEPENDENT; no known unresolved CRITICAL/HIGH, no PR blocking thread; 13/13 exact-head protected CI contexts SUCCESS on four workflows.
- Guarded expected-head squash PR #93 -> `main c25103...`, product tree exactly preserved.
- Fresh postproduct exact-main Governance `36579684792`, Desktop Shell `36579684754`, Native Package Matrix `36579684765`, Protected Release `36579684818` all SUCCESS. 13 required statuses passed. Linux/macOS Rust 49/49; Windows Rust 47/47; TS/Vitest 130/130; Windows launch smoke and desktop/security/version checks green.
- Six signer/attest/notarize/publish steps SKIPPED, no real key/endpoint, no signed download, installer, rollback, publication or live update; no fabricated independent-human signoff.

## Accepted owner-only and standalone context

Merged HCODER-OPS-0001 PR #96, accepted prospective DEC-032/DEC-033; no separate installed HIVE service or collaborator is an executor/review preflight. The HEDS review **activity** and high-assurance risk decision remain mandatory, even if both are performed under `KayzenRoot` and labeled OWNER_SELF_AUDIT / NOT_INDEPENDENT.

## Known security residual

The optional Dependabot security update `36579704036` FAILED: `glib 0.18.5` requires patched `>=0.20.0`, but is pinned through preexisting `gtk 0.18.2` / `webkit2gtk 2.0.2` / `tauri 2.11.5` Linux graph. The same glib version exists at base `a9b48b...` (before updater), so is not a regression of the new updater code. Runtime reachability UNKNOWN. The separate remediation and production Linux distribution restriction are Issue #97. Do not force unsound graph mixing, suppress this advisory, or claim a production-distributable Linux package.

## Exact promotion evidence slots (required before effectiveness)

Populate **externally** on the promotion PR/Issue after the final promotion docs HEAD exists:
- exact base/main SHA, reviewed candidate HEAD and reviewed Git tree;
- exact allowed path set + frozen technical file SHA comparison;
- owner-account separate semantic challenge/risk record `OWNER_SELF_AUDIT / NOT_INDEPENDENT`; zero unresolved HIGH/CRITICAL; verified independent of product implementation activity, no human-independent claim;
- 13 exact-head required CI SUCCESS / four runs with check IDs, optional jobs accurately distinguished and all blocking threads resolved;
- expected-head guarded squash merge and reviewed promotion tree = resulting main tree;
- fresh four workflow SUCCESS receipts launched on resulting exact promotion-main SHA, with thirteen required contexts, not product-stage reused receipts.

**Checkpoint Delta:** NONE until the effectiveness predicate is proven. **STOP:** do not claim CP0027 or DEC031 canonical merely because this proposal lands in a PR, or because prior product-stage checks passed.
