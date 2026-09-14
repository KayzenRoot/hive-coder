# Correction Delta — HCODER-WO-0003-CR-002

## Finding
**HIGH · SECRET BOUNDARY / LEAST PRIVILEGE.** The initial subprocess boundary copied the complete parent environment into Open Interpreter/Cua children and into foundation version probes. Ambient provider/API tokens could therefore be disclosed to a child that does not need them in this Work Order.

## Correction
`safe_child_environment()` now inherits only OS/runtime bootstrap paths and locale/config-home variables. Arbitrary credentials are excluded unless an explicit adapter caller deliberately supplies an override. Foundation `--version` probes use the same sanitized environment. Cua production construction forces `CUA_DRIVER_RS_TELEMETRY_ENABLED=false` after caller overrides, so this increment cannot silently re-enable Cua telemetry.

## Regression proof
Added deterministic tests proving a synthetic ambient secret is excluded, explicit overrides work, and Cua telemetry-disable cannot be overridden.
