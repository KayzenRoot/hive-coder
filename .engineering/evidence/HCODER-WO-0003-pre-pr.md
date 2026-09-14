# Evidence Bundle — HCODER-WO-0003

## Identity
- Base: `1591e3bca88096f51c87131a2b4f9cef0998e7c8`
- Candidate before PR evidence commit: `14de9d7388a22a3a2f7284864439511652c11ba7`
- Branch: `feat/HCODER-WO-0003-runtime-bridge`
- Issue: #5

## Local deterministic evidence
- `python -m compileall -q hive_runtime tests`: PASS.
- `PYTHONWARNINGS=error::ResourceWarning python -m unittest discover -s tests -p "test_*.py" -v`: PASS, including 10 runtime bridge tests before CR-001.
- CR-001 added canonical-lock tests and must be revalidated by exact-head Governance in PR.

## Safety evidence
- `InterpreterAdapter` exposes no prompt method in this increment.
- `CuaAdapter` exposes no `tools/call` method.
- No mouse/keyboard/clipboard/screen/window/browser action API exists in the bridge.
- Unsupported inbound JSON-RPC requests are denied with `-32601` by default.
- Production constructors perform exact version preflight before launching the protocol process.

## HEDS note
`HCODER-WO-0003-CR-001` removed duplicate hard-coded foundation versions from adapters; production preflight now resolves the canonical expected version from `foundations/foundations.lock.json`.

## Pending proof
PR exact-head Governance and final HEDS audit are required before checkpoint promotion or merge.
