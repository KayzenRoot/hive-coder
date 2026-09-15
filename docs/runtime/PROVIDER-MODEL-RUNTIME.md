# Provider & Model Runtime

Hive normalizes provider model catalogs before models enter routing. A provider name or model label never grants capabilities. Capability probes produce evidence consumed by the CP-0007 registry; only verified evidence can make a model eligible for a required capability.

## OpenCode Go
OpenCode Go is the first-class provider identity for this increment. The identity itself carries zero capability authority. Concrete model inventory and capabilities must come through the provider adapter/probe boundary at runtime.

## Credentials
Credentials live in an explicit `CredentialScope`. The object redacts values in representation and exposes only named retrieval to trusted adapter code. Secrets must not enter skill content, audit payloads, model profiles, prompts or repository fixtures.

## Routing
`ModelRouter` first eliminates models that do not satisfy verified required capabilities. A deterministic scorer may then rank the eligible set. No fallback may silently weaken required capabilities.

## Interpreter
ACP prompt execution is introduced only after a session exists. Prompt lifecycle does not create a Cua permit, capability grant or permission-control-plane transition. Desktop mutation remains governed exclusively by the existing HIGH_ASSURANCE boundary.
