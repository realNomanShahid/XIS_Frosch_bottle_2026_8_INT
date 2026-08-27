# Optimization Guide

How the Frosch bottle inspection pipeline was made fast and efficient.

---

## Goal

Run detection, segmentation, tracking, OCR, and display in real time on a single GPU while keeping measurements accurate.

---

## 1. Native TensorRT Engines

**What we did**
- Converted both models to TensorRT engines:
  - `rfdetr-medium.trt` (detection)
  - `rfdetr-seg-medium.trt` (segmentation)
- Loaded them with a custom `NativeTRTEngine` class

**Why it helps**
- TensorRT optimizes the model for the exact GPU
- Much faster than running the original PyTorch checkpoints

---

## 2. Dedicated CUDA Stream per Engine

**What we did**
- Each engine owns its own CUDA stream
- Detection and segmentation can run at the same time

**Why it helps**
- The GPU can overlap work instead of waiting for one model to finish
- Measured as higher inference FPS

---

## 3. Shared Pinned Host Buffer

**What we did**
- One reusable pinned-memory RGB buffer (`SharedPinnedRGBFrame`)
- Both engines read from the same staged frame

**Why it helps**
- Pinned memory allows faster CPU → GPU copies
- Avoids creating a new buffer every frame

---

## 4. Asynchronous Data Transfers

**What we did**
- Host → Device (H2D) copy is non-blocking
- Device → Host (D2H) copy of results is also non-blocking
- Only one stream wait is done after both engines finish

**Why it helps**
- CPU does not sit idle while data moves
- Reduces total time per frame

---

## 5. Reusable GPU Buffers

**What we did**
- Input and output TensorRT buffers are allocated once
- Same buffers are reused for every frame

**Why it helps**
- Avoids repeated memory allocation (which is slow)
- Keeps memory usage stable

---

## 6. GPU Mask Operations

**What we did**
- Orientation (PCA), centroid, and defect-overlap checks run on GPU
- A small per-frame GPU mask cache avoids repeated CPU → GPU transfers

**Why it helps**
- These calculations are much faster on GPU than on CPU
- Especially useful when many bottles or defects appear

---

## 7. Overlapped Detection + Segmentation

**What we did**
```python
model.enqueue_rgb(rgb_host)
seg_model.enqueue_rgb(rgb_host)
model.wait()
seg_model.wait()
```

**Why it helps**
- Both models start work without waiting for each other
- One of the biggest FPS gains in the pipeline

---

## 8. OCR on GPU + Throttling

**What we did**
- PaddleOCR runs on GPU
- OCR is **not** called every frame
- Only runs on the first frames of a track and then retries occasionally

**Why it helps**
- OCR is expensive
- Running it less often keeps overall FPS high while still getting a reliable capacity reading

---

## 9. Asynchronous Image Saving

**What we did**
- Bottle crops are saved using a `ThreadPoolExecutor` (background threads)

**Why it helps**
- Disk writing does not block the main inference loop
- Camera continues capturing while images are saved

---

## 10. Different Confidence Thresholds per Class

**What we did**
| Class     | Confidence |
|-----------|------------|
| bottle    | 0.70       |
| label     | 0.35       |
| capacity  | 0.35       |
| bump      | 0.50       |
| damage    | 0.30       |

**Why it helps**
- High threshold for bottle → fewer false bottles
- Lower threshold for defects → less chance of missing real damage
- Better balance between speed and accuracy

---

## 11. Lightweight Profiling

**What we did**
- Optional `--profile` flag
- Measures time of capture, preprocess, TensorRT, post-processing, OCR, saving

**Why it helps**
- Easy to see which part is slow
- Useful when tuning further

---

## Result (Sample)

| Metric                        | Value     |
|-------------------------------|-----------|
| Full pipeline FPS (with bottle) | ~18.7 FPS |
| Pure inference FPS            | ~74.7 FPS |

---

## Summary of Main Speed Techniques

1. TensorRT instead of pure PyTorch  
2. Dedicated CUDA streams + overlapped models  
3. Pinned memory + async copies  
4. Reusable buffers  
5. GPU mask math  
6. OCR only when needed  
7. Background image saving  

These changes keep the system real-time while still performing accurate orientation, centricity, defect, and capacity checks.
