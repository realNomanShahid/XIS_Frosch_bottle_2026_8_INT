# A01 — Question Set

**ID:** TASK-INTER-54-QS  
**Engineer:** Noman  
**Date:** 2026-08-05  
**Lead context:** Abdul Moiz  
**Related:** A02,A03,A13 

---

## Purpose of this artifact
The question set frames the industrial problem before models or thresholds are locked.  
It records what decision the system supports, what is measured, what data enters the system, and at what scale the solution must run.

---

## PURPOSE

### Decision driven on the line
- Classify each Frosch bottle as **GOOD**, **DEFECTIVE**, or **INCOMPLETE**.
- Classification is based on:
  - bottle orientation (tilt)
  - label horizontal centricity (H)
  - label vertical centricity (V) versus a capacity-specific reference
  - capacity text read by OCR (100 / 300 / 500 ml)
  - confirmed surface defects (bump / damage)

### What happens to an out-of-spec bottle
- Status is recorded in the pipeline outputs (CSV / JSON / saved crops).
- **DEFECTIVE** or **INCOMPLETE** is the AI package decision.
- Physical reject actuation on the conveyor (PLC / pusher / divert) is outside this software package and owned by line integration.

### Why this exists
Manual or purely visual checks are not sufficient for consistent multi-check inspection (geometry + capacity + defects) at conveyor speed.  
The system provides a repeatable, logged decision per bottle.

---

## MEASURED

### What is judged
| Output | Meaning |
| ------ | ------- |
| GOOD | Required checks pass and no confirmed defect |
| DEFECTIVE | A required check fails or a defect is confirmed |
| INCOMPLETE | Required measurement could not be completed (Pending path) |

### Features involved
- Bottle presence and tracking across frames  
- Segmentation mask of the bottle (and label region as needed)  
- Tilt / orientation from the bottle mask  
- Horizontal label offset (H)  
- Vertical label offset (V) versus expected V for the detected capacity  
- Capacity class via OCR on the capacity region  
- Defect classes used in operation: bump, damage (scratch exists in the label vocabulary)

### What this is not
- **Not** a millimetre dimensional metrology product (no burr / flash / chamfer mm outputs).  
- **Not** a single “defect-only” classifier without geometry and capacity rules.

### Ground-truth / reference method
- Ground-truth **sample images** were provided to the team.  
- Validation was performed against those samples under Lead-defined thresholds (see A09).  
- Operational acceptance rules are the Lead-confirmed tilt / H / V / defect limits (see A02).

### Part and process notes
- Bottle body is treated as rigid for mask geometry.  
- Capture is conveyor-belt product imagery under line ambient conditions.

---

## INPUTS

### Image / sensor inputs
- Live frames from **Vimba X + Harvester** camera path  
- Offline **folder** of frames for testing and regression  

### Product variants
- 100 ml Frosch bottles  
- 300 ml Frosch bottles  
- 500 ml Frosch bottles  

### Identification across frames
- Multi-frame **tracking** associates the same bottle until finalisation  
- Finalisation uses trigger-line and/or missing-frame rules  

### Calibration notes
- Pixel-to-mm conversion is **N/A** for this package: outputs are normalised offsets and degrees, not mm feature sizes.  
- Distortion correction as a formal camera-calibration deliverable is outside the recorded INTER-54 AI package scope.

---

## SCALE

### Hardware used for evaluation
- **GPU:** NVIDIA GeForce RTX 5060  
- **GPU memory total observed in soak log:** 16303 MB  

### Runtime evidence
- Formal soak on **2026-09-09** ran **120+ minutes** continuous  
- Final soak classification totals: 1009 completed bottles (673 GOOD, 336 DEFECTIVE, 0 INCOMPLETE)

### Behaviour when a bottle cannot be measured
- Required fields remain **Pending** where measurement is missing  
- Final status becomes **INCOMPLETE**  
- The system must **not** invent **GOOD** for a missing measurement  

### Throughput
- Sample inference and full-pipeline FPS are recorded under A17  
- Soak provides sustained classification counts rather than a single FPS headline

---

## CONDITIONAL

### People in imagery
- Expected content is product-only conveyor imagery.  
- No person-identification use case is in scope for this package.

### Data / annotation origin
- Dataset ID: `frosch-bottle-5-ypv4gi`  
- Annotations produced upstream; intake QA by **Abdul Rafay** (A05)  
- Engineer Noman consumed the QA-accepted train/val split for training  

### Licence / retention
- Dataset and weights are kept outside Git in the project dataset / model store.  

---

## ASSUMPTIONS
1. Lead-defined tilt, H, V, and defect thresholds are the acceptance rules for INTER-54 until a later superseding A02 is issued.  
2. Ground-truth sample images used for A09 are not mixed into the training set. **Owner:** Noman / data provider.  
3. RTX 5060-class hardware is valid for this evaluation package. **Owner:** Abdul Moiz if a different line PC is mandated later.  

---

## Downstream artifacts that close this question set
| Next artifact | Role |
| ------------- | ---- |
| A02 | Turns this framing into a confirmed objective |
| A03–A06 | Dataset inventory, schema, QA, version |
| A07 | Training runs |
| A08–A09 | Evaluation and validation |
| A11–A12 | Soak and fallback behaviour |
| A13 | Evaluation package manifest |

---

## Status
**COMPLETE.**  
