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
    snapshot.runtime.detail = "x".repeat(321);
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/runtime.detail/);
  });

  it("rejects schema drift", () => {
    const snapshot = { ...disconnectedSnapshot(), schemaVersion: 3 };
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/unsupported/);
  });

  it("rejects selected workspace without application-owned identity", () => {
    const snapshot = disconnectedSnapshot();
    snapshot.workspace.selected = true;
    snapshot.workspace.name = "demo";
    snapshot.workspace.root = "C:/demo";
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/trusted identity/);
  });

  it("rejects Git identity on a non-repository state", () => {
    const snapshot = disconnectedSnapshot();
    snapshot.git.head = "0123456789abcdef0123456789abcdef01234567";
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/non-repository/);
  });

  it("rejects malformed Git object identity", () => {
    const snapshot = disconnectedSnapshot();
    snapshot.git.repository = true;
    snapshot.git.head = "not-an-object-id";
    expect(() => parseDesktopSnapshot(snapshot)).toThrow(/git.head/);
  });
});
