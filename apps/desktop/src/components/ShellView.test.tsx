import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { disconnectedSnapshot } from "../contracts/desktopSnapshot";
import { ShellView } from "./ShellView";

describe("ShellView", () => {
  it("renders truthful disconnected state and disabled safety actions", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} />);
    expect(html).toContain("READ-ONLY SHELL");
    expect(html).toContain("DISCONNECTED");
    expect(html).toContain("HCODER-CP-0014");
    expect(html).toContain("Emergency stop");
    expect(html.match(/disabled=""/g)?.length ?? 0).toBeGreaterThanOrEqual(4);
  });

  it("never labels the fallback runtime as ready", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} />);
    expect(html).not.toContain(">Runtime</span><span class=\"state-chip state-chip--ready\"");
  });
});
