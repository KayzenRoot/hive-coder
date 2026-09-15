# Correction Delta — HCODER-WO-0019

**MODE:** CORRECTION  
**SEVERITY:** LOW — cross-platform evidence gap, no implementation defect observed  
**SAME PR:** required — PR #48  
**ACCEPTED/FROZEN:** CP-0018 protocol, WO-0019 one-shot sidecar implementation, CR-001 process-boundary rejection coverage, all authority exclusions and existing CI gates.  
**ONLY OPEN FINDING:** `HCODER-WO-0019-CR-002` — the new sidecar process suite was covered by Ubuntu source-pack but not by the Windows HIGH_ASSURANCE subset, leaving future Windows desktop consumption dependent on portability assumption.  
**ROOT CAUSE:** Governance Windows historically targeted the control-plane/Cua subset and was not extended when the sidecar process boundary was introduced.  
**DECISION:** add only `tests.runtime.test_runtime_status_sidecar` to the existing Windows HIGH_ASSURANCE unittest invocation; do not change product/runtime behavior.  
**TARGET FILES/SYMBOLS:** `.github/workflows/governance.yml` Windows HIGH_ASSURANCE test command and this correction record only.  
**PRESCRIBED TRANSFORM:** preserve exact-head checkout and existing 56-test suite, append the sidecar module, retain `PYTHONWARNINGS=error::ResourceWarning`, and require the expanded Windows suite to pass.  
**FORBIDDEN:** weakening/omitting existing tests, changing runner permissions, adding secrets, enabling network/provider access, changing product code, or expanding desktop/process authority.  
**REQUIRED TESTS:** exact-head Governance Ubuntu full suite + expanded Windows HIGH_ASSURANCE; exact-head Desktop Shell; HEDS.  
**SEARCH/PATCH/RETRY BUDGET:** one workflow-line extension plus this correction record; further changes only for concrete gate/HEDS findings.  
**STATUS:** RESOLVED IN CANDIDATE, pending exact-head Windows proof and HEDS.  
**STOP:** same governed WO-0019 STOP states.
