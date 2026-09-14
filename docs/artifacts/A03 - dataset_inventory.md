# A03 — Dataset Inventory

**ID:** PRJ-FROSCH-DS-INV-v1  
**Date:** 2026-08-05  
**Engineer:** Noman  
**Task:** INTER-54 — Frosch bottle live inspection  
**Related artifacts:** A04, A05, A06

---

## Purpose
This inventory records the image dataset used to train and evaluate the Frosch inspection models.  
It answers: where the data came from, how large it is, what it covers, and where it is stored.

---

## Sources
- **Dataset ID:** frosch-bottle-5-ypv4gi  
- **Domain:** Frosch consumer bottles on an industrial conveyor line  
- **Capture method:** Bottles moving on the conveyor belt; frames saved as images for training and evaluation  
- **Annotation ownership:** **not annotated by Noman**  
- **Intake date for this project:** 2026-08-05  

---

## Counts

| Split | Count |
| ----- | ----: |
| Train | 836 |
| Validation | 250 |
| **Train + validation total** | **1086** |


---

## Coverage

### Bottle sizes
- 100 ml  
- 300 ml  
- 500 ml  

### Label classes present in the set
| Class | Role in the pipeline |
| ----- | -------------------- |
| bottle | Main object for detection and tracking |
| label | Region used for H/V centricity |
| capacity | Region used to crop for OCR |
| bump | Surface defect class (raised / ping-like) |
| damage | Surface defect class (visible damage) |
| scratch | Surface defect class (thin line mark) |


---

## What this dataset is used for
- Training RF-DETR Medium detection (A07)  
- Training RF-DETR Seg Medium segmentation (A07)  
- Validation split checks during training  
- Supporting evaluation and operational runs documented under A08 / A17  

---

## Known boundaries
- Engineer did not create the original annotations.  
- Class definitions used operationally are recorded in A04; QA acceptance is recorded in A05.

---

## Status
**COMPLETE**.