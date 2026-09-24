# HCODER-WO-0027 — Evidence Bundle

**Status:** IMPLEMENTATION CANDIDATE — TECHNICAL LANE GREEN ON THE LOCAL HOST, NOT PUSHED, NO HOSTED RECEIPT EXISTS
**Issue:** #89
**Slice:** HCODER-DIST-001D
**Decision:** `DEC-031` — PROPOSED / NOT CANONICAL. Nothing in this bundle promotes it.
**Canonical base at prebuild:** `5d97df6cf2f69a35d14af140e28088a7659eff7a`

> **What this bundle is.** A record of what the repository now contains and of what was proven on one Windows host. No sentence here is evidence that an update endpoint, a signing key pair, a publisher, a certificate or a runner exists. Every hosted row is `NOT RUN`, because this round was deliberately not pushed; a receipt for a head that does not exist yet would be the first false statement in this file.

## Prebuild facts
- CP-0026 / DEC-030 canonical and sealed.
- PR #88 source-truth reconciliation merged and post-validated before this Work Order began.
- Current UpdateService is inert.
- No updater plugin dependency or JS guest binding exists at prebuild.
- desktop capability permissions are empty.
- bundle.active is false.
- no updater signing key/public production trust configuration is claimed.

## Evidence slots for executor
- **start SHA:** `e5cfe3267f968d80cc3c4dc91cb6acf54ee7eb80` (`feat/HCODER-WO-0027-tauri-updater`, i.e. Delta-001 `#91` merged).
- **final SHA:** the commit that carries this bundle. Resolve it with `git rev-parse HEAD` on that branch; it is written before the commit exists, so no SHA is asserted here, and no hosted run has measured any head of this branch.
- **changed files:** 11 — new `apps/desktop/src-tauri/src/update_admission.rs`; modified `apps/desktop/src-tauri/{Cargo.toml,Cargo.lock,src/lib.rs,tauri.conf.json}`, `apps/desktop/src/{contracts/updateState.ts,contracts/updateState.test.ts,lib/desktopBridge.ts,lib/updateService.ts,lib/updateService.test.ts}`, `tools/desktop/security_gate.py`. `apps/desktop/src-tauri/gen/` and `src-tauri/icons/` are generated locally and are deliberately untracked and unstaged.
- **selected updater crate:** `tauri-plugin-updater = "=2.12.0"` (exact pin, default features `rustls-tls`, `system-proxy`, `zip` retained).
- **selected Tauri CLI:** **unchanged** — `@tauri-apps/cli` stays at `2.11.4`, `tauri` crate at `=2.11.5`, `tauri-build` at `=2.6.3`. Not bumping it is a blocker, not a decision: see *The signed-version gap*.
- **upstream signed-version source:** `tauri-apps/tauri` `crates/tauri-cli/src/helpers/updater_signature.rs` — present with the `\tversion:` append at tag `@tauri-apps/cli-v2.11.5`, absent at `@tauri-apps/cli-v2.11.4`; consumer is `tauri-apps/plugins-workspace` `plugins/updater/src/config.rs` at tag `updater-v2.12.0` (`require_signed_version` line 135, `allow_downgrades` line 148) and `src/updater.rs` `verify_signature` → `verify_signed_version` → `signed_version` (lines ~1529–1606).
- **trust config model:** `UpdaterTrustProbe` — camelCase, `#[serde(deny_unknown_fields)]`, **seven required** fields (`pubkey`, `endpoints`, `requireSignedVersion`, `allowDowngrades`, three `dangerous*`). A missing field is refused, not defaulted, so the upstream `#[serde(default)]` posture cannot silently downgrade this client. An extra field is refused too, which includes upstream's own `windows` sub-node: the Delta-001 node shape is the only admitted trust shape, and a slice that needs `windows.installerTypes` must say so in a new delta rather than be tolerated here.
- **new command set:** `get_update_status`, `check_for_update`, `download_update_candidate` — three, argument-free, registered in `generate_handler![]` and reachable only through three named bindings in `desktopBridge.ts`.
- **capability diff:** none. `capabilities/desktop-read-only.json` is byte-identical to its prebuild content with `permissions: []`.
- **lockfile diff:** `Cargo.lock` 432 → 483 packages (+51, `tauri-plugin-updater` and its `reqwest`/`rustls`/`minisign`/`zip` graph plus the four direct pins `semver =1.0.28`, `serde_json =1.0.151`, `sha2 =0.10.9`, `tauri-plugin-updater =2.12.0`). No JS lockfile changed.
- **focused tests:** Rust `cargo test --locked` **32 passed / 0 failed**, of which 19 are new `update_admission` cases over the 13 the crate had at the base. Desktop `vitest run` **127 passed / 0 failed** across 9 files; `contracts/updateState.test.ts` went 39 → 40 cases and `lib/updateService.test.ts` 13 → 26, so +14 with no case deleted — several existing cases were retargeted to the DEC-031 law, and each rewrite is described in *Contract law added* below.
- **security gate:** `DESKTOP_SECURITY_GATE=PASS` with `TAURI_COMMANDS=check_for_update,choose_workspace,download_update_candidate,get_desktop_snapshot,get_runtime_status_envelope,get_update_status`, `FRONTEND_INVOKES=6`, `CAPABILITY_PERMISSIONS=0`, `UPDATE_COMMAND_ARGS=0`, `UPDATE_RAW_DECODER=STRICT`, `GUEST_UPDATER_PERMISSIONS=0`, `UPDATER_TRUST_CONFIG=DELTA_001_FAIL_CLOSED`, `UPDATER_PLUGIN_PIN=2.12.0`, `INSTALL_RESTART_AUTHORITY=0`, `FILESYSTEM_MUTATION_PRIMITIVES=0`, `GENERIC_PROCESS_EXECUTION=0`, `LOCKFILES=COMMITTED`.
- **version drift:** `VERSION_DRIFT=LOCKED`, canonical source `apps/desktop/src-tauri/tauri.conf.json:0.1.0`, mirrors `Cargo.toml:0.1.0` and `package.json:0.1.0`.
- **Rust tests/check:** `cargo check --locked --all-targets` clean, zero warnings; `cargo audit --no-fetch` exit 0 with **7 allowed warnings**, and the same command against `git show HEAD:…/Cargo.lock` reports the **same 7** (`glib` unsound, `proc-macro-error` + five `unic-*` unmaintained) — so the +51 packages add no finding.
- **web tests/typecheck/build:** `npm run typecheck` clean; `npx vitest run` 127/127; `npm run build:web` builds (`dist/assets/index-*.js 237.52 kB`).
- **npm audit:** `found 0 vulnerabilities`.
- **Governance run:** NOT RUN — this branch was not pushed, so no Actions run exists for any head of it.
- **Desktop Shell run:** NOT RUN — same reason.
- **Native Package Matrix run:** NOT RUN — same reason.
- **Protected Release run:** NOT RUN — same reason, and it is in any case unreachable: `bundle.active` is false and no signing or publication authority exists.
- **blockers:** the signed-version gap below; the local `tests/runtime` git-stage lane cannot run here (see *Local lanes that did not run*); no trust data exists by design, so no real check/download has ever executed.
- **HIVE refresh:** NOT PERFORMED — `no hive binary` on this host and no generated knowledge for the workspace, so nothing in this bundle rests on a HIVE card. Recorded as an unmet deliverable rather than simulated.
- **proposed checkpoint delta:** see *Proposed checkpoint delta* at the end of this file. Nothing is minted here.

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

