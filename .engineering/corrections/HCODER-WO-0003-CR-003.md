# Correction Delta — HCODER-WO-0003-CR-003

## Finding
**HIGH · EVIDENCE IDENTITY.** The PR workflow run was associated with branch head `369c8e561a03ec744d2cd068b45f571d9e29c97a`, but the checkout log proved `actions/checkout@v4` had tested GitHub's synthetic PR merge commit `f7a06f405282839fe865f3d3c01379510e5bd966`. That is mergeability evidence, not exact-head evidence, and cannot satisfy the project's exact-head gate.

## Correction
Governance now explicitly checks out `github.event.pull_request.head.sha` for pull requests and `github.sha` for pushes. A dedicated step compares `git rev-parse HEAD` to the expected event SHA and fails if they differ.

## Evidence rule
Run `34910508995` remains useful integration evidence but is explicitly not accepted as exact-head proof. A new successful Governance run on the corrected workflow and current branch head is required before HEDS approval/checkpoint promotion.
