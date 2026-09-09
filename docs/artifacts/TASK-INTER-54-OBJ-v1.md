# A02 — Objective

**ID:** TASK-INTER-54-OBJ-v1  
**parent:** TASK-INTER-54-QS  
**Engineer:** Noman  
**Confirmed by:** Abdul Moiz  
 

## Seven elements

| Element | Content |
|--------|---------|
| Subject | Frosch bottle inspection pipeline: detection, segmentation, OCR, tracking, geometry, defect confirmation, classification, saving. |
| Observable | Each finalised bottle is GOOD, DEFECTIVE, or INCOMPLETE; results written to CSV/JSON and image crops. |
| Measure | Orientation, H offset, V offset vs capacity-specific reference, confirmed defects, capacity in {100,300,500}. |
| Method | RF-DETR Medium detection; RF-DETR Seg Medium segmentation; TensorRT; PaddleOCR GPU; configs in configs/*.yaml; dataset frosch-bottle-5-ypv4gi; GT sample images for validation. |
| Conditions | Conveyor capture; 100/300/500 ml; Vimba/Harvester live and folder input; RTX 5060 evaluation hardware. |


## Status
COMPLETE.
