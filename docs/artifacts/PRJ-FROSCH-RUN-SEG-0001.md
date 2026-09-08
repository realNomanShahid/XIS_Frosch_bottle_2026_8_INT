# A07 — Training Run (Segmentation)

**ID:** PRJ-FROSCH-RUN-SEG-0001  
**parent:** PRJ-FROSCH-DSV-v1  
**Engineer:** Noman

## Environment
- **Seed:** **40**  
- **Hardware:** NVIDIA GeForce RTX 5060  
- **Config filename:** None retained  

## Hyperparameters
| Item | Value |
|------|-------|
| Model | RF-DETR Seg Medium |
| Epochs | 100 (same schedule family as detection) |
| Learning rate | 0.001 (same) |
| Batch size | 8 (same) |
| Augmentation | None |

## Checkpoint
- Project names include `checkpoint_best_model.pth` and documentation path `runs/frosch_seg_medium/checkpoint_best_total.pth`.  
- **SHA-256:** Not recorded.

**Note:** Single training approach; no second comparative run.
