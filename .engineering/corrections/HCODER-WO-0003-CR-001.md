# Correction Delta — HCODER-WO-0003-CR-001

## Finding
**MEDIUM · SOURCE-OF-TRUTH DRIFT RISK.** The first runtime candidate repeated foundation versions in adapter constructors even though `foundations/foundations.lock.json` is the approved version source.

## Correction
Added `hive_runtime.foundation_lock` as the runtime-side reader of the canonical lock. Production adapter constructors now identify their foundation key and resolve `discovery.expectedVersion` from the lock immediately before preflight. Unknown records/schema fail closed. Existing doctor and runtime preflight share the same exact-version matcher.

## Regression proof
Tests assert Open Interpreter and Cua production versions resolve from the canonical lock, while unknown foundations and unsupported lock schemas are rejected.
