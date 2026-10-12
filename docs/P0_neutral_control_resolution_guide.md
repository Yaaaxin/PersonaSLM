# English Neutral-Control Resolution Guide

Version `neutral_control_resolution_v1`, 2026-10-12. The original researcher review is complete (40/40), AI-assisted and not blind. This optional follow-up packet supports unresolved-issue adjudication and independent replication. It does not replace the registered ratings or presume another reviewer exists.

Use a separate copy of [the CSV](validation/P0_neutral_resolution_form_v1.csv); its [JSON master](validation/P0_neutral_resolution_form_v1.json) is immutable. Each of the 40 rows includes the exact neutral text, trusted current evidence, current question, relevant reference conditioning, final prompt token counts/difference and prompt/material hashes. The [100-input reconstruction](validation/P0_control_reconstruction_v1.json) supplies complete C0/C1/C3 and neutral prompts where needed. English synthetic data only; no model outputs or prior ratings are included in this packet. Condition identifiers and content are visible, so do not claim blind review.

Read the neutral text **including its heading, role labels, repetition and date**. The correct city in trusted evidence is intended; evaluate whether the added neutral block itself reveals it. Compare topic, number/type of factual assertions, reference identity, temporal load, dialogue adjacency and additional instructions. Token equality is only an input-length check. Do not infer neutral validity from model answers or rewrite any material.

| Field | PASS | FAIL | UNCERTAIN |
|---|---|---|---|
| answer_leakage | Added block does not reveal/imply answer | It reveals/implies answer | Implication cannot be decided |
| additional_factual_information | No additional personal fact | Adds personal/biographical fact | Fact status unclear |
| contradictory_information | No conflict with supplied evidence | Contains a conflicting assertion | Identity or assertion unclear |
| temporal_interference | No unintended temporal implication beyond matched design | Introduces stale/conflicting/unbalanced time cue | Timing effect unclear |
| unintended_linguistic_style | No identifiable extra style instruction/demonstration | Extra style/repetition/register cue | Influence unclear |
| semantic_neutrality | Suitable for the stated replacement contrast | Substantive interference invalidates that contrast | Suitability remains unresolved |

Complete all six dimensions for a reviewed row. For **FAIL and UNCERTAIN**, copy an exact contiguous excerpt from the supplied neutral/reference/evidence/question into that dimension's `*_evidence_quote` field. Explain the issue and any identity/topic/coherence concern in `reviewer_notes`; notes are interpretations, quotations are original evidence. Quote absence is represented by quoting the relevant supplied wording and explaining the missing link in notes. Multiple noncontiguous excerpts belong in notes, not in the validated single-quote field.

Record actual `reviewer_id` and `reviewed_utc` with a UTC offset, for example the format `YYYY-MM-DDTHH:MM:SS+00:00`. Do not use import time as review time. Keep all rows; leave every editable field blank for an unreviewed row. Do not copy another reviewer’s labels. Any access to earlier ratings must be disclosed in notes. This form supplies no agreement statistic or consensus decision.

Example import command (instructions only; no completed follow-up file has been imported):

```powershell
.\.venv\Scripts\python.exe -m personaslm.control_resolution_review --template docs/validation/P0_neutral_resolution_form_v1.json --input docs/validation/REVIEWER_COMPLETED_COPY.csv --output docs/validation/NEW_RESOLUTION_IMPORT.json
```

The importer checks schema/version/hash, unchanged materials, missing/invalid labels, duplicate/missing rows, reviewer ID, UTC time, quote support and completeness. It refuses empty imports and overwrite. Import validation checks structure, not human authenticity or adjudication correctness. Revised controls must use a new stimulus version, new real-tokenizer matching and review; do not alter historical prompts to close a finding.
