# A03 — Dataset Inventory

**ID:** PRJ-FROSCH-DS-INV-v1  
**Date:** 2026-08-05  
**Engineer:** Noman

## Sources
- **Dataset ID:** frosch-bottle-5-ypv4gi  
- **Capture:** Frosch bottles moving on a conveyor belt; images captured for inspection training/evaluation.  
- **Annotation:** Performed by another person/team; engineer **did not** annotate. Labels consumed as provided (COCO).  
- **Domain:** 100 / 300 / 500 ml Frosch bottles.

## Counts
| Split | Count (recorded) |
|-------|------------------|
| Train | 836 |
| Validation | 250 |
| **Total train+val** | **1086** |
| Prior project note | Dataset ID previously cited with ~1046 images — reconcile under Lead if store count differs |

## Coverage
- **Variants / sizes:** 100, 300, 500 ml  
- **Defect classes present in label set:** bottle, label, capacity, bump, damage, scratch  
- **Gaps:** Formal lighting/shift matrix not recorded by engineer.  

## Identifiable information
- Assumed product-only imagery (no identifiable people).  

## Store
- Raw / processed location: project dataset store (not committed to Git).  
- **Git rule:** images and weights must not be committed (handbook §7.2.3).

## Customer retention term
- N/A recorded — confirm with Lead if customer contract applies.
