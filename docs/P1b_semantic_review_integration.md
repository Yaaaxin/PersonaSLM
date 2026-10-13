# P1b Semantic Review Integration — v1

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Protocol v1.1 remains the formal baseline; v1.2 Revised Proposed r1 is unadopted. This is offline integration preparation, not a new experiment or a completed human review.

## Current readiness and preserved inputs

The existing review package is reused without regeneration. [Package integrity](validation/p1b/semantic_integration_v1/package_integrity_v1.json) verifies all 192 BR response IDs, 24 anonymous cases with eight cells each, original first-reply/full-continuation hashes, parser span reconstruction, frozen metric applicability, dataset and manifest hashes, and treatment mapping against all 192 reconstructed prompts. The frozen structural counts remain 186 CROSS_TURN, five TRUNCATED, one AMBIGUOUS and zero COMPLETE. These categories do not determine factual correctness.

| Existing master | Purpose | Columns | Imported researcher records |
|---|---|---:|---:|
| [semantic_scoring_view_v2.csv](validation/p1b/measurement_audit_v1/semantic_scoring_view_v2.csv) | Stage A: four semantic dimensions, completeness and answer-delivery diagnostic | 35 | 0 |
| [structural_review_view_v2.csv](validation/p1b/measurement_audit_v1/structural_review_view_v2.csv) | Stage B: frozen structure, first-reply verification and continuation notes | 22 | 0 |

Stage A contains no treatment, factor, request, structural-status, termination, token-count or full-continuation columns. Stable aliases and the existing presentation seed 714003 are retained. Text cues, evidence identifiers and prior knowledge may still reveal information. Column masking does not establish perfect blinding or independence.

Eligibility remains factual 192, temporal 88, relevance 192 and coherence 192. The other 104 temporal judgments require **Not Applicable**. All four primary dimensions remain separate; semantic completeness and answer delivery remain diagnostics. No semantic condition effect has been calculated from the blank research materials. Existing structural analyses remain unchanged.

## Review sequence and source preservation

Use the [existing English semantic review guide](P1b_calibration_semantic_review_guide.md) and its positive definitions. Do not alter evidence, outputs, hashes, applicability, aliases or frozen classifications.

1. Save a new Stage A working copy. Assess relevance, factual consistency, temporal consistency, coherence and semantic completeness before opening Stage B or analyst treatment files. Record actual assistance and prior access. Preserve this initial copy.
2. Save a new Stage B copy. Inspect the full continuation, original span and excluded turns. Enter PASS / FAIL / UNCERTAIN for reply-unit verification. Disagreements and the frozen AMBIGUOUS record need an explicit disposition in `human_continuation_notes`.
3. Preserve initial scores and any available AI-assisted structured proposal. If Stage B changes semantic judgments, save a separate final Stage A copy; do not overwrite earlier versions. Supply both versions during registration. Do not silently replace a disputed span: a different unit requires a separately versioned sensitivity analysis.
4. Obtain the researcher's explicit confirmation of the exact final Stage A and B files. The [pending confirmation template](validation/p1b/semantic_integration_v1/researcher_confirmation_PENDING_v1.json) deliberately contains no reviewer identity, approved IDs, approval or review timestamp. Complete a copy from actual confirmation; do not edit the pending master into an apparent historical approval.

Final registration uses `reviewer_id: Yaxin_ZHENG`, `review_status: RESEARCHER_CONFIRMED`, `decision_source: researcher` and `final_decision_authority: researcher`. The statement must identify the approved files and all 192 response IDs. State the actual review method and original assessment provenance, whether AI-assisted structured coding was used, condition-label masking, prior treatment knowledge, whether Stage B was seen before initial Stage A, and whether Stage A was revised after Stage B. Use YES / NO / UNCERTAIN where specified. Unknown provenance must remain uncertain. The software validates the recorded statement; it does not independently authenticate the reviewer or certify semantic truth.

Record `confirmation_utc` and CSV `reviewed_utc` only when actually known. The automatic registration time describes file import, not human review. The original model output, initial human assessment, proposed coding and researcher corrections remain distinguishable. Missing proposal files are reported as unavailable, never reconstructed. No second reviewer, agreement statistic, independent numerical entry or blind consensus is presumed.

## Validated import commands

[The integration tool](../tools/p1b_semantic_integration.py) extends the existing validator rather than changing its annotation definitions. It rejects missing/duplicate/unknown IDs, changed immutable fields, invalid labels, retrospective N/A, absent provenance, unconfirmed files and confirmation hashes that differ from the submitted bytes. Blank eligible scores require an explicit reason naming the affected metric; they stay missing. Unverifiable requires a reason. Case-specific evidence quotations remain required. The importer does not infer a value from other ratings.

Preparation has been executed once:

```powershell
.\.venv\Scripts\python.exe tools/p1b_semantic_integration.py prepare --output docs/validation/p1b/semantic_integration_v1
```

The following are **future commands**, not actions already performed on real annotations. Replace the uppercase paths with actual researcher-provided copies. Use a new output directory for every registration. If no preliminary coding file exists, omit `--proposed-stage-a`; disclose its absence. Initial Stage A is mandatory when revisions after Stage B are declared.

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath COMPLETED_STAGE_A.csv
Get-FileHash -Algorithm SHA256 -LiteralPath COMPLETED_STAGE_B.csv

