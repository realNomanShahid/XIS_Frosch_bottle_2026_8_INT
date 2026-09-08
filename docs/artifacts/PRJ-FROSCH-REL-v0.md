# A13 — Release Manifest

**ID:** PRJ-FROSCH-REL-v0  
**Date:** 2026-09-08  
**Approved by lead:** **NO**

## Deliverable
- Frosch live inspection software (evaluation package) — TensorRT det/seg, OCR, tracking, geometry, configs, tests, docs.

## Commit / tag
- **Not a production tag.** Working tree on `main` for evaluation; handbook prefers release tag only after gates.

## PARENTS (mandatory fields — status)
| Parent | ID | Status |
|--------|----|--------|
| A07 det | PRJ-FROSCH-RUN-DET-0001 | Recorded partial |
| A07 seg | PRJ-FROSCH-RUN-SEG-0001 | Recorded partial |
| A06 | PRJ-FROSCH-DSV-v1 | Partial |
| A08 | PRJ-FROSCH-EVAL-v1 | Partial |
| A09 | PRJ-FROSCH-MVR-v1 | **Missing formal** |
| A11 | PRJ-FROSCH-SOAK-001 | **Failed duration** |
| A12 | PRJ-FROSCH-FBA-001 | Draft |
| A02 | TASK-INTER-54-OBJ-v1 | Draft / unconfirmed |

## Config / checkpoint / lock
- Configs: `configs/*.yaml`  
- Engines: `output/rfdetr-medium.trt`, `output/rfdetr-seg-medium.trt` (runtime; not in git)  
- Dependency lock hash: **not recorded**

## Supersedes
- none

**Release state: NOT APPROVED FOR PRODUCTION**
