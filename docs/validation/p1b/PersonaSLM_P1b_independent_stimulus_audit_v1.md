# PersonaSLM P1b Stimulus Audit — Independent AI Review (Proposal Only)

## Scope and provenance

- Source: `stimulus_review_v2.csv`; SHA-256 `810ca7e751895aaf3f50b308f1af79aa3c2c67fb9ae6032e93daa0e1cd8658f9`.
- Source data: 24 proposed development cases, 8 task families × 3 designed levels, 12 fictional speakers, reference date metadata `2027-04-15`.
- The original 41-column reviewer CSV and all human decision fields are unchanged. This review was performed with access to stimulus contents and expected answers and is **not an independent blinded human review**.
- Review limited to the uploaded CSV. No eight-condition rendered prompts, inference config or frozen runtime hashes were available in the upload. Therefore token-matching, as-of-date exposure, invariant trusted evidence across C0–C7, absence of full-prompt answer leakage, and final model readiness cannot be verified from this file alone.

## Mechanical integrity results

- 24/24 unique case IDs; eight families with three levels each; one dataset SHA-256 reference shared by all rows.
- 24/24 `expected_answer` values are literally supported in supplied trusted evidence (some depend on joining multiple cited facts).
- All `dated_evidence_chain` fact IDs and source quotations match exact substrings in trusted evidence.
- All reference-answer JSON and applicability JSON parse successfully.
- All original 13 human check fields, `researcher_decision`, `reviewer_id`, `review_method`, `reviewed_utc`, evidence/notes remain blank.
- AI preliminary status counts: {'HOLD_REFERENCE_DATE_VISIBILITY': 13, 'REVIEW_READY_WITH_LIMITATIONS': 10, 'HOLD_TURN_BOUNDARY_CHECK': 1}; these are *workflow readiness suggestions*, not researcher verdicts or evidence of real-model discrimination.

## Central scientific issues before 192 real generations

### 1. Reference-time anchoring (mandatory verification)

Evidence records often become valid in 2027 and `evaluation_reference=2027-04-15`, which is a **fictional future evaluation date**, not the current computer date. Thirteen questions (families A/B/D/F and H_L1) do not themselves explicitly state the as-of date. If the model-facing prompt does not expose the fictional reference date, a model can reasonably interpret undated present-tense queries differently. Verify rendered prompts for all eight conditions; if the global reference is absent, create a versioned v3 dataset or common wrapper and recalculate hashes/manifests *before* any new inference. Do not silently rewrite previous artifacts.

### 2. Manipulation identification, answer leakage, and token limits

The 24 rows show compatible speaker history and supplemental facts, but do not prove the exact 8-factor generated prompts preserve identical trusted evidence and questions. Validate model-facing rendered prompts, maximum context length, actual GGUF tokenizer IDs/counts, and response parser boundaries. Independent S/F/H effects can be estimated within each case; however, style subtype is nested in speaker, factual supplement is uniformly about a woven bookmark, and H relevance is strongly task-family-dependent. Do not interpret cross-family interactions as isolated relevance or temporal mechanisms.

### 3. Task discrimination and interpretation

- Family A: Every correct archive record is the first fact; adding unrelated boxes mainly alters distractor count.
- Family B: Task complexity partly means more output slots; longer answers may be truncated under a fixed token budget.
- Family C: Explicit inclusive boundary dates are internally consistent.
- Family D: The only terminal target in a chain may allow an answer-shortcut; independent decoy variants would strengthen a multi-hop claim.
- Family E: Historical residence information is relevant to the task, unlike most other families, so H-content relevance is not balanced.
- Family F: The `F_L1` question explicitly names Morgan North and its record identifier, making it an easy baseline rather than a strong disambiguation test.
- Family G: Past/current answers are correctly distinguishable from the stated dates, including both outputs in G_L3.
- Family H: H_L1 and H_L2 each include only one parcel, so fixed-context *necessity* is not identified. H_L3 has two parcels, but the supplied fixed context already ends with a User turn; inspect the full prompt assembly for two consecutive User turns, which could especially affect Base-model turn boundaries.

### 4. Evidence sufficiency does not establish empirical discrimination

The supplied dataset passes a consistency check, but 24 unique gold answers and ablation diagnostics do not show that the 2B Base model will make discriminative semantic errors, nor that it can be meaningfully scored. The prior wave showed a factual/temporal ceiling and severe continuation issues. Keep this set labeled `development calibration`, with the original 24 trials frozen before any generation; select future independent confirmatory cases prospectively.

## Review decisions needed from the human researcher

1. Confirm whether the actual model-facing prompt exposes `2027-04-15` for undated items.
2. Decide whether F_L1, H_L1, H_L2 are deliberately retained as easy baselines or revised for stronger test discrimination; treat other structural shortcuts as limitations, not retroactively as failures.
3. Check H_L3 rendered turn boundaries and B_L3 output-budget adequacy without using model answers to tune controls.
4. Verify all C0–C7 prompts preserve evidence, question, gold answer, and frozen metric applicability; ensure 24 separate neutral controls remain **OPEN** pending human semantic review.
5. Independently verify the reference answers and evidence quotations, then fill the original human 13-check form and record a researcher decision. Do **not** copy AI proposals into human fields without genuine researcher inspection.

## Next action

After those checks, produce a revised and versioned calibration manifest, with real tokenizer/context preflight and an explicit go/no-go report. Run **0 new generations** until the researcher authorizes the 192-request development wave. This review does not adopt v1.2, modify historical P0/P1 scores, or declare scientific novelty.

## Algorithmic Opportunity Assessment

No novel algorithm is justified by this pre-inference stimulus audit. The priority is measurement identifiability, model-generated output validity and task discrimination. If later independent observations show repeatable stale-evidence selection errors, context-routing failures or cross-turn contamination beyond existing baselines, propose a separately validated candidate with a matched non-algorithmic baseline and held-out evaluation set.