.\.venv\Scripts\python.exe tools/p1b_semantic_integration.py import --stage-a COMPLETED_STAGE_A.csv --stage-b COMPLETED_STAGE_B.csv --confirmation RESEARCHER_CONFIRMATION.json --initial-stage-a INITIAL_STAGE_A.csv --proposed-stage-a AI_PROPOSED_STAGE_A.csv --output docs/validation/p1b/semantic_registered_v1
```

Copy SHA-256 values in lowercase into the confirmation copy. Hash the completed files, not the blank masters. Keep all review-source and output paths within this repository. All validation occurs before a registration directory is created. Existing output directories are rejected. Supplied source files are copied byte-for-byte; `correction_history_v1.json` records actual field differences between supplied versions. This records provenance, not an estimate of human correction quality. Intentionally missing ratings do not become completed measurements merely because a registration passes schema validation.

Only after a valid import:

```powershell
.\.venv\Scripts\python.exe tools/p1b_semantic_integration.py analyze --registration docs/validation/p1b/semantic_registered_v1 --output results/p1b_semantic_analysis/v1
```

Analysis verifies the registered file hashes and explicit confirmation again. It unblinds into a separate analysis artifact using the existing local mapping; neither review CSV acquires treatment labels. The mapping and suggested analysis directory are under ignored `results/`. Local separation is not encryption or access control. Share only the intended review stage, not analyst outputs or manifests. Changing imported files requires a new registration, never in-place correction.

## Frozen exploratory analysis specification

[Analysis specification](validation/p1b/semantic_integration_v1/analysis_specification_v1.json) records version `p1b_verified_semantic_factorial_v1`, exact contrast weights, implementation/dependency hashes and Git state. It implements the [existing pre-review analysis contract](validation/p1b/measurement_audit_v1/future_semantic_analysis_contract_v1.json). Preparation occurs after generation but before researcher semantic ratings are available; it is not retrospective preregistration or a protocol amendment.

| Analysis | Definition and units |
|---|---|
| C1-C0; C3-C0 | Two within-case differences; not average factorial main effects |
| S, F, H | Average difference over the other two factors; cell weights +/-0.25 |
| SxF, SxH, FxH | Difference-in-differences averaged over the third factor; weights +/-0.5 |
| SxFxH | Third-order difference; weights +/-1 |
| Primary outcomes | Four separate dimensions; ordinal means remain descriptive and full score distributions are retained |
| Additional diagnostic | Human semantic completeness, cross-tabulated with unchanged structural status |

There are **24 paired development cases and 12 synthetic speakers**, two cases per speaker. Temporal eligibility covers 11 cases and nine speakers. A simple contrast needs its two cells; average effects/interactions need the weighted cells. An unknown zero-weight cell does not invalidate a simple pair. No C0-correct filter or selection by effect direction is used. Task-family summaries retain all three cases per family and report their own eligibility and coverage.

The primary numerical analysis requires a researcher-confirmed first-reply unit. A FAIL/UNCERTAIN unit retains every original rating but is represented as `boundary_unresolved`, not Incorrect. A confirmed unit may remain CROSS_TURN, TRUNCATED or AMBIGUOUS under the frozen policy. Its semantic judgments are not rewritten from that structural label.

For categorical endpoints, Correct and Incorrect are coded 1 and 0 only when assessable; Unverifiable stays unknown. Missing ratings, uncertain completeness, unresolved units and frozen N/A have distinct labels and analysis states. Unknown eligible values receive signed case-wise lower/upper bounds under the contrast weights, using 0–1 for binary diagnostics and 1–5 for ordinal scores. These are hypothetical unknown-value bounds, **not confidence intervals or assertions about the unknown responses**. N/A cases never become failures. Reports retain all eligible denominators and both raw-label counts and numerical coverage.

Exploratory percentile intervals use 10,000 whole-speaker bootstrap draws with seed 714005, retaining the speaker's cases and all cells together. The estimate is the case-weighted mean of evaluable pairs, not 192 independent observations. Reports include eligible/evaluable cases and speaker clusters, unknown cases, empty resamples and degenerate intervals. Selective missingness can bias assessed-only means. Twelve purposively constructed speakers and nine temporal clusters give limited precision; these intervals do not incorporate annotation uncertainty, guarantee population coverage, adjust for multiplicity or establish significance. Family-level comparisons are descriptive without a three-case subgroup bootstrap. Zero observed variation does not prove a population null.

## Scientific interpretation and remaining gates

The pipeline permits positive, negative, mixed and null patterns across S/F/H and task families. It does not identify isolated historical relevance, temporal validity, post-training or external validity mechanisms from this wave. Those remain prospective questions with documented confounding. Persona Fidelity is not combined with reliability. Neutral-adjusted effects remain unavailable while the separate control review is OPEN.

The generated results report always includes **Algorithmic Opportunity Assessment**: observed failure modes, existing methods, possible improvements, validation feasibility and publication value. Use the [existing assessment](P1b_calibration_algorithmic_opportunity.md) and [related-work matrix](related_work_novelty_matrix.md); verify relevant prior algorithms before a later originality claim. This preparation introduces no algorithmic claim, new literature finding or mitigation experiment.

The outstanding gate is actual researcher-confirmed Stage A/B annotation and documented boundary dispositions. No such completed P1b files were supplied for this task. Once imported, inspect case-level coverage and provenance before interpreting factorial estimates. Publication readiness still requires reliable semantic measurement, suitable precision and independent validation; a successful importer is not scientific evidence.

## Verification evidence

The [delivery inventory](validation/p1b/semantic_integration_v1/delivery_v1.json) records actual tests, historical byte-preservation checks, commands, source hashes and Git state. Tests use explicitly synthetic software fixtures in disposable directories; they are not researcher annotations. The original review masters, original raw outputs, both protocol documents and historical evaluation versions remain unchanged. No new inference, model training, subsequent wave, commit or push is part of this task.
