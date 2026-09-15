export const RUNTIME_STATUS_PROTOCOL = "hive-runtime-status-ipc-v1" as const;
export const RUNTIME_STATUS_OPERATION = "status.snapshot" as const;
export const RUNTIME_STATUS_SCHEMA = "hive-runtime-status-v1" as const;

export const RUNTIME_STATUS_PROVENANCE = "hive-runtime-status" as const;
export const PROVIDER_CATALOG_PROVENANCE = "hive-provider-catalog" as const;
export const TASK_RUNTIME_PROVENANCE = "hive-agent-task-runtime" as const;
export const PERMISSION_CONTROL_PROVENANCE = "hive-permission-control-plane" as const;

export const MAX_RUNTIME_STATUS_REQUEST_BYTES = 512;
export const MAX_RUNTIME_STATUS_SNAPSHOT_BYTES = 32_768;
export const MAX_RUNTIME_STATUS_RESPONSE_BYTES = MAX_RUNTIME_STATUS_SNAPSHOT_BYTES + 256;
export const MAX_RUNTIME_STATUS_PROVIDERS = 16;
export const MAX_RUNTIME_STATUS_MODELS_PER_PROVIDER = 64;
export const MAX_RUNTIME_STATUS_TASK_NODES = 256;
export const MAX_RUNTIME_STATUS_COUNTER = 1_000_000;

export type RuntimeState = "READY" | "UNKNOWN" | "DISCONNECTED" | "DEGRADED";

export interface RuntimeStatusRequest {
  op: typeof RUNTIME_STATUS_OPERATION;
  protocol: typeof RUNTIME_STATUS_PROTOCOL;
  requestId: string;
}

export interface RuntimeStatusEnvelope {
  ok: true;
  protocol: typeof RUNTIME_STATUS_PROTOCOL;
  requestId: string;
  snapshot: {
    permission: {
      activeSessions: number | null;
      pendingApprovals: number | null;
      policyEpoch: number | null;
      provenance: typeof PERMISSION_CONTROL_PROVENANCE;
      state: RuntimeState;
    };
    providers: Array<{
      modelIds: string[];
      providerId: string;
      provenance: typeof PROVIDER_CATALOG_PROVENANCE;
      state: RuntimeState;
    }>;
    runtime: {
      detail: string;
      provenance: typeof RUNTIME_STATUS_PROVENANCE;
      state: RuntimeState;
    };
    schema: typeof RUNTIME_STATUS_SCHEMA;
    task: null | {
      executions: number;
      failures: number;
      nodeSucceeded: number;
      nodeTotal: number;
      provenance: typeof TASK_RUNTIME_PROVENANCE;
      state: string;
      taskId: string;
    };
  };
}

const STATES = new Set<RuntimeState>(["READY", "UNKNOWN", "DISCONNECTED", "DEGRADED"]);
const REQUEST_ID = /^[A-Za-z0-9_.:-]{1,64}$/;

function byteLength(value: string): number {
  return new TextEncoder().encode(value).byteLength;
}

function sortJson(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortJson);
  if (typeof value === "object" && value !== null) {
    const source = value as Record<string, unknown>;
    const sorted: Record<string, unknown> = {};
    for (const key of Object.keys(source).sort()) sorted[key] = sortJson(source[key]);
    return sorted;
  }
  return value;
}

function asciiEscapeJson(json: string): string {
  let result = "";
  for (const character of json) {
    const codePoint = character.codePointAt(0);
    if (codePoint === undefined || codePoint <= 0x7f) {
      result += character;
      continue;
    }
    if (codePoint <= 0xffff) {
      result += `\\u${codePoint.toString(16).padStart(4, "0")}`;
      continue;
    }
    const scalar = codePoint - 0x10000;
    const high = 0xd800 + (scalar >> 10);
    const low = 0xdc00 + (scalar & 0x3ff);
    result += `\\u${high.toString(16).padStart(4, "0")}\\u${low.toString(16).padStart(4, "0")}`;
  }
  return result;
}

function canonicalJson(value: unknown): string {
  const encoded = JSON.stringify(sortJson(value));
  if (encoded === undefined) throw new Error("runtime status value is not JSON serializable");
  return asciiEscapeJson(encoded);
}

function record(value: unknown, keys: string[]): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error("expected object");
  const actual = Object.keys(value as Record<string, unknown>).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new Error("unexpected runtime status object shape");
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, limit: number): string {
  if (typeof value !== "string") throw new Error("invalid bounded runtime status text");
  const normalized = value.trim();
  if (Array.from(normalized).length < 1 || Array.from(normalized).length > limit) {
    throw new Error("invalid bounded runtime status text");
  }
  return normalized;
}

function requestId(value: unknown): string {
  if (typeof value !== "string" || !REQUEST_ID.test(value)) throw new Error("invalid runtime status request id");
  return value;
}

function state(value: unknown): RuntimeState {
  if (typeof value !== "string" || !STATES.has(value as RuntimeState)) throw new Error("invalid runtime status state");
  return value as RuntimeState;
}

function counter(value: unknown, maximum = MAX_RUNTIME_STATUS_COUNTER): number {
  if (!Number.isInteger(value) || (value as number) < 0 || (value as number) > maximum) {
    throw new Error("invalid runtime status counter");
  }
  return value as number;
}

function nullableCounter(value: unknown): number | null {
  return value === null ? null : counter(value);
}

function provenance<T extends string>(value: unknown, expected: T): T {
  if (text(value, 160) !== expected) throw new Error("invalid runtime status provenance");
  return expected;
}

