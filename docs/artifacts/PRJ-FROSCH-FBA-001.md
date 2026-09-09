# A12 — Fallback Audit

**ID:** PRJ-FROSCH-FBA-001  
**Date:** 2026-08-30  
**Engineer:** Noman  
**Lead review:** Abdul Moiz  

## Failure paths and behaviour
| Condition | Behaviour |
|-----------|-----------|
| No bottle in frame | No bottle record finalised |
| OCR cannot read capacity | Capacity not accepted as 100/300/500; does not create a false capacity pass |
| Mask missing / measurement incomplete | INCOMPLETE, not GOOD |
| Track lost after missing-frame limit | INCOMPLETE |
| Geometry still Pending | INCOMPLETE |

## Soak evidence relevant to fallbacks
- INCOMPLETE count at end of 120.66 min soak: 0  
- System continued to finalise GOOD and DEFECTIVE only for completed bottles (1009 completed)

## Prohibited patterns
- No policy of writing GOOD when required measurements are missing  
- Config load fails if required YAML is absent (src/config.py)  
- Thresholds read from configs/*.yaml  

## Status
COMPLETE.
