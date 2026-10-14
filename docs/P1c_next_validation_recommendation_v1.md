# P1c consolidated semantic confirmation and next validation v1

Maintainer: Yaxin ZHENG. First submission target: PLOS ONE.

## One current researcher decision

The concrete review objects are the **72 primary AI-proposed records** and the **eight alternative boundary-prefix judgments**, with all original fields and explanations retained. The source files are immutable proposals, not human annotations. The mandatory gate comes from the researcher's instruction that official semantic effects require researcher-confirmed annotation registration. It does not arise from an engineering milestone and does not reopen prior experiment approvals.

| Object | Path within `docs/validation/p1c/calibration_v1/semantic_review_v1/` | SHA-256 |
|---|---|---|
| Primary reviewer CSV, 72 rows | `stage_a/semantic_proposals_UNCONFIRMED_v1.csv` | `0b86587c9d09a4cc976f3bbcce05f1307dc79ec4065f32ab12118f46efa2bdc8` |
| Primary machine snapshot | `stage_a/semantic_proposals_UNCONFIRMED_v1.json` | `2467cabf1d6df3ff7b997a4d10a097354c5ad61c322e42a37528489882fa6ac5` |
| Boundary review CSV, eight rows | `stage_b/ambiguous_boundary_review_UNCONFIRMED_v1.csv` | `f0f5189f395b665ae5602367674a5912c700360b8adecae33112be61c3ea6ded` |
| Secondary full sensitivity snapshot | `stage_b/boundary_sensitivity_proposals_UNCONFIRMED_v1.json` | `0df06bf52f11ad8e9071b398b1ae1f27772645caddbc680f3ed55369dfe5ae1a` |

Recommended review choice: adopt or explicitly correct the primary proposals, and separately accept defensible alternative prefixes **only for sensitivity analysis**. Available concrete decisions are `ADOPT_PRIMARY_AND_SECONDARY_AS_SENSITIVITY` or `ADOPT_PRIMARY_ONLY`; either supports explicit per-record corrections. A rejection/deferral leaves the affected annotations unconfirmed. Approval does not authorize new inference, establish reviewer independence or turn a proposal into confirmatory evidence.

Pay particular attention to PC004 (room/desk wording), PC006 (service-day/calendar wording), PC011/027/030/035/040 (entity versus temporal error), and PC010/023/033/039/042/044/054/063 (boundary alternatives, including three additional uncertain temporal judgments). PC023 also requires service-day wording adjudication. These are specific issues in one packet, not separate repeated gates. Every other proposed label also requires actual adoption, not presumed agreement.

The [72-item CSV](validation/p1c/calibration_v1/semantic_review_v1/stage_a/semantic_proposals_UNCONFIRMED_v1.csv), [eight-item CSV](validation/p1c/calibration_v1/semantic_review_v1/stage_b/ambiguous_boundary_review_UNCONFIRMED_v1.csv), [semantic report](P1c_semantic_review_report_v1.md) and [boundary report](P1c_structural_boundary_analysis_v1.md) contain the material needed to decide. A [machine-readable confirmation template](validation/p1c/calibration_v1/semantic_review_v1/analysis_preparation/researcher_confirmation_request_v1.json) supports a separately recorded actual decision and corrections; its human fields remain blank. Do not edit original proposal files or invent review times.

## Actions after confirmation

Register the actual decision, preserve original AI proposals and researcher corrections, freeze the confirmed snapshot, then join the protected mapping. Compute all 16 approved package contrasts for separate endpoints, uncertainty/unknown bounds, whole-speaker and leave-one-speaker-out sensitivity, task-family contributions and the separately approved boundary sensitivity. Reconstruct results twice. Do not select cells by baseline correctness or discard adverse outcomes. No further ordinary approval is needed for that already requested analysis.

## Independent validation before further scale

The primary next scientific action is **independent measurement validation**, not another large inference wave. A genuine second human reviewer should first use a disjoint rubric-calibration set, then score a prospectively selected blinded subset. Include all eight boundary-challenge items for diagnostic review and a reproducibly sampled set of 24 other items balanced across case and requested-date types. Report those two strata separately; oversampling difficult items does not estimate population agreement. Record the selection seed before the reviewer sees labels. No second reviewer has been obtained or invented.

Stage A must hide structure, treatments and AI suggestions. Stage B follows after its first judgments are frozen. Report raw agreement and categorical agreement statistics with prevalence caveats, ordinal weighted agreement, and explicit uncertainty/abstention. Adjudicate disagreements with evidence while retaining original independent labels. Researcher adoption of AI suggestions alone cannot supply inter-annotator agreement. If independent review is unavailable, disclose it and retain alternative label/boundary sensitivities; this is weaker validation.

Future empirical validation needs new speakers and task realizations, balanced current/historical queries, independent entity/value assignments, verified controls and a separately frozen analysis/sample plan. Retain the existing cluster-aware precision simulations as assumption-based planning, not measured ICCs or guaranteed effects. Six P1c speakers cannot establish interaction precision. Choose independent sample size from useful interval widths across plausible variances/ICCs, not the largest pilot effect.

Only after measurement is credible should a limited separately versioned Instruct/template comparison be considered. Its purpose would be testing coverage and model-configuration sensitivity with identical evidence/cases, not claiming a pure post-training effect. Official model-specific template, tokenizer/quantization provenance, budget and CPU costs must be frozen. No model download or inference was initiated here.

## Scientific contribution and publication

Potential evidence concerns boundary-dependent interpretation and conditional package differences under common evidence. Whether those differences exist, survive adjudication or replicate is unresolved. Prior work already addresses memory admission, time-aware retrieval, persona/factuality trade-offs and structural failure; the [updated matrix](related_work_novelty_matrix_monitor_v2.md) gives exact overlaps and falsification requirements.

PLOS ONE's [publication criteria](https://journals.plos.org/plosone/s/criteria-for-publication) emphasize original research, technical rigor, supported conclusions and ethical/data standards. The current development calibration is not submission-ready by itself. Independent evaluation, credible annotation, useful precision, scoped model generalization and shareable code/data remain necessary project work. Preserve truthful AI-assistance disclosure and check submission policies when preparing the manuscript. No publication or public release is authorized by this review.

## Algorithmic Opportunity Assessment

The [five-part opportunity assessment](P1c_algorithmic_opportunity_assessment_v2.md) recommends a bounded offline boundary benchmark with strong simple baselines before any claim of algorithmic improvement. A temporal/entity verifier remains a prospective incremental candidate; an interaction-aware intervention is premature. Existing methods may prove sufficient, which is a valid negative result for an innovation hypothesis.
