# ESCP prior-art kill test v1

Maintainer: Yaxin ZHENG. AI-assisted scientific development; human semantic confirmation remains pending. First submission target: PLOS ONE.


Phase P6 / RQ2 and RQ4. The formal candidate remains [ESCP v1](ESCP_candidate_specification_v1.md), including its multi-objective reliability/fidelity/CPU constraints. This update does not rename known rules or add a new algorithm.

| Candidate component | Closest method / simple baseline | New falsification evidence | Remaining gap |
| --- | --- | --- | --- |
| Evidence-state attribution | Zep source-linked graphs; relational joins | Same entity/attribute witnesses and diagnostic outputs | Free-text attribution errors and cost untested |
| Temporal provenance | Zep bi-temporal state; LongMemEval time filtering; interval/as-of predicates | Boundary dates and assertion cutoff handled equally by ordinary rules | No computational distinction established |
| Entity/value conflicts | Mem0 graph/update conflict handling; equality/set cardinality | Forged priority cannot override E; contradictory trusted values remain unresolved in both | No learned conflict advantage |
| Conditional persona admission | FC/PS typed permissions; whitelist/archive/quarantine | Equal admission groups, preserved style/behavior channels | Generated fidelity is unmeasured |
| Answer-component verification | Structured checks, CoVe, RARR | Correct intermediate, false extra claim, promise, abstention and semantic uncertainty distinguished equally | Extraction and model repair not tested |
| Persona preservation | History removal retaining S/F; faithful steering/admission comparators | Removing all persona empties channels; retaining them preserves only metadata | No measured linguistic/behavioral quality benefit |

## Observed Failure Modes

Historical Instruct errors motivate localization; the new oracle answers do not demonstrate persona interference. Original 16 fixtures and timing records remain intact. Sixteen **additional authored** adversarial fixtures test knowledge-as-of cutoffs, historical validity, inclusive endpoints, wrong entity/component, recollection versus answer, mixed correct/false claims, extra unsupported claims, abstention, unknown scope, unknown provenance, duplicate evidence and partial delivery.

## Existing Methods and Published Prior Art

The v8 matrix supplies primary sources and publication status. `tools/escp_kill_test.py` implements a plain relational rule baseline with the **same complete output contract** as ESCP: per-claim labels, support/conflict IDs, required-component states, abstention and task decision. It is neither a second annotator nor a reproduction of the larger published pipelines.

## Potential Algorithmic Improvements

Both implementations match all **16/16** new authored expectations, and their diagnostics are identical. Their admission channels are also identical. Therefore, the current proposed novelty is **not supported**. Do not add complexity without a residual failure beyond this baseline. Equal algorithmic information is privileged typed input, so no free-text capability or actual answer-recovery gain follows.

Both checks scan evidence for each claim: O(number of claims × evidence atoms), plus component matching. Indexing these joins would be a known engineering optimization, not a novel method. Future falsifiable claims must identify a different guarantee, extraction robustness or independently measured tradeoff; equal known rules falsify the present incremental-gain claim.

## Validation Feasibility

Three process-CPU batches of 5,000 × 16 cases: ESCP median **8.398 microseconds/case**, equal-output rules **5.273 microseconds/case**. Parsing, I/O and generation are excluded. No timing confidence claim or cross-machine speed guarantee is made. Earlier unequal-output timing is preserved, not substituted.

Ablations for entity/time/conflict/delivery remain in the original fixture records; new cases show that ordinary assertion-cutoff and speech-act predicates already cover the proposed extension. Channel retention is a falsification aid, not a measured Persona Fidelity cost. No algorithm inference was executed. Future independent evaluation needs real extraction, full costs, independent fidelity review and disjoint cases. Use no-persona, full-history, history removal, seeded random, relevance/BM25, entity-time and component checking baselines before expensive published adaptations.

## Publication Value

Current level: engineering adaptation and negative algorithm result. No replicated limitation of published methods or original contribution has been established. Preserve this result and prioritize the controlled empirical S/F/H study. PLOS ONE readiness still requires independent scientific evidence, not a renamed algorithm or passing fixtures.
