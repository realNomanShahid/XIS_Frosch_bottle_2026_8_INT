# A02 — Objective

**ID:** TASK-INTER-54-OBJ-v1  
**parent:** TASK-INTER-54-QS  
**Date raised:** 2026-08-05  
**Engineer:** Noman  
**Confirmed by:** Abdul Moiz  
**Confirm date:** 2026-08-31  

## Seven elements

| Element | Content |
|--------|---------|
| Subject | Frosch bottle inspection pipeline: detection, segmentation, OCR, tracking, geometry, defect confirmation, classification, saving. |
| Observable | Each finalised bottle is GOOD, DEFECTIVE, or INCOMPLETE; results written to CSV/JSON and image crops. |
| Measure | Orientation, H offset, V offset vs capacity-specific reference, confirmed defects, capacity in {100,300,500}. |
| Target | Lead-confirmed rules: tilt ≤ 45°; absolute H ≤ 0.15; absolute V error vs expected_V(capacity) ≤ 0.05; defect overlap ≥ 0.30 with confirmation streak. |
| Method | RF-DETR Medium detection; RF-DETR Seg Medium segmentation; TensorRT; PaddleOCR GPU; configs in configs/*.yaml; dataset frosch-bottle-5-ypv4gi; GT sample images for validation. |
| Conditions | Conveyor capture; 100/300/500 ml; Vimba/Harvester live and folder input; RTX 5060 evaluation hardware. |
| Boundary | Not in scope: mm gauge metrology product, PLC reject hardware, customer UI packaging. |

## Status
COMPLETE. Confirmed by Abdul Moiz on 2026-08-31.
