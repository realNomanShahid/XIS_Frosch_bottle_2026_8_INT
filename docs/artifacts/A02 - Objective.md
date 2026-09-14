# A02 — Objective

**ID:** TASK-INTER-54-OBJ-v1  
**parent:** TASK-INTER-54-QS  
**Engineer:** Noman  
**Confirmed by:** Abdul Moiz    
**Related:** A01, A08 , A09 , A11, A13

---

## Purpose
This objective defines what the Frosch inspection system must do, how success is observed, and under which conditions evaluation is valid.  
It is the parent target for evaluation, validation, and soak evidence.

---

## Confirmation
| Field | Value |
| ----- | ----- |
| Engineer | Noman |
| Confirmed by | Abdul Moiz |
| Parent question set | TASK-INTER-54-QS |

---

## Seven elements

| Element | Content |
| ------- | ------- |
| **Subject** | Frosch bottle inspection pipeline: detection, segmentation, OCR, tracking, geometry, defect confirmation, classification, and result saving. |
| **Observable** | Each finalised bottle is labelled **GOOD**, **DEFECTIVE**, or **INCOMPLETE**. Results are written to CSV/JSON and image crops (and optional video where enabled). |
| **Measure** | Orientation/tilt; horizontal label offset (H); vertical label offset (V) versus a capacity-specific reference; confirmed surface defects; capacity in {100, 300, 500} ml. |
| **Target** | rules: tilt ≤ 45°; absolute H ≤ 0.15; absolute V error versus expected_V(capacity) ≤ 0.05; defect mask-overlap ≥ 0.30 with confirmation streak. Pending measurements do not become GOOD. |
| **Method** | RF-DETR Medium detection; RF-DETR Seg Medium segmentation; TensorRT runtime; PaddleOCR (GPU) for capacity; thresholds in `configs/*.yaml`; dataset frosch-bottle-5-ypv4gi; ground-truth sample images for validation. |
| **Conditions** | Conveyor capture; bottle sizes 100/300/500 ml; Vimba/Harvester live input and folder input; evaluation hardware NVIDIA GeForce RTX 5060. |


---

## What “done” looks like for a bottle
1. Bottle is detected and tracked across frames.  
2. Mask-based geometry produces tilt and H/V where possible.  
3. Capacity is read when the OCR path succeeds.  
4. Defects are confirmed only with mask-overlap rules.  
5. Final status is one of:
   - **GOOD** — required checks pass and no confirmed defect  
   - **DEFECTIVE** — a required check fails or a defect is confirmed  
   - **INCOMPLETE** — required measurement still pending / cannot be completed  

---

## Evidence that sits under this objective
| Artifact | Role relative to A02 |
| -------- | -------------------- |
| A07 | Trains detection and segmentation models named in Method |
| A08 | Evaluates against these rules |
| A09 | Validates using provided ground-truth sample images |
| A11 | Soak under live conditions with classification totals |
| A12 | Confirms failure paths do not invent GOOD |
| A17 | Detection quality charts and sample FPS |

---

## Status
**COMPLETE.**  
Confirmed by **Abdul Moiz**.