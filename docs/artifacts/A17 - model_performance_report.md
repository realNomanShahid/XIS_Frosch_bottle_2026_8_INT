# A17 — Model Performance Report

**ID:** PRJ-FROSCH-MPR-v1  
**parent:** PRJ-FROSCH-RUN-DET-0001  
**parent:** PRJ-FROSCH-DSV-v1  
**Engineer:** Noman  
**Date:** 2026-08-28  

## Task
Detection metrics below; segmentation used for masks in the live pipeline.

## Quality metrics (from project per-class evaluation chart)
| Class | Precision | Recall | AP50 |
|-------|----------:|-------:|-----:|
| bottle | ~99% | ~100% | ~91% |
| bump | ~45% | ~55% | ~41% |
| capacity | ~92% | ~100% | ~91% |
| damage | ~36% | ~92% | ~84% |
| label | ~99% | ~100% | ~91% |
| scratch | ~33% | ~21% | ~20% |

## Runtime thresholds (configs/detection.yaml)
- bottle 0.70
- label 0.35
- capacity 0.35
- bump 0.50
- damage 0.30
- scratch 0.30

## Inference performance samples
| Metric | Value |
|--------|-------|
| Hardware | NVIDIA GeForce RTX 5060 |
| TensorRT det+seg sample inference | ~74.66 FPS |
| Full pipeline sample with bottle present | ~18.66 FPS |
| ONNX/CPU FPS | Not measured |

## Soak throughput evidence (A11)
In 120+ minutes: 1009 bottles completed (673 GOOD, 336 DEFECTIVE, 0 INCOMPLETE).

## Status
COMPLETE.
