# A04 — Annotation Schema

**ID:** PRJ-FROSCH-SCHEMA-v1  
**Date:** 2026-08-05  
**Recorded by:** Noman  
**Upstream labels:** Consumed COCO annotations from dataset provider  

## Classes
| Class | Definition used in this project |
|-------|----------------------------------|
| bottle | Full bottle instance |
| label | Label region for H/V centricity |
| capacity | Capacity text region for OCR |
| bump | Local raised / ping-like surface defect |
| damage | Visible damage region on bottle |
| scratch | Thin line-like surface mark |

## Edge policy
- Upstream COCO boxes/labels consumed as provided after QA by Rafay.  
- Ambiguous cases are not re-guessed at training time.

## Status
COMPLETE as consumed schema for INTER-54.
