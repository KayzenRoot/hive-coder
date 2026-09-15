import { invoke } from "@tauri-apps/api/core";
import {
  type DesktopSnapshot,
  disconnectedSnapshot,
  parseDesktopSnapshot,
} from "../contracts/desktopSnapshot";
import { decodeRuntimeStatusEnvelope, type RuntimeStatusEnvelope } from "../contracts/runtimeStatus";

const SNAPSHOT_COMMAND = "get_desktop_snapshot" as const;
const CHOOSE_WORKSPACE_COMMAND = "choose_workspace" as const;
const RUNTIME_STATUS_COMMAND = "get_runtime_status_envelope" as const;

export async function loadDesktopSnapshot(): Promise<DesktopSnapshot> {
  try {
    const raw: unknown = await invoke(SNAPSHOT_COMMAND);
    return parseDesktopSnapshot(raw);
  } catch {
    return disconnectedSnapshot();
  }
}

export async function chooseWorkspace(): Promise<DesktopSnapshot> {
  const raw: unknown = await invoke(CHOOSE_WORKSPACE_COMMAND);
  return parseDesktopSnapshot(raw);
}

export async function loadRuntimeStatusEnvelope(): Promise<RuntimeStatusEnvelope | null> {
  try {
    const raw: unknown = await invoke(RUNTIME_STATUS_COMMAND);
    if (typeof raw !== "string") return null;
    return decodeRuntimeStatusEnvelope(raw);
  } catch {
    return null;
  }
}
