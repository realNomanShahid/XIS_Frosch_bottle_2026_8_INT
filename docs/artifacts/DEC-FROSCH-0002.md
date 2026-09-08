# A14 — Decision Record

**ID:** DEC-FROSCH-0002  
**Decided by:** Noman  
**Date:** 2026-09-08

## Decision
Externalise thresholds and paths into `configs/*.yaml` and load via `src/config.py` (handbook configuration obligation).

## Alternatives rejected
- Leaving magic numbers only inside `live_inference.py` / `inference.py` — harder review and traceability.

## Reversible?
- Yes.

## Affects
- Runtime configuration, tests (`test_config_contracts.py`), code review surface.
