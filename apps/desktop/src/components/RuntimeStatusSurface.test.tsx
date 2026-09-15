import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { disconnectedSnapshot } from "../contracts/desktopSnapshot";
import type { RuntimeStatusEnvelope } from "../contracts/runtimeStatus";
import { ShellView } from "./ShellView";

const liveStatus: RuntimeStatusEnvelope = {
  ok: true,
  protocol: "hive-runtime-status-ipc-v1",
  requestId: "desktop-runtime",
  snapshot: {
    permission: {
      activeSessions: null,
      pendingApprovals: null,
      policyEpoch: null,
      provenance: "hive-permission-control-plane",
      state: "UNKNOWN",
    },
    providers: [{
      modelIds: ["fixture-model"],
      providerId: "opencode-go",
      provenance: "hive-provider-catalog",
      state: "READY",
    }],
    runtime: {
      detail: "Runtime observer connected.",
      provenance: "hive-runtime-status",
      state: "READY",
    },
    schema: "hive-runtime-status-v1",
    task: {
      executions: 1,
      failures: 0,
      nodeSucceeded: 1,
      nodeTotal: 3,
      provenance: "hive-agent-task-runtime",
      state: "running",
      taskId: "task-20",
    },
  },
};

describe("Runtime System Truth surface", () => {
  it("renders live read-only runtime/provider/task truth without enabling mutation", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} runtimeStatus={liveStatus} />);
    expect(html).toContain("Runtime observer connected.");
    expect(html).toContain("1 provider / 1 observed model");
    expect(html).toContain("task-20 · running");
    expect(html).toContain("1/3 nodes succeeded");
    expect(html).toContain("Mutation remains unavailable");
    expect(html).toContain("hive-runtime-status");
    expect(html).toContain("hive-provider-catalog");
    expect(html).toContain("hive-permission-control-plane");
    expect(html).toContain("Emergency stop");
    expect(html.match(/disabled=""/g)?.length ?? 0).toBeGreaterThanOrEqual(8);
  });

  it("keeps disconnected presentation when no live envelope is available", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} runtimeStatus={null} />);
    expect(html).toContain("DISCONNECTED");
    expect(html).toContain("No execution session attached");
    expect(html).toContain("Execution input unavailable in trusted read mode");
  });
});
