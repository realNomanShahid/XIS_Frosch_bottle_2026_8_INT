# A01 — Question Set

**ID:** TASK-INTER-54-QS  
**Task:** INTER-54 Frosch bottle live inspection  
**Engineer:** Noman  
**Date:** 2026-08-05  

## PURPOSE
- **Decision on the line:** Classify each bottle GOOD, DEFECTIVE, or INCOMPLETE from orientation, label H/V centricity, capacity OCR, and confirmed defects (bump/damage).
- **Out-of-spec handling:** DEFECTIVE or INCOMPLETE status is recorded and saved (crops, CSV, JSON). Line reject actuation is outside this package.

## MEASURED
- **Judged output:** GOOD / DEFECTIVE / INCOMPLETE.
- **Features:** Bottle detection; label H and V offsets; tilt from segmentation mask; capacity 100/300/500 ml via OCR; defects bump and damage with mask-overlap confirmation.
- **Burr/flash/chamfer:** N/A — not a millimetre dimensional measurement task.
- **Ground-truth method:** Ground-truth sample images provided to the team; validation performed against those samples and Lead-defined thresholds (see A09).
- **Part rigid:** Yes for mask geometry.
- **Temperature:** Assumed line ambient during capture. Review owner: Abdul Moiz.

## INPUTS
- Conveyor-belt Frosch bottles; live Vimba X + Harvester; folder mode for offline runs.
- Sizes: 100 ml, 300 ml, 500 ml.
- Pixel-to-mm: N/A — normalised offsets and degrees, not mm outputs.
- Cross-frame identity: multi-frame tracking until trigger-line or missing-frame finalisation.

## SCALE
- Inference hardware used: NVIDIA GeForce RTX 5060 (16303 MB GPU memory reported in soak log).
- Longest formal soak: 120.66 minutes continuous on 2026-09-09 (see A11).
- When measurement cannot complete: status INCOMPLETE (not GOOD).

## XVOID
- N/A — not an XVoid UI task.

## CONDITIONAL
- Identifiable people in images: none expected on product-only line imagery.
- Annotation origin: upstream annotators; intake QA by Rafay (see A05).

## ASSUMPTIONS
1. Lead-defined tilt/H/V/defect thresholds are the acceptance rules for INTER-54. Owner: Abdul Moiz.
2. External test / ground-truth sample images are not mixed into train/val. Owner: Noman / data provider.
