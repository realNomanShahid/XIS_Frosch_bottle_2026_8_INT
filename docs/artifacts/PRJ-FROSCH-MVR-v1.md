# A09 — Measurement Validation

**ID:** PRJ-FROSCH-MVR-v1  
**parent:** TASK-INTER-54-OBJ-v1  
**parent:** PRJ-FROSCH-EVAL-v1  
**Engineer:** Noman  
**Date:** 2026-09-08

## Ground-truth instrument
- **None used by engineer.**  
- Project lead specified tolerance thresholds (normalised H/V, tilt degrees, defect rules). Engineer implemented and ran against those rules.

## Parts measured independently
- Count / variants under controlled metrology: **Not performed / not known to engineer.**

## REPEATABILITY (30× unmoved part)
- **Not performed.**

## Criterion
- within [ACCURACY_REQ]: **N/A** (not mm task; no signed requirement).

## Offsets or correction constants in code
- **Present as rule thresholds** (expected V by capacity, H tolerance, tilt limit) — these are **acceptance rules**, not hidden mm bias corrections.  
- Handbook offset prohibition targets **silent correction of disagreement with ground truth**. No instrument GT loop was closed by applying a fudge factor to match a gauge.

## Measurements defensible?
- **Not yet** under handbook A09 standard (no independent instrument campaign).  
- **Sign-off:** Open — Abdul Moiz

**Status:** **MISSING / NOT PERFORMED** as formal A09.
