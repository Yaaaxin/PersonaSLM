# P1d algorithmic opportunity assessment — v1

Maintainer: Yaxin ZHENG. Main track: empirical validation. Optional algorithm track: evidence-driven and independently evaluated. No new inference or training was performed.

## 1. Observed Failure Modes

P1c's eight unresolved boundaries change exploratory package contrasts under sensitivity extraction; wrong-entity/time interpretations require care. P1b separately demonstrates correct factual partial answers without task completion. Neither establishes a novel memory mechanism. Shared scoring and structured fixtures are measurement issues. The six-speaker P1c interaction is too uncertain to justify an interaction-adaptive method.

## 2. Existing Methods and Published Prior Art

The [published comparison](P1d_published_baseline_comparison.md) and [primary-source matrix](related_work_novelty_matrix_monitor_v4.md) cover FPPS steering, FC/PS admission, time-aware retrieval, CoVe, RARR and AO-DA separation. Native stops, official templates, deterministic parsing, grammar constraints and metadata joins are established techniques. The new offline implementations are classified as **engineering adaptations**. Published hosted-model pipelines cannot be claimed replicated by a local checklist.

## 3. Potential Algorithmic Improvements

| Candidate | Specific falsifiable gap | Current classification / decision |
| --- | --- | --- |
| Temporal/entity resolution | Can a verifier reject wrong entity/interval claims without corrupting legitimate historical answers when metadata extraction is uncertain? | Exact join implemented; known baseline. Uncertain extraction is unvalidated, no original method yet |
| History admission | Can useful persona/history information be retained at an equal token budget while excluding conflict beyond lexical/time filters? | Existing-method adaptation; require FC/PS and retrieval comparisons |
| Persona/evidence separation | Can complete answer delivery improve with less style damage than removal or priority prompts at matched compute? | Incremental candidate; no current generated fidelity evidence |
| Component verification | Can missing final components be detected without confusing true intermediate claims, negation or promises with answers? | Structured prototype completed; free-language generalization unverified |
| Boundary abstention | Can calibrated abstention reduce false splits and answer loss beyond headings/fence rules? | Incremental candidate; unique independent spans absent, prior fence refinement gave no real gain |
| Interaction-aware conditioning | Is a reproducible conditional interaction large enough to support adaptation? | DEFER: no stable independent interaction evidence |

No candidate is classified as an independently supported contribution. The strongest simple structured baseline already solves the authored entity/time fixtures. Combining it with a component checklist does not create a demonstrated methodological gap. A new name or implementation is insufficient.

## 4. Validation Feasibility

The bounded next prototype, if independent measurement supports it, is a **selective structured verifier with explicit abstention**, developed on new synthetic development material. Input: proposed claim tuples with extraction uncertainty, query entity/date, required components and a trusted ledger. Output: supported/contradicted/unresolved claims, missing components and an abstain/review recommendation. Start with the current exact-join baseline; do not add learned thresholds until an independent development set exposes a reproducible deficiency. No rewriting or generation is part of this offline prototype plan.

Fair baselines are exact entity/date joins, time-only/lexical selection, a deterministic component checker, applicable published verification adaptations and boundary rules. Ablate entity binding, interval selection, delivery checking and abstention; preserve all errors. Freeze parameters before independent evaluation. An improvement must survive independently labeled raw spans, protect previously correct answers, reduce complete-task failure and retain persona fidelity. Compare cost and abstention coverage, not only an inflated accuracy on a smaller selected subset.

Required observations include independently adjudicated boundary errors and human-validated claim extraction errors. Current authored fixtures are insufficient for a new algorithm claim. Future private data or new model calls require the existing governance gates. No algorithm was tuned on future held-out answers; none exist yet.

## 5. Publication Value

The empirical route remains viable if every method matches a simpler baseline. Current evidence supports Level 0 engineering observations and Level 1 exploratory patterns. Levels 2–4 require independent replication, demonstrated limitations of strong existing methods, and independently validated methodological improvement respectively. Preserve abandoned ideas: pure R/T mechanism identification from P1c, a fence-aware recovery claim on real outputs, and calling ordinary filtering original have all been rejected for insufficient evidence.

The machine-readable [opportunity registry](validation/p1d/proposed_v1/algorithm_opportunity_registry_v2.json) records these decisions, baselines, costs and falsifiers. A PLOS ONE paper must rest on valid independent evidence; optional algorithm ambition must not replace that requirement.
