# Frosch INTER-54 Artifact Index

**Engineer:** Noman  
**Lead:** Abdul Moiz  
---

## Purpose of this folder
This folder holds the A01–A17 handbook artifacts.  
Use this index to see the project timeline, who signed and which file answers which review question.

---

## People
| Role | Name |
| ---- | ---- |
| Engineer | Noman |
| AI Lead | Abdul Moiz |
| Annotation QA reviewer | Abdul Rafay |

---

## Timeline

| Date | Activity |
| ---- | -------- |
| 2026-08-05 | Dataset intake; A05 QA by Abdul Rafay; A03 inventory, A04 schema, A06 dataset version |
| 2026-08-06 to 2026-08-10 | A07 detection and segmentation training |
| 2026-08-11 to 2026-08-18 | Geometry H/V/tilt iteration; A10 RCA; A15 re-entry |
| 2026-08-19 to 2026-08-25 | End-to-end pipeline integration (detect → track → OCR → classify → save) |
| 2026-08-26 to 2026-08-28 | A09 validation on ground-truth sample images; A17 performance report |
| 2026-08-30 to 2026-08-31 | A12 fallback audit; A02 Lead confirm; A13 evaluation manifest |
| 2026-09-09 | A11 soak 120+ minutes (1009 completed bottles) |

---

## Answers to common review questions

### A05 — Annotation QA
- **Who reviewed:** Abdul Rafay  
- **What:** annotation sample for frosch-bottle-5-ypv4gi  
- **Outcome:** dataset accepted for train 836 / val 250  

### A09 — Measurement validation
- **Ground-truth method:** ground-truth sample images provided to the team 
- **Pass-rate evidence from soak (A11 final row):** GOOD 673 / 1009 completed (66.70%); DEFECTIVE 336 / 1009 (33.30%); INCOMPLETE 0

### A11 — Soak
- **Date:** 2026-09-09  
- **Duration:** 120+ minutes continuous  
- **Completed bottles:** 1009  

---

## Artifact map (A01–A17)

| ID | File | What it records |
| -- | ---- | --------------- |
| A01 | TASK-INTER-54-QS.md | Question set / problem framing |
| A02 | TASK-INTER-54-OBJ-v1.md | Objective (confirmed by Abdul Moiz) |
| A03 | PRJ-FROSCH-DS-INV-v1.md | Dataset inventory |
| A04 | PRJ-FROSCH-SCHEMA-v1.md | Annotation schema as consumed |
| A05 | PRJ-FROSCH-QA-001.md | Annotation QA (Abdul Rafay) |
| A06 | PRJ-FROSCH-DSV-v1.md | Dataset version used for training |
| A07 | PRJ-FROSCH-RUN-DET-0001.md | Detection training run |
| A07 | PRJ-FROSCH-RUN-SEG-0001.md | Segmentation training run |
| A08 | PRJ-FROSCH-EVAL-v1.md | Evaluation against A02 rules |
| A09 | PRJ-FROSCH-MVR-v1.md | Measurement validation |
| A10 | PRJ-FROSCH-RCA-001.md | Geometry root-cause note |
| A11 | PRJ-FROSCH-SOAK-001.md | Soak test log and totals |
| A12 | PRJ-FROSCH-FBA-001.md | Fallback audit |
| A13 | PRJ-FROSCH-REL-v1.md | Evaluation release manifest |
| A14 | DEC-FROSCH-0001.md / DEC-FROSCH-0002.md | Decision records |
| A15 | TASK-INTER-54-RE-1.md | Geometry re-entry |
| A16 | EXC-NONE.md | No handbook exception |
| A17 | PRJ-FROSCH-MPR-v1.md | Model performance report |

---

## Reading order for reviewers
1. A01 → A02 (what problem and target)  
2. A03 → A06 (data)  
3. A07 → A17 (train and metrics)  
4. A08 → A09 (evaluate and validate)  
5. A11 → A12 (soak and failure behaviour)  
6. A13 → A14 / A15 / A16 (package, decisions, re-entry, exceptions)

---

## File list
All A01–A17 markdown files listed above are in this folder.