# Frosch Bottle Inspection Pipeline

Live computer-vision system for inspecting Frosch bottles on a production line or from recorded frames.

The pipeline detects bottles, measures label orientation and centricity, validates defects against the bottle mask, reads capacity via OCR, and classifies each bottle as **GOOD**, **DEFECTIVE**, or **INCOMPLETE**.

---

## Features

- Live camera inference (Vimba X + Harvester) or folder of images
- Detection + instance segmentation (native TensorRT)
- GPU-accelerated orientation (PCA on bottle mask)
- Horizontal / vertical label centricity
- Defect validation (damage / bump) against bottle mask
- Capacity OCR (PaddleOCR)
- Multi-frame tracking with temporal stabilization
- Annotated + clean crop saving
- CSV + JSON logging
- Live video recording and on-screen overlay

---

## Project Structure

```
.
├── inference.py          # TensorRT engines, BottlePipeline, mask utilities, OCR
├── live_inference.py     # CLI, camera/folder input, tracking, saving, UI
├── camerasetup.md        # Camera connection guide
├── results_saving.md     # Output files and folders explained
└── README.md
```

| File | Responsibility |
|------|----------------|
| `inference.py` | Device / TensorRT setup, `NativeTRTEngine` (dedicated CUDA stream), detection + segmentation decode, mask orientation / centroid / overlap helpers, `CapacityOCR` |
| `live_inference.py` | Argument parsing, camera or folder acquisition, bottle tracking, centricity / tilt bookkeeping, defect confirmation, image / video / CSV / JSON saving, on-screen overlay |

`live_inference.py` imports from `inference.py` and drives the whole pipeline.

---

## Pipeline Flow

```
Camera / Frame folder
        ↓
Frame acquisition
        ↓
Detection + Segmentation  (TensorRT, overlapped streams)
        ↓
OCR  ·  Orientation  ·  Centricity  ·  Defect check
        ↓
Bottle tracking + temporal validation
        ↓
GOOD  /  DEFECTIVE  
        ↓
Image saving + CSV / JSON / Video
```

---

## Models

| Role | Engine |
|------|--------|
| Detection | `rfdetr-medium.trt` |
| Segmentation | `rfdetr-seg-medium.trt` |

Both engines run on dedicated CUDA streams with reusable buffers and asynchronous H2D / D2H transfers.



## Passing Rules

**GOOD**  
- Orientation = PASS  
- H-center = PASS  
- V-center = PASS  
- No confirmed defects  

**DEFECTIVE**  
Any of the following:  
- Orientation FAIL  
- H-center FAIL  
- V-center FAIL  
- Confirmed damage or bump  


---

## Orientation

Computed from the **bottle segmentation mask** (not the bounding box):

1. Extract mask pixels  
2. Covariance matrix → eigenvectors  
3. Principal axis angle  

- ≤ 45° → PASS  
- > 45° → FAIL  

---

## Centricity

```
H = (label_x − bottle_x) / bottle_width
V = (label_y − bottle_y) / bottle_height
```

- H PASS if `|H| ≤ 0.15`  
- V PASS if `|V − expected_V| ≤ 0.05`  


---

## Defect Validation

A damage / bump detection is accepted only when it overlaps the bottle mask:

```
overlap ratio ≥ 0.20
```

- 1 valid frame confirms the defect  
- 1 missing frame is tolerated before the streak resets  

---

## Bottle Finalization

A tracked bottle is finalized when either:

1. **Trigger line** is crossed (40 % of frame width), or  
2. **Missing-frame** limit is reached (20 frames)

Final measurements are majority / median aggregated from the track history.

---

## Outputs

```
./
├── bottles_data.csv
├── bottles_data.json
├── live_stream.mp4
├── image_with_annotation/
│   ├── ok/
│   └── defective/
└── image_without_annotation/
    ├── ok/
    └── defective/
```

- **Annotated crops** → boxes, tilt lines, metrics  
- **Clean crops** → original region only  
- **CSV / JSON** → Bottle #, defect, tilt, H offset, V offset, Capacity  

See `results_saving.md` for full details.

---

## Camera Setup

The live path uses **Harvester** + **Vimba X** CTI.



```python
CTI_PATH = "Enter your CTI path"
```

Update this path for your real camera.  
Full steps are in `camerasetup.md`.

---

## Installation

```bash
# Create environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install torch torchvision
pip install tensorrt
pip install opencv-python numpy supervision
pip install harvesters paddleocr
pip install psutil pynvml
```

A CUDA-capable GPU is required.

---

## How to Run

**Live camera**
```bash
python3 live_inference.py --input camera
```

**Folder of frames**
```bash
python3 live_inference.py --input folder --frame-dir /path/to/frames
```

**Optional flags**
```bash
--ocr paddle          # OCR engine (default: paddle)
--profile             # Lightweight timing output
```

Press `q` to quit.

---

## Related Docs

| File | Content |
|------|---------|
| `camerasetup.md` | Vimba X + Harvester camera connection |
| `results_saving.md` | Exact files and folders produced by a run |

---

## Notes

- Both TensorRT engines use dedicated CUDA streams and shared pinned host staging.  
- OCR runs only periodically (throttled) to keep FPS high.  
- All thresholds and business rules above match the current production configuration.  
- Do not change thresholds, model paths, or classification semantics unless explicitly requested.
