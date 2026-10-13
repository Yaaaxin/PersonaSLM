> **Current researcher-decision update:**24/24 new candidate decisions are registered as AI-assisted human review. N_style:6 REVISION_REQUIRED; History A:6 ACCEPT_NARROW; History B:6 REJECT_AS_NEUTRAL; History C:6 DIAGNOSTIC_ONLY. The official65-column conversion preserves336 supplied checks but has18 missing suitability labels,6 disallowed N/A labels and81 missing required field-quote associations. **P0 PARTIAL; P1 NOT STARTED;334 tests passed.** See [the current decision and acceptance report](P0_control_decision_registration_report.md). Earlier review-status statements below remain historical records.

# Final Neutral-Control Review — v3 Guide

Researcher: Yaxin ZHENG. Protocol v1.1. Primary language: English. **P0 PARTIAL; review OPEN.** This form presents the same 24 selected v2 development candidates with more complete review context. `control_final_review_v3` is a **review-form version**, not a new prompt, selection or experimental version. The original v2 JSON/CSV masters and all 40 older human annotations remain unchanged.

Open [P0_final_control_review_v3.csv](validation/P0_final_control_review_v3.csv). Save your work under a new filename, for example `P0_final_control_review_v3_completed.csv`. In a spreadsheet, import as UTF-8 CSV, retain quoted multiline cells, enable wrap text and keep all rows/columns. There are **24 rows and 65 columns**: input materials, 15 judgments, corresponding quotation fields, reviewer metadata and reproducibility fields. The [JSON master](validation/P0_final_control_review_v3.json) is immutable. The CSV contains no human judgments.

## What to read

Each row includes a stable `candidate_id`, case/family, original active intervention, full candidate block including its heading, trusted evidence, current question, historical reference date, evaluation date, expected answer, exact complete-prompt token counts, intended comparison and review questions. Complete reference/candidate prompts and hashes follow the editable fields.

`reference_date` means the date in the historical dialogue header. For style-only rows it is `NOT_APPLICABLE`, because the style block has no date. `evaluation_date` is the date of the current question, 2026-10-12. Expected answers come from frozen synthetic fixtures and appear **only as review metadata** here; they were not inserted into candidate conditioning text. Reviewers see answers and comparison identities, so this review is **not blind**.

The four families have separate purposes:

| Family | Proposed comparison | What must not be assumed |
|---|---|---|
| `style_generic` | C1 style profile versus generic discourse under the same heading and total input length | A generic sentence or a style-profile heading is not necessarily stylistically inert |
| `history_format` (A) | C3 residence dialogue versus equally dated/formatted unrelated dialogue | Equal structure does not control residence topic or personal information |
| `history_topic` (B) | C3 past-residence answer versus clarification of the same question | Clarification changes speech act and may prime questions, uncertainty or answer avoidance |
| `history_stale_generalized` (C) | C3 named past city versus unspecified past-city residence | This is a specificity diagnostic, not a neutral placebo or a pure manipulation of factual time validity |

No candidate is preferred because of model output quality: no replies were generated for these candidates. The [identification matrix](P0_control_identification_matrix_v3.md) and [per-candidate analysis](P0_final_neutral_control_validation_report.md) are automated development analysis, not human ratings. If you consult that analysis, disclose assistance rather than claiming blind independent judgment.

## Completing the judgments

The `review_questions` cell states all 15 questions. **PASS** means the stated criterion is met; **FAIL** means it is not; **UNCERTAIN** means the available material does not support a confident decision. Every applicable field needs a judgment. UNCERTAIN is a completed judgment but does not close validity. Complete `comparison_suitability` for the specific, limited comparison rather than demanding every control remove every factor.

The fields are: answer leakage, additional factual information, contradiction, temporal interference, unintended linguistic style, semantic neutrality, unnecessary repetition, speaker identity, dialogue structure, timestamp format, topic alignment, temporal relationships, conversational coherence, evidence/question preservation and comparison suitability.

For `dialogue_structure`, consider speech acts as well as role/turn counts. For `additional_factual_information`, count personal assertions beyond current trusted evidence even if already present in the active historical intervention. For C, retaining a vague past-residence fact is intentional; marking that dimension FAIL under its absence criterion does not automatically make the diagnostic unsuitable. A can fail topic alignment and still be usable for a narrowly defined format/length-controlled **content replacement**, provided its other substantive issues are resolved. No single dimension is silently converted into overall acceptance.

`NOT_APPLICABLE` is allowed only for the five history-specific fields listed in `not_applicable_fields` for style rows, or for `semantic_neutrality` in C. It is not allowed as a substitute for uncertainty or for overall suitability. All permitted fields are initially blank; the software does not prefill labels.

For each FAIL or UNCERTAIN, enter an exact excerpt in its `_evidence_quote` column and explain the concern in `reviewer_notes`. Quotations must come from the supplied intervention, evidence, question or full prompts. To discuss a missing feature, quote the closest relevant text and describe the absence in notes. Supply your actual `reviewer_id` and `review_assistance` (`unassisted`, `AI-assisted`, or `other-assisted`). `reviewed_utc` may be left blank if the actual time is unavailable; otherwise use UTC with `Z` or `+00:00`. No second reviewer or agreement statistic is assumed.

Only judgment, quotation and reviewer fields are editable. Do not change the candidate ID, content, versions, expected answer, dates, questions, counts or hashes. Retain all 24 rows. The importer tolerates ordinary CSV CRLF/LF representation differences, but rejects changed experimental materials.

## Import a completed file

Run from the repository root after completing a separately saved CSV:

```powershell
.\.venv\Scripts\python.exe -m personaslm.control_final_review --input docs/validation/P0_final_control_review_v3_completed.csv --output docs/validation/P0_final_control_review_v3_import_001.json
```

This is a usage example, not a claim that a human submission was imported. The default master is the repository's v3 JSON. The importer validates its version/digest, all locked materials, candidate inventory, duplicate IDs/columns, labels, quotations, reviewer identifier, assistance and optional UTC time. It refuses incomplete review by default, an all-blank submission, or any existing output path. Use a new numbered output for each import; preserve every submitted CSV separately.

For an explicitly partial submission, append `--allow-partial`. Keep all rows, leaving unreviewed rows entirely blank. Partly filled rows are invalid. The result reports exact completed/remaining counts and never declares control acceptance automatically. This permits review of intended controls without making unused diagnostics a new P0 gate. Reviewer identity is a supplied attestation, not authenticated by the import program.

Current completion: **0/24**. Earlier review completion remains **40/40**, applicable only to its original materials. P0 remains PARTIAL until adopted controls are genuinely reviewed and substantive validity findings are resolved with appropriate claim boundaries. P1 requires separate researcher authorization.
