# Evidence Bundle — HCODER-WO-0024

**Status:** IMPLEMENTED / SECOND CORRECTION REVIEW PENDING — NO PROMOTION CLAIM  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Issue:** `#77`  
**Parent epic:** `#72`  
**PR:** `#80` (Draft, unmerged)  
**Reviewed prebuild head:** `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`  
**Reviewed first-correction head:** `97c533de73c9d8f007b6dfc4eaf73804fb1de220`  
**Independent reviews:** `5236275753` — CORRECTION_REQUIRED, CRITICAL `0` / HIGH `4` / MEDIUM `2`; `5236688350` — CORRECTION_REQUIRED, CRITICAL `0` / HIGH `2` / MEDIUM `1`  
**Correction authority:** Context Lock Delta `001` and Delta `002`

## Correction state 2 (why the first-correction claims were also withdrawn)

The first correction head `97c533de73c9d8f007b6dfc4eaf73804fb1de220` passed Governance `35229265839` and Desktop Shell `35229265814`, and independent review `5236688350` accepted the Prompt-21 corrections while returning three further findings. The following claims were therefore **false at that head** and are withdrawn:

- "the install path is unreachable and cannot be asserted" — `evaluateStatus()` still accepted a direct `state:"success"` snapshot while `success` is reachable only through the proof-gated path, and recorded history could report a proof-gated transition as successful without carrying any gate evidence (`H-21-01`).
- "one canonical version law" — the product TypeScript parser rejected core identifiers above `Number.MAX_SAFE_INTEGER` that the Python gate accepted, and the Python gate accepted a trailing newline that TypeScript rejects (`H-21-02`). A third divergence, Python's `\d` matching Unicode decimal digits, was found while correcting it.
- "exact-object validation is closed" — `asRecord()` accepted any non-array object and key checks inspected only `Object.keys()`, so required fields could be inherited or getter-backed and validation could execute accessors (`M-21-03`).

Corrections are carried in the same Work Order. As with the first round, green gates on the reviewed head did not mean the properties held.

## Correction state 1 (review `5236275753`)

The prebuild head `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d` passed Governance `35224933911` and Desktop Shell `35224933743` yet carried four HIGH and two MEDIUM findings: the authenticity gate sat on `ready -> installing` while `verifying -> ready` was ungated and a direct `ready`/`installing` status was accepted (`H-20-01`); version and channel were validated independently so `0.1.0` + `beta` was accepted (`H-20-02`); status snapshots were neither closed nor reconstructed (`H-20-03`); numeric prerelease precedence used floating-point conversion (`H-20-04`); the channel contract carried a second, looser parser (`M-20-05`); and `DEC-028` was referenced without existing (`M-20-06`). All six were corrected under Context Lock Delta 001.

## Claims allowed now
- A canonical product-version source of truth is **declared**: `apps/desktop/src-tauri/tauri.conf.json` → `version`, with `Cargo.toml` and `package.json` as exact mirrors.
- A deterministic, offline drift verifier exists (`tools/desktop/version_drift.py`) and reports `LOCKED` against the live manifests at the base.
- Version parsing, the release-channel contract, the update-state model, the authenticity gate and the bounded redaction-safe error metadata are implemented as pure contract law, with the reviewed defects of both rounds corrected in source.
- The product parser and the Python drift gate share one bounded SemVer 2.0.0 acceptance set, pinned by a deterministic cross-language vector file.
- A Hive-owned `UpdateService` boundary exists whose production implementation is inert and exposes no mutating, transport or installation member.
- A bounded, read-only Settings/About read model exists.
- Contract tests, including the required negative proofs and the adversarial regression cases for all nine recorded findings, exist in source.

## Claims explicitly NOT allowed
- That Hive Coder is installable, signed, notarized, auto-updatable or production-distributable.
- That any update, download, install, restart or release path exists or is authorised.
- That cryptographic verification is implemented. **No scheme is admitted**, so the whole install path is structurally unreachable.
- That `DEC-028` is canonical. It is PROPOSED / NOT CANONICAL.
- That any platform's native distribution behaviour is proven. Only the contract lane is exercised.
- That the corrected contracts are *proven*: the corrected head has not yet been gated or independently reviewed.

## Base-state facts to re-verify
Re-read live files from the exact base before relying on these; repository source wins:
- `tauri.conf.json`: `productName="Hive Coder"`, `version="0.1.0"`, `bundle.active=false`.
- `Cargo.toml`: package version `0.1.0`, Tauri `=2.11.5`.
- `package.json`: version `0.1.0`, `@tauri-apps/api` `2.11.1`, `@tauri-apps/cli` `2.11.4`.

## Acceptance state at the reviewed first-correction head
- Version/channel/update-state/about contracts: MATERIALISED, with three findings open.
- Version drift verifier: MATERIALISED, reports `LOCKED` at base.
- `UpdateService` boundary + inert adapter: MATERIALISED.
- Negative proofs carried from the first round: MATERIALISED.
- Whole-install-path unreachability, cross-language acceptance parity, plain own-data record validation: **NOT PROVEN** at the reviewed head; corrected in source, exact-head proof pending.
- Native Windows/Linux/macOS distribution behaviour: **UNPROVEN**.
- Signing/notarization/release publication: **UNPROVEN** and unauthorised.
- HEDS: NOT YET RUN on any head.

## Promotion evidence template
For each exact technical head record:
- commit SHA;
- workflow/run/job IDs;
- runner OS/version/architecture;
- focused test counts and zero implementation skips;
- version-drift gate result against live manifests;
- cross-language parity result: the shared vector file is accepted by both suites;
- the desktop security gate result under CI conditions (`node_modules` absent, as the gate runs before `npm ci`);
- explicit confirmation that no updater plugin, HTTP client, download, install, restart, signing, release or credential path exists;
- explicit confirmation that `bundle.active` remains `false`;
- HEDS HIGH/CRITICAL counts.

## STOP
`UNKNOWN` never becomes `PASS`. Exact-head evidence proves only the exact SHA it names. Do not merge, do not declare the decision canonical, and do not begin HCODER-DIST-001B from this ledger.

## STOP
`UNKNOWN` never becomes `PASS`. Exact-head evidence proves only the exact SHA it names. Do not merge, do not declare the decision canonical, and do not begin HCODER-DIST-001B from this ledger.
