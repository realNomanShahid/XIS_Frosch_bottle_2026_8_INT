# A11 — Soak Test

**ID:** PRJ-FROSCH-SOAK-001  
**Commit tested:** (fill SHA)  
**Date:** 2026-09-08  
**Engineer:** Noman

## Environment
- **Camera path:** Vimba X + Harvester  
- **GPU:** NVIDIA GeForce RTX 5060  
- **Must match target line spec?** Not confirmed as production line PC.

## Duration
- **Observed longest continuous run:** ~**30 minutes**  
- **Handbook D5 minimum:** 2 hours continuous  
- **Meets D5?** **NO**

## Frames / mix
- Live camera traffic with bottles on belt (qualitative).  
- Structured mix counts (no part / partial / unsegmentable): **Not logged.**

## MEMORY
- **Crash / OOM note:** None observed in 30 min run.  
- **Growth plateau vs D4:** **Not measured** (no A11 instrumentation log).  

## LATENCY / throughput
- Sample only (see A17); not a locked soak percentile report.

## RECOVERY
- Not formally tested (camera disconnect, restart, dropped frame scripts).

## Verdict
- **FAIL handbook soak gate** (duration & metrics incomplete).  
- Useful as **engineering smoke evidence only**.

**Verified by lead:** Open
