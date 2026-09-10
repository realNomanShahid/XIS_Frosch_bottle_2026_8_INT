# A14 — Decision Record

**Date:** 2026-08-10  
**Related artifacts:** A07,A17, A02
---

## Context
the dataset version was fixed (train 836 / val 250) and training had to lock a detection model, a segmentation model, a runtime path, and a capacity-reading approach. 

---

## Decision
The project standardises on the following stack:

- **Detection:** RF-DETR Medium  
- **Segmentation:** RF-DETR Seg Medium  
- **Runtime:** TensorRT engines for both models  
- **Capacity reading:** PaddleOCR (GPU)  
- **Final status:** rule-based classification into **GOOD**, **DEFECTIVE**, or **INCOMPLETE**

These components work together as one live/folder pipeline: detect bottle and related classes, segment the bottle/label region for geometry, read capacity text, track the bottle across frames, apply tilt/H/V and defect rules, then write results.

---

## Why this combination
- RF-DETR Medium gave a practical balance of accuracy and speed for multi-class bottle-line detection on the available GPU.  
- A **separate segmentation model** was required because orientation and H/V centricity need a mask, not only a bounding box.  
- **TensorRT** was selected for line-style latency on the evaluation GPU (RTX 5060).  
- **PaddleOCR** was selected to read capacity markings (100 / 300 / 500 ml) from the capacity crop.  
- **Rule-based finalisation** keeps the business decision explicit and auditable under Lead thresholds (tilt, H, V, defect overlap).

---

## Alternatives rejected
- **Box-only geometry for tilt and H/V**  
  - Tried during early geometry work.  
  - Unstable on conveyor views where the box does not follow the bottle body well.  
  - Rejected in favour of mask-based PCA orientation and label-vs-bottle offsets.

- **Early stopping during training**  
  - Not used.  
  - Full **100-epoch** schedule retained for both detection and segmentation so the final checkpoint reflects the full planned run.

- **Data augmentation**  
  - Not applied for this training run.  
  - Training used the provided COCO set as-is after QA intake.

- **Skipping segmentation and relying on detection boxes alone**  
  - Insufficient for orientation and centricity requirements of A02.

---

## Impact
- Training runs A07 (detection and segmentation) follow this decision.  
- Runtime engines and OCR path in `src/` follow this decision.  
- Evaluation (A08), validation (A09), soak (A11), and performance report (A17) all assume this stack.

---

## Reversibility
- Reversible at engineering level by a new A07 training run and a new A14 record.  
- Changing the stack after Lead-confirmed A02 requires re-evaluation under the same gates.

---

## Status
**COMPLETE**