| What | Exact command | Result |
| --- | --- | --- |
| Rust admission + shell lane | `cargo test --locked` | `32 passed; 0 failed` |
| Rust build, all targets | `cargo check --locked --all-targets` | clean, no warnings |
| Rust advisories, this lock | `cargo audit --no-fetch` | exit 0, 7 allowed warnings |
| Rust advisories, base lock | `cargo audit --no-fetch -f <git show HEAD:…/Cargo.lock>` | exit 0, the **same** 7 warnings |
| Desktop unit lane | `npx vitest run` | `127 passed (9 files)` |
| Desktop types | `npm run typecheck` | clean |
| Web bundle | `npm run build:web` | built |
| JS advisories | `npm audit` | `found 0 vulnerabilities` |
| Governance gate | `python tools/desktop/security_gate.py` | `DESKTOP_SECURITY_GATE=PASS` |
| Version lock | `python tools/desktop/version_drift.py` | `VERSION_DRIFT=LOCKED` |
| Python lanes not touched by this WO | `python -m pytest tests/desktop tests/control_plane tests/foundations -q` | `334 passed` |

## Local lanes that did not run, and why

`python -m pytest tests -q` on this host is `39 failed, 698 passed, 72 skipped`. All 39 failures are in `tests/runtime/test_git_stage_*` and every one of them is the WO-0023 provenance gate refusing to proceed because the admitted pure-Python backend is absent — `ModuleNotFoundError: No module named 'dulwich'` — with the install command named in the exception text. They do not import anything this Work Order changed, and no file under `hive_runtime/` or `tests/runtime/` is modified. Reported as an environment gap on this host, not as a pass and not as a regression.

