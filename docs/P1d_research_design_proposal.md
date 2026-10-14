# P1d independent validation design — proposed v1

Maintainer: Yaxin ZHENG. Status: NOT ADOPTED; no execution authorization. The official paper title and PLOS ONE target remain unchanged.

## Recommended sequence and scientific question

First establish independent measurement of answer boundaries and distinct reliability constructs. Then evaluate whether historically true auxiliary claims interfere with answering from an identical sufficient ledger, conditional on entity match and query-time validity. Preserve useful persona style and measure its adherence separately. The proposed primary study deliberately narrows identification to **source-selection packages E×V**. E/V is a new prospective estimand, not a relabeling of P1c R/T. Adoption of this refinement requires approval of the P1d addendum.

The primary recommendation is 144 new synthetic speakers, two cases each, six conditions: 288 paired cases and 1,728 Base requests. A prospectively selected, balanced 24-speaker subset contributes 48 paired cases and 288 same-family Instruct requests. The total proposed main plus model-sensitivity scope is **2,016**, currently **zero authorized**. The Instruct subset is secondary and not powered to establish small model interactions. No sample is selected by the old effect direction or any baseline correctness.

An optional non-answer topical/date-scope module is specified separately in [identification and controls](P1d_identification_and_controls.md). It is not part of these 2,016 requests. This separation avoids asserting that a change in competing entity/value content is a pure relevance manipulation.

## Independent material boundary

The 16 newly authored examples, eight fictional personas and 96 rendered prompts in `validation/p1d/proposed_v1/development_examples_v3.json` are **development-only**, not the 288 independent cases. Versions v1/v2 are preserved: v1 reused distractor names across inconsistent ledgers; v2 still allowed arithmetic locker-to-hub-to-exit shortcuts. V3 fixes those issues without any model output selection. The examples remain a single demonstration domain and are not a representative corpus.

The future validation bank must use new speakers, independently authored task templates in at least four domains, independently permuted values, balanced query dates and a fresh frozen allocation. Do not merely run this generator with another seed and claim independent external validity. Freeze task templates, difficulty criteria, reference derivations and exclusions before response generation. Review material validity without model responses. Preserve all later failures; never drop a case because no-history or Base answers incorrectly.

The allocation tooling crosses four families with speakers through balanced incomplete blocks: each speaker receives two different families and one current/one historical query; each family has 72 cases across 72 speakers, half of each date type. A family is no longer nested within a tiny fixed speaker group. Four domains and multiple lexical realizations must be balanced in the final bank; their main effects remain nuisance strata rather than newly claimed mechanisms.

## Decision hierarchy

The [policy](validation/p1d/proposed_v1/analysis_policy_proposal_v1.json) proposes temporal Incorrect-label incidence and complete task success as separate primary endpoints. E, V and E×V yield six primary comparisons. All four reliability metrics, component coverage, semantic completeness, structural status and narrow persona-style adherence remain reported. There is no composite score.

Measurement acceptance precedes confirmatory freeze: material ground truth must be unique, requested dates explicit, controls appropriately scoped, boundary procedures independently adjudicable and scoring passes uncoupled. The proposed sample size is a precision-informed compromise, not a promise of significance. [Simulation results](P1d_sample_size_precision_plan.md) show that unresolved outcomes can dominate sampling uncertainty.

## Algorithmic Opportunity Assessment

**Observed Failure Modes:** P1c measurement sensitivity and prior P1b incomplete correct answers. **Existing Methods and Published Prior Art:** existing selection/verification baselines are implemented offline; literature overlap is explicit. **Potential Algorithmic Improvements:** only a failure beyond these baselines would justify a new method. **Validation Feasibility:** reserve new validation materials from all tuning and report CPU/fidelity trade-offs. **Publication Value:** a meaningful independently measured null result remains useful; more requests alone do not establish contribution.
