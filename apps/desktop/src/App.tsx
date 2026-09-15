import { useEffect, useState } from "react";
import { ShellView } from "./components/ShellView";
import { type DesktopSnapshot, disconnectedSnapshot } from "./contracts/desktopSnapshot";
import type { RuntimeStatusEnvelope } from "./contracts/runtimeStatus";
import { chooseWorkspace, loadDesktopSnapshot, loadRuntimeStatusEnvelope } from "./lib/desktopBridge";

export default function App() {
  const [snapshot, setSnapshot] = useState<DesktopSnapshot>(() => disconnectedSnapshot());
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatusEnvelope | null>(null);
  const [choosingWorkspace, setChoosingWorkspace] = useState(false);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void loadDesktopSnapshot().then((next) => {
      if (active) setSnapshot(next);
    });
    void loadRuntimeStatusEnvelope().then((next) => {
      if (active) setRuntimeStatus(next);
    });
    return () => { active = false; };
  }, []);

  async function handleChooseWorkspace() {
    if (choosingWorkspace) return;
    setChoosingWorkspace(true);
    setWorkspaceError(null);
    try {
      setSnapshot(await chooseWorkspace());
    } catch {
      setWorkspaceError("The selected workspace could not be admitted into the trusted read-only boundary.");
    } finally {
      setChoosingWorkspace(false);
    }
  }

  return (
    <ShellView
      snapshot={snapshot}
      runtimeStatus={runtimeStatus}
      choosingWorkspace={choosingWorkspace}
      workspaceError={workspaceError}
      onChooseWorkspace={handleChooseWorkspace}
    />
  );
}
