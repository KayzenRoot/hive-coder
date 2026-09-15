import { describe, expect, it } from "vitest";
import {
  DESKTOP_SNAPSHOT_SCHEMA_VERSION,
  disconnectedSnapshot,
  parseDesktopSnapshot,
} from "./desktopSnapshot";

describe("DesktopSnapshot contract", () => {
  it("accepts the bounded fallback shape", () => {
    const snapshot = disconnectedSnapshot();
    expect(parseDesktopSnapshot(snapshot)).toEqual(snapshot);
    expect(snapshot.schemaVersion).toBe(DESKTOP_SNAPSHOT_SCHEMA_VERSION);
  });

  it("rejects unknown states", () => {
    const snapshot = disconnectedSnapshot() as unknown as Record<string, unknown>;
    snapshot.runtime = {
      state: "MAGIC_READY",
      label: "Runtime",
      detail: "invented",
      provenance: "caller",
    };
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/runtime.state/);
  });

  it("rejects safety authority without an actionable session", () => {
    const snapshot = disconnectedSnapshot();
    snapshot.safety.pause = true;
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/actionable session/);
  });

  it("rejects unbounded presentation strings", () => {
    const snapshot = disconnectedSnapshot();
    snapshot.runtime.detail = "x".repeat(241);
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/runtime.detail/);
  });

  it("rejects schema drift", () => {
    const snapshot = { ...disconnectedSnapshot(), schemaVersion: 2 };
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/unsupported/);
  });
});
