# A15 — Re-entry Record

**ID:** TASK-INTER-54-RE-1  
**Item:** Geometry tilt and H/V methods  
**Engineer:** Noman  
**Date:** 2026-08-18   
**Related:** A10,A02,A09,A14 

---

## Purpose
Handbook re-entry records when implementation shows that the current approach cannot meet the objective and work must return to an earlier stage.  
This file documents the geometry re-entry for tilt and H/V centricity.

---

## Item under change
- **Topic:** bottle orientation (tilt) and label horizontal/vertical offsets  
- **Why it matters:** these measurements feed PASS/FAIL/Pending under the confirmed A02 rules   

---

## Trigger
**Trigger type 5 — implementation evidence**

Earlier geometry approaches could not deliver stable measurements on conveyor imagery.  
Single-frame or box-based methods that looked acceptable in isolation failed once tracking and multi-frame finalisation were applied.

---

## Re-entry point
Work re-entered at **implementation / method redesign** for geometry:

- Mask-based orientation (PCA on the bottle segmentation mask)  
- Label-vs-bottle H and V computation  
- Capacity-specific expected V references for 100 / 300 / 500 ml  

This is not a dataset recollect re-entry and not a new A02 rewrite.  
It is a method change inside the same objective.

---

## Cause (one clear statement)
**Box-only tilt/offset methods failed to stabilise on conveyor imagery.**

Supporting detail:
- Detection boxes do not follow the bottle silhouette reliably when the box is loose, clipped, or shifted  
- Orientation taken from a box is not the same as the bottle principal axis  
- H/V from box centres inherits that instability across frames  

Full development narrative is in **A10**.

---

## What changed after re-entry
| Before | After |
| ------ | ----- |
| Box-oriented tilt / offset trials | PCA orientation on segmentation mask |
| Weak single-frame decisions | Temporal history with median/majority stabilisation |
| Ad-hoc numeric limits in experiments | Thresholds placed in `configs/geometry.yaml` |
| One global vertical expectation | Capacity-specific expected V |

---
## Objective / plan impact
- **A02 subject and rules:** unchanged (still tilt / H / V / defects / capacity → GOOD/DEFECTIVE/INCOMPLETE)  
- **Implementation plan:** updated to the mask-based geometry path  
- **Parents to re-check after the change:** A08 evaluation behaviour, A09 sample validation, A12 failure paths  

---

## Status
**COMPLETE.**  
