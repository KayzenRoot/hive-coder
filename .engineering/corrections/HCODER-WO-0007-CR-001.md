# Correction Delta — HCODER-WO-0007-CR-001

## Finding
**HIGH · caller-controlled promotion authority.** Initial candidate accepted a caller-supplied evaluation dictionary and caller-supplied `granted_capabilities` during activation. Although tests used honest callers, exposing those values at the skill-facing API could let an untrusted orchestration path self-assert evaluation success or a broader grant.

## Correction
- `SkillStore` now receives evaluator and capability-authorizer callbacks only at trusted host construction.
- Skill-facing lifecycle exposes `evaluate(skill_id, version)` and `activate(skill_id, version)` with no caller-supplied PASS or grant.
- Evaluation evidence is bound to exact skill id/version/content SHA-256.
- Activation queries the trusted authorizer at promotion time and still requires requested capabilities to be a subset.
- Added adversarial test proving caller cannot inject a capability grant into `activate`.

## Residual boundary
The trusted host must wire the capability authorizer to the canonical Permission & Control Plane/session authority before skills can drive privileged execution. WO-0007 itself does not expose skills to Cua or provider execution.
