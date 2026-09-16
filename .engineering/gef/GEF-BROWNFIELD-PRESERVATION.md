# GEF V1 Brownfield Preservation Plan — Hive Coder

## Preservation objective
Adopt universal GEF without changing product behavior or rewriting project history.

## Collision map
| Area | Classification | Action |
|---|---|---|
| `docs/project-brain/*` | EXISTS_PROJECT_AUTHORITY | Preserve and map; no template replacement. |
| `.engineering/gef/*` | EXISTS_NEEDS_MERGE | Reconcile Hive-specific GEF with universal rules. |
| `.engineering/work-orders/*` | EXISTS_PROJECT_AUTHORITY | Preserve all historical Work Orders. |
| `.engineering/context-locks/*` | EXISTS_PROJECT_AUTHORITY | Preserve historical locks; add adoption lock only. |
| `.engineering/evidence/*` | EXISTS_PROJECT_AUTHORITY | Preserve historical evidence; add adoption evidence only. |
| `.engineering/templates/*` | EXISTS_COMPATIBLE | Extend templates with universal brownfield/recovery/PDF requirements. |
| `.github/workflows/*` | EXISTS_PROJECT_AUTHORITY | Preserve CI unchanged during adoption. |
| `.github/PULL_REQUEST_TEMPLATE.md` | EXISTS_COMPATIBLE | Merge universal fields without deleting existing governance intent. |
| `README.md` | EXISTS_PROJECT_AUTHORITY | Preserve. |
| product/runtime/tests | EXISTS_PROJECT_AUTHORITY | No behavior changes in adoption. |
| machine adoption checkpoint | CREATE_SAFE | Add under `.engineering/gef/`. |

## Behavior freeze
Universal adoption is governance/documentation only. No source/runtime/test/workflow/package/release behavior may change in `HCODER-GEF-ADOPT-0001`.

## Legacy mapping
Pre-adoption Hive GEF/HEDS artifacts remain valid only for what their exact repository evidence proves. They are not relabeled as universal-GEF historical completion.

## Active branch protection
Draft PR #69 is independent user work. Adoption will merge to `main` separately. PR #69 must reconcile the resulting main before the next executor mutation.
