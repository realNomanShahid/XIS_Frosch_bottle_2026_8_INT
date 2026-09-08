# A04 — Annotation Schema

**ID:** PRJ-FROSCH-SCHEMA-v1  
**Author (consumer of schema):** Noman  
**Upstream annotator:** Other team member (name not recorded here)  
**Date:** 2026-08-05  
**Lead approval of schema:** Upstream / to be confirmed by Abdul Moiz

## Feature / task
Multi-class detection (+ operational use of bottle/label masks from segmentation model).

## CLASS DEFINITIONS (as used operationally)
| Class | Definition (engineer understanding) |
|-------|-------------------------------------|
| bottle | Full bottle instance |
| label | Bottle label region (used for H/V centricity) |
| capacity | Region containing capacity text (OCR crop) |
| bump | Local raised / “ping”-like surface defect on bottle |
| damage | Broader / visible bottle damage region |
| scratch | Thin line-like surface mark |

## Edge / ambiguity rules
- Detailed pixel-edge policy was **not authored by this engineer** (labels inherited).  
- Unclear cases: should be flagged by annotators, not guessed (handbook).  
- **Change log:** v1 — initial record of consumed schema for Frosch INTER-54.

## Note
Formal lead-approved schema text with positive/edge examples should be attached or superseded when upstream documentation is available.
