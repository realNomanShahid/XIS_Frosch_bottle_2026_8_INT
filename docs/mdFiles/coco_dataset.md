# Frosch Dataset (COCO Format)

**Dataset ID:** frosch-bottle-5-ypv4gi  

---

## Format

- **Annotation format:** COCO  
- **What that means:** each image has JSON labels with bounding boxes and class IDs (standard COCO detection style).  
- **Images:** conveyor-belt photos of Frosch bottles.  
- **Who annotated:** not the pipeline engineer.  
- **Who QA’d:** **Rafay** (annotation sample review at intake).

---

## Counts

| Split | Images |
|-------|-------:|
| Train | 836 |
| Validation | 250 |
| **Train + val** | **1086** |

**Test / ground-truth samples:** provided **separately**.  
Those bottles are **not** mixed into train or validation.

---

## Classes

| Class | Meaning (simple) |
|-------|------------------|
| bottle | Whole bottle |
| label | Label area (for H/V centricity) |
| capacity | Area with 100 / 300 / 500 text (for OCR) |
| bump | Raised / “ping”-like defect |
| damage | Visible damage on the bottle |
| scratch | Thin line-like mark |

---

## How labels are used

1. **Train / val** → train RF-DETR detection (and related seg training data path).  
2. **Detection boxes** → find bottle, label, capacity, defects at run time.  
3. **Hold-out test / GT sample images** → check the system; **not** used to train.

---

## Rules we keep

- Train and val only for learning.  
- Test / ground-truth sample images stay outside train and val.  
- Dataset files and weights are **not** committed to Git (store by ID / local paths).

---

## One-line summary

COCO-labelled Frosch images (836 train / 250 val), six classes, QA by Rafay; test samples are separate and not in train/val.
