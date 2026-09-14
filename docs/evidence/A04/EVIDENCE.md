# A04 evidence

## Primary record
The annotation schema record is:

- `docs/artifacts/PRJ-FROSCH-SCHEMA-v1.md`

## What this evidence supports
- Class definitions as consumed by INTER-54:
  - bottle, label, capacity, bump, damage, scratch
- Operational meaning of bump (ping-like), damage, scratch (thin line)
- Schema is the consumed COCO label set after QA, not a new schema invented at training time

## How the schema is reflected in code/config
- Class confidence thresholds: `configs/detection.yaml`
- Pipeline class handling in `src/inference.py` / live path
- Architecture diagram: `docs/Frosch_Architecture_Diagrams.pdf`
