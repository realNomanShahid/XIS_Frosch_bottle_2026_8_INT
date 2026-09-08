# A14 — Decision Record

**ID:** DEC-FROSCH-0001  
**Decided by:** Noman (technical) / pending Abdul Moiz (release)  
**Date:** 2026-08-05 … 2026-09-08

## Decision
Use **RF-DETR Medium** detection + **RF-DETR Seg Medium** segmentation, TensorRT runtime, PaddleOCR for capacity, config-externalised thresholds, and rule-based GOOD / DEFECTIVE / INCOMPLETE finalisation with multi-frame tracking.

## Alternatives rejected (and why)
1. **Box-only geometry for tilt/H/V** — unstable / inaccurate vs mask-based PCA and centroids.  
2. **Multiple abandoned tilt/offset formulations** during development — did not stabilise; exact variants not retained in writing.  
3. **Early stopping** — not used; full 100-epoch schedule preferred for final checkpoint.  
4. **Heavy augmentation** — not applied for this training run.  
5. **Committing weights/datasets to git** — rejected per handbook store rules.

## Reversible?
- Yes at engineering level (new A07 + re-eval).  
- Production release decision is **not** approved.

## Affects
- Model choice, training schedule, runtime stack, repository layout (configs/src/tests/docs).
