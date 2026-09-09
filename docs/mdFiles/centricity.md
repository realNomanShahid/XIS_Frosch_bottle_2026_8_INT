# Label Centricity (H / V) — Frosch Bottle Inspection

---

## 1. What “centricity” means here

On each bottle we care whether the **label sits in the right place** on the bottle body.

| Check | Question in simple words |
|-------|---------------------------|
| **H (horizontal)** | Is the label too far left or right on the bottle? |
| **V (vertical)** | Is the label too high or too low on the bottle? |

If H or V is outside the allowed band → that measurement is **FAIL** → bottle can become **DEFECTIVE** (when finalised).  
If we do not yet have a stable reading → **Pending** → bottle can become **INCOMPLETE**, not automatically DEFECTIVE.

---

## 2. What we use in the current system

### Inputs
- **Bottle** box and/or **bottle segmentation mask** (centre of the bottle)
- **Label** box (centre of the label)
- **Capacity** from OCR: `100`, `300`, or `500` ml (selects the vertical reference)

### Formulas

**Horizontal offset**

```text
H = (label_center_x − bottle_center_x) / bottle_width
```

**Vertical offset**

```text
V = (label_center_y − bottle_center_y) / bottle_height
```

Both are **normalised** (roughly in a −1…1 style range). That way different image sizes and bottle scales stay comparable.

### Pass / fail rules (from `configs/geometry.yaml`)

| Rule | Value |
|------|--------|
| H PASS | \|H\| ≤ 0.15 |
| V PASS | \|V − expected_V\| ≤ 0.05 |

### Expected vertical position by capacity

Label height is **not** the same for every bottle size, so V is compared to a **capacity-specific** target:

| Capacity | Expected V |
|----------|------------|
| 100 ml | 0.12 |
| 300 ml | 0.07 |
| 500 ml | 0.01 |

Example: a 500 ml bottle with V ≈ 0.01 is centred vertically for that type; the same V on a 100 ml bottle would be wrong for that type’s reference.

### Stability across frames
- Keep a short **history** of H and V (window size 5, need at least 3 reliable samples)
- Ignore sudden impossible jumps (spatial jump tolerance 0.08)
- Final value uses a **stable / median-style** aggregate so one noisy frame does not decide the bottle

### Where centres come from
- Prefer **mask-based** bottle centre when the segmentation mask is available  
- Label centre from the label detection box  
- If the mask is missing and we cannot measure reliably → leave centricity **Pending** (do not invent a PASS)

---

## 3. Four earlier methods that did **not** work for this project

These are approaches tried (or equivalent attempts) during development that failed on real conveyor images. They are recorded so we do not repeat them.

### Method 1 — Bounding box only (no mask)

**Idea:** Use only detection boxes for bottle and label. Take box centres and compute H/V.

**Why it failed**
- Box centre is not the true bottle body centre when the box is loose or shifted
- Tilted bottles make the box centre drift
- H/V jumped frame to frame even when the label looked fine to the eye

**Result:** Unstable PASS/FAIL, many false DEFECTIVE or flickering decisions.

---

### Method 2 — Same vertical target for all bottle sizes

**Idea:** Use one global “ideal V” (for example always 0) for 100, 300, and 500 ml.

**Why it failed**
- Real Frosch labels sit at **different heights** on different capacities
- A correct 100 ml label failed the global rule; a correct 500 ml label failed another way

**Result:** Systematic errors by capacity — not random noise.

---

### Method 3 — Single-frame decision (no history)

**Idea:** Compute H/V on the current frame only and immediately PASS/FAIL.

**Why it failed**
- OCR and detection flicker for a frame or two
- One bad frame marked a good bottle DEFECTIVE
- Conveyor motion and partial views created outliers

**Result:** Noisy decisions; not acceptable for line use.

---

### Method 4 — Pixel distances without normalising by bottle size

**Idea:** Use raw pixel gaps (label_x − bottle_x) with a fixed pixel threshold.

**Why it failed**
- Bottle appears larger or smaller when distance to camera changes
- Same physical offset looked “OK” in pixels on one frame and “bad” on another
- Thresholds could not transfer across resolutions or crop sizes

**Result:** Thresholds that worked on one recording failed on another.

---

## 4. What works now (final approach)

| Piece | Choice | Why |
|-------|--------|-----|
| Bottle centre | Mask centroid when possible | Follows the real body, not a loose box |
| Label centre | Label detection box centre | Stable enough for H/V once bottle centre is good |
| H rule | \|H\| ≤ 0.15 | Shared horizontal tolerance |
| V rule | \|V − expected_V(capacity)\| ≤ 0.05 | Respects different label heights per size |
| Capacity | OCR → 100 / 300 / 500 | Selects the correct expected V |
| Time | History + median/stable aggregate | One frame cannot dominate |
| Missing data | Pending → INCOMPLETE | No silent PASS/GOOD |

**End-to-end in one sentence**

> Find bottle and label, measure normalised H and V, compare V to the expected value for the OCR capacity, smooth over a few frames, then PASS/FAIL — or Pending if the measurement is not ready.

---

## 5. How this ties to the rest of the pipeline

1. Detector finds bottle, label, capacity region, defects  
2. Segmenter provides bottle mask (for centre and tilt)  
3. OCR reads capacity (or leaves it unknown)  
4. **Centricity** computes H/V and PASS/FAIL/Pending  
5. Tracker keeps history until trigger line or missing-frame finalisation  
6. Final status: GOOD / DEFECTIVE / INCOMPLETE  

Tilt (orientation) is separate: it uses PCA on the bottle mask and a 45° limit. Centricity is only about **label position** on the bottle.

---

## 6. Config location

All numeric limits live in config (not hardcoded in logic):

- `configs/geometry.yaml` — H/V tolerances, expected V by capacity, history window, jump tolerance  

Change thresholds there; do not bury new magic numbers in code.

---

## 7. Short summary

| Topic | Answer |
|-------|--------|
| What we measure | Label position vs bottle (H and V) |
| What failed before | Box-only centres; one V for all sizes; single-frame decisions; raw pixel thresholds |
| What works | Mask-based bottle centre, capacity-specific expected V, normalised offsets, multi-frame stabilisation, Pending when unknown |
| Output | PASS / FAIL / Pending → feeds GOOD / DEFECTIVE / INCOMPLETE |

