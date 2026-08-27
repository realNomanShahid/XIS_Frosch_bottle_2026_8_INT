# Results Saving Guide

Overview of what the pipeline saves and where.

---

## Files Created

| File | Format | Location | Description |
|------|--------|----------|-------------|
| `bottles_data.csv` | CSV | Current working directory | Log of every completed bottle |
| `bottles_data.json` | JSON | Current working directory | Same data in JSON format |
| `live_stream.mp4` | MP4 | Current working directory | Recorded live display video |
| Bottle crops | JPG | See folder structure below | Annotated and original images |

---

## Folder Structure

```
./
├── bottles_data.csv
├── bottles_data.json
├── live_stream.mp4
├── image_with_annotation/
│   ├── ok/
│   │   └── bottle_001.jpg
│   └── defective/
│       └── bottle_002.jpg
└── image_without_annotation/
    ├── ok/
    │   └── bottle_001.jpg
    └── defective/
        └── bottle_002.jpg
```

- **`image_with_annotation/`** → crops with boxes, labels, tilt lines, and metrics drawn  
- **`image_without_annotation/`** → clean original crops  
- **`ok/`** → bottles classified as GOOD  
- **`defective/`** → bottles classified as DEFECTIVE or INCOMPLETE  

---

## What Each Bottle Record Contains

CSV / JSON columns:
- Bottle #
- defect (e.g. damage, bump, or None)
- tilt
- H offset
- V offset
- Capacity

---

## When Files Are Written

- **CSV** → header written at start; one row appended each time a bottle is saved  
- **Images** → saved as soon as a bottle is finalized (trigger line crossed or track lost)  
- **JSON** → written once at the end of the run  
- **Video** → frames written continuously; file closed at the end  

---

## End of Run

When the program stops (user presses `q`, all folder frames processed, or Ctrl+C):

1. Any remaining unfinished bottles are finalized and saved if possible  
2. `bottles_data.json` is written  
3. Summary is printed (total, defective, average FPS)  
4. Video writer is released  
5. Camera / folder source is closed  

---

**All paths are relative to the directory where you launch the script.**
