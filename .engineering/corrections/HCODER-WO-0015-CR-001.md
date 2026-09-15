# HCODER-WO-0015-CR-001 — Vite/Vitest configuration typing

**Severity:** MEDIUM  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0015`

## Finding
The first desktop-web candidate imported `defineConfig` from `vite` while also declaring Vitest's `test` configuration block. TypeScript rejected the configuration with TS2769 because the plain Vite config type did not admit the Vitest field.

## Correction
`vite.config.ts` now imports `defineConfig` from `vitest/config`, preserving the same Vite/React behavior while making the test configuration type-safe.

Exact-head typecheck, frontend tests and production build now pass.

## Closure gate
RESOLVED becomes final only after the promotion head passes exact-head Governance + Desktop Shell and final HEDS reports no unresolved HIGH/CRITICAL finding.
