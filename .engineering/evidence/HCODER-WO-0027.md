# HCODER-WO-0027 — Evidence Bundle

**Status:** IMPLEMENTATION CANDIDATE — RECONCILED ONTO THE DELTA-002 EXACT SOURCE, LOCAL LANES GREEN, PUBLISHED AS A DRAFT PR, NOT MERGED
**Issue:** #89
**Slice:** HCODER-DIST-001D
**Decision:** `DEC-031` — PROPOSED / NOT CANONICAL. Nothing in this bundle promotes it.
**Canonical base at prebuild:** `5d97df6cf2f69a35d14af140e28088a7659eff7a`
**Exact source for this run:** `a9b48bce43fcc2c1a14b70036ed4555f52ba3537` — `origin/main` after `HCODER-WO-0027: correct executor base after CR-001`, verified by `git fetch origin --prune` before any edit, which is the handoff's stop-before-editing condition. It is not triggered, so implementation continues on that source.

> **What this bundle is.** A record of what the repository now contains and of what was proven on one Windows host. No sentence here is evidence that an update endpoint, a signing key pair, a publisher, a certificate or a runner exists. Hosted receipts are not duplicated into this file at all, following the `HCODER-WO-0026` rule that a mutable run identifier inside a frozen document is how a bundle starts lying after its head moves: the four workflow runs and their per-job status are recorded in the Draft PR thread and in Issue `#89`, each bound to the exact head they measured.

## Prebuild facts
- CP-0026 / DEC-030 canonical and sealed.
- PR #88 source-truth reconciliation merged and post-validated before this Work Order began.
- Current UpdateService is inert.
- No updater plugin dependency or JS guest binding exists at prebuild.
- desktop capability permissions are empty.
- bundle.active is false.
- no updater signing key/public production trust configuration is claimed.

