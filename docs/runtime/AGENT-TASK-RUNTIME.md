# Resumable Agent Task Runtime

The Agent Task Runtime coordinates long-running Hive work without becoming a new permission system.

## Task plan
A `TaskPlan` is a deterministic DAG of model-prompt and governed-skill nodes. Dependencies must be valid and acyclic. Model nodes declare required verified capabilities; skill nodes declare only skill identity/version. The runtime does not accept raw shell, browser or Cua actions as task-node kinds.

## Persistence
Checkpoints are atomic JSON envelopes authenticated with host-owned HMAC-SHA256. They are bound to a canonical plan fingerprint. Raw prompts are represented only by SHA-256 inside the fingerprint and are never persisted. Checkpoints do not persist credentials, approvals, permits, capability grants, skill contents or model outputs.

The HMAC protects checkpoint integrity against modification without the trusted host key. It is not a substitute for OS account/storage security and does not confer authorization.

## Recovery
A process interruption while a model prompt is running may be reissued only when its node attempt budget still permits it. A running skill is treated as potentially side-effecting and becomes `INTERRUPTED`; it cannot auto-replay. The trusted host must explicitly choose retry or fail, and retry still obeys the node attempt budget.

## Budgets
Global execution/failure budgets and per-node attempt budgets are mandatory and bounded. Budget exhaustion pauses the task rather than silently expanding limits.

## Model and skill boundaries
Model selection uses the CP-0008 `ModelRouter`, so unverified required capabilities fail closed. Skills execute only through a host-injected `SkillExecutionPort`; the runtime neither activates skills nor creates permission grants.

## Observability
The checkpoint carries an ordered structured event history with only normalized event/result/error type codes. Exception messages, prompts and provider/model outputs are deliberately excluded to reduce secret leakage.
