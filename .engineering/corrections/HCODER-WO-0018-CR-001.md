# HCODER-WO-0018-CR-001 — Remove semantic-parser bypass from public desktop IPC API

**Status:** RESOLVED IN CANDIDATE  
**Severity:** MEDIUM  
**Detected by:** HEDS semantic pre-review  
**Affected implementation head:** `2f4dc76f7b8d98ce01af13313019491bf2ffdfa4`

## Finding
The initial canonical reconstruction correctly implemented a raw response decoder that enforces response-byte ceilings and deterministic canonical JSON before returning presentation state. However, it also exported the lower-level object semantic parser.

A future consumer could therefore import the object parser directly after an arbitrary `JSON.parse()` and bypass the protocol's raw canonical-wire proof. That would weaken duplicate-key/noncanonical-wire rejection even though it grants no execution authority today.

The initial cross-language test also covered only ASCII status text, leaving Python `ensure_ascii=True` and TypeScript canonical escaping parity under Unicode presentation text implicit rather than proven.

## Resolution
- the object semantic parser is now private to `runtimeStatus.ts`;
- the only public response-admission API is `decodeRuntimeStatusEnvelope(raw)`;
- adversarial frontend tests now exercise protocol/schema/provenance/readiness/counter cases through the raw decoder rather than the internal semantic layer;
- Python and TypeScript tests explicitly prove matching canonical ASCII escaping for `café 🍯`, including the surrogate-pair wire representation;
- request encoding remains the only other public IPC operation on the desktop contract.

## Authority impact
None. This correction narrows the desktop status boundary and adds no Tauri command, process lifecycle, provider/model execution, credential access, task/permission mutation, filesystem/Git mutation or computer-use authority.

## Closure gate
The final head containing this correction must independently pass exact-head Governance + Desktop Shell and HEDS with unresolved HIGH/CRITICAL findings = 0 before WO-0018 may advance.
