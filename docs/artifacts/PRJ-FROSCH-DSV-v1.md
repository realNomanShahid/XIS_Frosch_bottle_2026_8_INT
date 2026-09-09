# A06 — Dataset Version

**ID:** PRJ-FROSCH-DSV-v1  
**parent:** PRJ-FROSCH-DS-INV-v1  
**parent:** PRJ-FROSCH-QA-001  
**Date issued:** 2026-08-05  
**Engineer:** Noman    


---

## Version content
- **Schema parent:** PRJ-FROSCH-SCHEMA-v1  
- **Inventory parent:** PRJ-FROSCH-DS-INV-v1  
- **QA parent:** PRJ-FROSCH-QA-001  
- **Dataset ID:** frosch-bottle-5-ypv4gi  
- **Train size:** 836 images  
- **Validation size:** 250 images  
- **Combined train+val:** 1086 images  
- **QA outcome:** accepted by **Abdul Rafay**  


---

## Quality gate before issue
- Annotation sample reviewed by Rafay (A05)    
- Schema classes aligned with pipeline needs: bottle, label, capacity, bump, damage, scratch  

---

## Leak / hold-out notes
- Training and validation images come from the provided train/val split.   
- Operational sample folders under `results/` are run outputs, not additional training data.

---

## Change policy
If images, labels, or the train/val membership change, a **new** A06 version must be issued.  

---

## Status
**COMPLETE.**  
