# A14 — Decision Record

**ID:** DEC-FROSCH-0001  
**Decided by:** Noman  
**Lead context:** Abdul Moiz  
**Date:** 2026-08-10  

## Decision
Use RF-DETR Medium for detection and RF-DETR Seg Medium for segmentation, exported to TensorRT, with PaddleOCR for capacity and rule-based GOOD/DEFECTIVE/INCOMPLETE finalisation.

## Alternatives rejected
- Box-only geometry for tilt and H/V: unstable on conveyor views  
- Early stopping: not used; full 100-epoch schedule retained  
- Data augmentation: not applied for this training run  

## Status
COMPLETE.
