import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { disconnectedSnapshot } from "../contracts/desktopSnapshot";
import { ShellView } from "./ShellView";

describe("ShellView", () => {
  it("renders truthful disconnected state and disabled safety actions", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} />);
    expect(html).toContain("TRUSTED READ MODE");
    expect(html).toContain("DISCONNECTED");
    expect(html).toContain("HCODER-CP-0015");
    expect(html).toContain("Emergency stop");
    expect(html.match(/disabled=""/g)?.length ?? 0).toBeGreaterThanOrEqual(8);
  });

  it("never labels the fallback runtime as ready", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} />);
    expect(html).not.toContain(">Runtime</span><span class=\"state-chip state-chip--ready\"");
  });

  it("does not advertise unavailable execution or navigation as active", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} />);
    expect(html).toContain("No execution session attached");
    expect(html).toContain("Execution input unavailable in trusted read mode");
    expect(html).toContain("Open workspace");
    expect(html).not.toContain("Ready for a governed session");
    expect(html).toContain('aria-current="page"');
    expect(html.match(/aria-disabled="true"/g)?.length ?? 0).toBeGreaterThanOrEqual(7);
  });

  it("renders bounded live workspace, Git and evidence facts without enabling Run", () => {
    const snapshot = disconnectedSnapshot();
    snapshot.shell.state = "READY";
    snapshot.workspace = {
      signal: { state: "READY", label: "Workspace", detail: "trusted", provenance: "trusted-workspace-read-v1" },
      selected: true,
      workspaceId: "ws-0000000000000001",
      name: "hive-coder",
      root: "C:/src/hive-coder",
      projectMarkers: ["Git", "Cargo", "Hive Checkpoint"],
      topLevelEntries: 23,
      truncated: false,
    };
    snapshot.git = {
      signal: { state: "READY", label: "Git", detail: "observed", provenance: "git-head-read-v1" },
      repository: true,
      branch: "main",
      head: "0123456789abcdef0123456789abcdef01234567",
      detached: false,
    };
    snapshot.evidence = {
      signal: { state: "READY", label: "Evidence", detail: "observed", provenance: "hive-evidence-read-v1" },
      checkpoint: "HCODER-CP-0015",
      checkpointStatus: "APPROVED",
      evidenceBundles: 4,
      truncated: false,
    };
    const html = renderToStaticMarkup(<ShellView snapshot={snapshot} onChooseWorkspace={() => undefined} />);
    expect(html).toContain("hive-coder");
    expect(html).toContain("C:/src/hive-coder");
    expect(html).toContain("main");
    expect(html).toContain("0123456789ab");
    expect(html).toContain("4 bundles");
    expect(html).toContain("Change workspace");
    expect(html).toContain("Run");
    expect(html).toContain('disabled=""');
  });
});
