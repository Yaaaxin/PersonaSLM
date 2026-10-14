# P1c analysis readiness v1

Maintainer: Yaxin ZHENG. Status: AI-assisted review; researcher confirmation pending.

## Ready implementation, blocked official effects

The additive importer tools/p1c_integrity_registration.py accepts only an explicit researcher decision bound to exact source hashes. It retains original proposals, revised recommendations and actual corrections; refuses blank provenance, invalid scores, missing scope and overwriting. Registration freezes annotations before any treatment mapping is read for analysis. Current registered semantic annotations: **0**. Official semantic treatment effects: **not computed**.

After actual confirmation, use `register --approval ACTUAL_DECISION.json --output NEW_REGISTRATION_DIRECTORY`, then `analyze --registration NEW_REGISTRATION_DIRECTORY --output NEW_ANALYSIS_DIRECTORY`. These are instructions, not commands executed during this audit. Analysis rechecks the frozen registration and reconstructs numerical outputs twice. The wrapper reuses the existing paired-statistical implementation; no replacement estimator was introduced.

## Preserved specification

[primary_sensitivity_specification_v1.json](validation/p1c/calibration_v1/semantic_integrity_v1/primary_sensitivity_specification_v1.json) copies all 16 weights exactly from the approved registry (SHA-256 `713a7679d5a606707f8075bae51d3fa5716a721eccf86f1f56cebc73b4bbc4e7`). With cells R0T0,R0T1,R1T0,R1T1, R weights are -1/2,-1/2,+1/2,+1/2; T weights -1/2,+1/2,-1/2,+1/2; RxT weights +1,-1,-1,+1. Four fixed-factor contrasts, eight active-history-versus-baseline contrasts and one procedural-versus-no-history contrast complete the 16. Original condition IDs and interpretation remain unchanged.

All cells remain within their case; two cases per speaker, six equally weighted speaker clusters. Bootstrap resamples whole speakers with both cases/all cells, seed 715004, 10,000 replicates. Leave-one-speaker-out, task-family summaries, category/threshold distributions, paired signs and signed-weight unknown bounds are retained. Synthetic unit fixtures verify reconstruction and unknown handling; their results are not empirical model results. No current proposal was joined to conditions for semantic-effect calculation.

## Denominators and uncertainty

All seven semantic axes are eligible on 72 outputs; per condition 12. Fidelity is N/A. Missing, Unverifiable, incorrect, unresolved boundary, incomplete and N/A remain distinct. Correct-label incidence is not C-versus-I accuracy. Assessed-only contrasts require every nonzero-weight cell to be assessable and disclose condition-dependent censoring; never reweight surviving cells or condition on baseline correctness. Alternative boundaries remain sensitivity only. Descriptive all-eligible bounds are in [descriptive_sensitivity_bounds_v1.json](validation/p1c/calibration_v1/semantic_integrity_v1/descriptive_sensitivity_bounds_v1.json); they do not replace later sampling uncertainty.

Six clusters provide weak uncertainty estimation, particularly for interactions and sparse subgroups. Cluster bootstrap intervals may be unstable or optimistic; leave-one-out instability must be shown. Full reporting across 16 contrasts and separate endpoints is exploratory, without significance selection. Constant proposed coherence scores do not prove absence of an effect. No power, empirical ICC or independent replication is inferred from this development set.

## Validation and next evidence

Full tests: **947 passed in 47.38s**. Gate failures, original-field preservation, literal prefix hashes, ordinal edits, six-cluster routing and exact contrast weights have regression coverage. A test-only temporary approval fixture verifies software behavior; it is explicitly synthetic and never registered as a research decision.

First obtain the single annotation decision, then publish all registered exploratory contrasts internally with provenance. Independent validation should use new speakers/cases and a frozen precision target, prospective stratified independent human review, a separately controlled model/template comparison, and measurement examples that discriminate true partial completion from false complete answers. Sample size must follow cluster/interaction precision sensitivity, not the desired pilot sign. New inference still needs its own authorization. PLOS ONE submission readiness is not established by these tests or this calibration.
