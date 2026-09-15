# Model Capabilities & Hive Skills

## Capability truth
Hive never enables a feature because a model name, marketing label or model-generated text claims support. A capability becomes negotiable only when a normalized `CapabilityEvidence` record is `verified`. Declared and unknown evidence stays non-authoritative.

This lets the UI and agent runtime eventually adapt to the selected model without silently overestimating it. Examples include tool calling, structured output, vision, long context, code execution and computer-use planning.

## Skill boundary
A Hive skill is a versioned artifact with identity, provenance, optional content digest, entrypoint and requested capabilities. Installation, validation and activation are separate states.

MCP skill resources are always ingested as `mcp_untrusted`. A verified transport or server does not make the resource instructions trusted. Skill content cannot edit policy, mint approvals or create capabilities.

Activation requires deterministic evaluation plus an already-existing permission grant covering every requested capability. This is deliberately one-way: permissions constrain skills; skills never expand permissions.

## Learning direction
Future learned skills must be generated into a candidate state, evaluated against deterministic fixtures/adversarial tests, versioned, provenance-stamped and promoted through the same lifecycle. Runtime self-modification is not part of this foundation.
