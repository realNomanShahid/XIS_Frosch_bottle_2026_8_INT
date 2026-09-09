# A10 — Root-Cause Note

**ID:** PRJ-FROSCH-RCA-001  
**parent:** PRJ-FROSCH-MVR-v1  
**Engineer:** Noman  
**Date:** 2026-08-18  
**Related:** A02 , A15, A14

---

## Purpose
This note records why early geometry methods failed during development and what was changed at source so tilt and H/V measurements became stable enough for the Lead-confirmed rules.

---

## Context
- **Problem area:** bottle orientation (tilt) and label horizontal/vertical centricity  
- **Development window:** 2026-08-11 to 2026-08-18  
- **Symptom:** successive tilt / H / V approaches did not stabilise on conveyor imagery  
- **End state after this RCA:** mask-based geometry design locked for the pipeline  

---

## What was going wrong
### Observed behaviour
- Orientation and label offsets jumped or disagreed across nearby frames  
- Box-only cues did not follow the real bottle body well on conveyor views  
- Methods that looked plausible on a single frame failed once tracking and multi-frame rules were applied  

### Impact on the product decision
- Unstable geometry would push bottles into incorrect PASS/FAIL outcomes under A02  
- Defect and capacity logic could not be trusted if the bottle/label geometry itself was noisy  

---

## Root cause of earlier failures
**Bounding-box-only geometry was unstable for orientation and label centricity on conveyor views.**  

---

## Fix applied at source
The pipeline was changed to a mask-first geometry path:

1. **Orientation**  
   - Computed from PCA on the **bottle segmentation mask**  
   - Gives a principal axis aligned with the bottle body rather than the detection rectangle  

2. **H and V centricity**  
   - Computed from **label vs bottle** geometry  
   - Vertical reference is **capacity-specific** (expected V for 100 / 300 / 500 ml)  

3. **Temporal stabilisation**  
   - Multi-frame history with median / majority style aggregation  
   - Reduces single-frame spikes before finalisation  

4. **Configuration**  
   - Thresholds moved into `configs/geometry.yaml`  
   - Acceptance limits stay visible and changeable without editing core logic  

---

## Link to re-entry and validation
- Geometry method change is also reflected in **A15** (re-entry on implementation of mask-based orientation and capacity-specific V).  
- Validation against provided ground-truth sample images is recorded under **A09**.  
- Final operational rules remain those confirmed in **A02**.

---

## Status
**COMPLETE**.