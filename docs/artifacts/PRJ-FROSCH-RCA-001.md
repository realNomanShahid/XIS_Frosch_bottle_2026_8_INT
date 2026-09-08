# A10 — Root-Cause Note

**ID:** PRJ-FROSCH-RCA-001  
**parent:** PRJ-FROSCH-MVR-v1  
**Engineer:** Noman  
**Date:** 2026-09-08

## Context
Multiple earlier **approaches to tilt and H/V offset** were tried and abandoned during development. Exact intermediate algorithms are **not remembered in detail** by the engineer.

## Disagreement with instrument GT
- N/A — formal GT campaign not run.

## ERROR SHAPE
- [x] Development instability on geometry methods (historical)  
- [ ] Same mm on every size (N/A)

## Causes ruled out
- Not documented per attempt (gap).

## Root cause (development)
- Geometry needed **mask-based** orientation and capacity-specific V references; box-only methods were insufficient (final design rationale).

## Fix applied at source
- PCA-on-mask tilt; capacity-keyed expected V; history/median stabilisation; config-externalised thresholds.

## Resolved?
- Operational pipeline uses the final method.  
- **Formal A09 still open**, so measurement disagreements vs independent GT remain untested.

**Status:** Informal development note only — not a closed metrology RCA.
