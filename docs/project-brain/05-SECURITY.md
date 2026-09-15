# Security — Hive Coder

Computer control is a primary threat boundary.

Security baseline: least privilege; workspace scoping; application/action allowlists where feasible; emergency stop/user takeover; explicit confirmation for materially destructive/privileged actions; secrets redaction; sensitive screenshot/trace minimization; command and action audit; dependency/license review; secure provider-key storage; no plaintext secrets in repo/logs.

High-risk capabilities require `HIGH_ASSURANCE`, strong tests, independent review, and rollback/roll-forward obligations. Unknown permission state must fail closed.

## Provider Certification Lab security boundary
Certification evidence is security-sensitive because it may influence which specialist stack Hive selects. Competence evidence must never become an alternate permission channel.

- Provider/model output is untrusted data and cannot grade, seal, verify or certify itself.
- Runner and grader identities are host-sealed, role-separated, independence-lineage-separated and endpoint-separated. Logical relabeling cannot substitute for real endpoint separation.
- Host HMAC keys for actor seals, StackSeal, SuiteLineage, TrialReceipts, durable journal records and EvidenceDNA are trusted-host secrets. They must not enter provider prompts, model-visible material, repository content, logs or portable benchmark reports.
- ShadowBench oracle material remains host-side. TrialForge exposes neither plaintext oracle material nor its host oracle digest to the provider runner.
- Trial lineage is reserved before provider execution and is one-shot within the journal authority domain. Unknown/replayed lineage fails closed.
- GradeProof is mandatory before a passing/failing TrialReceipt can be issued.
- Durable chronology is hash-chained/HMAC-authenticated and validated against a host-injected monotonic floor. Signed rollback below that floor is a security failure.
- EvidenceDNA must match the exact sealed profile/StackGenome, repository snapshot, Semantic Twin and SuiteLineage before benchmark evidence may enter certification.
- Contamination signals are negative-only. They may block/lower confidence but cannot increase score, rank or authority.
- Repository semantic extraction remains static/no-exec. Repository text, comments, manifests and schemas are data, not Hive instructions.
- No certification record, benchmark result, Semantic Twin node or provider capability claim may grant a CP-0005 permission, create an execution permit, activate a skill or bypass emergency/takeover controls.

Cross-process/distributed trial reservation and a production secure monotonic anchor are not approved in CP-0013. Production adoption of either requires its own threat model, deterministic/adversarial tests and governed promotion.

## Elite Specialist Forge & Arena security boundary
WO-0014 treats specialist composition, arena evidence and routing as security-sensitive competence metadata, never as execution authority.

- `SpecializationPack`, `SkillGenome`, specialist labels, model/provider names and self-description contain zero permission or rank authority.
- ForgeSeal must verify the sealed AgentProfile and bind the exact StackGenome, repository snapshot, Semantic Repository Twin, trusted SpecializationPack, exact SkillGenome and trusted certification evidence. Unknown/tampered/transplanted context fails closed.
- SkillGenome must fingerprint-match the StackGenome skillset digest before a specialist blueprint can exist. Caller-controlled skill labels cannot transplant competence to another stack.
- ChallengeMorph may vary a trusted ShadowBench challenge only under sealed SuiteLineage. Challenge variants do not create independent mastery when they share one sealed base source lineage.
- Anti-Overfit Horizon protections are enforced again when evidence enters Mastery Lattice. Bypassing the helper cannot manufacture diversity.
- ArenaEvidence is admitted only when GradeProof, challenge/blueprint identity, repository/twin bindings and telemetry verification all match.
- Arena telemetry is non-authoritative until a trusted host-injected verifier accepts it. Cost/latency observations can never relax security, quality or reliability floors.
- Reliability Shadow is negative-only. Operational regressions may block/demote/force recertification but positive observations cannot mint benchmark evidence or rank.
- Pareto Crown directly revalidates AgentProfile authority and exact certification context at final routing time. Critical, policy and tamper incidents block selection before optimization.
- Competence artifacts cannot create CP-0005 permits, activate skills, grant credentials, authorize purchases/billing, expose remote control or bypass emergency/takeover controls.
- Hosted CI remains mock/deterministic. It proves contracts and adversarial invariants only, not the security or elite quality of any real provider stack.

Production attestation for real provider billing/latency/reliability telemetry and durable cross-restart mastery/reputation are not approved in WO-0014. Any future `TelemetrySeal` or `MasteryVault` must receive a separate HIGH_ASSURANCE threat model, rollback protection, adversarial tests and governed promotion before use.

## Desktop shell security boundary — WO-0015 / WO-0016
The desktop shell remains intentionally non-privileged.

