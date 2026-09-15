import type { DesktopSnapshot, OperationalState, StatusSignal } from "../contracts/desktopSnapshot";
import { HiveMark } from "./HiveMark";

const NAV_ITEMS = ["Workspace", "Tasks", "Code", "Computer", "Evidence"] as const;

function StateDot({ state }: { state: OperationalState }) {
  return <span className={`state-dot state-dot--${state.toLowerCase()}`} aria-hidden="true" />;
}

function StatusCard({ signal }: { signal: StatusSignal }) {
  return (
    <article className="status-card">
      <div className="status-card__head">
        <span>{signal.label}</span>
        <span className={`state-chip state-chip--${signal.state.toLowerCase()}`}>
          <StateDot state={signal.state} />
          {signal.state}
        </span>
      </div>
      <p>{signal.detail}</p>
      <span className="status-card__provenance">{signal.provenance}</span>
    </article>
  );
}

function SafetyButton({ label, enabled, kind = "default" }: { label: string; enabled: boolean; kind?: "default" | "danger" }) {
  return (
    <button className={`safety-button safety-button--${kind}`} type="button" disabled={!enabled} aria-disabled={!enabled}>
      {label}
    </button>
  );
}

export function ShellView({ snapshot }: { snapshot: DesktopSnapshot }) {
  const statusSignals = [snapshot.runtime, snapshot.provider, snapshot.git, snapshot.evidence, snapshot.permission];

  return (
    <main className="app-shell">
      <aside className="rail" aria-label="Primary navigation">
        <div className="rail__brand"><HiveMark compact /></div>
        <nav className="rail__nav">
          {NAV_ITEMS.map((item, index) => {
            const active = index === 0;
            return (
              <button
                key={item}
                className={active ? "rail-button rail-button--active" : "rail-button"}
                type="button"
                disabled={!active}
                aria-disabled={!active}
                aria-current={active ? "page" : undefined}
              >
                <span className="rail-button__glyph" aria-hidden="true">{item.slice(0, 1)}</span>
                <span>{item}</span>
              </button>
            );
          })}
        </nav>
        <div className="rail__footer"><span className="avatar">K</span></div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <div className="eyebrow">HIVE WORKSPACE</div>
            <h1>{snapshot.product.name}</h1>
          </div>
          <div className="topbar__meta">
            <span className="read-only-pill"><span className="read-only-pill__dot" />READ-ONLY SHELL</span>
            <span className="checkpoint">BASE {snapshot.product.baselineCheckpoint}</span>
          </div>
        </header>

        <div className="content-grid">
          <section className="project-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">CURRENT WORKSPACE</span>
                <h2>Hive Coder</h2>
              </div>
              <span className={`state-chip state-chip--${snapshot.shell.state.toLowerCase()}`}>
                <StateDot state={snapshot.shell.state} />
                {snapshot.shell.state}
              </span>
            </div>

            <div className="project-card">
              <div className="project-card__top">
                <HiveMark />
                <div>
                  <span className="project-card__label">Desktop foundation</span>
                  <h3>Safe Workspace Read Model</h3>
                </div>
              </div>
              <p>
                This first vertical slice exposes only bounded presentation state. Runtime mutations, shell commands,
                computer input and credentials remain outside this UI boundary.
              </p>
              <div className="mini-grid">
                <div><span>Version</span><strong>{snapshot.product.version}</strong></div>
                <div><span>Schema</span><strong>DesktopSnapshot v{snapshot.schemaVersion}</strong></div>
                <div><span>Authority</span><strong>Read only</strong></div>
              </div>
            </div>

            <div className="task-surface">
              <div className="task-surface__glow" />
              <span className="section-kicker">TASK / CONVERSATION</span>
              <h3>No execution session attached</h3>
              <p>
                Task execution is intentionally unavailable in this read-only desktop increment. Connective and
                mutating workflows arrive only through later approved application boundaries.
              </p>
              <div className="composer" aria-label="Inactive task composer">
                <span>Task input unavailable in read-only mode</span>
                <button type="button" disabled>Run</button>
              </div>
            </div>
          </section>

          <aside className="inspector" aria-label="System inspector">
            <div className="inspector__heading">
              <div>
                <span className="section-kicker">SYSTEM TRUTH</span>
                <h2>Inspector</h2>
              </div>
              <span className="inspector__pulse" aria-hidden="true" />
            </div>
            <div className="status-stack">
              {statusSignals.map((signal) => <StatusCard key={signal.label} signal={signal} />)}
            </div>
          </aside>
        </div>

        <footer className="safety-bar" aria-label="Safety controls">
          <div className="safety-bar__copy">
            <span className={snapshot.safety.actionableSession ? "safety-orb safety-orb--live" : "safety-orb"} aria-hidden="true" />
            <div>
              <strong>Safety control plane</strong>
              <span>{snapshot.safety.detail}</span>
            </div>
          </div>
          <div className="safety-actions">
            <SafetyButton label="Pause" enabled={snapshot.safety.pause} />
            <SafetyButton label="Emergency stop" enabled={snapshot.safety.emergencyStop} kind="danger" />
            <SafetyButton label="Take control" enabled={snapshot.safety.takeControl} />
          </div>
        </footer>
      </section>
    </main>
  );
}