## Evidence slots for executor
- **start SHA:** `a9b48bce43fcc2c1a14b70036ed4555f52ba3537` for the reconciled branch. The work itself began one commit earlier, on `e5cfe3267f968d80cc3c4dc91cb6acf54ee7eb80` (Delta-001 `#91` merged); see *Source-truth reconciliation onto Delta-002* for how the earlier head was preserved rather than redone.
- **final SHA:** not asserted here. This bundle is carried by the branch tip, and a SHA written into a frozen document goes stale the moment a commit follows it. The candidate head, the four hosted runs measured against it and the review state are recorded in the Draft PR and Issue `#89`, each bound to the exact head it measured.
- **changed files:** 12 — new `apps/desktop/src-tauri/src/update_admission.rs` and this bundle; modified `apps/desktop/src-tauri/{Cargo.toml,Cargo.lock,src/lib.rs,tauri.conf.json}`, `apps/desktop/src/{contracts/updateState.ts,contracts/updateState.test.ts,lib/desktopBridge.ts,lib/updateService.ts,lib/updateService.test.ts}`, `tools/desktop/security_gate.py`. Nothing under `docs/project-brain/`, no workflow, no capability file, no `package.json`/`package-lock.json`. `apps/desktop/src-tauri/gen/` and `src-tauri/icons/` are generated locally and are deliberately untracked and unstaged.
- **selected updater crate:** `tauri-plugin-updater = "=2.12.0"` (exact pin, default features `rustls-tls`, `system-proxy`, `zip` retained).
- **selected Tauri CLI:** **unchanged** — `@tauri-apps/cli` stays at `2.11.4`, `tauri` crate at `=2.11.5`, `tauri-build` at `=2.6.3`. Not bumping it is a blocker, not a decision: see *The signed-version gap*.
- **upstream signed-version source:** `tauri-apps/tauri` `crates/tauri-cli/src/helpers/updater_signature.rs` — present with the `\tversion:` append at tag `@tauri-apps/cli-v2.11.5`, absent at `@tauri-apps/cli-v2.11.4`; consumer is `tauri-apps/plugins-workspace` `plugins/updater/src/config.rs` at tag `updater-v2.12.0` (`require_signed_version` line 135, `allow_downgrades` line 148) and `src/updater.rs` `verify_signature` → `verify_signed_version` → `signed_version` (lines ~1529–1606).
- **trust config model:** `UpdaterTrustProbe` — camelCase, `#[serde(deny_unknown_fields)]`, **seven required** fields (`pubkey`, `endpoints`, `requireSignedVersion`, `allowDowngrades`, three `dangerous*`). A missing field is refused, not defaulted, so the upstream `#[serde(default)]` posture cannot silently downgrade this client. An extra field is refused too, which includes upstream's own `windows` sub-node: the Delta-001 node shape is the only admitted trust shape, and a slice that needs `windows.installerTypes` must say so in a new delta rather than be tolerated here.
- **new command set:** `get_update_status`, `check_for_update`, `download_update_candidate` — three, argument-free, registered in `generate_handler![]` and reachable only through three named bindings in `desktopBridge.ts`.
- **capability diff:** none. `capabilities/desktop-read-only.json` is byte-identical to its prebuild content with `permissions: []`.
- **lockfile diff:** `Cargo.lock` 432 → 483 packages (+51, `tauri-plugin-updater` and its `reqwest`/`rustls`/`minisign`/`zip` graph plus the four direct pins `semver =1.0.28`, `serde_json =1.0.151`, `sha2 =0.10.9`, `tauri-plugin-updater =2.12.0`). No JS lockfile changed.
- **focused tests:** Rust `cargo test --locked` **33 passed / 0 failed**, of which 20 are new `update_admission` cases over the 13 the crate had at the base. Desktop `vitest run` **127 passed / 0 failed** across 9 files; `contracts/updateState.test.ts` went 39 → 40 cases and `lib/updateService.test.ts` 13 → 26, so +14 with no case deleted — several existing cases were retargeted to the DEC-031 law, and each rewrite is described in *Contract law added* below.
- **security gate:** `DESKTOP_SECURITY_GATE=PASS` with `TAURI_COMMANDS=check_for_update,choose_workspace,download_update_candidate,get_desktop_snapshot,get_runtime_status_envelope,get_update_status`, `FRONTEND_INVOKES=6`, `CAPABILITY_PERMISSIONS=0`, `UPDATE_COMMAND_ARGS=0`, `UPDATE_RAW_DECODER=STRICT`, `GUEST_UPDATER_PERMISSIONS=0`, `UPDATER_TRUST_CONFIG=DELTA_001_FAIL_CLOSED`, `UPDATER_PLUGIN_PIN=2.12.0`, `INSTALL_RESTART_AUTHORITY=0`, `FILESYSTEM_MUTATION_PRIMITIVES=0`, `GENERIC_PROCESS_EXECUTION=0`, `LOCKFILES=COMMITTED`.
- **version drift:** `VERSION_DRIFT=LOCKED`, canonical source `apps/desktop/src-tauri/tauri.conf.json:0.1.0`, mirrors `Cargo.toml:0.1.0` and `package.json:0.1.0`.
- **Rust tests/check:** `cargo check --locked --all-targets` clean, zero warnings — and that is the command the zero-warning claim rests on. `cargo test --locked` additionally emits one MSVC linker line (`Criando biblioteca …` / `link.exe` stdout) on this host while building the test binary; it is the toolchain announcing an output file, not a compiler diagnostic, and it is not counted as a warning either way. `cargo audit --no-fetch` exit 0 with **7 allowed warnings**, and the same command against `git show a9b48bc:apps/desktop/src-tauri/Cargo.lock` reports the **same 7** (`glib` unsound, `proc-macro-error` + five `unic-*` unmaintained) — so the +51 packages add no finding.
- **web tests/typecheck/build:** `npm run typecheck` clean; `npx vitest run` 127/127; `npm run build:web` builds (`dist/assets/index-*.js 237.52 kB`).
- **npm audit:** `found 0 vulnerabilities`.
- **Governance run:** measured against the exact pushed head and reported in the Draft PR, never restated here — see *Proposed checkpoint delta* item 4.
- **Desktop Shell run:** same placement rule as Governance.
- **Native Package Matrix run:** same placement rule. This is the head that closes U16's hosted half.
- **Protected Release run:** same placement rule, and it is in any case structurally capped: `bundle.active` is false, no signing or publication authority exists, so its credential-bearing stages stay `UNKNOWN` / `BLOCKED` and are not reported as passing on any head.
- **blockers:** the signed-version gap below; the local `tests/runtime` git-stage lane cannot run here (see *Local lanes that did not run*); no trust data exists by design, so no real check/download has ever executed.
- **HIVE refresh:** NOT PERFORMED — `no hive binary` on this host and no generated knowledge for the workspace, so nothing in this bundle rests on a HIVE card. Recorded as an unmet deliverable rather than simulated.
- **proposed checkpoint delta:** see *Proposed checkpoint delta* at the end of this file. Nothing is minted here.

