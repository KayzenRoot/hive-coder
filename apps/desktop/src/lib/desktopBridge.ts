import { invoke } from "@tauri-apps/api/core";
import {
  type DesktopSnapshot,
  disconnectedSnapshot,
  parseDesktopSnapshot,
} from "../contracts/desktopSnapshot";

const SNAPSHOT_COMMAND = "get_desktop_snapshot" as const;

export async function loadDesktopSnapshot(): Promise<DesktopSnapshot> {
  try {
    const raw: unknown = await invoke(SNAPSHOT_COMMAND);
    return parseDesktopSnapshot(raw);
  } catch {
    return disconnectedSnapshot();
  }
}
