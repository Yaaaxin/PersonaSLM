# P1b Researcher Review Guide

Maintainer: Yaxin ZHENG. English development materials; Protocol v1.1. **All new human decisions are blank.** Analytical reference checks in this package are tool-assisted, not human approval. Reviewing visible reference answers and interventions is stimulus validation, not blinded outcome scoring.

## Materials and provenance

1. [24-case stimulus form](validation/p1b/final_v1/stimulus_review_v2.csv): complete evidence, question, fixed context, speaker, dated support quotations, expected components, S/F/H, applicability and analytic risks. Bound to development v2 and its file hash. Review all 24, including the three documented corrections.
2. [24 existing neutral-control candidates](validation/p1b/final_v1/neutral_control_review_v1.csv): byte-identical copy of the original Wave 1 review master. Includes active and candidate text, full prompts and actual recorded token counts. **These belong to Wave 1, not to the new P1b cases.** No approval or matching result transfers across datasets.
3. [Case-level analytic record](validation/p1b/final_v1/case_validation_v1.json) and [correction register](validation/p1b/final_v1/correction_register_v1.json): source-derived assistance, not judgments to copy automatically.

Save completed forms under a new filename. Never edit the masters. Enter your real reviewer identifier and disclose whether the reference derivations or other assistance were seen. Do not call the review blind merely because the reviewer agrees with an earlier assessment. Record a review date only if actually known; it may remain blank. Import timestamps are separate. No second reviewer or agreement statistic is presumed.

## Positive-criterion stimulus judgments

Use `PASS`, `FAIL`, or `UNCERTAIN` for every `check_*` field. Each question asks whether a desirable property holds. `NOT_APPLICABLE` can be preserved with explanatory notes on a non-accepted record; it cannot satisfy these core checks for acceptance. Even a non-temporal endpoint requires checking that the displayed dates are interpreted consistently.

| Field | Positive question |
|---|---|
| evidence_sufficient | Can all requested components be answered from the displayed trusted evidence and fixed context, without external knowledge? |
| answers_unique | Are the intended values uniquely defined, allowing legitimate paraphrases but no competing supported value at the same relevant time? |
| reference_answer_correct | Does each reference component follow from the quoted source, including every link, rather than a naming/template clue? |
| temporal_interpretation_correct | Do the answer and supporting dates respect inclusive intervals and the time actually asked about? |
| entities_clear | Are the target person/object and all pronouns or roles resolvable without an unannounced assumption? |
| question_clear | Does the English wording request exactly the declared components? |
| context_valid | Is the preceding dialogue coherent enough to establish the intended referent and question? |
| speaker_consistent | Do speaker names, personal facts and history consistently refer to the declared synthetic speaker? |
| reference_stable_across_cells | Is the same answer valid in every C0–C7 cell with identical evidence/question/context? |
| no_accidental_answer_leakage | Do S, F and H avoid supplying the current requested answer outside the common evidence? |
| no_unplanned_contradictions | Are past assertions true at their stated dates, with no accidental incompatible fact at the same time? |
| applicability_correct | Are the four endpoint eligibility flags and the absence of fidelity ground truth appropriate? |
| demand_description_appropriate | Does the proposed demand description acknowledge shortcuts and avoid claiming empirically demonstrated difficulty? |

Decision: `ACCEPT`, `REVISION_REQUIRED`, or `UNCERTAIN`. `ACCEPT` requires all thirteen core checks PASS. A negative/uncertain check requires an explanation in reviewer notes; quote the source where possible. Evidence quotation fields support auditability; do not invent quotations. Do not reverse a single-item judgment to agree with an overall decision. If an honest narrow acceptance needs a different representation, preserve the submission and resolve the schema prospectively rather than converting labels silently.

## Specific questions by family and case

- **A_L1/L2/L3:** Is “archive box” clearly distinct from supply boxes? Confirm the reference is still a single fact. Do not equate the added boxes with demonstrated greater difficulty.
- **B_L1:** Are workshop and role both requested? **B_L2/L3:** Does the revised wording resolve the referent without changing the requested components? Is the role attached to the speaker and the entrance to the meeting place?
- **C_L1:** Check April 5 against the Birch interval. **C_L2:** Check April 10 is included in Cedar. **C_L3:** Check that “preceding day” means April 9, with Birch as the second component.
- **D_L1/L2/L3:** Independently follow every named-object link. Also identify whether a unique final location permits a shortcut; acceptance of calibration does not prove genuine multi-step behavior.
- **E_L1/L2/L3:** Confirm the historical residence is genuinely true in 2026. Confirm the 2027 residence and, where required, its hub and opening day. For E_L3 explicitly approve or reject changing Thursday to Tuesday; do not substitute the weekday of the reference date.
- **F_L1:** Check the explicit North identifier. **F_L2/L3:** Confirm only one archivist is active and follow that person's folder. Note recurring North/archivist and Amber templates.
- **G_L1/L2/L3:** Distinguish a correct past statement from an outdated claim presented as current. G_L3 needs both March 20 and April 15 values.
- **H_L1/L2:** The context identifies a parcel, but there is only one candidate; confirm the weak-disambiguation limitation is accurately disclosed. **H_L3:** Resolve Parcel 111 despite Parcel 151, and inspect the two consecutive User turns at the context/question join.

## Neutral-control form

The original eight positive questions and permitted narrow scope are included verbatim in every row. Inspect leakage, extra personal facts, contradictions, unwanted style, evidence preservation, speaker identity, format/length, and suitability for the stated contrast. Use the original allowed decisions: `ACCEPT_NARROW`, `REVISION_REQUIRED`, `REJECT_AS_NEUTRAL`, `DIAGNOSTIC_ONLY`, `UNCERTAIN`.

N_style is explicit absence of speaker-style information, not C0-equivalent context. N_history contrasts dated residence with unrelated coherent dialogue; topic, factual content and temporal information differ. Exact full-prompt token equality controls length, not meaning. Current status remains **OPEN, 0/24 human reviews**. Resolving this packet is not a prerequisite for the eight-cell P1b calibration, which contains no neutral-control requests; it is a prerequisite for using these exact Wave 1 candidates in matched-control comparisons. P1b-specific matched controls would need their own design, real tokenization and review if later proposed.

## Validated import commands — for completed copies only

These are future instructions, **not commands executed in this task**:

```powershell
.\.venv\Scripts\python.exe tools/p1b_readiness.py import-review --csv docs/validation/p1b/P1b_stimulus_completed.csv --output docs/validation/p1b/researcher_stimulus_registration_v1
.\.venv\Scripts\python.exe tools/p1_review.py import --csv docs/validation/p1b/P1_controls_completed.csv --output docs/validation/p1b/researcher_control_registration_v1
```

The stimulus importer rejects missing/duplicate IDs, altered non-annotation fields, wrong versions/hashes, invalid/missing labels, absent reviewer/method, invalid supplied timestamps and inconsistent acceptance. It preserves the submitted CSV and records its hash. The control importer retains the original 41-column contract and source master. Neither importer fills labels, fabricates timestamps, edits old records or authorizes inference. A refusal preserves the supplied file for correction, with no automatic relabelling.

## Prospective output evaluation

Accepting a stimulus does not score its future response. Retain `response_status_v1` and `separate_axes_policy_v1`; see [readiness and scoring rules](P1b_inference_readiness_report.md). A later condition-masked output packet should retain full continuation, first reply, evidence, proposition dates and applicability, with treatment mapping separate. There is no new output packet containing invented model text or judgments in this task.