## Source-truth reconciliation onto Delta-002

Implementation of this Work Order ran in two pieces, and the seam is recorded rather than smoothed over.

- The code was written on `e5cfe3267f968d80cc3c4dc91cb6acf54ee7eb80`, the head Delta-001 produced, and was committed there. That is the head every local gate in *Verification executed locally* was first measured against.
- `a9b48bce43fcc2c1a14b70036ed4555f52ba3537` then became `origin/main`: `HCODER-WO-0027: correct executor base after CR-001`, merging PR `#92`. Its whole diff is `.engineering/context-locks/HCODER-WO-0027.md` and `.engineering/prebuilt/HCODER-WO-0027-EXECUTOR-BRIEF.md` — verified with `git diff --name-only e5cfe32 a9b48bc`. Neither path is one this implementation touches, and neither carries a product, runtime, trust, dependency, workflow or test-contract change, so Delta-002 grants no new authority and unlocks nothing beyond what Delta-001 already did.
- Reconciliation moved the branch instead of redoing it: local `main` was fast-forwarded to the verified `a9b48bc` and the feature branch rebased onto it. No reset, clean, discard, force-push or history rewrite was used, and no local work was dropped. Reading Delta-002 *before* editing is what the handoff requires, because an executor that starts from a superseded source cannot know which lock delta governs it.
- **Every gate was then re-measured on the rebased head** (see *Verification executed locally*). A commit is not evidence, but it does invalidate receipts: the pre-rebase numbers below are reproduced from the post-rebase tree, not carried forward.

The practical consequence for the reviewer is that the candidate's ancestry contains both the Delta-001 trust-node unlock and the Delta-002 source correction, so the Context Lock it must be read against is the one at its own tip.

## What the repository now contains

Source-materialized claims — true of the tree, independent of any runner:

- `apps/desktop/src-tauri/src/update_admission.rs` is the only place in this build that can hold updater state. It resolves trust from this build's own configuration, evaluates the DEC-028 channel/version law against what an endpoint announced, and keeps one pending slot (`Empty | Admitted | InFlight | Verified | Refused`) behind a mutex, with the official `Update` handle stored beside the identity it was admitted for. It performs no install, restart, publication or filesystem mutation; two `const _: fn(&tauri_plugin_updater::Config) -> bool` items make the 2.12 field surface a compile-time dependency rather than a hope.
- Three commands reach the guest. Each is argument-free; each answers with a `hive-update-state-v1` snapshot built from a closed `WireStatus` of exactly the eight contract keys, so a remote body, URL, signature, public key or header has no field to arrive in. Upstream error messages are classified into a 16-name refusal vocabulary and discarded, because they quote endpoints.
- `apps/desktop/src/lib/desktopBridge.ts` remains the only file that calls `invoke`, now with 6 sites and no generic helper: a shared `invoke(command)` function would have turned three named bindings back into one caller-selectable surface, so each of the three repeats its own literal command constant.
- `BridgedUpdateService` caches only what `evaluateStatus` accepted, and additionally refuses a snapshot whose `currentVersion`/`channel` disagree with this client's own identity. Any fault — throw, malformed wire, identity disagreement — replaces the cached claim with an honest `unavailable` snapshot rather than keeping a stale one.
- The frontend never sees the trust root: `tauri.conf.json → plugins.updater` is the Delta-001 fail-closed node (`pubkey: ""`, `endpoints: []`, `requireSignedVersion: true`, `allowDowngrades: false`, three `dangerous*` false), and the security gate now fails if that node drifts in either direction.

