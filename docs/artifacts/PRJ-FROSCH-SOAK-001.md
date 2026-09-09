# A11 — Soak Test

**ID:** PRJ-FROSCH-SOAK-001  
**Date:** 2026-09-09  
**Engineer:** Noman    
**Related:** A02, A08, A12, A17 
---

## Purpose
This artifact records a continuous live soak of the Frosch inspection pipeline.  
It shows duration, resource behaviour, and bottle classification totals under sustained operation.

---

## Run identity
| Field | Value |
| ----- | ----- |
| Start timestamp | 2026-09-09 09:07:39 |
| Final timestamp | 2026-09-09 11:15:02 |
| Elapsed | 120+ minutes (log final metrics row at 120.66 minutes) |
| Engineer | Noman |
| Mode | Live pipeline with GPU monitoring log |

---

## Environment
- **Pipeline path:** live inspection stack (detect → segment → track → OCR → geometry → classify → save)  
- **Hardware class:** NVIDIA GeForce RTX 5060  
- **GPU memory total:** 16303 MB  
- **Monitoring:** periodic CPU %, GPU util %, GPU memory used, bottle counters  

---

## Duration vs handbook D5
| Requirement | Result |
| ----------- | ------ |
| Handbook D5 minimum | 2 hours continuous |
| Achieved | 120+ minutes continuous (125+ minutes wall span in run header; metrics log through 120.66 minutes) |
| Meets D5 duration | **YES** |
| Hard stop / crash before end | Not observed |

---

## Periodic log (from soak CSV)

| elapsed_min | cpu% | gpu_util% | gpu_mem_used_mb | completed | good | defective | incomplete | seen |
| ----------: | ---: | --------: | --------------: | --------: | ---: | --------: | ---------: | ---: |
| 0 | 7.9 | 0 | 8535.6 | 0 | 0 | 0 | 0 | 0 |
| 15 | 2.3 | 26 | 8969.6 | 140 | 94 | 46 | 0 | 140 |
| 30 | 4.4 | 26 | 8969.6 | 283 | 189 | 94 | 0 | 283 |
| 45 | 2.2 | 26 | 8969.6 | 425 | 284 | 141 | 0 | 425 |
| 60.01 | 38.0 | 0 | 8969.6 | 567 | 378 | 189 | 0 | 568 |
| 75.01 | 3.9 | 25 | 8969.6 | 711 | 474 | 237 | 0 | 711 |
| 90.01 | 8.7 | 39 | 13468.9 | 846 | 564 | 282 | 0 | 846 |
| 105.02 | 39.6 | 0 | 8969.6 | 985 | 657 | 328 | 0 | 986 |
| 120.66 | 31.7 | 0 | 8969.6 | 1009 | 673 | 336 | 0 | 1010 |

---

## Final classification totals
| Metric | Count | Share of completed |
| ------ | ----: | -----------------: |
| Completed bottles | 1009 | 100% |
| GOOD | 673 | 66.70% |
| DEFECTIVE | 336 | 33.30% |
| INCOMPLETE | 0 | 0.00% |
| Bottle count seen | 1010 | — |
| Tracked bottles at final snapshot | 1 | — |

---

## Memory and stability
| Point | GPU mem used (MB) |
| ----- | ----------------: |
| Start | 8535.6 |
| Steady level for most samples | 8969.6 |
| Peak in log | 13468.9 at 90.01 minutes |
| End | 8969.6 |

- **Hard crash:** not observed  
- **OOM stop:** not observed  
- **Run completion:** metrics reached the final logged row at 120+ minutes; wall clock end recorded as 11:15:02  


---

## What this soak test does 
- Continuous operation past the 2-hour D5 duration bar  
- Recorded resource samples and bottle status counts from the soak CSV  
- No crash/OOM termination in this run  

---

## Verdict
**PASS** on duration (2 h continuous completed).  
Classification and resource rows above are the recorded evidence.

---

## Status
**COMPLETE.**