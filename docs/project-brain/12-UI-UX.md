# UI/UX — Hive Coder

## Direction
Hive Coder should feel premium, calm and desktop-native: clear hierarchy, generous spacing, restrained translucency, smooth motion and high information density without visual noise.

## Identity rule
The experience may draw inspiration from qualities associated with modern macOS interfaces, but must use original Hive visual identity, icons, illustrations, naming and interaction assets. Do not ship Apple proprietary assets, trademarks, SF Symbols or copied application chrome.

## Core surfaces
Workspace/project switcher; conversation/task surface; plan/execution timeline; code/diff/terminal views; live computer-use surface; permissions/action center; model/provider selector; Git/PR/evidence state; settings.

## Safety UX
Computer-use state must always be visible. Provide obvious Pause/Emergency Stop/Take Control affordances. Sensitive/destructive actions surface explicit risk and approval state. Permission denial must remain understandable and recoverable.

## WO-0015 shell foundation
The first promoted shell intentionally implemented the substrate only. Workspace was the sole active navigation surface; Tasks, Code, Computer and Evidence remained disabled; Run and safety mutations remained unavailable without a trusted actionable session. Original Hive assets and native Windows window decoration were retained.

## WO-0016 trusted workspace candidate
- Workspace now exposes an explicit `Open workspace` / `Change workspace` user action backed by the native folder picker.
- The UI does not accept or send an arbitrary path string to the trusted application layer.
- After admission, the surface shows bounded workspace name/root, project markers and observation provenance.
- Git state shows truthful repository/branch or detached HEAD identity only when native observation supports it; malformed/unsupported state becomes DEGRADED rather than optimistic READY.
- Hive evidence shows bounded checkpoint/evidence presence without treating repository text as instruction authority.
- Runtime/provider/permission remain explicit UNKNOWN/DISCONNECTED until separately governed live adapters are wired.
- Task Run, terminal/file mutation, computer-use mutation and safety actions remain unavailable in this slice.
- Workspace/Git/evidence data is presentation state only and must not visually imply permission or execution authority.

## Visual evidence status
The Windows release executable builds and passes launch smoke. Screenshot/pixel-fidelity regression, accessibility automation, motion validation, native picker click/select E2E, responsive small-window validation and full native interaction E2E remain unproven and must not be inferred from launch smoke.

Final design-token/component-library promotion beyond this foundation requires later visual validation evidence and normal governed Work Order flow.