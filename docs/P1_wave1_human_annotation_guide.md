# P1 Wave 1 Human Annotation Guide

Maintainer: Yaxin ZHENG. Packet version: `p1_output_human_review_v1`. This is an English, development-stage review package for the 96 existing outputs under Protocol v1.1. It does not amend frozen automatic scores or turn development examples into an independent confirmatory test.

## Distribution and provenance

Give reviewers a copy of [output_human_review_v1.csv](validation/p1/output_human_review_v1.csv) and this guide only. Keep the master unchanged. Do not distribute the curator mapping at `results/p1_measurement_audit/v1/admin/output_human_review_mapping_v1.json`, automatic-score tables, condition prompts or analysis reports with the scoring packet. This directory is Git-ignored, not encrypted or access-controlled by this tool. Repository access or output clues can compromise masking; disclose prior access honestly. Independent blind judgment cannot be inferred from agreement or from hidden column names.

Only columns beginning `human_`, plus `reviewer_notes`, `reviewer_id`, `review_assistance`, `prior_access_to_treatments_or_scores`, and `reviewed_utc` may be edited. Preserve spelling/capitalization of categorical labels, all 96 IDs, raw whitespace/newlines, hashes and every applicability value. Use UTF-8 CSV. Spreadsheet exports must not replace embedded newlines or change quoted text. Human fields are currently blank; no label should be inferred from an automatic structural status.

## Unit and completeness

Read the current question, trusted evidence, evaluation date and fixed preceding context. The fact ledger supplies source context shared across conditions, not proof that a particular generation received that history. Identify who each statement concerns and when its fact is valid.

Score `raw_first_reply` as the frozen primary unit. Inspect `raw_full_continuation` and the excluded continuation to assess extraction fidelity, but do not silently replace the unit or combine later generated turns with the first reply. Mark `human_reply_unit_confirmed` YES, NO or UNCERTAIN. If NO/UNCERTAIN, quote the ambiguity and proposed boundary in notes; do not edit the saved first reply. Any dependent semantic label that cannot be justified on the frozen unit should be Unverifiable/Unscorable with a reason. A completed import does not authorize pooling disputed units; adjudication remains explicit and separately versioned.

Use `human_semantic_completeness` COMPLETE, INCOMPLETE or UNCERTAIN. COMPLETE means an interpretable, finished communicative act responding to the request; it can be factually wrong. INCOMPLETE means required continuation is clearly missing; it need not be factually wrong. UNCERTAIN means the evidence does not settle completeness. EOS, punctuation and a role transition alone do not settle this judgment. A 96-token continuation may contain a complete first reply plus later dialogue. Conversely, do not promote a quoted candidate greeting inside unfinished deliberation into a final answer. Preserve such text and explain the judgment.

## Four separate reliability dimensions

Apply the predeclared `applicable_*` columns even when the generated text contains unexpected claims. Ineligible factual/temporal dimensions require exactly `Not Applicable`. Do not convert a nonfactual task into a factual one after seeing its response.

For factual consistency use `Correct`, `Incorrect` or `Unverifiable`. Correct requires supported, appropriately attributed assertions against trusted facts valid at the evaluation time. Incorrect requires a verifiable contradiction, not merely an unusual wording or an absent answer. Unverifiable covers insufficient evidence, abstention, ambiguous attribution, unresolved conflicting readings, unsupported assertions or an unassessable reply. Quote support/contradiction and explain the cause. Check negation, multiple incompatible claims and whether an outdated claim is presented as current. A date-bearing answer is not wrong because the automatic grammar did not recognize it. City-name or club-name overlap alone is insufficient.

For temporal consistency use the same three categories against dated facts and event ordering. A historical residence valid in the past is not false simply because it is no longer current. Distinguish correctly described past facts from stale facts asserted as current. Factual and temporal errors may overlap; record each applicable dimension independently. Uncertainty in one dimension need not force the same judgment in another.

For response relevance use an integer 1–5, following the existing [annotation guidelines](annotation_guidelines.md): 1 non-responsive/irrelevant, 3 partial, 5 adequately responsive. For conversational coherence use 1–5 for integration with the **fixed** context, including reference resolution and topic continuity. Values 2/4 represent intermediate judgments; explain them if helpful. Use `Unscorable` when the unit/evidence does not support a rating. An incomplete response is not automatically relevance 1 or coherence 1. Do not use the full invented conversation as the fixed context. These are draft operational instructions for new human review, not retroactive automatic rating changes.

Keep Persona Fidelity separate: no linguistic/behavioral fidelity ground truth or human fidelity score is supplied in this wave. Do not construct a composite reliability/fidelity score.

## Evidence and reviewer fields

`human_evidence_quotations` must contain verbatim passages from the supplied response and/or trusted record, with field names for traceability. `human_unverifiable_reason` is required when any dimension is Unverifiable or Unscorable. Record continuation-only problems in `human_continuation_notes` without changing the primary unit. Use notes for ambiguities, abstention, unavailable evidence and apparent review-material problems.

Supply your actual `reviewer_id`. Set `review_assistance` to `unaided`, `AI-assisted`, or `other-disclosed-in-notes`; disclose the latter in notes. Set `prior_access_to_treatments_or_scores` to YES, NO or UNCERTAIN. Record `reviewed_utc` only if an actual review time is available; leaving it blank is allowed. Do not reconstruct a time from file modification metadata. No second reviewer, agreement or consensus is assumed. Independent duplicate scoring and a declared adjudication procedure remain desirable before publication; their absence must be reported.

## Import and audit trail

After all 96 records are complete, retain the reviewer's source file and use a **new** output directory. The following is an example command, not an executed import of real judgments:

```powershell
.\.venv\Scripts\python.exe tools/p1_measurement_audit.py import-review --csv docs/validation/p1/output_human_review_completed_v1.csv --output results/p1_measurement_audit/v1/human_reviews/review_01
```

The importer validates IDs, column schema, review version, unchanged materials/applicability, all required labels, reviewer identification, assistance/access disclosures and evidence/reason fields. It copies original submitted bytes and writes a separate registration with source/master hashes and an actual registration time. Registration time is not substituted for review time. Existing directories cannot be overwritten. No historical score is rewritten. Syntax validation cannot establish that quotations support a decision or that the review was independent; those are substantive checks for subsequent analysis.
