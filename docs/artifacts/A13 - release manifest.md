# A13 — Release Manifest (Evaluation package)

**ID:** PRJ-FROSCH-REL-v1  
**Date:** 2026-08-31  
**Lead:** Abdul Moiz  
**Engineer:** Noman  
**Task:** INTER-54  

## Deliverable
Frosch bottle inspection evaluation package: TensorRT detection and segmentation, OCR, tracking, geometry rules, configs/, src/, tests/, docs/, artifacts/.

## Parents
| Artifact | ID | Status |
|----------|-----|--------|
| A02 | TASK-INTER-54-OBJ-v1 | Confirmed |
| A05 | PRJ-FROSCH-QA-001 | Complete; reviewer Rafay|
| A06 | PRJ-FROSCH-DSV-v1 | Complete 2026-08-05 |
| A07 | RUN-DET-0001 / RUN-SEG-0001 | Complete 2026-08-06 to 2026-08-10 |
| A08 | PRJ-FROSCH-EVAL-v1 | Complete |
| A09 | PRJ-FROSCH-MVR-v1 | Complete; GT sample images method |
| A11 | PRJ-FROSCH-SOAK-001 | Complete; 120.66 min on 2026-09-09 |
| A12 | PRJ-FROSCH-FBA-001 | Complete |

## Runtime artifacts (not in Git)
- output/rfdetr-medium.trt  
- output/rfdetr-seg-medium.trt  
- checkpoints: checkpoint_best_regular.pth, checkpoint_best_model.pth  

## Declaration
Lead-reviewed evaluation evidence package for INTER-54.  
Soak evidence dated 2026-09-09 attached via A11 log totals.

## Status
COMPLETE as evaluation manifest.
