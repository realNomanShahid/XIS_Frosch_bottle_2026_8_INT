# A09 — Measurement Validation

**ID:** PRJ-FROSCH-MVR-v1  
**parent:** TASK-INTER-54-OBJ-v1  
**parent:** PRJ-FROSCH-EVAL-v1  
**Engineer:** Noman  
**Validation window:** 2026-08-26 to 2026-08-28  
**Lead alignment:** 2026-08-31 with A02 confirmation  

## Ground-truth method
- Ground-truth **sample images** were provided to the team.  
- Validation was performed **by the project team against those ground-truth sample images**, using the Lead-defined thresholds for tilt, H offset, V offset, defects, and capacity behaviour.  
- Instrument type: image-based ground-truth samples (not a separate contact gauge instrument).  

## What was checked
- Orientation / tilt decisions vs expected sample behaviour  
- H and V centricity vs capacity-specific expected V  
- Defect flags vs visible bump/damage on samples  
- Capacity OCR path on samples with readable markings  

## Pass-rate numbers from sustained run (linked operational evidence)
From A11 soak log final row (2026-09-09, 120.66 minutes):

| Metric | Count | Share of completed |
|--------|------:|-------------------:|
| Completed bottles | 1009 | 100% |
| GOOD | 673 | 66.70% |
| DEFECTIVE | 336 | 33.30% |
| INCOMPLETE | 0 | 0.00% |

Bottle count seen (final): 1010.

## Offsets in code
Expected V by capacity and H/tilt limits live in configs/geometry.yaml as acceptance rules, not as silent gauge fudge factors.

## Sign-off
Validation method and results accepted in Lead package review with A02 confirmation (Abdul Moiz, 2026-08-31). Soak counts above recorded 2026-09-09.

## Status
COMPLETE.
