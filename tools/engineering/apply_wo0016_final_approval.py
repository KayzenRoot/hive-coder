from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one approval anchor in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


checkpoint = ROOT / "docs/project-brain/11-CHECKPOINT.md"
replace_once(checkpoint, "**Status:** PROMOTION CANDIDATE — NOT YET CANONICAL", "**Status:** APPROVED FOR SQUASH MERGE — NOT YET CANONICAL")
replace_once(checkpoint, "**PR:** `#35` — DRAFT", "**PR:** `#35` — FINAL APPROVAL CANDIDATE")
replace_once(
    checkpoint,
    "**Technical reviewed head:** `07dda00f7371bcb02158f0c26258b03fa0dec88d`",
    "**Technical reviewed head:** `07dda00f7371bcb02158f0c26258b03fa0dec88d`  \n**Promotion reviewed head:** `50c280004b0d869e32fda8f20806082654e63255`",
)
replace_once(checkpoint, "## Candidate state", "## Approved candidate state")
replace_once(
    checkpoint,
    "## Explicit residual boundaries",
    """## Promotion evidence
Exact promotion head `50c280004b0d869e32fda8f20806082654e63255`:
- Governance run `34997849021` (#204): **SUCCESS**, Ubuntu **256/256 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**.
- Desktop Shell run `34997849241` (#40): **SUCCESS**, security gate PASS, Vitest **12/12 PASS**, npm audit **0 vulnerabilities**, RustSec no blocking vulnerability with **7 allowed warning-class advisories**, Windows Rust **11/11 PASS**, `cargo check --locked` PASS, Tauri release build PASS, `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS promotion review `5213131975`: **APPROVED FOR FINAL APPROVAL MUTATION**, unresolved HIGH/CRITICAL findings **0**.
- Compare from technical reviewed head to promotion head contains documentation/evidence/governance changes only, with no application/workflow/dependency/lock/capability/permission drift.

## Decision
`DEC-020 — Trusted Workspace & Git Read Boundary` is APPROVED. This approval adds no privilege and remains non-canonical until squash merge plus post-merge validation on `main`.

## Explicit residual boundaries""",
)
replace_once(
    checkpoint,
    "## Promotion gates still required\nThis candidate is not canonical. The documentation-only promotion mutation must pass exact-head Governance + Desktop Shell, then HEDS must verify no application/workflow/dependency/lock/capability drift. Only after final approval mutation, final exact-head gates/HEDS, squash merge and post-merge validation may CP-0016 become canonical/COMPLETE.",
    "## Final gates still required\nThis checkpoint is approved for squash merge but is **not canonical**. This documentation/governance-only approval mutation must pass exact-head Governance + Desktop Shell and final HEDS with unresolved HIGH/CRITICAL = 0. Then PR #35 may be squash-merged. CP-0016 becomes canonical/COMPLETE only after post-merge Governance + Desktop Shell pass on the resulting `main` SHA and canonical closeout records those receipts.",
)
replace_once(
    checkpoint,
    "No WO-0017 may be promoted from this candidate state. The next NECESSARY increment is chosen only after CP-0016 is canonical on `main` and a fresh source-check reconciles remaining live runtime/provider/permission read surfaces.",
    "WO-0017 may remain technically staged, but it may not be promoted until CP-0016 is canonical on `main` and its stacked base is reconciled to the canonical merge.",
)

ledger = ROOT / "docs/project-brain/10-DECISIONS-LEDGER.md"
ledger_text = ledger.read_text(encoding="utf-8")
if "## DEC-020" in ledger_text:
    raise SystemExit("DEC-020 already exists")
ledger_text = ledger_text.rstrip() + """

## DEC-020 — Trusted Workspace & Git Read Boundary
**Status:** APPROVED  
**Work Order:** `HCODER-WO-0016`

Hive Coder admits its first user-mediated live workspace boundary as bounded read-only presentation state. Native `choose_workspace` accepts no caller-controlled target/path payload; the trusted Rust application layer canonicalizes/validates the selected directory and retains application-owned session identity. `DesktopSnapshot v2` reports bounded workspace, Git HEAD/branch and Hive checkpoint/evidence observations with explicit provenance and READY/UNKNOWN/DISCONNECTED/DEGRADED semantics.

Git observation reads bounded `.git` metadata directly and never executes an external `git` command or repository hooks. The Tauri capability remains `desktop-read-only`, scoped to `main`, with zero plugin permissions. No terminal/shell, filesystem mutation, provider credential/model execution, runtime spawn, computer-use mutation, remote control, automatic skill activation, billing/purchase authority or Permission & Control Plane expansion is approved by this decision.

`HCODER-WO-0016-CR-001` HIGH and `HCODER-WO-0016-CR-002` MEDIUM are resolved. Technical head `07dda00f7371bcb02158f0c26258b03fa0dec88d` passed Governance `34996930586`, Desktop Shell `34996930809` and HEDS technical review `5213079423`. Promotion head `50c280004b0d869e32fda8f20806082654e63255` passed Governance `34997849021`, Desktop Shell `34997849241` and HEDS promotion review `5213131975`, with unresolved HIGH/CRITICAL findings 0. This decision is approved for the merge candidate but becomes canonical only after the final approval head passes exact-head gates/HEDS, squash merge, and post-merge validation on `main`.
"""
ledger.write_text(ledger_text, encoding="utf-8", newline="\n")

evidence = ROOT / ".engineering/evidence/HCODER-WO-0016.md"
replace_once(evidence, "**Status:** TECHNICAL COMPLETE — PROMOTION CANDIDATE", "**Status:** APPROVED FOR SQUASH MERGE — FINAL GATES PENDING")
replace_once(
    evidence,
    "## Explicit residual boundaries",
    """## Promotion evidence
Exact promotion head `50c280004b0d869e32fda8f20806082654e63255` passed Governance `34997849021` (#204) and Desktop Shell `34997849241` (#40). Ubuntu remained **256/256 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**, frontend **12/12 PASS**, Windows Rust **11/11 PASS**, npm audit **0 vulnerabilities**, RustSec had no blocking vulnerability with seven warning-class advisories, Tauri release build passed and `DESKTOP_LAUNCH_SMOKE=PASS`.

HEDS promotion review `5213131975` verified that the promotion delta from technical head `07dda00f7371bcb02158f0c26258b03fa0dec88d` is documentation/evidence/governance-only and returned **APPROVED FOR FINAL APPROVAL MUTATION** with unresolved HIGH/CRITICAL findings **0**.

## Explicit residual boundaries""",
)
replace_once(
    evidence,
    "Technical implementation is complete, but the Work Order is **not canonical/complete yet**. Remaining gates are promotion-candidate exact-head Governance + Desktop Shell, promotion HEDS, final approval mutation, final exact-head gates/HEDS, squash merge and post-merge validation on canonical `main`.",
    "Technical implementation and promotion review are complete. `DEC-020` and CP-0016 are approved for the merge candidate, but the Work Order is **not canonical/complete yet**. Remaining gates are fresh exact-head Governance + Desktop Shell on this final approval mutation, final HEDS, squash merge, and post-merge Governance + Desktop Shell on canonical `main`.",
)

work_order = ROOT / ".engineering/work-orders/HCODER-WO-0016.md"
replace_once(work_order, "**Status:** APPROVED FOR EXECUTION", "**Status:** APPROVED FOR SQUASH MERGE — NOT YET CANONICAL")

print("WO0016_FINAL_APPROVAL_PATCH=APPLIED")
