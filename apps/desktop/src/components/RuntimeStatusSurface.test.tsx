import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { disconnectedSnapshot } from "../contracts/desktopSnapshot";
import type { RuntimeStatusEnvelope } from "../contracts/runtimeStatus";
import { ShellView } from "./ShellView";

const liveStatus: RuntimeStatusEnvelope = {
  protocol: "hive-runtime-status-ipc-v1",
  requestId: "desktop-runtime",
  ok: true,
  snapshot: {
    schema: "hive-runtime-status-v1",
    runtime: { state: "READY", provenance: "fixture-runtime", detail: "Runtime observer connected." },
    providers: [{ providerId: "opencode-go", modelIds: ["fixture-model"], state: "READY" }],
    task: { taskId: "task-20", state: "running", nodeTotal: 3, nodeSucceeded: 1, executions: 1, failures: 0 },
    permission: { state: "UNKNOWN", policyEpoch: null, activeSessions: null, pendingApprovals: null },
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
    expect(html).toContain("Emergency stop");
    expect(html.match(/disabled=""/g)?.length ?? 0).toBeGreaterThanOrEqual(8);
  });
});
