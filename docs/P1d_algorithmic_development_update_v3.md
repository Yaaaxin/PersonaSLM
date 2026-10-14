# P1d algorithmic development — v3

Maintainer: Yaxin ZHENG. Empirical research remains primary. No independent P1d output was generated or used for tuning. The only model computation was the separately authorized sixteen-request Base diagnostic; no additional algorithm inference or training occurred. All semantic measurements remain AI proposals. See the [focused primary-source matrix](related_work_novelty_matrix_monitor_v6.md).

## Response-boundary reliability

1. **Observed Failure Modes.** No-stop outputs repeat dialogue; stopped outputs retain promise-only first replies and section headings. Recoverability is16/16, while complete task answers are provisionally0/16.
2. **Existing Methods and Published Prior Art.** Native EOG, standard newline stops, role/fence extraction and official templates are mandatory simple baselines. Grammar-constrained decoding and draft-conditioned constrained decoding are generation methods, not equivalent to post-hoc extraction.
3. **Potential Algorithmic Improvements.** The implemented offline comparison finds exact agreement between conventional stop shadows and actual stopped outputs in8/8 pairs. This defeats a claim that a new parser is needed to obtain these cuts. Existing prefix-locality work still has zero additional P1c recoveries. No new mathematical/computational contribution is justified here.
4. **Validation Feasibility.** Five extractors were evaluated on all sixteen saved outputs. Two existing authored fenced-role fixtures demonstrate premature cuts from the same stop strings; those fixtures are not independent accuracy data. CPU batch measurements are saved, but several zero values reflect Windows timer resolution, not free computation. Runtime boundary truth requires real independent adjudication, with over/under-extraction and answer loss measured separately.
5. **Publication Value.** A reproducible negative diagnostic establishes a local distinction between continuation suppression and answer delivery. It does not establish a general mechanism, universal stop safety or a new algorithm.

## Evidence-state and answer-component verification

1. **Observed Failure Modes.** Eight new proposals are factual Correct only through generic policy repetition while task Failure. The other eight have no assessable factual claim; all lack requested components.
2. **Existing Methods and Published Prior Art.** Existing structured component checks, CoVe's factored verification and RARR's research/revision are relevant baselines. Their additional model/search calls are part of the algorithm cost.
3. **Potential Algorithmic Improvements.** A falsifiable development hypothesis is that explicit claim ownership, asserted date, requested date and delivered-component states reduce false task-success decisions at a fixed answer-loss rate. Existing structured checks already encode these distinctions. A new name or a regex promise detector would not supply originality; no additional ad-hoc parser is introduced just to claim a prototype.
4. **Validation Feasibility.** Use the existing metric contracts and new separate evidence forms; independently label promises, supported partial answers, wrong complete answers, quotations, negation and historical claims. Compare exact component matching, the structured verifier, a cost-matched CoVe adaptation and an evidence-revision baseline. Count false acceptance, false rejection, abstention, full task delivery and style preservation. No such downstream comparison has been executed.
5. **Publication Value.** Measurement improvement is defensible; an algorithmic contribution is unverified until stronger baselines fail and independent evidence supports a concrete difference. Current status: engineering adaptation / unresolved research hypothesis.

## Temporal provenance and historical evidence selection

1. **Observed Failure Modes.** P1b/P1c motivate entity/time distinctions. New H_none promise-only outputs do not demonstrate selection of stale history and cannot identify a temporal-selection failure.
2. **Existing Methods and Published Prior Art.** BM25, supplied-time/entity filters and LongMemEval time-aware expansion are required. The existing fair top-one experiment yielded time+BM25 and entity+time+BM25 success16/16 on author-structured development pools.
3. **Potential Algorithmic Improvements.** No remaining selection gap is shown on that pool. The potential gap is reliable free-text temporal attribution with abstention, not ordinary date filtering. LongMemEval already identifies date-extraction errors, so that observation alone is not novel.
4. **Validation Feasibility.** Independently authored unresolved-date/entity/conflicting-source tasks, equal candidate budgets, extraction errors counted and oracle-metadata upper bounds kept separate. Required CPU cost includes extraction, retrieval and generation; no new inference is authorized.
5. **Publication Value.** An honest baseline/negative result supports a rigorous empirical paper. No original temporal algorithm is currently supported.

## Persona/evidence separation and memory admission

1. **Observed Failure Modes.** Past package-level effects and source ambiguity suggest a question, not a unique causal mechanism. The current H_none diagnostic contains no additional history intervention.
2. **Existing Methods and Published Prior Art.** FPPS, FC/PS admission, query relevance gates, evidence-priority prompts and history removal must be compared. FPPS needs activation instrumentation; the memory-admission methods require adjudication resources.
3. **Potential Algorithmic Improvements.** Typed evidence-state constraints could be an incremental adaptation only after defining a failure left unresolved by these methods. No demonstrated computational distinction or independently supported originality currently exists.
4. **Validation Feasibility.** Keep trusted evidence, same cases and generation budgets; measure retained useful personalization and narrow persona fidelity as well as errors. History deletion is an informative baseline, not an adequate success criterion by itself. Include entity/time-check ablations only on development data.
5. **Publication Value.** Empirical tradeoffs remain worthwhile even without algorithm novelty. Avoid unsupported claims that the published methods fail on PersonaSLM.

## Interaction-aware conditioning

1. **Observed Failure Modes.** Prior R/T interactions were uncertain and boundary-sensitive; this16-request H_none study estimates no E/V interaction.
2. **Existing Methods and Published Prior Art.** Gating/steering/reranking are established families; no interaction-adaptive superiority baseline has been tested locally.
3. **Potential Algorithmic Improvements.** Defer adaptive algorithms until an interaction is independently replicated and localized. This is an evidence-based stopping decision for that hypothesis, not abandonment of the original S/F/H programme.
4. **Validation Feasibility.** A preregistered held-out test, fixed adaptation rule, full relevant cells and equal compute are necessary. Sixteen outputs from eight cases do not meet that standard.
5. **Publication Value.** No originality claim. The empirical validation path proceeds through model/measurement adequacy, then the approved scientific questions.

The [versioned opportunity registry](validation/p1d/format_calibration_v1/followup_v1/algorithm_opportunity_registry_update_v6.json) preserves failed hypotheses and falsification conditions. No candidate is classified as an independently supported original contribution.
