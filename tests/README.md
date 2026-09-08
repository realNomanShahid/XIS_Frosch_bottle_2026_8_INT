# Frosch tests (A12 code/evidence checks)

These tests support handbook **A12** (fallback / code contracts) and basic traceability of configs and docs.

They do **not** claim:
- signed A02 objective
- A09 independent measurement validation
- full 2-hour A11 soak on line hardware
- A13 production approval

## Run

From repository root:

```bash
python -m pytest -q
python tests/run_quality_checks.py
python tests/run_pipeline_lints.py