## The signed-version gap (DEC-031's loadable premise, checked rather than assumed)

`requireSignedVersion: true` is only meaningful if the signature's minisign trusted comment carries a `version:` field. Three facts, each reproducible on this host:

1. The plugin reads that field and refuses without it. `tauri-plugin-updater` 2.12.0 `src/updater.rs`: `signed_version()` splits the trusted comment on tabs and looks for a `version:` prefix; when it finds none and `require_signed_version` is set, `verify_signed_version()` returns `Error::MissingSignedVersion`.
2. Only CLI ≥ 2.11.5 writes it. `crates/tauri-cli/src/helpers/updater_signature.rs` appends `\tversion:{version}` at tag `@tauri-apps/cli-v2.11.5`; at `@tauri-apps/cli-v2.11.4` the file contains no `version:` line at all. The pinned `@tauri-apps/cli` here is **2.11.4**, and its installed binary `node_modules/@tauri-apps/cli-win32-x64-msvc/cli.win32-x64-msvc.node` carries the trusted-comment format `\ntimestamp:` … `\tfile:` with no version field — the format string, not an inference.
3. 2.11.x of the plugin cannot honour the config at all. `plugins/updater/src/config.rs` at tag `updater-v2.11.0` has neither `require_signed_version` nor `allow_downgrades`, and the struct carries no `deny_unknown_fields`, so a `requireSignedVersion` key would be parsed away and silently ignored. `MIN_UPDATER_PLUGIN_VERSION = (2, 12, 0)` in the gate exists because a floor is the only durable answer to a key that fails open.

**Consequence, stated as a refusal rather than a pass.** With the toolchain pinned here, every artifact the repository could actually produce is signed without a version field, so `download+verify` on a real release ends in `MissingSignedVersion`. That is the correct outcome for this slice and it is fail-closed, not a PASS: the updater cannot be *demonstrated* to work, and no claim in the acceptance map that needs a live verified download is satisfied. Two independent reasons keep the path shut, and both are intentional at this head — empty trust data means unavailable before any request, and the pinned CLI could not satisfy the signed-version requirement even with real data.

Resolving the gap needs a `@tauri-apps/cli` 2.11.4 → 2.11.5 move in `apps/desktop/package.json` plus its lockfile. **That was not done here**: neither file is an admitted implementation path under this Work Order's Context Lock, and Delta-001 unfroze exactly one node of exactly one file. It is recorded as the first required follow-up delta rather than slipped in as an unrelated edit.

## Deviations from the Implementation Pack

One, and it is deliberate. The pack's step 8 says "store exact update handle + verified bytes in memory". The handle is stored; **the bytes are not** — `admit_verified_bytes()` hashes them and drops them, because this slice has no install authority, so retaining a full artifact would park an unconsumed payload in memory and let `ready` age into a claim about bytes that were long since superseded. A future install must re-admit and re-verify. Recorded here because the pack said otherwise.

## Contract law added while making that gap honest

Admitting a proof scheme made `ready` producible, which exposed an asymmetry the pre-DEC-031 law had handled with one gate: a caller presenting a well-formed proof could reach `installing`. Install readiness and install progress are different claims — the first says a verified artifact was obtained, the second says the running product was mutated — so they are now gated separately:

- `PROOF_GATED_TRANSITIONS` shrank to `verifying → ready` only.
- `evaluateTransition` refuses any edge whose destination is `installing` or `success` with the new `install_authority_not_governed` reason, **before** the proof gate, whatever evidence accompanies it.
- `evaluateStatus` refuses an install-progress snapshot on its face, and `evaluatePersistedEvent` refuses both an install-progress source and an install-progress outcome.
- Fixing this surfaced a real defect: `evaluateStatus` passed its internal validated record into the public `evaluateAuthenticityProof`, which re-wrapped it and read `data("scheme")` off the wrapper, so **a legitimate `ready` snapshot could never have been admitted**. It now calls a record-level internal, and the public entry point keeps its untrusted-input contract.
- The pack's TS list required the exact admitted proof shape, so `AUTHENTICITY_PROOF_KEYS` is exported and a proof carrying any extra key is refused — unreviewed material cannot ride along with a nominally valid proof.

