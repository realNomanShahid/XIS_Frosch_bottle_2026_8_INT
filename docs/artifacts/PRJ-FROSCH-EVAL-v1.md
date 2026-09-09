# A08 — Evaluation

**ID:** PRJ-FROSCH-EVAL-v1  
**parent:** TASK-INTER-54-OBJ-v1  
**parent:** PRJ-FROSCH-DSV-v1  
**parent:** PRJ-FROSCH-RUN-DET-0001  
**Engineer:** Noman    
**Related:** A07 , A09, A11, A17  

---

## Evaluation period
- **Model / operational evaluation window:** 2026-08-19 to 2026-08-28  
- **Sustained run evidence:** soak on 2026-09-09 (detail in A11)  

---

## Criterion (what “pass” means)
Evaluation is against the **Lead-confirmed A02 rules**, not against a millimetre gauge product:

| Check | Rule used in evaluation |
| ----- | ------------------------ |
| Orientation / tilt | Tilt ≤ 45° |
| Horizontal centricity (H) | Absolute H ≤ 0.15 |
| Vertical centricity (V) | Absolute error vs expected_V(capacity) ≤ 0.05 |
| Defects | Mask overlap ≥ 0.30 with confirmation streak |
| Capacity | OCR path for 100 / 300 / 500 ml; invalid/unknown does not invent a pass |
| Final status | GOOD / DEFECTIVE / INCOMPLETE |

Pending or incomplete measurements are not scored as GOOD.

---

## Detection quality evidence
Detection quality is evidenced by:

- Per-class **Precision / Recall / AP50** from training evaluation  
- **Confusion matrix** at IoU ≥ 0.50  
- Full numeric discussion and class table retained under **A17** (PRJ-FROSCH-MPR-v1)

### Classes covered in the chart
- bottle  
- label  
- capacity  
- bump  
- damage  
- scratch  

---

## Segmentation role in evaluation
- Segmentation is not scored as a separate public class table in this A08 body.  
- It is required for mask-based orientation and for validating defect overlap against the bottle region.  
- Segmentation training parent: PRJ-FROSCH-RUN-SEG-0001  

---

## Operational sample runs
Folder samples under the repository `results/` tree:

| Folder | Content |
| ------ | ------- |
| results/bottle1 | CSV + JSON sample run (capacity group in project samples) |
| results/bottle2 | CSV + JSON sample run |
| results/bottle3 | CSV + JSON sample run |

Each sample records bottle-level fields used in the product output, including:

- defect  
- tilt  
- H offset  
- V offset  
- Capacity 

---

## How the pieces fit together
1. **A07** provides trained detection (and segmentation) weights.  
2. **A17** records detection quality charts and sample FPS.  
3. **This A08** states the rule criteria and points to sample runs + soak counts.  
4. **A09** records validation against provided ground-truth sample images.  
5. **A11** records the 120+ minute continuous soak log.

---

## Boundaries
- This evaluation does not claim a customer-signed ±mm accuracy product.  
- This evaluation does not replace A09 (GT sample validation) or A11 (soak).  
- Single overall “accuracy %” is not used as the handbook acceptance headline; class charts + rule outcomes + soak counts are the evidence set.

---

## Status
**COMPLETE**.