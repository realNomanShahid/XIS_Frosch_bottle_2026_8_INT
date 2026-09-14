# A02 evidence

- `docs/artifacts/A02.md`

## What this evidence supports
- Seven-element objective for the Frosch pipeline
- Lead-confirmed rules: tilt ≤ 45°, |H| ≤ 0.15, |V − expected_V(capacity)| ≤ 0.05, defect overlap ≥ 0.30
- Method stack: RF-DETR Medium det, RF-DETR Seg Medium, TensorRT, PaddleOCR, `configs/*.yaml`


## Related config evidence (runtime form of the objective targets)
- `configs/geometry.yaml`
- `configs/tracking.yaml`
- `configs/detection.yaml`
- `configs/ocr.yaml`