## Non-vacuity proof

A green gate proves nothing if it cannot fail. Ten single-line mutations were applied to an isolated copy of the working tree (drivers and copies kept outside the repository, `/tmp/w0027mut`, destroyed after the run; the repository re-measured `PASS` afterwards and `git status` unchanged). Each was expected to be caught, and all ten were, on the content this bundle describes:

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

The TS lane carries the same non-vacuity duty from the other side: `exposesForbiddenMember` is asserted against a fixture that *does* expose `installUpdate`, the `BridgedUpdateService` suite drives a fake bridge that can answer with a valid `ready`, an unadmitted proof, another client's identity, install progress, a snapshot with a ride-along key and a transport failure, and asserts the service caches, refuses or faults exactly as declared. Because that backend is fake, every `ready` in those tests is contract behaviour against a simulated authority — it is not, and must not be read as, evidence that a real artifact was verified.

## Claims explicitly unavailable at prebuild

No real update check, real signed download, install, restart, rollback, publication or N→N+1 evidence exists yet.

**And still unavailable at this head:** the same list, unchanged in kind. This slice produced the boundary, the trust posture, the law and the proofs that the guards bite. It did not produce a verified update, and on the evidence above it cannot produce one until the CLI pin moves and real trust material is governed somewhere else.

## Proposed checkpoint delta

Nothing is minted here; this is the text a reviewer can turn into a delta, and no `HCODER-CP-*` number is claimed by this Work Order.

1. **`DEC-031` stays PROPOSED.** Its technical content is implemented and locally proven, but a decision whose loadable premise — a signed version a real release can carry — is unmet on the pinned toolchain cannot be canonicalised by local green. Promotion needs the next two items plus a genuine N→N+1 proof.
2. **A Context Lock delta admitting `apps/desktop/package.json` and `apps/desktop/package-lock.json`,** scoped to moving `@tauri-apps/cli` from `2.11.4` to `2.11.5` and nothing else. This is the only unlock that makes the admitted `requireSignedVersion: true` satisfiable by an artifact this repository could actually build, so it gates everything downstream of it.
3. **An `HCODER-DIST-001E` scope statement** that re-adds `ready → installing` and `installing → success` to `PROOF_GATED_TRANSITIONS` at the same moment it introduces install authority, and that keeps `bundle.active: false` until then. The obligation already sits in the code comment; it belongs in the governance record too, because a slice that adds install without re-adding those two edges would leave `ready` one step from a mutation with nothing between them.
4. **No hosted-evidence claim may be back-filled into this file.** When this branch is pushed, the four hosted rows are re-measured against the new head and the old rows are superseded, not edited — a head move invalidates every receipt above it.
