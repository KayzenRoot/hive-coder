# Work Order — HCODER-WO-0005

**Class:** HIGH_ASSURANCE  
**Base checkpoint:** HCODER-CP-0004  
**Issue:** #10

## Objective
Introduce the first Hive-owned gated Cua Action Executor behind `PermissionControlPlane`.

## Allowed delta
- Add an executor that is the only Hive surface allowed to issue Cua `tools/call`.
- Start with an explicit safe subset: pointer click and text typing only.
- Require a valid request-bound single-use execution permit for every dispatch.
- Revalidate live application/window identity immediately before dispatch.
- Propagate session cancellation/user takeover/emergency stop into executor cancellation state.
- Validate Cua result shape and support post-action verification.
- Add adversarial tests and Windows gate evidence.

## Explicitly forbidden
- Shell execution, filesystem mutation, clipboard read/write, destructive or privileged actions.
- Broad/unmapped Cua tools.
- Model-accessible approval minting.
- Automatic dependency installation.
- Claims that physical Windows desktop E2E is proven unless a real pinned Cua Driver run demonstrates it.

## STOP CONDITION
HEDS APPROVED; exact-head Ubuntu broad regression and Windows targeted tests green; checkpoint/decision promoted; squash merge and post-merge main validation complete.
