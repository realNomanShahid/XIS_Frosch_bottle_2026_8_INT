# A01 — Question Set

**ID:** TASK-INTER-54-QS  
**Task:** INTER-54 — Frosch bottle live inspection  
**Engineer:** Noman  
**Date:** 2026-08-05  
**Lead (context):** Abdul Moiz

## PURPOSE
- **Decision it drives on the line:** Accept or reject each Frosch bottle as GOOD / DEFECTIVE / INCOMPLETE based on orientation, label H/V centricity, capacity OCR, and confirmed surface defects (bump / damage).
- **What happens to an out-of-spec part:** Bottle is classified DEFECTIVE (or INCOMPLETE if required measurements are still Pending). Downstream line handling of rejected bottles is owned outside this AI package (integrator / production).

## MEASURED
- **What is judged:** Final status GOOD / DEFECTIVE / INCOMPLETE (rule-based, not a direct model class).
- **Features:** Bottle presence; label position (H/V offset vs capacity-specific reference); tilt from segmentation mask; capacity text (100 / 300 / 500 ml); defects bump / damage (scratch in model vocabulary).
- **Includes burr / flash / chamfer?** N/A — not a dimensional mm measurement task.
- **Ground-truth instrument:** N/A for mm. Operational thresholds set by project lead (pixel / normalised offset rules). Independent instrument validation (A09) not performed by engineer.
- **Part rigid?** Yes (plastic bottle body treated as rigid for mask geometry).
- **Measured at line temp or cooled?** Assumed: line ambient. If false: thermal change may shift label appearance. Review by: Lead.

## INPUTS
- **Image data:** Frames of Frosch bottles on a conveyor belt; live path via Vimba X + Harvester; also folder mode for offline tests.
- **Variants / sizes:** 100 ml, 300 ml, 500 ml.
- **Pixel-to-mm + distortion:** N/A — system reports normalised offsets and degrees, not mm dimensions.
- **How a part is identified across frames:** Multi-frame tracking (IoU + spatial association), track ID until trigger-line or missing-frame finalisation.

## SCALE
- **Line rate:** Not signed in a numeric A02 target at time of record. Operational sample inference ~74 FPS (TRT pair path); full pipeline sample ~18 FPS with bottle present.
- **Inference hardware (dev):** NVIDIA GeForce RTX 5060.
- **Runtime between restarts:** Longest observed continuous run ~30 minutes (camera / Harvester). Formal ≥2 h soak (D5) not completed.
- **Required behaviour when a part cannot be measured:** Required fields left Pending → final status INCOMPLETE (must not be silently forced to GOOD). See A12 notes for path-by-path behaviour as implemented.

## XVOID
- N/A — not an XVoid UI task.

## CONDITIONAL
- **Identifiable people in images:** Assumed none (product-only line imagery). If false: remove and escalate per handbook §5.3.
- **Customer-supplied model/dataset licence:** Dataset used from internal/shared annotation source; engineer did not annotate. Licence/retention to be confirmed on A03 by Lead if required.

## ASSUMPTIONS
1. Assumed: Lead-defined offset/tilt thresholds are the acceptance rule until a signed ±-style or rate-style A02 exists. If false: re-enter at objective. Review by: Abdul Moiz.
2. Assumed: Test images provided for operational checks are disjoint from train/val bottles. If false: evaluation is contaminated — re-seal test set. Review by: Abdul Moiz.
3. Assumed: RTX 5060-class GPU is acceptable for current evaluation hardware. If false: re-benchmark on target line PC (A17). Review by: Abdul Moiz.
