# HCODER-WO-0027 — Executor Brief

## Read order
1. HIVE project state/context if available.
2. AGENTS.md.
3. CP-0026 checkpoint + DEC-028 + DEC-030.
4. WO-0027 + Context Lock + DEC-031.
5. Implementation Pack + Acceptance/Security Map.
6. Only then bounded implementation files.

Git/code/exact-head evidence beat HIVE if stale.

## Do
- do not implement from the historical post-PR-#90 base `3c3e6d9566bdde5653518ae253386cfd205b330c` or pre-correction `e5cfe3267f968d80cc3c4dc91cb6acf54ee7eb80`; wait until Context Lock Delta 002 is accepted/merged with exact-main gates and independent HEDS approval, then capture the full current `main` SHA at preflight as the implementation start SHA;
- create `feat/HCODER-WO-0027-tauri-updater` from that captured post-Delta-002 `main` SHA; verify the merge and source fingerprints before any edits, and stop/recompile if the head moved or local work cannot be reconciled safely;
- read Context Lock Delta 002 first and retain Delta 001 as historical authority; refresh/confirm the exact Tauri updater source facts before dependency edits;
- apply the Delta-001-bounded `plugins.updater` fail-closed config and implement the locked Rust-only bridge;
- keep frontend plugin authority at zero;
- produce focused evidence;
- open a Draft PR;
- never merge.

## Intended upstream security posture
- updater version must expose signed-version binding;
- require signed version;
- never allow downgrade;
- HTTPS only;
- download returns only signature-verified bytes;
- no custom comparator weakening Hive strictly-newer law.

## Delta 001 execution note (trust-config constraints remain in force)
- Canonical `plugins.updater` is allowed to remain explicitly unconfigured with `pubkey: ""` and `endpoints: []`; this must yield unavailable before any request.
- Keep `requireSignedVersion=true`, `allowDowngrades=false`, and every dangerous transport/TLS flag false.
- Do not generate, fetch or invent a production updater key or endpoint to make the positive path pass. Use deterministic test doubles for positive contract coverage.
- Only the `plugins.updater` node is unfrozen; all other `tauri.conf.json` content remains frozen.

## Do not
- invent endpoint/public key values;
- ask for or read private updater signing key;
- add JS updater package;
- add updater capability permission;
- add install/restart frontend command;
- touch release workflows;
- publish anything;
- broaden into UI/rollback/E2E.

## Local-heavy reason
Dependency resolution (`Cargo.lock` and possibly npm lock alignment), Rust compilation and native Tauri validation require a real workspace/toolchain. That is the concrete reason a later implementation handoff may need Codex; planning and governance do not.

## Terminal states
- `IMPLEMENTATION_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW`
- `BLOCKED_UPSTREAM_COMPATIBILITY`
- `BLOCKED_TRUST_CONFIG_MODEL`
- `BLOCKED_TOOLCHAIN`
- `BLOCKED_SOURCE_TRUTH`

Never merge.