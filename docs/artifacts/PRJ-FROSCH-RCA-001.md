# A10 — Root-Cause Note

**ID:** PRJ-FROSCH-RCA-001  
**parent:** PRJ-FROSCH-MVR-v1  
**Engineer:** Noman  
**Date:** 2026-08-18  

## Context
During 2026-08-11 to 2026-08-18, multiple tilt and H/V offset approaches were tried and rejected before the final mask-based design.

## Root cause of earlier failures
Bounding-box-only geometry was unstable for orientation and label centricity on conveyor views.

## Fix applied at source
- Orientation from PCA on bottle segmentation mask  
- H/V from label vs bottle geometry with capacity-specific expected V  
- Temporal history with median/majority stabilisation  
- Thresholds externalised to configs/geometry.yaml  

## Status
COMPLETE as development RCA for geometry iteration.
