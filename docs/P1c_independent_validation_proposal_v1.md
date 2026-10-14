# P1c independent measurement validation and empirical replication proposal v1

Maintainer: Yaxin ZHENG. Prospective, not a new protocol adoption or inference authorization. Historical protocols and observations remain unchanged.

## Two different goals

Independent **measurement validation** asks whether another genuinely independent human applies the rubrics and identifies spans consistently. Independent **empirical replication** asks whether package effects recur on new speakers, cases and implementations. Researcher adoption of AI proposals supplies neither a second independent rater nor a new experimental sample.

## Measurement validation without new inference

Prefer a genuine second human to review all 72 existing outputs, because the development set is small. Do not claim this reviewer exists. Calibrate the rubric on separate examples that cross factual truth, completion, component support, relevance and coherent discourse; do not train the reviewer on the study's disputed labels. Freeze these instructions before access to evaluation outputs.

Randomize anonymous presentation with a recorded review-only seed. Stage A hides treatment, AI scores, previous comparisons, structural categories and raw continuation. Stage B independently examines complete continuations and proposes boundaries before seeing AI alternatives. Preserve initial judgments, uncertainty and adjudication separately. The researcher adjudicates only after both records are locked; do not erase disagreements. Report raw confusion matrices and agreement, nominal kappa where meaningful, weighted ordinal kappa, and exact/token-span agreement. Constant coherence can make chance-corrected agreement undefined or misleading. Use speaker-cluster sensitivity and disclose that the sample is purposive.

If reviewing all 72 is infeasible, preselect a stratified sample **before** the reviewer sees outcomes: retain all eight ambiguities and sample identifiable cases across task families and requested-date types with a fixed recorded seed. Report enriched strata separately; do not interpret unweighted agreement as population prevalence. Absence of independent review remains a limitation, not a reason to invent reliability statistics. New independent interpretation can motivate a separately versioned sensitivity analysis, not silent replacement of the approved primary snapshot.

## Independent empirical materials

Two candidate allocations remain **48 new speakers/96 cases/576 requests** and **96 new speakers/192 cases/1,152 requests per model arm**. Use three task families (single-fact, multi-component, entity/relation) and two query-date types. A balanced incomplete-block allocation gives each speaker two different task families, one current and one historical; rotate both assignments across 12 blocks. This partially crosses family with speaker, unlike the original family's nesting within two speakers. Package contrasts remain paired within each case; this design does not by itself identify a causal requested-date or task-family effect.

Generate new independent identities, entity/value assignments and wording templates before evaluation, without selecting cases by prior error direction. Include true partial-answer opportunities, explicit intermediate/final distinctions and questions that require the supplied context. Validate every answer path and potential shortcut. Keep sufficient evidence, question, reference, query date and fixed context identical across six cells. Assess whether relevance and temporal status can be crossed with stable propositions; otherwise retain the narrower package estimand. Answer competition is a separate manipulation, not automatically introduced into the R/T design.

Review control neutrality independently. Token matching is necessary for the intended length comparison but does not validate semantics. Retain shorter no-history and procedural diagnostic comparisons transparently if truly neutral content cannot be justified.

## Precision and cost

The [machine-readable calculation](validation/p1c/independent_validation_proposal_v1/precision_sensitivity_v1.json) preserves hypothetical contrast SD/ICC assumptions rather than fitting them from the six pilot speakers. For two cases per speaker, normal planning half-width is `z*SD*sqrt((1+ICC)/(2*K))`. The existing 135-scenario simulation is preserved; this is a transparent sensitivity calculation, not a new empirical power estimate.

| Speakers / paired cases / requests | Main half-width, SD .25, ICC .2–.5 | RxT half-width, SD .50, ICC .2–.5 | P1c-based request-time proxy |
| --- | --- | --- | --- |
| 48 / 96 / 576 | ±5.48–6.13 percentage points | ±10.96–12.25 points | about 154 minutes |
| 96 / 192 / 1,152 | ±3.87–4.33 points | ±7.75–8.66 points | about 308 minutes |

Higher SD .50 for main effects and 1.00 for interactions doubles these margins. Illustrative six-test Bonferroni margins are wider and are included in the calculation. Ordinal scales need their own distribution assumptions. Missing/unverifiable fractions of 0%, 10% and 25% must be stress-tested separately: adding speakers cannot eliminate unidentified outcome bounds. Candidate useful margins of ±5 points for main effects and ±10 for interactions are planning targets requiring formal adoption, not universal sample-size rules. Ninety-six speakers meet these targets only under the lower-SD assumptions, before stronger multiplicity or censoring penalties.

Runtime uses the 72 actual P1c latency records, approximately 16.06 seconds/request. These proxies exclude setup, review labor, longer prompts and model differences; use at least .5×/2× runtime sensitivity. No new model runtime has been measured. Increasing cases merely to accumulate responses is not justified if boundary or construct validity remains unresolved.

## Models, estimands and freeze

Retain the pinned Base as the reproducible reference. A separate same-family Instruct arm is scientifically useful for coverage and model/configuration sensitivity, but must use its official model-specific template and separately pinned weights, tokenizer, quantization and backend. Do not interpret Base/Instruct differences as pure post-training. A limited independently designed model-sensitivity calibration can precede a large second arm; it cannot substitute for independent replication or justify choosing whichever model gives the desired sign.

Before any new generation, approve the endpoint hierarchy, useful precision targets, model arms, allocation, missingness policy and bounded execution. A possible six-test confirmatory family is temporal Incorrect incidence and task success across R, T and RxT, with multiplicity control; this remains a future proposal and does not replace the current 16-contrast exploratory plan. Freeze fresh material and evaluator policy before use; do not tune on the future test set or reuse the inspected development cases as confirmation.

## Algorithmic Opportunity Assessment

The offline boundary investigation tests known extraction baselines and a small fence-aware engineering variant. Its accuracy still lacks independent boundary truth. A temporal or component method must beat query-time/entity joins, ordinary verification and applicable published methods at matched compute, preserve correct historical answers and evaluate persona fidelity where claimed. Independent measurement, then controlled replication, is a stronger immediate path to PLOS ONE than claiming a parser or time filter as a new algorithm. The current study is not ready for submission merely because registration and software checks pass.
