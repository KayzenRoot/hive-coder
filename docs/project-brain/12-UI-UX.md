# UI/UX — Hive Coder

## Direction
Hive Coder should feel premium, calm and desktop-native: clear hierarchy, generous spacing, restrained translucency, smooth motion and high information density without visual noise.

## Identity rule
The experience may draw inspiration from qualities associated with modern macOS interfaces, but must use original Hive visual identity, icons, illustrations, naming and interaction assets. Do not ship Apple proprietary assets, trademarks, SF Symbols or copied application chrome.

## Core surfaces
Workspace/project switcher; conversation/task surface; plan/execution timeline; code/diff/terminal views; live computer-use surface; permissions/action center; model/provider selector; Git/PR/evidence state; settings.

## Safety UX
Computer-use state must always be visible. Provide obvious Pause/Emergency Stop/Take Control affordances. Sensitive/destructive actions surface explicit risk and approval state. Permission denial must remain understandable and recoverable.

## WO-0015 first-shell candidate
The first promoted shell intentionally implements only the substrate and truthful read model, not all roadmap surfaces.

- Workspace is the only active navigation destination in this slice.
- Tasks, Code, Computer and Evidence remain visibly present but disabled until corresponding governed implementations exist.
- The central task/composer surface explicitly states that no execution session is attached and Run remains unavailable in read-only mode.
- The right-side System Truth inspector renders state with explicit provenance. Runtime/provider/Git/evidence/permission signals remain UNKNOWN/DISCONNECTED unless a live governed adapter provides evidence.
- Pause, Emergency Stop and Take Control remain visible for safety discoverability but disabled without an actionable trusted session.
- `HiveMark` and the visual system are original Hive assets. Apple-specific font references are prohibited by the desktop security gate in addition to the existing prohibition on proprietary Apple visual assets.
- The desktop shell uses a premium dark/translucent information-dense composition while retaining native Windows window decoration in this increment.

## Visual evidence status
The Windows release executable builds and passes launch smoke. Screenshot/pixel-fidelity regression, accessibility automation, motion validation, responsive small-window validation and full native interaction E2E are still unproven and must not be inferred from the launch smoke.

Final design tokens/component-library promotion beyond this foundation requires later visual validation evidence and the normal governed Work Order flow.