export function encodeRuntimeStatusRequest(id: string): string {
  const normalizedId = requestId(id);
  const request: RuntimeStatusRequest = {
    op: RUNTIME_STATUS_OPERATION,
    protocol: RUNTIME_STATUS_PROTOCOL,
    requestId: normalizedId,
  };
  const encoded = canonicalJson(request);
  if (byteLength(encoded) > MAX_RUNTIME_STATUS_REQUEST_BYTES) throw new Error("runtime status request exceeds byte ceiling");
  return encoded;
}

function parseRuntimeStatusEnvelope(input: unknown): RuntimeStatusEnvelope {
  const root = record(input, ["ok", "protocol", "requestId", "snapshot"]);
  if (root.protocol !== RUNTIME_STATUS_PROTOCOL || root.ok !== true) throw new Error("unsupported runtime status envelope");
  const normalizedRequestId = requestId(root.requestId);

  const snapshot = record(root.snapshot, ["permission", "providers", "runtime", "schema", "task"]);
  if (snapshot.schema !== RUNTIME_STATUS_SCHEMA) throw new Error("unsupported runtime status schema");

  const rawRuntime = record(snapshot.runtime, ["detail", "provenance", "state"]);
  const runtime = {
    detail: text(rawRuntime.detail, 160),
    provenance: provenance(rawRuntime.provenance, RUNTIME_STATUS_PROVENANCE),
    state: state(rawRuntime.state),
  };

  if (!Array.isArray(snapshot.providers) || snapshot.providers.length > MAX_RUNTIME_STATUS_PROVIDERS) {
    throw new Error("invalid runtime status providers");
  }
  const seenProviders = new Set<string>();
  const providers = snapshot.providers.map((rawProvider) => {
    const provider = record(rawProvider, ["modelIds", "providerId", "provenance", "state"]);
    const providerId = text(provider.providerId, 80).toLowerCase();
    if (seenProviders.has(providerId)) throw new Error("duplicate runtime status provider");
    seenProviders.add(providerId);
    if (!Array.isArray(provider.modelIds) || provider.modelIds.length > MAX_RUNTIME_STATUS_MODELS_PER_PROVIDER) {
      throw new Error("invalid runtime status models");
    }
    const modelIds = provider.modelIds.map((model) => text(model, 128));
    if (new Set(modelIds).size !== modelIds.length) throw new Error("duplicate runtime status model");
    const providerState = state(provider.state);
    if (providerState === "READY" && modelIds.length === 0) throw new Error("fake provider readiness");
    return {
      modelIds,
      providerId,
      provenance: provenance(provider.provenance, PROVIDER_CATALOG_PROVENANCE),
      state: providerState,
    };
  });

  let task: RuntimeStatusEnvelope["snapshot"]["task"] = null;
  if (snapshot.task !== null) {
    const rawTask = record(snapshot.task, ["executions", "failures", "nodeSucceeded", "nodeTotal", "provenance", "state", "taskId"]);
    const nodeTotal = counter(rawTask.nodeTotal, MAX_RUNTIME_STATUS_TASK_NODES);
    const nodeSucceeded = counter(rawTask.nodeSucceeded, MAX_RUNTIME_STATUS_TASK_NODES);
    const executions = counter(rawTask.executions);
    const failures = counter(rawTask.failures);
    if (nodeSucceeded > nodeTotal || failures > executions) throw new Error("inconsistent runtime status task counters");
    task = {
      executions,
      failures,
      nodeSucceeded,
      nodeTotal,
      provenance: provenance(rawTask.provenance, TASK_RUNTIME_PROVENANCE),
      state: text(rawTask.state, 32),
      taskId: text(rawTask.taskId, 128),
    };
  }

  const rawPermission = record(snapshot.permission, ["activeSessions", "pendingApprovals", "policyEpoch", "provenance", "state"]);
  const permissionState = state(rawPermission.state);
  const activeSessions = nullableCounter(rawPermission.activeSessions);
  const pendingApprovals = nullableCounter(rawPermission.pendingApprovals);
  const policyEpoch = nullableCounter(rawPermission.policyEpoch);
  if ((permissionState === "UNKNOWN" || permissionState === "DISCONNECTED") && [activeSessions, pendingApprovals, policyEpoch].some((value) => value !== null)) {
    throw new Error("unknown permission state carries counters");
  }

  const normalized: RuntimeStatusEnvelope = {
    ok: true,
    protocol: RUNTIME_STATUS_PROTOCOL,
    requestId: normalizedRequestId,
    snapshot: {
      permission: {
        activeSessions,
        pendingApprovals,
        policyEpoch,
        provenance: provenance(rawPermission.provenance, PERMISSION_CONTROL_PROVENANCE),
        state: permissionState,
      },
      providers,
      runtime,
      schema: RUNTIME_STATUS_SCHEMA,
      task,
    },
  };

  if (byteLength(canonicalJson(normalized.snapshot)) > MAX_RUNTIME_STATUS_SNAPSHOT_BYTES) {
    throw new Error("runtime status snapshot exceeds byte ceiling");
  }
  return normalized;
}

export function decodeRuntimeStatusEnvelope(raw: string): RuntimeStatusEnvelope {
  if (typeof raw !== "string" || raw.length === 0 || byteLength(raw) > MAX_RUNTIME_STATUS_RESPONSE_BYTES) {
    throw new Error("runtime status response exceeds byte ceiling");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error("invalid runtime status response JSON");
  }
  const normalized = parseRuntimeStatusEnvelope(parsed);
  if (raw !== canonicalJson(normalized)) {
    throw new Error("runtime status response must use canonical JSON encoding");
  }
  return normalized;
}
