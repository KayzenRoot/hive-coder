import { describe, expect, it } from "vitest";
import {
  decodeRuntimeStatusEnvelope,
  encodeRuntimeStatusRequest,
  MAX_RUNTIME_STATUS_RESPONSE_BYTES,
  PERMISSION_CONTROL_PROVENANCE,
  PROVIDER_CATALOG_PROVENANCE,
  RUNTIME_STATUS_PROVENANCE,
  TASK_RUNTIME_PROVENANCE,
} from "./runtimeStatus";

const canonicalDisconnected =
  '{"ok":true,"protocol":"hive-runtime-status-ipc-v1","requestId":"r-1","snapshot":{"permission":{"activeSessions":null,"pendingApprovals":null,"policyEpoch":null,"provenance":"hive-permission-control-plane","state":"DISCONNECTED"},"providers":[],"runtime":{"detail":"No trusted live runtime observation is connected.","provenance":"hive-runtime-status","state":"DISCONNECTED"},"schema":"hive-runtime-status-v1","task":null}}';

function replaceOnce(source: string, search: string, replacement: string): string {
  const index = source.indexOf(search);
  if (index < 0) throw new Error(`fixture token not found: ${search}`);
  return source.slice(0, index) + replacement + source.slice(index + search.length);
}

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

  it("matches Python ensure_ascii wire semantics for Unicode presentation text", () => {
    const unicodeWire = replaceOnce(
      canonicalDisconnected,
      "No trusted live runtime observation is connected.",
      "caf\\u00e9 \\ud83c\\udf6f",
    );
    const parsed = decodeRuntimeStatusEnvelope(unicodeWire);
    expect(parsed.snapshot.runtime.detail).toBe("café 🍯");
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

  it("rejects unknown fields, protocol drift and schema drift through the raw decoder", () => {
    const extra = canonicalDisconnected.replace('{"ok":true,', '{"extra":true,"ok":true,');
    expect(() => decodeRuntimeStatusEnvelope(extra)).toThrow(/shape/);
    expect(() => decodeRuntimeStatusEnvelope(canonicalDisconnected.replace("hive-runtime-status-ipc-v1", "future"))).toThrow(/unsupported/);
    expect(() => decodeRuntimeStatusEnvelope(canonicalDisconnected.replace("hive-runtime-status-v1", "future"))).toThrow(/schema/);
  });

  it("requires canonical provenance for every subsystem", () => {
    const runtime = replaceOnce(
      canonicalDisconnected,
      '"provenance":"hive-runtime-status"',
      '"provenance":"caller"',
    );
    expect(() => decodeRuntimeStatusEnvelope(runtime)).toThrow(/provenance/);

    const permission = replaceOnce(
      canonicalDisconnected,
      '"provenance":"hive-permission-control-plane"',
      '"provenance":"caller"',
    );
    expect(() => decodeRuntimeStatusEnvelope(permission)).toThrow(/provenance/);

    const provider = replaceOnce(
      canonicalDisconnected,
      '"providers":[]',
      '"providers":[{"modelIds":["m-1"],"provenance":"caller","providerId":"opencode-go","state":"READY"}]',
    );
    expect(() => decodeRuntimeStatusEnvelope(provider)).toThrow(/provenance/);

    const task = replaceOnce(
      canonicalDisconnected,
      '"task":null',
      '"task":{"executions":1,"failures":0,"nodeSucceeded":1,"nodeTotal":1,"provenance":"caller","state":"running","taskId":"t-1"}',
    );
    expect(() => decodeRuntimeStatusEnvelope(task)).toThrow(/provenance/);
  });

  it("accepts canonical observed provider and task presentation state", () => {
    let raw = replaceOnce(
      canonicalDisconnected,
      '"providers":[]',
      `"providers":[{"modelIds":["m-1"],"provenance":"${PROVIDER_CATALOG_PROVENANCE}","providerId":"opencode-go","state":"READY"}]`,
    );
    raw = replaceOnce(
      raw,
      '"task":null',
      `"task":{"executions":2,"failures":1,"nodeSucceeded":1,"nodeTotal":2,"provenance":"${TASK_RUNTIME_PROVENANCE}","state":"running","taskId":"t-1"}`,
    );
    const parsed = decodeRuntimeStatusEnvelope(raw);
    expect(parsed.snapshot.providers[0]?.providerId).toBe("opencode-go");
    expect(parsed.snapshot.task?.provenance).toBe(TASK_RUNTIME_PROVENANCE);
  });

  it("rejects fake READY providers and duplicate provider/model identity", () => {
    const fakeReady = replaceOnce(
      canonicalDisconnected,
      '"providers":[]',
      `"providers":[{"modelIds":[],"provenance":"${PROVIDER_CATALOG_PROVENANCE}","providerId":"opencode-go","state":"READY"}]`,
    );
    expect(() => decodeRuntimeStatusEnvelope(fakeReady)).toThrow(/readiness/);

    const duplicateProvider = replaceOnce(
      canonicalDisconnected,
      '"providers":[]',
      `"providers":[{"modelIds":["m-1"],"provenance":"${PROVIDER_CATALOG_PROVENANCE}","providerId":"OpenCode-Go","state":"READY"},{"modelIds":["m-2"],"provenance":"${PROVIDER_CATALOG_PROVENANCE}","providerId":"opencode-go","state":"READY"}]`,
    );
    expect(() => decodeRuntimeStatusEnvelope(duplicateProvider)).toThrow(/duplicate.*provider/);

    const duplicateModel = replaceOnce(
      canonicalDisconnected,
      '"providers":[]',
      `"providers":[{"modelIds":["m-1","m-1"],"provenance":"${PROVIDER_CATALOG_PROVENANCE}","providerId":"opencode-go","state":"READY"}]`,
    );
    expect(() => decodeRuntimeStatusEnvelope(duplicateModel)).toThrow(/duplicate.*model/);
  });

  it("rejects inconsistent task counters", () => {
    const raw = replaceOnce(
      canonicalDisconnected,
      '"task":null',
      `"task":{"executions":1,"failures":2,"nodeSucceeded":3,"nodeTotal":2,"provenance":"${TASK_RUNTIME_PROVENANCE}","state":"running","taskId":"t-1"}`,
    );
    expect(() => decodeRuntimeStatusEnvelope(raw)).toThrow(/task counters/);
  });

  it("rejects authoritative-looking counters on unknown permission state", () => {
    let raw = canonicalDisconnected.replace('"policyEpoch":null', '"policyEpoch":1');
    raw = raw.replace('"state":"DISCONNECTED"', '"state":"UNKNOWN"');
    expect(() => decodeRuntimeStatusEnvelope(raw)).toThrow(/permission state carries counters/);
  });
});
