# A06 — Dataset Version

**ID:** PRJ-FROSCH-DSV-v1  
**parent:** PRJ-FROSCH-DS-INV-v1  
**parent:** PRJ-FROSCH-QA-001 (QA incomplete)  
**Date:** 2026-08-05

## Version content
- **Schema version:** PRJ-FROSCH-SCHEMA-v1 (consumed)  
- **Split key:** Image-level train/val split as provided (**not** verified by engineer as part/batch leak-free under handbook §7.2.2).  
- **Proportions:** Train 836 / Val 250 (≈ 77% / 23%). Default D2 is 80/15/5 — this project used train/val only at recorded counts; **no 5% sealed test inside this version object**.  
- **Reason not D2:** Upstream split consumed as given; no engineer-side re-split.

## LEAK CHECK
- **No part in more than one of train/val?** Not independently verified by engineer.  
- **External test bottles:** Engineer states a test set was provided by someone else and those bottles are **not** present in training/validation.  
- **How verified:** Statement of provider / engineer — **not** a scripted leak report attached here.

## Seal
- Train/val used for training.  
- External test set referenced for operational checks — **formal seal date / hash not recorded**.

**Status:** Partial. Issue a superseding DSV when leak script + hashes + sealed test manifest exist.
