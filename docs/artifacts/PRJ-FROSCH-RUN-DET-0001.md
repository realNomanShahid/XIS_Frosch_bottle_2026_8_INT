# A07 — Training Run (Detection)

**ID:** PRJ-FROSCH-RUN-DET-0001  
**parent:** PRJ-FROSCH-DSV-v1  
**Engineer:** Noman  
**Recorded before run start?** Retrospective record (mark as reconstruction if exact pre-run form was not filed).

## Environment
- **Commit:** Record at tag time (fill SHA when tagging).  
- **Config path:** No separate training config filename retained (hyperparameters listed below).  
- **Seed (D1):** **40**  
- **Dependency lock hash:** Not recorded.  
- **Hardware:** NVIDIA GeForce RTX 5060  
- **Calibration mm:** N/A  

## Hyperparameters
| Item | Value |
|------|-------|
| Model | RF-DETR Medium |
| Task | Detection |
| Epochs | 100 |
| Early stopping | Not used |
| Learning rate | 0.001 |
| Batch size | 8 |
| Input size | 576 × 576 (RF-DETR standard) |
| Augmentation | None |

## Results
- Per-class Precision / Recall / AP50: see chart evidence retained in project docs (approximate values recorded under A17).  
- Confusion matrix IoU≥0.50 retained as evaluation evidence.

## Checkpoint
- **Ref (lineage names used in project):** `checkpoint_best_regular.pth` / related best checkpoint naming as stored under training runs directory.  
- Pipeline also references `runs/frosch_medium/checkpoint_best_regular.pth` in documentation.  
- **Re-run matches?** Only one training run — N/A second run.

**SHA-256 of checkpoint:** Not recorded in this artifact (open).
