# A07 — Training Run (Segmentation)

**ID:** PRJ-FROSCH-RUN-SEG-0001  
**parent:** PRJ-FROSCH-DSV-v1  
**Engineer:** Noman  
**Training window:** 2026-08-06 to 2026-08-10  
**Related:** A07, A10, A09, A14

---

## Purpose
This record freezes the segmentation training run used to produce bottle/label masks for orientation, H/V centricity, and defect-overlap checks in the live pipeline.

---

## Why segmentation was trained separately
Detection boxes alone were not enough for stable geometry on conveyor views (see A10).  
A dedicated RF-DETR Seg Medium model provides the mask needed for:

- PCA-based bottle orientation (tilt)  
- Label-vs-bottle horizontal and vertical offsets  
- Defect confirmation against the bottle mask region  

---

## Dataset parent
- **Dataset version:** PRJ-FROSCH-DSV-v1  
- **Dataset ID:** frosch-bottle-5-ypv4gi  
- **Train images:** 836  
- **Validation images:** 250  
- **QA parent:** PRJ-FROSCH-QA-001  

Same dataset version as the detection run; no separate DSV was issued for segmentation.

---

## Environment
| Item | Value |
| ---- | ----- |
| Engineer | Noman |
| Seed | 40 |
| Hardware | NVIDIA GeForce RTX 5060 |
| Training window | 2026-08-06 to 2026-08-10 |

---

## Hyperparameters

| Item | Value |
| ---- | ----- |
| Model | RF-DETR Seg Medium |
| Epochs | 100 |
| Learning rate | 0.001 |
| Batch size | 8 |
| Seed | 40 |
| Augmentation | None |

### Alignment with detection run
- Same epoch count (100)  
- Same learning rate (0.001)  
- Same batch size (8)  
- Same seed (40)  
- Same “no augmentation” choice  

---

## Checkpoint and export path
| Stage | Path / name |
| ----- | ----------- |
| Best training checkpoint used in project | `checkpoint_best_model.pth` |
| Runtime engine used later in pipeline | `output/rfdetr-seg-medium.trt` |
| SHA-256 of checkpoint | Not recorded on disk log at training time |

Weights and engines remain in the model store outside Git.

---

## Role in the pipeline
After export to TensorRT, this segmentation engine is used whenever the pipeline needs a mask:

1. Select / refine the bottle region  
2. Estimate orientation from the mask  
3. Support label geometry relative to the bottle  
4. Validate defect detections by overlap with the bottle mask  
---

## Second / comparative run
- No second comparative segmentation training run was performed for INTER-54.
---

## Status
**COMPLETE.**