# Correction Delta — HCODER-WO-0002 / CR-001

**MODE:** CORRECTION  
**ACCEPTED/FROZEN:** upstream pins, artifact hashes, license/provenance evidence, non-installing doctor architecture  
**ONLY OPEN FINDING:** `CR-001` — version probe used substring matching and could accept a lookalike version such as `0.0.430` for expected `0.0.43`.  
**SEVERITY:** MEDIUM  
**ROOT CAUSE:** version comparison optimized for varied CLI output without enforcing token boundaries.  
**DECISION:** require an exact standalone version token; reject prerelease/suffixed/lookalike versions and add direct regression tests.  
**TARGETS:** `tools/foundations/doctor.py`, `tests/foundations/test_doctor.py`.  
**FORBIDDEN:** changing upstream pins, expanding runtime scope, installing binaries, invoking live computer control.  
**REQUIRED TESTS:** full foundation unit suite + exact-head Governance.  
**STOP:** corrected candidate only; no next increment.
