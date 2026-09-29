# HCODER-WO-0027 — Promotion Context Lock

**State:** PROPOSED; `HCODER-CP-0026` remains canonical until formal CP-0027 effectiveness.  
**Branch:** `docs/HCODER-WO-0027-cp0027-promotion`  
**Exact source base:** `c25103bdfdfb74e12891fcdc13b0495d3fcf786d`  
**Accepted product merge tree:** `39b8f665a4e46341d10b378fb13f867a1a0ae209` (same as independently rechecked owner-reviewed PR #93 tree).  
**Related sources:** WO-0027, its accepted Context Lock Delta 001-004, DEC-028/030, DEC-032/033 accepted 2026-09-29 via PR #96, Issue #89, Issue #97.

## Exact base Git blob fingerprints
- `AGENTS.md`: `90015dcb61422094e4df22d884489f7f275da6f3`
- `README.md`: `9df3ff3c158642e2c505bf50ade87e2671601178`
- `docs/project-brain/08-BACKLOG.md`: `973222819447822d52efb3ef7d5e81480fb940fa`
- `docs/project-brain/10-DECISIONS-LEDGER.md`: `212357e40f6e6836bcfa1ea7ced91fb648420c5a`
- `docs/project-brain/11-CHECKPOINT.md`: `df0ead8e90a46320b8e02bc8dce4f3e27dd67266`
- `docs/project-brain/adrs/DEC-031-GOVERNED-TAURI-UPDATER-ADMISSION-BRIDGE.md`: `1ac5e2fa599c50fc04b058008e6aaef6fb286a40`
- `docs/project-brain/adrs/DEC-032-STANDALONE-NO-EXTERNAL-HIVE.md`: `d7d86aa43b945669820f9057b62696b1dc60de82`
- `docs/project-brain/adrs/DEC-033-OWNER-ONLY-GOVERNANCE.md`: `8a2d4107ce802e4e08a3bf0422977efc91237d3f`
- `.engineering/context-locks/HCODER-WO-0027.md`: `f62e0894ee9d92609de4de88ed1d1f7f8bb504c9`
- `.engineering/evidence/HCODER-WO-0027.md`: `961664462daeb9ea7f8c885f11910ab22b2cd44c`

## Frozen product/CI and truth
Freeze exactly all tracked paths **except** the docs-only allowed file set in `.engineering/work-orders/HCODER-WO-0027-PROMOTION.md`. Approved/merged product tree is the only technical source; promotion is documentation-only and must not change any product byte. Preserve the existing CP-0026 historical independent-review predicate verbatim. No code paths or new release capabilities. The owner audit for the promotion candidate is **NOT INDEPENDENT**, under now-accepted prospective DEC-033; the owner must separately challenge source/security/evidence against current actual Git and tests, disclose all unavailable/live tests, retain Issue #97 as nontrivial Linux distribution risk. Stale historical “HIVE local preflight” and mandatory second-account wording is prospectively superseded by accepted DEC-032/033, not silently deleted from old records.

## Current verified objective receipts
Post-product-merge exact-main `c25103...`:
- Governance `36579684792` SUCCESS
- Desktop Shell `36579684754` SUCCESS
- Native Package Matrix `36579684765` SUCCESS
- Protected Release `36579684818` SUCCESS
- Required 13/13 checks SUCCESS; six protected credential stages SKIPPED.
- Optional Dependabot `36579704036` FAILURE: pre-existing `glib 0.18.5` and patched `>=0.20.0` incompatible with current GTK3 graph, Issue #97. No claim of clean production Linux release.

## STALE and promotion gate
If base `main`, approved source fingerprints, product tree or guarded GitHub ruleset change, stop and reconcile this lock before any edit. Candidate exact-head source, 13 required checks, no blocking threads and owner risk/audit comment are required before squash merge. Only fresh exact-main postpromotion workflows and tree preservation activate CP-0027; never predeclare canonical or confuse product postmerge checks with promotion postmerge checks.
