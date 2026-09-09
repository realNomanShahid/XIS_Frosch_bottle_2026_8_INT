# A11 — Soak Test

**ID:** PRJ-FROSCH-SOAK-001  
**Date:** 2026-09-09  
**Engineer:** Noman  
**Start timestamp:** 2026-09-09 09:07:39  
**Final timestamp:** 2026-09-09 10:55:19  
**Elapsed:** 120.66 minutes  

## Environment
- Live pipeline path with GPU monitoring log  
- GPU memory total: 16303 MB  
- Hardware class: NVIDIA GeForce RTX 5060  

## Duration vs handbook D5
- Required minimum: 2 hours continuous  
- Achieved: 120.66 minutes  
- Meets D5 duration: YES  

## Periodic log (from soak CSV)

| elapsed_min | cpu% | gpu_util% | gpu_mem_used_mb | completed | good | defective | incomplete | seen |
|------------:|-----:|----------:|----------------:|----------:|-----:|----------:|-----------:|-----:|
| 0 | 7.9 | 0 | 8535.6 | 0 | 0 | 0 | 0 | 0 |
| 15 | 2.3 | 26 | 8969.6 | 140 | 94 | 46 | 0 | 140 |
| 30 | 4.4 | 26 | 8969.6 | 283 | 189 | 94 | 0 | 283 |
| 45 | 2.2 | 26 | 8969.6 | 425 | 284 | 141 | 0 | 425 |
| 60.01 | 38.0 | 0 | 8969.6 | 567 | 378 | 189 | 0 | 568 |
| 75.01 | 3.9 | 25 | 8969.6 | 711 | 474 | 237 | 0 | 711 |
| 90.01 | 8.7 | 39 | 13468.9 | 846 | 564 | 282 | 0 | 846 |
| 105.02 | 39.6 | 0 | 8969.6 | 985 | 657 | 328 | 0 | 986 |
| 120.66 | 31.7 | 0 | 8969.6 | 1009 | 673 | 336 | 0 | 1010 |

## Final totals
- Completed bottles: 1009  
- GOOD: 673 (66.70% of completed)  
- DEFECTIVE: 336 (33.30% of completed)  
- INCOMPLETE: 0  
- Tracked bottles at final snapshot: 1  
- Bottle count seen: 1010  

## Memory
- Start used: 8535.6 MB  
- Steady used: 8969.6 MB for most samples  
- Peak used in log: 13468.9 MB at 90.01 minutes  
- End used: 8969.6 MB  
- Hard crash / OOM stop: not observed; run reached final row at 120.66 minutes  

## Verdict
PASS on duration (2 h continuous completed). Classification and resource rows above are the recorded evidence.

## Status
COMPLETE.
