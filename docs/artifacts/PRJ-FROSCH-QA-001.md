# A05 — Annotation QA

**ID:** PRJ-FROSCH-QA-001  
**parent:** PRJ-FROSCH-SCHEMA-v1  
**Batch:** frosch-bottle-5-ypv4gi  
**Reviewer:** Abdul Rafay  
**Engineer:** Noman  
**Related:** A03, A04, A06 

---

## Purpose
This artifact records the annotation quality review performed before the Frosch dataset was used for training.  
It answers who reviewed the labels, what was checked, and whether the batch was accepted.

---

## Batch under review
- **Dataset ID:** frosch-bottle-5-ypv4gi  
- **Annotation format:** COCO detection labels  
- **Train size after acceptance:** 836  
- **Validation size after acceptance:** 250  
- **Combined train+val:** 1086    

---

## Who reviewed what
- **Reviewer:** Abdul Rafay    
- **Engineer role:** Noman used only for A07 training  

### Classes checked for operational sense
| Class | Checked meaning in this project |
| ----- | -------------------------------- |
| bottle | Full bottle instance |
| label | Label region for H/V work |
| capacity | Capacity text region for OCR crop |
| bump | Raised / ping-like local defect |
| damage | Visible damage region |
| scratch | Thin line-like mark |

---

## Share reviewed
- An annotation **sample** was reviewed by Abdul Rafay.   
- An exact numeric “percent of images checked” was **not written to a separate quantitative log file**.  


---

## Edge disagreement figure
- **Millimetre edge disagreement:** N/A  
- Reason: labels are COCO detection boxes/classes, not a millimetre edge-metrology annotation schema.  

---

## Downstream effect
After this QA acceptance:
- A06 issued the dataset version used for all training  
- A07 detection and segmentation runs trained on that version  
- A08 / A17 evaluation evidence depends on those runs  

---

## Status
**COMPLETE.**  
Reviewer: Abdul Rafay.  
