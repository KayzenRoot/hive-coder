# Correction Delta — HCODER-WO-0001 / CR-001

**MODE:** CORRECTION  
**ACCEPTED/FROZEN:** GEF/HEDS model, source hierarchy, product direction, adapter architecture  
**ONLY OPEN FINDING:** `CR-001` — initial Source Pack omitted UI/UX, Integration Contracts and License/Provenance sources required by the product's desktop + third-party-foundation nature.  
**SEVERITY:** MEDIUM  
**ROOT CAUSE:** Minimal Source Pack was created before applying project-specific documentation extensions.  
**DECISION:** Add the three canonical sources and require them in Governance CI.  
**TARGETS:** `docs/project-brain/12-UI-UX.md`, `13-INTEGRATION-CONTRACTS.md`, `14-LICENSE-PROVENANCE.md`, `.github/workflows/governance.yml`  
**FORBIDDEN:** Product implementation, dependency import, final license selection, architecture expansion.  
**REQUIRED TESTS:** required-file check + exact-head Governance workflow.  
**STOP:** corrected candidate only; no next increment.
