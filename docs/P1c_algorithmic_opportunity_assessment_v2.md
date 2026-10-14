# P1c Algorithmic Opportunity Assessment v2

Maintainer: Yaxin ZHENG. Empirical research remains primary. This additive report preserves [v1](P1c_algorithmic_opportunity_assessment.md). No new inference, training or remedy implementation was performed.

## 1. Observed Failure Modes

The verified engineering observations are 64 cross-turn continuations, eight ambiguous heading boundaries and 70 full-output budget stops. AI proposals identify 15 wrong-target-period replies and five other-entity/attribute errors among identifiable primary spans. Those labels still require human confirmation. Eight alternative first prefixes are plausible; four would be correct and four incorrect. Previous P1b confirmed analysis also shows correct intermediate content without full task delivery. These observations motivate bounded validation, but do not establish history causation or a gap in every existing method.

## 2. Existing Methods and Published Prior Art

The [updated source matrix](related_work_novelty_matrix_monitor_v2.md) verifies direct overlap with FPPS steering, LongMemEval time-aware retrieval/structured reading, FC/PS admission, AO-DA separation, CoVe and RARR. CUPMem and MemConflict remain additional temporal/conflict baselines from the earlier audit. Native stop handling, official chat templates, delimiter splitting, constrained output and deterministic ledger joins are known engineering. No prior method was reproduced on the current model in this task; an unavailable hidden-state or adapter implementation must not be replaced silently by a weaker namesake.

## 3. Potential Algorithmic Improvements

| Direction | Candidate and concrete unresolved question | Current classification / required baselines |
|---|---|---|
| Temporal-aware evidence selection | Bind the requested date, target entity and attribute jointly while retaining historical-query support. Is any residual error left after correct selection, rather than ordinary interval filtering? | Known engineering / incremental candidate. Compare all-evidence, latest-only negative control, exact query-time filter, structured reader, LongMemEval-style time-aware retrieval and feasible CUPMem adaptation. No originality established. |
| History relevance gating | Retain useful auxiliary history while avoiding unsupported influence. Current P1c has no confirmed semantic package effect and no direct answer competition. | Hypothesis only. Compare no gating, lexical/semantic relevance, random equal-budget selection and FC/PS; do not call text deletion a new algorithm. |
| Persona–evidence separation | Separate task evidence from expressive conditioning without losing fidelity. P1c has no fidelity target, so it cannot establish the trade-off. | Published method family. FPPS, mixed/separated prompts and AO-DA-style separation are required comparators where feasible. Additional compute/access differences must be explicit. |
| Answer-component verification | Distinguish supported target assertions from promises, wrong entities, correct intermediate facts and incomplete component sets. | Incremental candidate. Compare the retained literal baseline, typed evidence joins, structured planning, CoVe and RARR-style verification; candidate generation budgets must match. |
| Response-boundary management | Detect an attributable first reply without splitting quoted headings or treating a generated document as dialogue. | Measurement prototype candidate supported by reproducible traces. Compare response_status_v1, native EOS, first-role delimiter, literal section-header split and independently annotated boundaries. It is not a new generation method. |
| Interaction-aware conditioning | Adapt packages only if a reproducible interaction survives measurement and realization controls. | Not currently justified. No confirmed P1c semantic interaction exists; six clusters cannot validate a learned routing policy. Retain as a hypothesis, not an implementation task. |

## 4. Validation Feasibility

The most defensible bounded prototype plan is an **offline boundary evaluation**, after adjudicating the present spans. No prototype is claimed to be validated here. Use a separate development bank of 24 hand-authored synthetic continuations: six genuine role transitions, six genuine section-header transitions, six literal/quoted/code-block headers inside valid replies, and six document-style ambiguous outputs. Pair supported and contradicted answers across boundary types. Author and freeze a separate 24-item evaluation bank before tuning. These would be artificial fixtures, never reported as model generations.

Compare unchanged v1 extraction, a simple literal-header baseline, and a candidate state-aware splitter; ablate quote/code awareness and heading checks. Report boundary precision/recall, false splits, abstention, span agreement and semantic-label changes using independently annotated boundaries. An abstention is not an error fix. Improvement must persist on held-out formats and both correct/incorrect answers. If the simple baseline matches the candidate, record no algorithmic gain. This is ordinary local validation of measurement machinery, not authorization for a new model run.

For a subsequent answer verifier, use separate entity/date/component templates including negation, alternatives, promises, partial answers and historical queries. Do not use gold answer strings as deployable inputs. Compare fixed-evidence entailment/typed-join baselines before adding model-based checking. Ablate entity, temporal and answer-act checks; measure false acceptance, false rejection and correct-answer preservation. Any extra verifier generation requires its own bounded authorization. All unsuccessful variants and source/runtime hashes must remain available.

Offline string/ledger baselines require no model calls; wall time and peak RAM have not yet been measured. Model-based verification costs additional forward/decode passes and cannot be presented as free. The observed P1c request average was approximately 16.06 seconds in this local run; it is only a rough planning reference, not an estimate of another model or verifier. Persona fidelity effects are **unknown**, and removing all history cannot establish fidelity-preserving success.

## 5. Publication Value

The immediate value is credible measurement and a falsifiable account of where interpretation depends on extraction. A new algorithm would require a residual failure after strong baselines, a concrete methodological distinction, independent evaluation, ablations and cost/fidelity accounting. None is established now. Boundary repair alone and a higher pilot error count do not provide scientific novelty. A rigorous empirical paper can remain viable if no algorithm succeeds; null or adverse comparisons should be retained.

No candidate currently exceeds Level 1 exploratory evidence; confirmed structural traces are Level 0, and semantic proposals are not yet official observations. There is no Level 2 replication, Level 3 identified prior-method limitation or Level 4 independently validated original algorithm. The next research priority is independent measurement validity before larger inference.
