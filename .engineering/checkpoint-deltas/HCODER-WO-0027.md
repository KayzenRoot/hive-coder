# Conditional Checkpoint Delta — HCODER-WO-0027 / HCODER-CP-0027

**State on this proposed documentation revision:** CONDITIONAL / NOT YET EFFECTIVE.  
**Decision to promote if effective:** `DEC-031` — bounded governed Tauri updater admission bridge.  
**Predecessor:** `HCODER-CP-0026` / `DEC-030` SEALED; all existing checkpoint law and evidence preserved.  
**Issue:** #89; **product PR:** #93 MERGED; **separate promotion PR:** to be recorded externally.  
**Governance:** accepted DEC-032 (no separately installed HIVE) and DEC-033 (KayzenRoot owner-account review, explicitly NOT INDEPENDENT).  
**Risk:** HIGH_ASSURANCE, narrowly scoped to fail-closed no-production-trust bridge.

## Conditional effectiveness: `HCODER_CP_0027_EFFECTIVE`

`HCODER_CP_0027_EFFECTIVE` is true if and only if all these conditions hold for **one and the same exact promotion candidate revision**:

A. That candidate is reviewed at its exact Git SHA as a substantive source/scope/security HEDS-style `OWNER_SELF_AUDIT / NOT_INDEPENDENT` under DEC-033. The owner-account review must record a separate implementation-independent challenge activity, explicit high-assurance *bounded inert-slice* risk acceptance, zero unresolved CRITICAL/HIGH, no unresolved source/evidence/preservation conflict, the original merged product source identity and the upstream Issue #97 residual Linux dependency risk. A paid review bot or a second human account is NOT necessary and may not be fabricated.

B. All thirteen applicable required GitHub check contexts across Governance, Desktop Shell, Native Package Matrix and Protected Release succeed on that **exact promotion head**. All blocking review threads are resolved, the actual branch ruleset is satisfied, and GitHub performs a protected `squash` merge with expected candidate HEAD preserving the reviewed candidate's Git tree exactly.

C. **After that merge**, the resulting exact `main` SHA passes fresh Governance, Desktop Shell, Native Package Matrix and Protected Release runs, with all thirteen required contexts SUCCESS; the fresh runs must use the new merge SHA, not a PR head, previous product head or predecessor main.

This predicate uses source and proof properties rather than hard-coding a candidate SHA, external review comment, mutable issue/PR state, run ID or moving current-main value. Exact promotion lifecycle evidence is recorded externally in the promotion PR, Issue #89 and current checkpoint Issue #30. This declaration is not self-approval and never becomes true from its own text.

**Selection law:** if `HCODER_CP_0027_EFFECTIVE` then `HCODER-CP-0027` and `DEC-031` are canonical; otherwise `HCODER-CP-0026` and `DEC-030` remain authoritative, subject to their already proven predecessor predicate. The historical CP-0026 effectiveness law and independent past audit remain immutable. The newly accepted owner-only policy is prospective.

## What CP-0027 would admit, and nothing more

The exact HCODER-DIST-001D product tree from protected product PR #93, source-verified against prior main and fresh postproduct checks, gains canonical standing only as:
- One Rust-only `tauri-plugin-updater =2.12.0` check/download admission boundary behind three named, main-window-bound, argument-free Tauri commands (read status, check fixed trusted config, download+verify only); no JS plugin or updater capability.
- An explicit strict seven-key trusted `plugins.updater` configuration with `requireSignedVersion:true`, `allowDowngrades:false`, all dangerous transport flags false, **no public key and zero endpoints** in the shipped build. Missing trust refuses before any network, never masquerades as configured.
- DEC-028 same-channel/strictly-newer/platform-matching admission combined with the official updater's signature and signed-version verification. A single trusted Rust in-memory candidate owns the handle and retained verified payload bytes, bound to its immutable metadata/artifact hashes. No arbitrary file staging, frontend-controlled trust or candidate substitution.
- Closed bounded error/status/proof vocabulary and regressions for trust refusal, stale-check recovery, concurrency and verified-byte custody; TypeScript proof is presentation evidence, not authorization.
- Exact-head CI and strong negative/security evidence for this **inert** boundary only.

## What remains withheld / deferred

No signing key, nonempty production public key, HTTPS release endpoint, real signed download, updater artifact generation, installer execution, user install/restart permission, rollback, real N-to-N+1 update, tag/release publication, macOS notarization or Windows signing. These remain unapproved later slices requiring their own source/trust/security gates; the six credential-bearing Protected Release jobs are SKIPPED, never PASS. `bundle.active:false` and the desktop read-only/zero-guest capability persist. The pre-existing Rust `glib 0.18.5` advisory/Dependabot update incompatibility is tracked at Issue #97, requires separate risk/reachability/remediation before a clean production Linux distribution claim and is not erased by this checkpoint.

## Evidence and recovery

The product PR was owner-audited (NOT INDEPENDENT) at exact `281b719ab715eb94eeb9e193580c09adadced882`, protected-squash-merged as `c25103bdfdfb74e12891fcdc13b0495d3fcf786d`, with both Git trees exactly `39b8f665a4e46341d10b378fb13f867a1a0ae209`. All four fresh exact-product-main runs were green (Governance `36579684792`, Desktop Shell `36579684754`, Native Package Matrix `36579684765`, Protected Release `36579684818`), thirteen required statuses SUCCESS. These are *product-stage* receipts and cannot satisfy this promotion's later C predicate.

A documentation-only rollback before promotion is to close its PR without altering main; after promotion, reverse only via a separately governed successor change. Never force-push or silently retract historical proof.

## STOP

No effective/canonical declaration until A, B and C are objectively proven. STOP on source drift, changed product bytes, unresolved HIGH/CRITICAL, unsafe trust/installer privilege, red required checks, open blocking threads, a failed protected merge or false independent review claim. Do not continue to the next product capability increment until the applicable current-stage closeout is proven.
