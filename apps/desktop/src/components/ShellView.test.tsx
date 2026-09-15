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
    expect(html.match(/disabled=""/g)?.length ?? 0).toBeGreaterThanOrEqual(8);
  });

  it("never labels the fallback runtime as ready", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} />);
    expect(html).not.toContain(">Runtime</span><span class=\"state-chip state-chip--ready\"");
  });

  it("does not advertise unavailable task execution or navigation as active", () => {
    const html = renderToStaticMarkup(<ShellView snapshot={disconnectedSnapshot()} />);
    expect(html).toContain("No execution session attached");
    expect(html).toContain("Task input unavailable in read-only mode");
    expect(html).not.toContain("Ready for a governed session");
    expect(html).toContain('aria-current="page"');
    expect(html.match(/aria-disabled="true"/g)?.length ?? 0).toBeGreaterThanOrEqual(7);
  });
});
