import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  invoke: vi.fn(),
}));

vi.mock("@tauri-apps/api/core", () => ({
  invoke: mocks.invoke,
}));

import { loadRuntimeStatusEnvelope } from "./desktopBridge";

const canonicalDisconnected =
  '{"ok":true,"protocol":"hive-runtime-status-ipc-v1","requestId":"desktop-runtime","snapshot":{"permission":{"activeSessions":null,"pendingApprovals":null,"policyEpoch":null,"provenance":"hive-permission-control-plane","state":"DISCONNECTED"},"providers":[],"runtime":{"detail":"No trusted live runtime observation is connected.","provenance":"hive-runtime-status","state":"DISCONNECTED"},"schema":"hive-runtime-status-v1","task":null}}';

describe("desktop runtime status bridge", () => {
  beforeEach(() => {
    mocks.invoke.mockReset();
  });

  it("uses the named argument-free command and admits only canonical raw wire", async () => {
    mocks.invoke.mockResolvedValue(canonicalDisconnected);

    const envelope = await loadRuntimeStatusEnvelope();

    expect(mocks.invoke).toHaveBeenCalledTimes(1);
    expect(mocks.invoke).toHaveBeenCalledWith("get_runtime_status_envelope");
    expect(envelope?.requestId).toBe("desktop-runtime");
    expect(envelope?.snapshot.runtime.state).toBe("DISCONNECTED");
  });

  it("fails closed to no live status for malformed or noncanonical wire", async () => {
    mocks.invoke.mockResolvedValue(" " + canonicalDisconnected);
    await expect(loadRuntimeStatusEnvelope()).resolves.toBeNull();

    mocks.invoke.mockResolvedValue('{"protocol":"hive-runtime-status-ipc-v1"}');
    await expect(loadRuntimeStatusEnvelope()).resolves.toBeNull();
  });

  it("fails closed for non-string transport results and invoke failures", async () => {
    mocks.invoke.mockResolvedValue({ ok: true });
    await expect(loadRuntimeStatusEnvelope()).resolves.toBeNull();

    mocks.invoke.mockRejectedValue(new Error("sidecar unavailable"));
    await expect(loadRuntimeStatusEnvelope()).resolves.toBeNull();
  });
});
