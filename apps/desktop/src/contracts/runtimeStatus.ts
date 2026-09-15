export const RUNTIME_STATUS_PROTOCOL = "hive-runtime-status-ipc-v1" as const;
export const RUNTIME_STATUS_SCHEMA = "hive-runtime-status-v1" as const;
export const MAX_RUNTIME_STATUS_RESPONSE_BYTES = 40_000;

export type RuntimeState = "READY" | "UNKNOWN" | "DISCONNECTED" | "DEGRADED";

export interface RuntimeStatusEnvelope {
  protocol: typeof RUNTIME_STATUS_PROTOCOL;
  requestId: string;
  ok: true;
  snapshot: {
    schema: typeof RUNTIME_STATUS_SCHEMA;
    runtime: { state: RuntimeState; provenance: string; detail: string };
    providers: Array<{ providerId: string; modelIds: string[]; state: RuntimeState }>;
    task: null | { taskId: string; state: string; nodeTotal: number; nodeSucceeded: number; executions: number; failures: number };
    permission: { state: RuntimeState; policyEpoch: number | null; activeSessions: number | null; pendingApprovals: number | null };
  };
}

const STATES = new Set<RuntimeState>(["READY", "UNKNOWN", "DISCONNECTED", "DEGRADED"]);

function record(value: unknown, keys: string[]): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error("expected object");
  const actual = Object.keys(value as Record<string, unknown>).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) throw new Error("unexpected object shape");
  return value as Record<string, unknown>;
}

function text(value: unknown, limit: number): string {
  if (typeof value !== "string" || value.trim().length < 1 || value.trim().length > limit) throw new Error("invalid bounded text");
  return value.trim();
}

function state(value: unknown): RuntimeState {
  if (typeof value !== "string" || !STATES.has(value as RuntimeState)) throw new Error("invalid state");
  return value as RuntimeState;
}

function counter(value: unknown): number {
  if (!Number.isInteger(value) || (value as number) < 0 || (value as number) > 1_000_000) throw new Error("invalid counter");
  return value as number;
}

function nullableCounter(value: unknown): number | null {
  return value === null ? null : counter(value);
}

export function parseRuntimeStatusEnvelope(input: unknown): RuntimeStatusEnvelope {
  const bytes = new TextEncoder().encode(JSON.stringify(input)).byteLength;
  if (bytes > MAX_RUNTIME_STATUS_RESPONSE_BYTES) throw new Error("runtime status response exceeds byte ceiling");
  const root = record(input, ["protocol", "requestId", "ok", "snapshot"]);
  if (root.protocol !== RUNTIME_STATUS_PROTOCOL || root.ok !== true) throw new Error("unsupported runtime status envelope");
  const requestId = text(root.requestId, 64);
  if (!/^[A-Za-z0-9_.:-]+$/.test(requestId)) throw new Error("invalid request id");
  const snapshot = record(root.snapshot, ["schema", "runtime", "providers", "task", "permission"]);
  if (snapshot.schema !== RUNTIME_STATUS_SCHEMA) throw new Error("unsupported runtime status schema");
  const runtime = record(snapshot.runtime, ["state", "provenance", "detail"]);
  const runtimeValue = { state: state(runtime.state), provenance: text(runtime.provenance, 160), detail: text(runtime.detail, 160) };
  if (!Array.isArray(snapshot.providers) || snapshot.providers.length > 16) throw new Error("invalid providers");
  const seenProviders = new Set<string>();
  const providers = snapshot.providers.map((raw) => {
    const provider = record(raw, ["providerId", "modelIds", "state"]);
    const providerId = text(provider.providerId, 80).toLowerCase();
    if (seenProviders.has(providerId)) throw new Error("duplicate provider");
    seenProviders.add(providerId);
    if (!Array.isArray(provider.modelIds) || provider.modelIds.length > 64) throw new Error("invalid models");
    const modelIds = provider.modelIds.map((model) => text(model, 128));
    if (new Set(modelIds).size !== modelIds.length) throw new Error("duplicate model");
    const providerState = state(provider.state);
    if (providerState === "READY" && modelIds.length === 0) throw new Error("fake provider readiness");
    return { providerId, modelIds, state: providerState };
  });
  let task: RuntimeStatusEnvelope["snapshot"]["task"] = null;
  if (snapshot.task !== null) {
    const rawTask = record(snapshot.task, ["taskId", "state", "nodeTotal", "nodeSucceeded", "executions", "failures"]);
    const nodeTotal = counter(rawTask.nodeTotal);
    const nodeSucceeded = counter(rawTask.nodeSucceeded);
    const executions = counter(rawTask.executions);
    const failures = counter(rawTask.failures);
    if (nodeTotal > 256 || nodeSucceeded > nodeTotal || failures > executions) throw new Error("inconsistent task counters");
    task = { taskId: text(rawTask.taskId, 128), state: text(rawTask.state, 32), nodeTotal, nodeSucceeded, executions, failures };
  }
  const rawPermission = record(snapshot.permission, ["state", "policyEpoch", "activeSessions", "pendingApprovals"]);
  const permissionState = state(rawPermission.state);
  const policyEpoch = nullableCounter(rawPermission.policyEpoch);
  const activeSessions = nullableCounter(rawPermission.activeSessions);
  const pendingApprovals = nullableCounter(rawPermission.pendingApprovals);
  if ((permissionState === "UNKNOWN" || permissionState === "DISCONNECTED") && [policyEpoch, activeSessions, pendingApprovals].some((value) => value !== null)) {
    throw new Error("unknown permission state carries counters");
  }
  return {
    protocol: RUNTIME_STATUS_PROTOCOL,
    requestId,
    ok: true,
    snapshot: {
      schema: RUNTIME_STATUS_SCHEMA,
      runtime: runtimeValue,
      providers,
      task,
      permission: { state: permissionState, policyEpoch, activeSessions, pendingApprovals },
    },
  };
}
