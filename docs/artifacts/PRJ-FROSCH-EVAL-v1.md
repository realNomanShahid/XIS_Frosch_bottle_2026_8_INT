# A08 — Evaluation

**ID:** PRJ-FROSCH-EVAL-v1  
**parent:** TASK-INTER-54-OBJ-v1  
**parent:** PRJ-FROSCH-DSV-v1  
**parent:** PRJ-FROSCH-RUN-DET-0001  
**Engineer:** Noman  
**Period:** 2026-08-19 to 2026-08-28 operational evaluation; soak metrics 2026-09-09  

## Criterion
Lead-confirmed A02 rules: tilt, H, V, defect overlap, capacity handling.

## Detection quality evidence
Per-class Precision / Recall / AP50 chart and IoU 0.50 confusion matrix retained in project documentation (see A17).  
Values originate from the training evaluation export chart (not a separate CSV export file).

## Operational samples
results/bottle1, results/bottle2, results/bottle3 CSV/JSON sample runs for 100/300/500 ml.

## Soak classification counts (full numbers in A11)
On 2026-09-09 soak final row: completed 1009; good 673; defective 336; incomplete 0.

## Status
COMPLETE under confirmed A02.
