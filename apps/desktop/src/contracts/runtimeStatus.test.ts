import { describe, expect, it } from "vitest";
import {
  decodeRuntimeStatusEnvelope,
  encodeRuntimeStatusRequest,
  MAX_RUNTIME_STATUS_RESPONSE_BYTES,
  parseRuntimeStatusEnvelope,
  PERMISSION_CONTROL_PROVENANCE,
  PROVIDER_CATALOG_PROVENANCE,
  RUNTIME_STATUS_PROTOCOL,
  RUNTIME_STATUS_PROVENANCE,
  RUNTIME_STATUS_SCHEMA,
  TASK_RUNTIME_PROVENANCE,
} from "./runtimeStatus";

const disconnected = (): Record<string, any> => ({
  ok: true,
  protocol: RUNTIME_STATUS_PROTOCOL,
  requestId: "r-1",
  snapshot: {
    permission: {
      activeSessions: null,
      pendingApprovals: null,
      policyEpoch: null,
      provenance: PERMISSION_CONTROL_PROVENANCE,
      state: "DISCONNECTED",
    },
    providers: [],
    runtime: {
      detail: "No trusted live runtime observation is connected.",
      provenance: RUNTIME_STATUS_PROVENANCE,
      state: "DISCONNECTED",
    },
    schema: RUNTIME_STATUS_SCHEMA,
    task: null,
  },
});

const canonicalDisconnected =
  '{"ok":true,"protocol":"hive-runtime-status-ipc-v1","requestId":"r-1","snapshot":{"permission":{"activeSessions":null,"pendingApprovals":null,"policyEpoch":null,"provenance":"hive-permission-control-plane","state":"DISCONNECTED"},"providers":[],"runtime":{"detail":"No trusted live runtime observation is connected.","provenance":"hive-runtime-status","state":"DISCONNECTED"},"schema":"hive-runtime-status-v1","task":null}}';

