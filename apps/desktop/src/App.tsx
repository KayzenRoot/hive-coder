import { useEffect, useState } from "react";
import { ShellView } from "./components/ShellView";
import { type DesktopSnapshot, disconnectedSnapshot } from "./contracts/desktopSnapshot";
import { loadDesktopSnapshot } from "./lib/desktopBridge";

export default function App() {
  const [snapshot, setSnapshot] = useState<DesktopSnapshot>(() => disconnectedSnapshot());

  useEffect(() => {
    let active = true;
    void loadDesktopSnapshot().then((next) => {
      if (active) setSnapshot(next);
    });
    return () => { active = false; };
  }, []);

  return <ShellView snapshot={snapshot} />;
}
