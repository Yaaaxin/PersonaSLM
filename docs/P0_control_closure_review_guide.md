# P0 Narrow Closure Review Guide

Maintainer: Yaxin ZHENG. English review materials; Protocol v1.1 unchanged. This package contains six new style proposals, eighteen proposed History A evidence associations and six categorical clarification rows. It is not a new review of all24 old candidates. Preserve every master and save completed copies separately.

## Revised style texts

Open [P0_style_closure_review_v1.csv](validation/P0_style_closure_review_v1.csv), a six-row,65-column form. Read both full prompts, the active and candidate additions, trusted evidence, question, expected answer, exact counts and the15 positive `review_questions`. All human fields are blank; old annotations have not been transferred. The candidate version is `neutral_style_closure_v1_dev`, while the unchanged schema version is `control_final_review_v3`.

Use PASS, FAIL or UNCERTAIN according to each positive question. Use NOT_APPLICABLE only for fields explicitly listed in that row's `not_applicable_fields`; style conversational_coherence is not on that list. Judge coherence of the addition in its actual prompt, or record uncertainty with evidence; do not silently repair the historical N/A. For each FAIL/UNCERTAIN supply a verbatim quotation from the supplied material in its corresponding `_evidence_quote` field. PASS quotations are optional. Record actual reviewer identity and assistance (`AI-assisted`, `unassisted` or `other-assisted` as applicable); do not enter a blind-review claim if preliminary analysis or expected answers were visible. A missing real review timestamp stays blank.

All six retain the profile heading. Assess whether an absence-of-style-information statement still cues an unwanted register, changes perceived instructions or interferes semantically. Exact tokens do not answer these questions. Five rows have zero difference; **Tessa / control_v2_dev_004 has difference+1 and is marked FAILED**. That row is included transparently as the best observed failure. It cannot become an adopted exact-match control by receiving positive semantic ratings. If not reviewed, leave its fields blank; do not manufacture completion. The optional `--allow-partial` mode imports fully reviewed rows while preserving entirely blank rows, never partially filled rows.

Prospective import example, not a completed human import:

```powershell
.\.venv\Scripts\python.exe -m personaslm.control_final_review --master docs/validation/P0_style_closure_review_v1.json --input docs/validation/P0_style_closure_researcher_completed_v1.csv --output docs/validation/P0_style_closure_researcher_import_v1.json
```

The reviewed copy must retain locked columns, IDs and wording. The importer checks labels, required quotation provenance, metadata, versions and uniqueness; it does not automatically grant experimental adoption or waive matching. Never overwrite the master or an earlier import.

## History A source evidence

Open [P0_history_a_evidence_v1.csv](validation/P0_history_a_evidence_v1.csv); the [readable table](P0_history_a_evidence_verification.md) shows the same18 associations. For each case, inspect both verbatim passages, their source field and offsets, the original rating and the stated narrow comparison. In `researcher_confirmation`, choose CONFIRM if the proposed source association accurately documents the rated issue; REJECT if it does not; UNCERTAIN if unresolved. This confirms evidence attribution, not a new semantic PASS and not a reversal of FAIL/UNCERTAIN. Preserve original decisions and ratings. Explain rejected or uncertain associations in `researcher_notes`, with an alternative exact quotation where appropriate. Actual reviewer_id is required; reviewed_utc is optional and must be an actual UTC value if supplied. Import time is separate.

## Six categorical clarification rows

Open [P0_closure_correction_form_v1.csv](validation/P0_closure_correction_form_v1.csv). Only History A's six `comparison_suitability` cells need explicit categorical confirmation for the selected narrow comparison. The old PASS was converter-derived, not a directly supplied categorical score. Enter PASS, FAIL or UNCERTAIN in `researcher_value`, with actual identity and any explanatory notes. This does not reopen or erase ACCEPT_NARROW, does not rate complete semantic neutrality and does not change the endpoint applicability matrix. Any discrepancy remains visible and requires scope interpretation, not automatic overwriting.

Prospective import example for the two completed copies:

```powershell
.\.venv\Scripts\python.exe tools/p0_closure_review_import.py --evidence docs/validation/P0_history_a_evidence_researcher_completed_v1.csv --corrections docs/validation/P0_closure_correction_researcher_completed_v1.csv --output docs/validation/P0_history_a_confirmed_closure_v1.json
```

The importer checks exact IDs/counts/column order, locked passages and ratings, valid labels, completeness, duplicates and identity. Blank/invalid/unknown fields are rejected. REJECT and UNCERTAIN remain such in the output; import success is not acceptance. Original files remain untouched. No review identity, human timestamp, second reviewer or agreement statistic has been prefilled. New materials were prepared with automated assistance and are visibly unblinded.
