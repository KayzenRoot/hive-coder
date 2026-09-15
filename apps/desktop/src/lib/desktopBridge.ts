import { invoke } from "@tauri-apps/api/core";
import {
  type DesktopSnapshot,
  disconnectedSnapshot,
  parseDesktopSnapshot,
} from "../contracts/desktopSnapshot";

const SNAPSHOT_COMMAND = "get_desktop_snapshot" as const;
const CHOOSE_WORKSPACE_COMMAND = "choose_workspace" as const;

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
