# A07 — Training Run (Detection)

**ID:** PRJ-FROSCH-RUN-DET-0001  
**parent:** PRJ-FROSCH-DSV-v1  
**Engineer:** Noman  
**Training window:** 2026-08-06 to 2026-08-10  
**Related:** A03/A06, A08, A17 , A14 

---

## Purpose
This record freezes the detection training run that produced the weights later exported to TensorRT for the live Frosch pipeline.

---

## Dataset parent
- **Dataset version:** PRJ-FROSCH-DSV-v1  
- **Dataset ID:** frosch-bottle-5-ypv4gi  
- **Train images:** 836  
- **Validation images:** 250  
- **Annotation format:** COCO  
- **QA parent:** PRJ-FROSCH-QA-001 (accepted by Abdul Rafay)

---

## Environment
| Item | Value |
| ---- | ----- |
| Engineer | Noman |
| Seed (D1) | 40 |
| Hardware | NVIDIA GeForce RTX 5060 |
| Separate training config filename | None — hyperparameters listed in this artifact |
| Training window | 2026-08-06 to 2026-08-10 |

---

## Hyperparameters

| Item | Value |
| ---- | ----- |
| Model | RF-DETR Medium |
| Task | Multi-class detection |
| Classes | bottle, label, capacity, bump, damage, scratch |
| Epochs | 100 |
| Early stopping | Not used |
| Learning rate | 0.001 |
| Batch size | 8 |
| Input size | 576 × 576 |
| Augmentation | None |
| Annotation format | COCO |

---

## Checkpoint and export path
| Stage | Path / name |
| ----- | ----------- |
| Best training checkpoint used in project | `checkpoint_best_regular.pth` |
| Runtime engine used later in pipeline | `output/rfdetr-medium.trt` |
| SHA-256 of checkpoint | Not recorded on disk log at training time |

Weights and engines are kept in the model store, not in Git.

---

## Second / comparative run
- No second comparative detection training run was performed for INTER-54.  
- This A07 ID is the sole detection training parent for the evaluation package.

---

## Status
**COMPLETE.**