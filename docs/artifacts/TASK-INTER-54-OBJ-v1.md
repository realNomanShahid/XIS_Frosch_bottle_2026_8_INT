# A02 — Objective

**ID:** TASK-INTER-54-OBJ-v1  
**parent:** TASK-INTER-54-QS  
**Date:** 2026-08-05  
**Engineer:** Noman  
**Lead confirm:** Pending formal sign-off — Abdul Moiz

## Seven elements

| Element | Content |
|--------|---------|
| **Subject** | Live / folder Frosch bottle inspection pipeline (detect, segment, OCR capacity, track, geometry, defect confirm, classify). |
| **Observable** | Each finalised bottle receives GOOD, DEFECTIVE, or INCOMPLETE; crops + CSV/JSON (+ optional video) are written. |
| **Measure** | Rule outcomes: orientation PASS/FAIL/Pending; H PASS/FAIL/Pending; V PASS/FAIL/Pending; confirmed defects; capacity ∈ {100,300,500} or unknown. |
| **Target** | **No signed numeric customer target was recorded at implementation start.** Operational engineering rules in force: tilt ≤ 45°; \|H\| ≤ 0.15; \|V − expected_V(capacity)\| ≤ 0.05; defect mask-overlap ≥ 0.30 with streak confirmation. Sample detection metrics recorded under A17 (chart / confusion matrix). |
| **Method** | RF-DETR Medium det + RF-DETR Seg Medium (TensorRT); PaddleOCR (GPU); config-driven thresholds (`configs/*.yaml`); train/val from frosch-bottle-5-ypv4gi; operational checks on provided test bottles and live camera. |
| **Conditions** | Conveyor-belt capture; bottle sizes 100/300/500 ml; Vimba/Harvester live or image folder; GPU TensorRT path. |
| **Boundary** | Not in scope: camera calibration to mm; line PLC reject actuation; packaging/UI productisation; formal 2 h production soak on sealed line hardware; independent metrology lab validation. |

## TARGET block (handbook form)
- **Accuracy requirement (±mm):** N/A — classification / normalised geometry task, not mm feature measurement.
- **Share within requirement:** N/A until signed rate/quality targets exist.
- **Edge agreement:** N/A (annotation owned upstream; engineer consumed existing labels).
- **Latency / throughput:** Not signed. Sample evidence only (see A17).
- **Groups that must not be worse:** 100 / 300 / 500 ml (operational sample tables in results/).

## Lead confirmation
- **Confirmed by lead:** Not yet (record as open).  
- **Date:** —  
- **Supersedes:** none (v1)

**Status:** Objective is **draft / engineering-rule based**. Handbook requires lead confirmation before release gates close.
