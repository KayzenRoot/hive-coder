# Correction Delta — HCODER-WO-0019

**MODE:** CORRECTION  
**SEVERITY:** LOW — test/evidence coverage gap, no implementation bypass observed  
**SAME PR:** required — PR #48  
**ACCEPTED/FROZEN:** CP-0018 canonical protocol, fixed one-shot sidecar design, prebuilt `disconnected_snapshot()`, `ManagedStdioProcess` shell-free/sanitized environment and all WO-0019 authority exclusions.  
**ONLY OPEN FINDING:** `HCODER-WO-0019-CR-001` — initial process-level suite relied on lower-level CP-0018 protocol tests for duplicate-key / future-version / unsupported-operation rejection and did not prove a buffered second request remains unserved before process exit.  
**ROOT CAUSE:** initial process tests sampled malformed, non-canonical, oversized and missing-newline cases but did not mirror every high-value protocol rejection at the process boundary.  
**DECISION:** keep implementation/protocol unchanged; strengthen only process-level tests so the executable boundary itself proves fail-closed behavior and one-shot semantics.  
**TARGET FILES/SYMBOLS:** `tests/runtime/test_runtime_status_sidecar.py` only.  
**PRESCRIBED TRANSFORM:** send two canonical requests in the success case and prove only the first yields a response; add duplicate-key, future-protocol and unsupported-operation payloads to process-level rejection cases; retain canonical `encode_request()`/`parse_response()` on accepted wire.  
**FORBIDDEN:** weakening `parse_request`, broadening accepted wire, adding fallback JSON normalization, adding retry/loop/daemon behavior, introducing dynamic dispatch/listeners, changing authority boundaries, touching provider/model/credential/mutation paths.  
**REQUIRED TESTS:** exact-head full Governance + Desktop Shell; source-pack must remain ResourceWarning-clean; Windows HIGH_ASSURANCE unchanged.  
**SEARCH/PATCH/RETRY BUDGET:** one bounded test-file patch plus this correction record; further changes only for concrete gate/HEDS findings.  
**STATUS:** RESOLVED IN CANDIDATE `b0456dfb5895160ed465da53850640bb573c5473`, pending exact-head gates and HEDS.  
**STOP:** same governed WO-0019 STOP states.
