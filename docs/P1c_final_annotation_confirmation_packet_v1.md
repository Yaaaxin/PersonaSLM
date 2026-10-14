# P1c final annotation confirmation packet v1

Maintainer: Yaxin ZHENG. Status: AI-assisted review; researcher confirmation pending.

## One actual pending decision

The experiment, applicability, protocol addendum and execution were already approved; none needs reapproval. **Only adoption/correction of semantic annotation remains pending.** The researcher's earlier provisional preference for primary ratings plus boundary sensitivity is not final confirmation. No human decision or timestamp has been inferred.

Recommended adoption: the 72 reviewed primary proposals, including the six ordinal field recommendations below, retaining original boundaries; accept the eight alternative-prefix judgments exclusively as separately reported sensitivity. All original categorical/task/component/completeness proposals remain unchanged. The secondary view inherits the six ordinal changes and additionally proposes PC023 relevance/coherence 4 to 5. The choice concerns these disclosed versions, not an open-ended authorization to rescore.

| Response | Metric | Original | Recommended |
| --- | --- | --- | --- |
| PC004 | conversational_coherence | 4 | 5 |
| PC006 | response_relevance | 4 | 5 |
| PC006 | conversational_coherence | 4 | 5 |
| PC011 | conversational_coherence | 4 | 5 |
| PC027 | conversational_coherence | 4 | 5 |
| PC030 | conversational_coherence | 4 | 5 |


## Exact evidence packet

| File relative to repository | SHA-256 |
| --- | --- |
| docs/validation/p1c/calibration_v1/semantic_integrity_v1/reviewed_primary_proposals_UNCONFIRMED_v1.csv | 276a67c7a47994f6149834261b488a93399b100ac8fc1e2253f764f1d90d9285 |
| docs/validation/p1c/calibration_v1/semantic_integrity_v1/reviewed_primary_proposals_UNCONFIRMED_v1.json | 144a63679d2267b725dacb90294d7b72cbfbb9a5c724f4ed1312e099c78f5068 |
| docs/validation/p1c/calibration_v1/semantic_integrity_v1/boundary_sensitivity_table_v1.csv | d1d4318acfa298a45591c6b186ea17e3ede8f7c631f2a858538ef4613e219f4c |
| docs/validation/p1c/calibration_v1/semantic_integrity_v1/boundary_sensitivity_table_v1.json | 5c1b76d172018daf2e30f8be16c467cdbcdc61e79135a50865e1ff9f10ffad69 |
| docs/validation/p1c/calibration_v1/semantic_integrity_v1/reviewed_boundary_sensitivity_UNCONFIRMED_v2.json | 790e9f6210f3e0b465703911988343f89680a0650c83d51009c23be442f62a77 |
| docs/validation/p1c/calibration_v1/semantic_integrity_v1/uncertainty_classification_v1.json | 9e5fbdaff48e1d4ee40b2831eacdb1671f82fbfa4703668297e956e7b30303f4 |
| docs/validation/p1c/calibration_v1/semantic_integrity_v1/primary_sensitivity_specification_v1.json | 20d764c35a1ee8dfe5a4bf4121b46cfa5ea7885408e6a27afb9b3a402b2c6ba5 |
| docs/validation/p1c/calibration_v1/semantic_integrity_v1/researcher_confirmation_request_v1.json | 22ed47f13b07d603d4e59a25c4d07da88fc34437895d9d6b123e8b3faa945a6a |

The complete 72-row review is [reviewed_primary_proposals_UNCONFIRMED_v1.csv](validation/p1c/calibration_v1/semantic_integrity_v1/reviewed_primary_proposals_UNCONFIRMED_v1.csv); all original fields and seven original AI scores coexist with reviewed_AI_ratings, change reasons, separate evidence arguments and blank researcher fields. The eight-item view is [boundary_sensitivity_table_v1.csv](validation/p1c/calibration_v1/semantic_integrity_v1/boundary_sensitivity_table_v1.csv). Its full raw continuations and structural diagnostics are Stage B material: score the primary view first. The active all-72 secondary JSON is v2; inactive v1 preserves an incomplete CSV export and must not be imported.

Read [integrity](P1c_semantic_integrity_audit_v1.md), [boundary uncertainty](P1c_boundary_uncertainty_analysis_v1.md), [factual/task comparison](P1c_factual_task_success_comparison_v1.md) and [ordinal recommendations](P1c_relevance_coherence_ceiling_audit_v1.md). PC004 alias wording, PC006 calendar wording, five entity/time ambiguities and all eight alternative spans are explicitly flagged; a researcher may correct any of them rather than adopt the recommendations. No independent second reviewer or complete blinding is claimed.

## Explicit choices and consequences

1. **Adopt reviewed recommendations; retain eight boundaries only as sensitivity (recommended).** This accepts the six primary ordinal changes and the two additional PC023 secondary changes, with all stated uncertainties. Register a new confirmed snapshot, then run the unchanged 16 contrasts in distinct primary and sensitivity outputs.
2. **Adopt original proposals; retain eight boundaries only as sensitivity.** Use the original ordinal ratings, disclose the coupled-coding and ceiling concerns, and preserve reviewed recommendations as rejected/unadopted alternatives. The importer supports this without erasing either version.
3. **Provide specific corrections or defer adoption.** Record view, anonymous ID, metric, replacement and reason. Only the dependent semantic-effect workflow waits; no new inference is implied. The researcher may also exclude secondary analysis by explicitly choosing primary-only.

The existing JSON confirmation form records the chosen rating version and sensitivity scope. A text reply identifying this packet and choice can also be faithfully registered. All human fields are currently blank. No fabricated review date is required. The additive state flags separate boundary, evidence and annotation uncertainty without changing approved scoring or denominators; they are not a new approval gate. Any genuinely different primary boundary or estimand would require a separately specified policy change and is not authorized by these choices.

## Scientific scope

The official analysis will concern 12 paired development cases within six synthetic speakers. R/T are text-package effects; procedural controls remain DIAGNOSTIC_ONLY and no-history is shorter. No pure relevance, temporal mechanism or stale-answer competition claim follows. This approval would establish researcher adoption of AI-assisted judgments, not independent human agreement, confirmatory evidence or publication readiness. The packet hash is recorded externally in reproducibility_manifest_v1.json, avoiding a circular self-hash.
