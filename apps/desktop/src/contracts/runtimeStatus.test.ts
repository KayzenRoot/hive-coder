import { describe, expect, it } from "vitest";
import { parseRuntimeStatusEnvelope, RUNTIME_STATUS_PROTOCOL, RUNTIME_STATUS_SCHEMA } from "./runtimeStatus";

const disconnected = (): Record<string, any> => ({
  protocol: RUNTIME_STATUS_PROTOCOL,
  requestId: "r-1",
  ok: true,
  snapshot: {
    schema: RUNTIME_STATUS_SCHEMA,
    runtime: { state: "DISCONNECTED", provenance: "hive-runtime-status", detail: "No trusted live runtime observation is connected." },
    providers: [],
    task: null,
    permission: { state: "DISCONNECTED", policyEpoch: null, activeSessions: null, pendingApprovals: null },
  },
});

describe("runtime status IPC contract", () => {
  it("accepts the Python disconnected envelope shape", () => {
    const parsed = parseRuntimeStatusEnvelope(disconnected());
    expect(parsed.snapshot.runtime.state).toBe("DISCONNECTED");
    expect(parsed.snapshot.permission.activeSessions).toBeNull();
  });

  it("rejects unknown fields and protocol drift", () => {
    expect(() => parseRuntimeStatusEnvelope({ ...disconnected(), extra: true })).toThrow();
    expect(() => parseRuntimeStatusEnvelope({ ...disconnected(), protocol: "future" })).toThrow();
  });

  it("rejects fake READY providers", () => {
    const raw = disconnected();
    raw.snapshot.providers = [{ providerId: "opencode-go", modelIds: [], state: "READY" }];
    expect(() => parseRuntimeStatusEnvelope(raw)).toThrow(/readiness/);
  });

  it("rejects authoritative-looking counters on disconnected permission state", () => {
    const raw = disconnected();
    raw.snapshot.permission.policyEpoch = 1;
    expect(() => parseRuntimeStatusEnvelope(raw)).toThrow(/counters/);
  });
});
