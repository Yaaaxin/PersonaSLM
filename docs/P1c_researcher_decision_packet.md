# P1c Researcher Decision Packet — Proposed v1

Maintainer and final decision authority: Yaxin ZHENG. All decision fields below are deliberately blank. Preparing this packet does not authorize an experiment.

## Concrete proposal

Review [the design](P1c_history_mechanism_design.md), [identification limits](P1c_identifiability_assessment.md), [12-case form](validation/p1c/proposed_v1/stimulus_review_v1.csv), [precision plan](P1c_statistical_precision_plan.md), [neutral review](P1c_neutral_control_review.md) and [model proposal](P1c_instruct_model_proposal.md). Proposed development allocation: six new speakers, two requested-date cases each, four auxiliary R/T cells plus neutral/no-history controls; 72 Base-model requests. All cases are development only. No request is authorized or executed by this package.

| Researcher decision | Required scope | Decision / notes |
|---|---|---|
| Scientific target | Accept narrow topical auxiliary R/T, or prefer a separately prepared T0 stale-target comparison; do not conflate them | |
| Ground truth and semantics | Review all new cases, source intervals and selected history texts; explicitly accept residual topic/lexical/date differences | |
| Neutral controls | Accept a narrow length/format replacement interpretation or require a new version; no automatic P0/P1 transfer | |
| Development allocation/model | Approve 12 cases/6 speakers/72 cells, Base only, exact runtime configuration and budget | |
| Outcomes and annotation | Approve applicability, requested-date rubric, independent review plan and conservative unknown-unit policy | |
| Precision objective | State meaningful CI widths, candidate independent allocation and variance/ICC assumptions | |
| Protocol addendum | Approve exact prospective statements below without adopting v1.2 wholesale | |
| Execution | After all gates pass, authorize a named final manifest/hash and exact request limit separately | |

## Proposed addendum text — not adopted

1. **Scope.** P1c is a prospective, separately versioned history-content diagnostic within P1 Track A. It does not replace S/F/H or C0–C7. S and F are held at zero in the initial diagnostic. No historical estimate is reclassified as an R/T effect.
2. **Factors.** In the proposed auxiliary design, R denotes topical relation of a non-answer historical fact to the task, and T denotes its interval validity at the date explicitly requested by the question. Both values of T use historically true statements. This operationalization does not estimate direct stale-answer competition.
3. **Time reference.** Factual support for an explicitly historical question is evaluated at its requested date; the evaluation date anchors the fictional conversation but does not force the newest fact to be correct. This clarification is prospective and does not rescore prior data.
4. **Controls.** Keep identical trusted evidence, question, fixed context, answer requirements and within-arm model settings. Require exact full-prompt token matching among the four history cells and the reviewed neutral history, fixed wrapper/turn count/speaker and evidence position. No-history is a documented shorter baseline. Semantic validity requires explicit review; matching alone is insufficient.
5. **Endpoints.** Preserve four separate reliability axes and `response_status_v1`. Track delivery, component coverage and semantic completeness separately. Unverifiable and unavailable units remain distinct from Incorrect. Proposed primary future family is temporal Incorrect-label incidence and task success under R/T/R×T; six contrasts and multiplicity policy require approval before confirmatory freeze.
6. **Population and freeze.** The initial 12-case/6-speaker bank is development only. A later independent validation uses new speakers and withheld templates, a fixed sample, annotation policy and analysis before outputs. No future test set may be tuned after evaluation.
7. **Separate arms.** Presentation, Instruct models, direct stale-target competition, evidence deletion and algorithms are not included automatically. Each needs its own justified, versioned authorization; evidence availability remains Track B.

These statements require explicit researcher approval because they add prospective factors, a narrower relevance definition, date-specific scoring clarification and endpoint priorities beyond the historical executed design. Neither protocol file is edited. Acceptance of a document does not constitute inference authorization unless explicitly stated.

## GO / NO-GO rules

| Gate | Evidence required for GO | Present disposition |
|---|---|---|
| Scientific identification | Approved estimand and acknowledged limits | PENDING |
| Stimulus validity | Case-specific researcher decisions with preserved provenance | OPEN |
| Tokenizer/control construction | All intended zero differences, pinned native identities, reconstructed prompts and context fit | PASS for [v2 matched sets](validation/p1c/proposed_v2/tokenizer_validation_v2.json): 12/12, zero difference; v1 failures preserved |
| Neutral semantics | Selected text explicitly approved for narrow role | OPEN |
| Measurement | Fixed applicability, response-unit policy, rubric and annotation plan | PROPOSED |
| Execution freeze | Approved dataset/prompt/source/runtime hashes, order, seeds, raw logging and resume policy | NOT CREATED |
| Inference authorization | Researcher authorizes the exact frozen request set | NOT GRANTED |

**Current recommendation: NO-GO for inference; GO for researcher review of this prospective design.** Do not launch a smaller or altered experiment to bypass a failed gate. No algorithm, additional phase or model training is authorized.

The final [history review packet](validation/p1c/proposed_v2/history_semantic_review_v2.csv) contains 60 blank review records (four active histories and one neutral per case). The [selected configuration](validation/p1c/proposed_v2/configuration_proposal_v2.json) preserves the proposed 72-cell order. Full tests: 751 passed, zero failed, pytest 29.95 seconds, exit 0. These technical results do not supply human decisions. All 12 stimulus approvals and all 60 history judgments remain unprovided.

## What would warrant the bounded study

The researcher should judge whether a non-answer auxiliary relevance manipulation is informative enough for the central research question. If not, request only the narrower alternative comparison needed to address direct stale-target exposure, retaining sufficient trusted evidence and documenting answer-repetition limits. This is a targeted scientific decision, not a recommendation for another broad stimulus search. The independent validation allocation is a later decision, not a prerequisite to performing offline review now.
