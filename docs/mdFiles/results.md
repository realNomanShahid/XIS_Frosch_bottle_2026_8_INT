# Results

Sample results from the Frosch Bottle Inspection Pipeline.  
These are example runs only — not a full formal evaluation.

---

## 500 ml Bottles

| Bottle # | Defect | Tilt (°) | H offset | V offset | Capacity |
|----------|--------|----------|----------|----------|----------|
| 1 | None | 4.368 | 0.035 | 0.012 | 500 |
| 2 | None | 5.164 | 0.023 | 0.007 | 500 |
| 3 | None | 4.404 | 0.025 | 0.010 | 500 |
| 4 | None | 5.001 | 0.021 | 0.002 | 500 |
| 5 | None | 5.437 | 0.016 | 0.001 | 500 |
| 6 | None | 4.714 | 0.032 | 0.009 | 500 |
| 7 | None | 5.206 | 0.030 | 0.010 | 500 |
| 8 | None | 5.102 | 0.021 | 0.002 | 500 |
| 9 | None | 5.050 | 0.032 | 0.011 | 500 |
| 10 | None | 4.687 | 0.019 | 0.002 | 500 |
| 11 | None | 4.892 | 0.024 | 0.012 | 500 |
| 12 | bump | 4.902 | 0.025 | 0.014 | 500 |
| 13 | None | 4.749 | 0.027 | 0.006 | 500 |
| 14 | None | 4.851 | 0.024 | 0.011 | 500 |
| 15 | bump | 4.050 | 0.031 | 0.010 | 500 |
| 16 | None | 4.595 | 0.029 | 0.010 | 500 |

**Summary:** 16 bottles · 2 defective (bump) · 14 good

---

## 300 ml Bottles

| Bottle # | Defect | Tilt (°) | H offset | V offset | Capacity |
|----------|--------|----------|----------|----------|----------|
| 1 | None | 0.177 | 0.021 | 0.066 | 300 |
| 2 | None | 0.481 | 0.034 | 0.070 | 300 |
| 3 | None | 0.220 | 0.019 | 0.058 | 300 |
| 4 | damage | 0.202 | 0.032 | 0.063 | 300 |
| 5 | None | 0.174 | 0.041 | 0.061 | 300 |
| 6 | None | 0.484 | 0.049 | 0.067 | 300 |
| 7 | None | 0.170 | 0.047 | 0.071 | 300 |
| 8 | bump | 0.271 | 0.021 | 0.064 | 300 |
| 9 | damage | 0.376 | 0.019 | 0.063 | 300 |

**Summary:** 9 bottles · 3 defective (damage / bump) · 6 good

---

## 100 ml Bottles

| Bottle # | Defect | Tilt (°) | H offset | V offset | Capacity |
|----------|--------|----------|----------|----------|----------|
| 1 | bump, damage | 0.132 | 0.018 | 0.118 | 100 |
| 2 | None | 0.458 | 0.311 | 0.174 | 100 |
| 3 | None | 0.194 | 0.013 | 0.113 | 100 |
| 4 | None | 0.591 | 0.061 | 0.119 | 100 |
| 5 | None | 0.593 | 0.082 | 0.121 | 100 |
| 6 | None | 0.195 | 0.074 | 0.121 | 100 |
| 7 | None | 0.637 | 0.105 | 0.115 | 100 |
| 8 | None | 0.379 | 0.019 | 0.121 | 100 |
| 9 | None | 0.501 | 0.028 | 0.124 | 100 |
| 10 | bump | 0.217 | 0.064 | 0.116 | 100 |
| 11 | None | 0.224 | 0.054 | 0.124 | 100 |
| 12 | bump | 0.209 | 0.029 | 0.121 | 100 |
| 13 | None | 0.454 | 0.020 | 0.122 | 100 |

**Summary:** 13 bottles · 3 defective (bump / damage) · 10 good

---

## Overall Sample Summary

| Capacity | Total | Good | Defective |
|----------|-------|------|-----------|
| 500 ml | 16 | 14 | 2 |
| 300 ml | 9 | 6 | 3 |
| 100 ml | 13 | 10 | 3 |
| **All** | **38** | **30** | **8** |

---

## FPS Measurement

| Metric | What it measures | Value |
|--------|------------------|-------|
| Average FPS (bottle detected only) | Full pipeline: capture → detection → tracking → OCR → drawing → video → display | **18.66 FPS** |
| Average Inference FPS | Only AI model step: preprocess → GPU copy → TensorRT detection + segmentation → results copy | **74.66 FPS** |

---

**Note:** These are sample runs used for validation. They do not represent formal precision, recall, or mAP scores.
