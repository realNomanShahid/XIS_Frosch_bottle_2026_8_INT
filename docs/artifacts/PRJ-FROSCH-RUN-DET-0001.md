# A07 — Training Run (Detection)

**ID:** PRJ-FROSCH-RUN-DET-0001  
**parent:** PRJ-FROSCH-DSV-v1  
**Engineer:** Noman  
**Training window:** 2026-08-06 to 2026-08-10  

## Environment
- Seed: 40  
- Hardware: NVIDIA GeForce RTX 5060  
- Separate training config filename: none — hyperparameters listed below  

## Hyperparameters
| Item | Value |
|------|-------|
| Model | RF-DETR Medium |
| Task | Multi-class detection |
| Epochs | 100 |
| Early stopping | Not used |
| Learning rate | 0.001 |
| Batch size | 8 |
| Input size | 576 x 576 |
| Augmentation | None |
| Annotation format | COCO |

## Checkpoint
- Filename used in project: checkpoint_best_regular.pth  
- Runtime export path used later: output/rfdetr-medium.trt  
- SHA-256: Not recorded on disk log at training time  

## Second run
- No second comparative training run.

## Status
COMPLETE.
