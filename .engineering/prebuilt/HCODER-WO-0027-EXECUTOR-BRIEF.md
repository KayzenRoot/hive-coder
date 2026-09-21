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
- verify base exactly `5d97df6cf2f69a35d14af140e28088a7659eff7a`;
- use branch `feat/HCODER-WO-0027-tauri-updater` from the final prebuild main after this governance PR is merged;
- refresh Tauri official updater/source facts before dependency edits;
- implement the locked Rust-only bridge;
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