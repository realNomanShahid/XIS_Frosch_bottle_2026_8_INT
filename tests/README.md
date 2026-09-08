# Frosch Tests (A12 Code/Evidence Checks)

These tests support handbook **A12** (fallback / code contracts) and basic traceability of configs and docs.

They do **not** claim:
- Signed A02 objective
- A09 independent measurement validation
- Full 2-hour A11 soak on line hardware
- A13 production approval

## Run

From repository root:

    python -m pytest -q
    python tests/run_quality_checks.py
    python tests/run_pipeline_lints.py

## Files

| File | Purpose |
|---|---|
| `test_config_contracts.py` | YAML exists; required keys; `load_all()` works |
| `test_postprocessing_contracts.py` | H/V/tilt/defect/Pending decision rules |
| `test_code_review_contracts.py` | Config used; no old `CAP_TYPE` constants; basic failure path |
| `test_evidence_contracts.py` | Docs / README / requirements layout |
| `run_quality_checks.py` | Writes `compliance/test_reports/A12_code_quality_report.*` |
| `run_pipeline_lints.py` | Optional Ruff report under `compliance/test_reports/linter/` |
