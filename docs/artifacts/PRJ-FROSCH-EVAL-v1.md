# A08 — Evaluation

**ID:** PRJ-FROSCH-EVAL-v1  
**parent:** TASK-INTER-54-OBJ-v1  
**parent:** PRJ-FROSCH-DSV-v1  
**parent:** PRJ-FROSCH-RUN-DET-0001  
**Engineer:** Noman  
**Date:** 2026-09-08

## Sealed test set ref
- External test bottles stated disjoint from train/val — **formal seal ID/hash not filed**.

## Criterion vs objective
- Signed numeric A02 targets: **none**.  
- Evaluation is against **engineering rules** (tilt / H / V / defect overlap) and **detection quality charts**.

## Detection quality (from project chart — approximate)
| Class | Precision | Recall | AP50 |
|-------|-----------|--------|------|
| bottle | ~99% | ~100% | ~91% |
| bump | ~45% | ~55% | ~41% |
| capacity | ~92% | ~100% | ~91% |
| damage | ~36% | ~92% | ~84% |
| label | ~99% | ~100% | ~91% |
| scratch | ~33% | ~21% | ~20% |

## Operational sample (results/ CSVs — illustrative, not formal P/R)
- Sample runs across 100 / 300 / 500 ml recorded in `results/bottle1|2|3/` and `docs/results.md`.  
- These are **not** a full per-criterion pass table against a signed A02.

## Per-group
- Breakdown by capacity exists in sample CSVs.  
- Single overall “accuracy %” is **not** claimed as handbook acceptance.

## M1
- N/A (no ±mm share metric).  

**All signed criteria met?** N/A — no signed criteria.  
**Status:** Evaluation evidence **partial**; cannot close release on A08 alone.
