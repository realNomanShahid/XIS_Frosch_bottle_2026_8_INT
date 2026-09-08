# A12 — Fallback Audit

**ID:** PRJ-FROSCH-FBA-001  
**Commit audited:** (fill SHA)  
**Date:** 2026-09-08  
**Engineer:** Noman

## FAILURE PATHS (as stated by engineer)

| Path | Condition | Returns / behaviour | Explicit absent / safe? |
|------|-----------|---------------------|-------------------------|
| No bottle in frame | Empty scene | Nothing (no bottle finalisation) | Yes — no fabricated GOOD |
| OCR fails | Cannot read capacity | Capacity not recorded; UI may show `00ml` | **Review:** ensure final status does not treat `00` as a real capacity pass; prefer Pending/unknown |
| Mask missing | No usable bottle mask | Engineer states bottles **fail** | **Review:** handbook prefers explicit Pending/INCOMPLETE over silent FAIL if measurement was impossible |
| Track lost | Missing frames beyond limit | **INCOMPLETE** | Yes — aligns with Pending≠GOOD |
| Geometry Pending | Insufficient history | **INCOMPLETE** | Yes |

## PROHIBITED PATTERNS (§5.1.6) — self check
- [ ] Previous measurement returned when no contour found — not intended  
- [ ] except/catch returning a fake dimension — N/A mm; watch OCR `00ml` display  
- [ ] Hardcoded GOOD when config missing — thresholds moved to YAML; missing YAML should fail load  
- [ ] Result clamped into “always pass” — not intended  
- [ ] Stale track promoted to GOOD — finalisation rules use INCOMPLETE when Pending  

**Any prohibited pattern confirmed fixed?** Partially documented; **OCR `00ml` and mask-missing→fail** need Lead review for handbook purity.

## AI-assisted code
- Present in project history. Broad except handlers reviewed in tests (`test_code_review_contracts.py`).

## BAD INPUT
- Config load fails hard if YAML missing (`src/config.py`).  
- Empty frame: no bottle record.

## Automated support
- `tests/` contract suite + `run_quality_checks.py` support code-side A12 checks.  
- They **do not** replace this audit narrative.

**Status:** Draft audit — Lead review required before claiming A12 closed.