When HCODER-DIST-001E governs install authority, `ready → installing` and `installing → success` must re-enter the proof-gated set; that obligation is written into the `PROOF_GATED_TRANSITIONS` doc comment, not just here.

## Verification executed locally

Every row was measured on the rebased candidate head (`a9b48bc` + this branch's two commits), after the reconciliation described above — not carried forward from the pre-rebase head. Hosted lanes are absent by construction here, so nothing below is claimed as exact-head CI.

| What | Exact command | Result |
| --- | --- | --- |
| Rust admission + shell lane | `cargo test --locked` | `33 passed; 0 failed` (plus one MSVC linker output notice, not a diagnostic) |
| Rust build, all targets | `cargo check --locked --all-targets` | clean, no warnings |
| Rust advisories, this lock | `cargo audit --no-fetch` | exit 0, 7 allowed warnings |
| Rust advisories, base lock | `cargo audit --no-fetch -f <git show a9b48bc:…/Cargo.lock>` | exit 0, the **same** 7 warnings |
| Desktop unit lane | `npx vitest run` | `127 passed (9 files)` |
| Desktop types | `npm run typecheck` | clean |
| Web bundle | `npm run build:web` | built |
| JS advisories | `npm audit` | `found 0 vulnerabilities` |
| Governance gate | `python tools/desktop/security_gate.py` | `DESKTOP_SECURITY_GATE=PASS` |
| Version lock | `python tools/desktop/version_drift.py` | `VERSION_DRIFT=LOCKED` |
| Python lanes not touched by this WO | `python -m pytest tests/desktop tests/control_plane tests/foundations -q` | `334 passed` |

## Local lanes that did not run, and why

`python -m pytest tests -q` on this host is `39 failed, 698 passed, 72 skipped`, re-measured unchanged on the rebased candidate head. All 39 failures are in `tests/runtime/test_git_stage_*` and every one of them is the WO-0023 provenance gate refusing to proceed because the admitted pure-Python backend is absent: the traceback reaches `distribution("dulwich")` at `hive_runtime/git_stage_index_codec.py:146` and raises for the missing distribution, with the install command named in the exception text. They do not import anything this Work Order changed, and no file under `hive_runtime/` or `tests/runtime/` is modified. Reported as an environment gap on this host, not as a pass and not as a regression.

## Non-vacuity proof

A green gate proves nothing if it cannot fail. Ten single-line mutations were applied to clean mirrors extracted from the candidate head itself with `git archive HEAD -- apps/desktop tools/desktop` (drivers kept outside the repository under `/tmp`, mirrors destroyed after the run; the control mirror measured `PASS` before the campaign, the repository re-measured `PASS` afterwards with `git status` unchanged). Each was expected to be caught, and all ten were:

| Mutation | Gate verdict |
| --- | --- |
| pin `tauri-plugin-updater` down to `=2.11.2` | DETECTED — floor message plus lock/manifest parity |
| `"requireSignedVersion": false` | DETECTED — node must equal the Delta-001 posture, drifted |
| non-empty `"pubkey"` | DETECTED — same node equality, drifted |
| `install_update` registered in `generate_handler![]` | DETECTED — forbidden install command + command-set mismatch |
| `invoke(UPDATE_CHECK_COMMAND, args)` | DETECTED — invoke site must name a constant and carry no arguments |
| `invoke(command)` generic helper | DETECTED — same rule; the payload-free shape is what makes it enforceable |
| capability `"permissions": ["updater:default"]` | DETECTED — permissions must be empty + guest permission reference |
| `update.install(...)` in production Rust | DETECTED — forbidden updater install call |
| trust keys named in frontend `.ts` | DETECTED — forbidden updater trust root in frontend source |
| drop `deny_unknown_fields` from the trust probe | DETECTED — updater admission guard missing |

Result: **10 detected / 10 applied**, control mirror `PASS`. Each row above is the gate's own first refusal line, not a paraphrase.

The TS lane carries the same non-vacuity duty from the other side: `exposesForbiddenMember` is asserted against a fixture that *does* expose `installUpdate`, the `BridgedUpdateService` suite drives a fake bridge that can answer with a valid `ready`, an unadmitted proof, another client's identity, install progress, a snapshot with a ride-along key and a transport failure, and asserts the service caches, refuses or faults exactly as declared. Because that backend is fake, every `ready` in those tests is contract behaviour against a simulated authority — it is not, and must not be read as, evidence that a real artifact was verified.

## Acceptance-map self-audit (U1–U20)

Each property in `.engineering/prebuilt/HCODER-WO-0027-ACCEPTANCE-SECURITY-MAP.md` was walked against the named proof column, and the audit found one real gap: **U6 had no test that the signed-version refusals map into the bounded vocabulary** — `download_refusal()` classified `MissingSignedVersion` and `SignedVersionMismatch`, but nothing asserted it, so the CRITICAL binding property rested on reading the match arms. `upstream_faults_map_to_bounded_denials_and_never_forward_text` closes that, and doubles as the U18 test that a hostile endpoint string cannot be echoed. The table records the state after that fix.

| U | Proof in this tree | Verdict |
| --- | --- | --- |
| U1 Rust-only | exact `tauri-plugin-updater = "=2.12.0"` in `Cargo.toml`; gate forbids `@tauri-apps/plugin-updater` in frontend source and any `updater` capability permission (`GUEST_UPDATER_PERMISSIONS=0`) | PROVEN_LOCALLY |
| U2 Single bridge | `FRONTEND_INVOKES=6`, all in `desktopBridge.ts`, against the exact allowlist | PROVEN_LOCALLY |
| U3 Argument-free | `UPDATE_COMMAND_ARGS=0` plus `ARGUMENT_FREE_COMMANDS` signature scan; nothing at the Rust entry points accepts a payload | PROVEN_LOCALLY |
| U4 No placeholder trust | `shipped_configuration_is_the_fail_closed_delta_001_node`, `absent_updater_node_is_a_malformed_configuration`, `probe_rejects_unknown_missing_and_alias_ed_keys`; blank-key and empty-endpoint arms reach `service_unavailable` before any request in `unsafe_or_relaxed_controls_are_refused_as_unavailable` | PROVEN_LOCALLY |
| U5 HTTPS only | `only_https_origin_endpoints_are_trusted`, `unsafe_or_relaxed_controls_are_refused_as_unavailable`; `dangerous*` pinned false in config **and** probe | PROVEN_LOCALLY |
| U6 Signed-version binding | `requireSignedVersion: true` written and gate-enforced both ways; `MIN_UPDATER_PLUGIN_VERSION=(2,12,0)` because 2.11.x parses the key away; two `const _: fn(&Config) -> bool` field-surface pins; refusal mapping now covered | PARTLY — the *refusal* is proven, a *successful* verified download is not demonstrable on the pinned CLI. See the gap section |
| U7 No downgrade | `allowDowngrades: false` in config and probe; `eligibility_is_same_channel_and_strictly_newer_only`, `prerelease_ordering_cannot_be_bypassed_by_string_length`, `version_profile_matches_the_shared_parity_vectors` (DEC-028) | PROVEN_LOCALLY for the Hive law; upstream comparator unexercisable, same reason as U6 |
| U8 Same channel | `channel_is_derived_from_the_installed_version_shape`, cross-channel arm of the eligibility test | PROVEN_LOCALLY |
| U9 Strictly newer | equal/older arms of `eligibility_is_same_channel_and_strictly_newer_only` | PROVEN_LOCALLY |
| U10 Signature before ready | `admitted_without_handle_and_ready_without_download_both_refuse`, `proof_binds_artifact_and_metadata_without_exposing_trust_data`; `PROOF_GATED_TRANSITIONS` restricts `verifying → ready` to an admitted proof | PROVEN_LOCALLY |
| U11 Candidate identity binding | `candidate_identity_substitution_is_refused`, `metadata_identity_is_deterministic_and_binds_every_input`; the `Update` handle is stored only beside the identity it was admitted for | PROVEN_LOCALLY |
| U12 Verified-bytes custody | `pending_slot_holds_exactly_one_candidate`; `FILESYSTEM_MUTATION_PRIMITIVES=0`; no staging path exists. Bytes are hashed then dropped, which is the recorded pack deviation | PROVEN_LOCALLY |
| U13 Proof non-authority | `the_bridge_never_asserts_install_progress`; TS "never lets install progress enter product state, whatever the backend claims"; `install_authority_not_governed` refuses before the proof gate | PROVEN_LOCALLY |
| U14 No install/restart invoke | 6-command allowlist, `INSTALL_RESTART_AUTHORITY=0`, `PRODUCTION_RUST_INSTALL_PRIMITIVES` and `FRONTEND_FORBIDDEN_UPDATE_TEXT` scans; mutation case in the non-vacuity table | PROVEN_LOCALLY |
| U15 No generic network surface | `status_wire_carries_exactly_the_contract_key_set` + `wire_keys` (closed `WireStatus`, no `url`/`signature`/header field exists to arrive in); no generic HTTP plugin; argument-free commands | PROVEN_LOCALLY |
| U16 Package law preserved | `bundle.active: false` unchanged and gate-checked; the six-target matrix itself is a hosted claim | PARTLY — needs Native Package Matrix on the exact head |
| U17 Existing authority preserved | `capabilities/desktop-read-only.json` byte-identical with `permissions: []`; `CAPABILITY_PERMISSIONS=0`; gate green | PROVEN_LOCALLY |
| U18 Error redaction | `Denial { code: &'static str, detail: &'static str }` makes echoing unrepresentable; `every_refusal_uses_the_closed_vocabulary_and_safe_detail`; the new fault test asserts a hostile URL never appears in a detail | PROVEN_LOCALLY |
| U19 Platform truth | `expected_platform()` (updater `Update::target` shape) kept deliberately distinct from `platform_binding()` (`{os}-{arch}`); no arm reports install or restart success on any platform | PROVEN_LOCALLY |
| U20 Exact-head evidence | four workflows green on one SHA | NOT SATISFIED LOCALLY — only hosted runs can close it, and they measure the pushed head, not this commit's ancestors |

Nothing in the right-hand column is a PASS for a property the map marks CRITICAL in a live sense: U6, U16 and U20 are stated as partial or unsatisfied, because the toolchain pin and the absence of hosted evidence make that the honest verdict. Per the map's closing line, no finding above is closed by prose — every PROVEN_LOCALLY row names a test function or a gate counter that the non-vacuity campaign shows can fail.

## Claims explicitly unavailable at prebuild

No real update check, real signed download, install, restart, rollback, publication or N→N+1 evidence exists yet.

**And still unavailable at this head:** the same list, unchanged in kind. This slice produced the boundary, the trust posture, the law and the proofs that the guards bite. It did not produce a verified update, and on the evidence above it cannot produce one until the CLI pin moves and real trust material is governed somewhere else.

## Proposed checkpoint delta

Nothing is minted here; this is the text a reviewer can turn into a delta, and no `HCODER-CP-*` number is claimed by this Work Order.

1. **`DEC-031` stays PROPOSED.** Its technical content is implemented and locally proven, but a decision whose loadable premise — a signed version a real release can carry — is unmet on the pinned toolchain cannot be canonicalised by local green. Promotion needs the next two items plus a genuine N→N+1 proof.
2. **A Context Lock delta admitting `apps/desktop/package.json` and `apps/desktop/package-lock.json`,** scoped to moving `@tauri-apps/cli` from `2.11.4` to `2.11.5` and nothing else. This is the only unlock that makes the admitted `requireSignedVersion: true` satisfiable by an artifact this repository could actually build, so it gates everything downstream of it.
3. **An `HCODER-DIST-001E` scope statement** that re-adds `ready → installing` and `installing → success` to `PROOF_GATED_TRANSITIONS` at the same moment it introduces install authority, and that keeps `bundle.active: false` until then. The obligation already sits in the code comment; it belongs in the governance record too, because a slice that adds install without re-adding those two edges would leave `ready` one step from a mutation with nothing between them.
4. **No hosted-evidence claim may be back-filled into this file.** When this branch is pushed, the four hosted rows are re-measured against the new head and the old rows are superseded, not edited — a head move invalidates every receipt above it.
