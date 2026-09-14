# Evidence Bundle — HCODER-WO-0003

## Identity
- Base: `1591e3bca88096f51c87131a2b4f9cef0998e7c8`
- Branch: `feat/HCODER-WO-0003-runtime-bridge`
- Issue: #5
- PR: #7

## Deterministic evidence
- Local pre-PR compile/tests passed before CR-001.
- Governance run `34910508995` passed 26 tests with `ResourceWarning` treated as error and all foundation/compile checks green.
- HEDS inspection of that run proved checkout used synthetic merge SHA `f7a06f405282839fe865f3d3c01379510e5bd966`, so it is NOT accepted as exact-head evidence.
- `HCODER-WO-0003-CR-003` corrects Governance to explicitly checkout and verify the PR head SHA. A fresh successful run is mandatory.

## Corrections
- CR-001: runtime versions resolve from canonical `foundations/foundations.lock.json` instead of duplicate adapter constants.
- CR-002: subprocesses/version probes use a least-privilege environment allowlist; ambient secrets are not inherited; Cua telemetry is forced off.
- CR-003: Governance now verifies the actual checked-out commit equals the expected PR/push SHA.

## Safety evidence
- `InterpreterAdapter` exposes no prompt method in this increment.
- `CuaAdapter` exposes no `tools/call` method.
- No mouse/keyboard/clipboard/screen/window/browser action API exists in the bridge.
- Unsupported inbound JSON-RPC requests are denied with `-32601` by default.
- Production constructors perform canonical-lock exact-version preflight before launching the protocol process.

## Pending proof
Fresh exact-head Governance and final HEDS verdict are required before checkpoint promotion or merge.
