# GEF V1 Repository Discovery Receipt — Hive Coder

## Identity
- Repository: `KayzenRoot/hive-coder`.
- Visibility: public.
- Default branch: `main`.
- Adoption base: `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`.
- Classification: `BROWNFIELD`.

## Material project surface discovered
- Python governed runtime: `hive_runtime/`.
- Desktop app: `apps/desktop/` using React/Tauri.
- Tests: `tests/` plus desktop TS/Rust tests.
- Foundations/dependency locks: `foundations/`.
- CI: `.github/workflows/`, including `Governance` and `Desktop Shell`.
- GitHub templates/CODEOWNERS already exist.
- Canonical planning/source docs: `docs/project-brain/`.
- Existing engineering governance: `.engineering/` with work-orders, context-locks, evidence, checkpoint-deltas, corrections, prompts, prebuilt packs, templates and a Hive-specific GEF layer.
- Active product work: Draft PR #69, `HCODER-WO-0023`.

## Real validation surfaces
Hosted workflows are the authoritative cross-platform proof surface. Existing repository evidence records Python, frontend, Rust/Tauri, dependency/security and native Windows/Linux/macOS lanes. No new validation command is invented by this adoption.

## GitHub policy discovery
Repository supports merge, squash and rebase methods. No repository rulesets were present at discovery time. The project is single-owner; universal GEF therefore requires technical exact-head audit but does not invent a ceremonial human approval gate.

## Security/recovery observations
Existing Project Brain and Work Orders already govern secrets, permission/control-plane authority, path/symlink/reparse safety, process execution, dependency audits, failure recovery and redaction. Universal adoption maps these rather than duplicating controls.

## Discovery conclusion
This is not an empty repository. Treat conservatively as BROWNFIELD. Adoption must be documentation/governance additive and behavior-preserving.