- The frontend exposes only the named read/workspace-selection invoke paths governed by the desktop security gate.
- Native read commands accept no arbitrary command, process, shell string, provider credential or desktop-input payload.
- Commands revalidate the caller WebView label as `main`; the declarative capability is also scoped to `main`.
- Tauri capability `desktop-read-only` grants zero plugin permissions; shell/filesystem/process plugins are prohibited by the desktop security gate.
- `choose_workspace` accepts no caller-controlled target/path argument and is initiated by explicit user interaction through the native picker.
- Bounded workspace/Git/evidence observations remain read-only and presentation-only.
- The UI cannot mint or consume CP permits, activate skills, write arbitrary files, inject keyboard/mouse input, access credentials, expose remote control or authorize billing/purchases.
- Unknown/disconnected live subsystems must remain visibly unknown/disconnected rather than being inferred READY.
- Safety actions remain disabled until an actionable trusted session exists.
- The desktop security gate rejects generic process execution, unsafe HTML sinks, extra unapproved invoke sites, nonempty capability permissions, missing lockfiles and Apple-specific font references.

Supply-chain evidence includes npm audit with zero vulnerabilities and RustSec scanning over the locked Cargo graph. RustSec nevertheless reports seven warning-class advisories, including an unsoundness warning in transitive `glib 0.18.5`; these remain explicit dependency debt and the Rust graph is not claimed warning-free.

The current local CSP still permits `style-src 'unsafe-inline'`. That is a known LOW hardening residual, not approval for untrusted HTML/style injection. Stricter CSP requires later validation.

## Runtime observability security boundary — WO-0017
Runtime status is security-sensitive because UI state can mislead a user or future orchestrator even when it carries no direct mutation primitive. WO-0017 therefore treats status as hostile-at-the-boundary presentation data rather than trusted authority.

- `RuntimeStatusSnapshot v1` contains no credentials, raw prompts, model outputs, permits, approval tokens, audit secret material or trusted-host signing keys.
- Status cannot be consumed as authorization. A `READY` label can never grant a CP capability, create a permit, activate a skill, start a provider/model, mutate task state or enable computer use.
- Provider READY means only a concrete bounded catalog observation. It is explicitly distinct from provider reachability/authentication and from CP-0007 VERIFIED capability evidence.
- Permission status must not scrape private Permission & Control Plane sessions/challenges/permits. If no safe public observer exists, the truthful state is UNKNOWN/DISCONNECTED with null counters.
- Canonical provenance is fixed per Hive subsystem and rejects caller-defined provenance labels.
- JSON input is bounded before parse, requires UTF-8, rejects duplicate keys and unknown object fields, enforces exact schema/state/counter/collection bounds and rejects booleans as counters.
- In-memory records also require governed typed `StatusState` values so Python type hints cannot be bypassed at runtime.
- Fake READY provider summaries without concrete observed models fail closed.
- Invalid encode/decode paths reduce only to a fixed generic DEGRADED snapshot; rejected values and exception details are not echoed back into presentation state.
- The safe CLI exports a deterministic disconnected snapshot only. It does not enumerate credentials, invoke providers, execute models, spawn subprocesses or mutate runtime/control-plane state.

WO-0017 introduces no Tauri command and no desktop IPC/process authority. CP-0017 is canonical; live transport/process lifecycle remains separately governed.

## Cross-runtime status IPC security boundary — WO-0018
WO-0018 treats the wire itself as hostile input and freezes it before any runtime process lifecycle is approved.

- Protocol identity is exactly `hive-runtime-status-ipc-v1`; the only operation is `status.snapshot`.
- Request IDs are bounded ASCII identifiers. Request, snapshot and response-envelope byte ceilings are fixed and independently checked.
- Python rejects duplicate keys during parse and both sides require deterministic canonical JSON. Desktop raw-wire admission reserializes the fully validated normalized envelope and requires byte-for-byte canonical equality.
- The lower-level TypeScript semantic object parser is private. Future consumers cannot legitimately bypass the raw response boundary through the public contract API.
- Runtime/provider/task/permission provenance literals are revalidated across the language boundary; transport cannot invent provenance.
- Fake READY providers, duplicate provider/model identity, inconsistent task counters and authoritative-looking permission counters under UNKNOWN/DISCONNECTED fail closed.
- The Python one-shot server receives a prebuilt validated snapshot rather than an observation callback, preventing the protocol primitive from acquiring provider/model/process/task/permission execution authority.
- No error-detail/free-form metadata field exists that could become a secret/exfiltration channel.
- No generic RPC, socket listener, HTTP/WebSocket service, Tauri command or new dependency is introduced.

A valid status envelope is never authorization. It cannot grant a CP capability, create/consume a permit, approve a request, activate a skill, certify a model capability, mutate a task/permission state, access credentials or authorize filesystem/Git/terminal/computer-use action.

CP-0018 canonicalizes only this wire security boundary. It does not prove helper binary authenticity, child-process containment, restart/shutdown policy or desktop supervisor behavior. Those remain later HIGH_ASSURANCE process-boundary concerns and must not be inferred from IPC validity.
