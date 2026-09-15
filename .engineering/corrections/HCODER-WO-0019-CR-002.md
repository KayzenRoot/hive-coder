# Correction Delta — HCODER-WO-0019

**MODE:** CORRECTION  
**SEVERITY:** LOW — cross-platform evidence gap, no implementation defect observed  
**SAME PR:** required — PR #48  
**ACCEPTED/FROZEN:** CP-0018 protocol, WO-0019 one-shot sidecar implementation, CR-001 process-boundary rejection coverage, all authority exclusions and existing CI gates.  
**FINDING:** `HCODER-WO-0019-CR-002` — the sidecar process suite was covered by Ubuntu source-pack but not by the Windows HIGH_ASSURANCE subset, leaving future Windows desktop consumption dependent on portability assumption.  
**ROOT CAUSE:** Governance Windows historically targeted the control-plane/Cua subset and was not extended when the sidecar process boundary was introduced.  
**DECISION:** add only `tests.runtime.test_runtime_status_sidecar` to the existing Windows HIGH_ASSURANCE unittest invocation; do not change product/runtime behavior.  
**TARGET FILES/SYMBOLS:** `.github/workflows/governance.yml` Windows HIGH_ASSURANCE test command and this correction record only.  
**PRESCRIBED TRANSFORM:** preserve exact-head checkout and existing 56-test suite, append the sidecar module, retain `PYTHONWARNINGS=error::ResourceWarning`, and require the expanded Windows suite to pass.  
**FORBIDDEN:** weakening/omitting existing tests, changing runner permissions, adding secrets, enabling network/provider access, changing product code, or expanding desktop/process authority.  
**CLOSURE EVIDENCE:** exact technical head `ba10ba72f76316806cd820dc0d205e68105f61bb`; Governance #250 Windows Server 2025 HIGH_ASSURANCE **61/61 PASS** with the status-sidecar module and ResourceWarning fatal; Ubuntu **288/288 PASS**; Desktop Shell #86 SUCCESS; HEDS technical `5216093993` APPROVED FOR PROMOTION with H/C 0.  
**STATUS:** **RESOLVED**.  
**STOP:** same governed WO-0019 STOP states.
