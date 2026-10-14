# P1c exploratory semantic analysis readiness v1

Maintainer: Yaxin ZHENG. Status: implementation ready; official semantic analysis blocked only by the genuine annotation-confirmation gate. No new experiment approval is requested.

## Inputs and estimands

The approved six-cell experiment contains 12 paired cases and six synthetic speakers, two cases per speaker. Each semantic endpoint is eligible on all 72 requests. The [analysis specification](validation/p1c/calibration_v1/semantic_review_v1/analysis_preparation/analysis_specification_v1.json) copies the 16 original contrast weights exactly and preserves the original case/speaker membership. [192 case-by-contrast definitions](validation/p1c/calibration_v1/semantic_review_v1/analysis_preparation/case_contrast_specifications_v1.csv) contain no observed semantic effect values.

Let A=R0T0, B=R0T1, C=R1T0, D=R1T1, N=N_history and H=H_none. R=(C+D−A−B)/2; T=(B+D−A−C)/2; R×T=D−C−B+A. Fixed-factor comparisons are C−A, D−B, B−A, D−C. The other nine contrasts are each of A/B/C/D minus N, each minus H, and N−H. Interactions are unscaled differences in differences. No average main effect is substituted for a fixed-factor simple comparison.

All are **implemented package contrasts**. R also varies topic/predicate/entity and lexical cues; T varies dates/intervals/attribute values. N remains a procedural DIAGNOSTIC_ONLY control, not semantically neutral evidence. H has shorter context. Neither stale-answer competition nor internal model mechanisms are identified.

## Estimation, coverage and uncertainty

The code produces full label and ordinal distributions by condition and task family, eligible/recorded/unverifiable/null counts, case contrasts, speaker means, positive/negative/zero/unknown contributions, leave-one-speaker-out results and whole-speaker bootstrap sensitivity. Each case contrast retains its original weights; two cases are averaged within speaker, then six speakers equally. Bootstrap uses 10,000 draws, seed 715004, resampling both cases and all cells together.

Correct-, Incorrect- and Unverifiable-label incidences are distinct endpoints. Coding a Correct-label indicator as zero for an Unverifiable label does not reclassify it as Incorrect. The assessed C-versus-I sensitivity uses unknown values for Unverifiable, reports complete-case selection and maintains all-eligible signed bounds. Numerical nulls retain original explanations. Boundary ambiguity, uncertain semantics, inapplicability and missing human ratings are not interchangeable.

For incompletely observed endpoints, no all-eligible point estimate or conventional bootstrap interval is manufactured. The implementation reports identification bounds, selected complete-case sensitivity, and leave-one-speaker-out / resampling sensitivity of bound endpoints. Those endpoint percentiles are **not confidence intervals for an identified population mean**. For fully observed endpoints, percentile cluster intervals and leave-one-speaker-out estimates are available. Only six purposive clusters make all such intervals fragile, sometimes degenerate. No empirical ICC or population significance is inferred.

For the 1–5 axes, means are descriptive only. Full distributions, threshold indicators at >=2/3/4/5 and paired sign distributions provide ordinal sensitivities. All 16 comparisons are disclosed for every separate endpoint; there is no significance-based selection or post-hoc confirmatory hierarchy. Task-family contributions retain their case/speaker identities; each family has only two speakers. No semantic family effects have yet been computed.

## Confirmation, freezing and treatment join

`tools/p1c_semantic_analysis.py` has separate `prepare`, `register` and `analyze` actions. Preparation is complete. Registration rejects missing researcher adoption, incorrect source hashes, changed non-annotation fields, invalid ratings and duplicate corrections. It preserves AI proposals and explicit researcher changes separately, records actual registration time, and leaves an unrecorded human review time null. Existing destinations cannot be overwritten.

Only `analyze` reads the protected treatment mapping, after reconstructing the confirmed snapshot and checking hashes. The primary frozen-span dataset and any approved boundary sensitivity are analyzed separately, and each numerical analysis is reconstructed twice before export. The current run has not called either real registration or semantic analysis. Unit-test approvals are labeled synthetic fixtures in temporary test state, not scientific records.

After explicit researcher adoption, the commands are:

```text
.venv\Scripts\python.exe tools/p1c_semantic_analysis.py register --approval <separately registered actual researcher decision.json> --output <new confirmed annotation directory>
.venv\Scripts\python.exe tools/p1c_semantic_analysis.py analyze --registration <that confirmed annotation directory> --output <new analysis directory>
```

The source confirmation template is [here](validation/p1c/calibration_v1/semantic_review_v1/analysis_preparation/researcher_confirmation_request_v1.json). Do not pre-fill its human fields or treat this document as authorization. All 74 earlier scoped decisions and the later three experiment approvals remain valid within their original scope.

## Verification and Algorithmic Opportunity Assessment

Tests cover refusal of unconfirmed imports, exact source preservation, no overwrite, explicit corrections, rating ranges, Unverifiable handling, signed interaction bounds and reproducible whole-cluster calculations. These verify implementation, not scientific judgment validity. The closeout manifest records the complete suite.

No interaction-aware algorithm is justified before valid semantic effects exist and replicate. The [algorithm assessment](P1c_algorithmic_opportunity_assessment_v2.md) instead prioritizes independent measurement validation and fair existing-method comparisons.