describe("runtime status IPC contract", () => {
  it("encodes the only request operation as canonical JSON", () => {
    expect(encodeRuntimeStatusRequest("r-1")).toBe(
      '{"op":"status.snapshot","protocol":"hive-runtime-status-ipc-v1","requestId":"r-1"}',
    );
    expect(() => encodeRuntimeStatusRequest("../unsafe")).toThrow(/request id/);
  });

  it("decodes the canonical Python disconnected envelope", () => {
    const parsed = decodeRuntimeStatusEnvelope(canonicalDisconnected);
    expect(parsed.snapshot.runtime.state).toBe("DISCONNECTED");
    expect(parsed.snapshot.runtime.provenance).toBe(RUNTIME_STATUS_PROVENANCE);
    expect(parsed.snapshot.permission.provenance).toBe(PERMISSION_CONTROL_PROVENANCE);
  });

  it("rejects duplicate and noncanonical wire encodings", () => {
    const duplicate = canonicalDisconnected.replace('{"ok":true,', '{"ok":true,"ok":true,');
    expect(() => decodeRuntimeStatusEnvelope(duplicate)).toThrow(/canonical/);
    expect(() => decodeRuntimeStatusEnvelope(" " + canonicalDisconnected)).toThrow(/canonical/);
  });

  it("rejects oversized raw responses before semantic admission", () => {
    const oversized = '{"padding":"' + "x".repeat(MAX_RUNTIME_STATUS_RESPONSE_BYTES) + '"}';
    expect(() => decodeRuntimeStatusEnvelope(oversized)).toThrow(/byte ceiling/);
  });

  it("rejects unknown fields, protocol drift and schema drift", () => {
    expect(() => parseRuntimeStatusEnvelope({ ...disconnected(), extra: true })).toThrow(/shape/);
    expect(() => parseRuntimeStatusEnvelope({ ...disconnected(), protocol: "future" })).toThrow(/unsupported/);
    const schemaDrift = disconnected();
    schemaDrift.snapshot.schema = "future";
    expect(() => parseRuntimeStatusEnvelope(schemaDrift)).toThrow(/schema/);
  });

  it("requires canonical provenance for every subsystem", () => {
    const runtime = disconnected();
    runtime.snapshot.runtime.provenance = "caller";
    expect(() => parseRuntimeStatusEnvelope(runtime)).toThrow(/provenance/);

    const permission = disconnected();
    permission.snapshot.permission.provenance = "caller";
    expect(() => parseRuntimeStatusEnvelope(permission)).toThrow(/provenance/);

    const provider = disconnected();
    provider.snapshot.providers = [{
      modelIds: ["m-1"],
      providerId: "opencode-go",
      provenance: "caller",
      state: "READY",
    }];
    expect(() => parseRuntimeStatusEnvelope(provider)).toThrow(/provenance/);

    const task = disconnected();
    task.snapshot.task = {
      executions: 1,
      failures: 0,
      nodeSucceeded: 1,
      nodeTotal: 1,
      provenance: "caller",
      state: "running",
      taskId: "t-1",
    };
    expect(() => parseRuntimeStatusEnvelope(task)).toThrow(/provenance/);
  });

  it("accepts canonical observed provider and task presentation state", () => {
    const raw = disconnected();
    raw.snapshot.providers = [{
      modelIds: ["m-1"],
      providerId: "opencode-go",
      provenance: PROVIDER_CATALOG_PROVENANCE,
      state: "READY",
    }];
    raw.snapshot.task = {
      executions: 2,
      failures: 1,
      nodeSucceeded: 1,
      nodeTotal: 2,
      provenance: TASK_RUNTIME_PROVENANCE,
      state: "running",
      taskId: "t-1",
    };
    const parsed = parseRuntimeStatusEnvelope(raw);
    expect(parsed.snapshot.providers[0]?.providerId).toBe("opencode-go");
    expect(parsed.snapshot.task?.provenance).toBe(TASK_RUNTIME_PROVENANCE);
  });

  it("rejects fake READY providers and duplicate provider/model identity", () => {
    const fakeReady = disconnected();
    fakeReady.snapshot.providers = [{
      modelIds: [],
      providerId: "opencode-go",
      provenance: PROVIDER_CATALOG_PROVENANCE,
      state: "READY",
    }];
    expect(() => parseRuntimeStatusEnvelope(fakeReady)).toThrow(/readiness/);

    const duplicateProvider = disconnected();
    duplicateProvider.snapshot.providers = [
      { modelIds: ["m-1"], providerId: "OpenCode-Go", provenance: PROVIDER_CATALOG_PROVENANCE, state: "READY" },
      { modelIds: ["m-2"], providerId: "opencode-go", provenance: PROVIDER_CATALOG_PROVENANCE, state: "READY" },
    ];
    expect(() => parseRuntimeStatusEnvelope(duplicateProvider)).toThrow(/duplicate.*provider/);

    const duplicateModel = disconnected();
    duplicateModel.snapshot.providers = [
      { modelIds: ["m-1", "m-1"], providerId: "opencode-go", provenance: PROVIDER_CATALOG_PROVENANCE, state: "READY" },
    ];
    expect(() => parseRuntimeStatusEnvelope(duplicateModel)).toThrow(/duplicate.*model/);
  });

  it("rejects inconsistent task counters", () => {
    const raw = disconnected();
    raw.snapshot.task = {
      executions: 1,
      failures: 2,
      nodeSucceeded: 3,
      nodeTotal: 2,
      provenance: TASK_RUNTIME_PROVENANCE,
      state: "running",
      taskId: "t-1",
    };
    expect(() => parseRuntimeStatusEnvelope(raw)).toThrow(/task counters/);
  });

  it("rejects authoritative-looking counters on unknown permission state", () => {
    const raw = disconnected();
    raw.snapshot.permission.state = "UNKNOWN";
    raw.snapshot.permission.policyEpoch = 1;
    expect(() => parseRuntimeStatusEnvelope(raw)).toThrow(/permission state carries counters/);
  });
});
