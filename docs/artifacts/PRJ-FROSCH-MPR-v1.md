# A17 — Model Performance Report

**ID:** PRJ-FROSCH-MPR-v1  
**parent:** PRJ-FROSCH-RUN-DET-0001  
**parent:** PRJ-FROSCH-DSV-v1  
**Date:** 2026-09-08  
**Engineer:** Noman

## Task
Detection (primary metrics below). Segmentation used operationally for masks (separate A07).

## Evaluated on
- Validation / chart export from training evaluation; operational samples on external test bottles (not formally sealed in A06).

## QUALITY METRICS (from project per-class chart — approximate)
| Class | Precision | Recall | AP50 |
|-------|-----------|--------|------|
| bottle | ~99% | ~100% | ~91% |
| bump | ~45% | ~55% | ~41% |
| capacity | ~92% | ~100% | ~91% |
| damage | ~36% | ~92% | ~84% |
| label | ~99% | ~100% | ~91% |
| scratch | ~33% | ~21% | ~20% |

- Confusion matrix IoU≥0.50: retained in project evaluation materials (bottle/capacity/label strong; bump/scratch weaker).

## Decision thresholds (runtime)
- bottle 0.70; label 0.35; capacity 0.35; bump 0.50; damage 0.30; scratch 0.30  
- Chosen as operational settings (document in config); **not** claimed as optimised on a sealed test set.

## INFERENCE PERFORMANCE (sample, TensorRT path)
| Metric | Value |
|--------|-------|
| Hardware | NVIDIA GeForce RTX 5060 |
| Det+seg inference sample | ~74.66 FPS |
| Full pipeline sample (bottle present) | ~18.66 FPS |
| ONNX/CPU FPS | Not measured |
| Warm-up excluded? | Not stated |
| Precision | TensorRT engine (project path) |

## Against production model
- N/A — no prior production model comparison recorded.

## Verdict: fit for release candidate?
- **NO** — supports evaluation only; handbook parents incomplete.

**Sign-off:** Open — Abdul Moiz
