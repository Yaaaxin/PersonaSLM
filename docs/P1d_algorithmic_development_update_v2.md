# P1d algorithmic development — v2

Maintainer: Yaxin ZHENG. Empirical research remains primary. This update reports offline development work only; the separately authorized 144-request budget study is not an algorithm trial. See the [prior-art update](related_work_novelty_matrix_monitor_v5.md) and [opportunity registry v5](validation/p1d/final_preparation_v1/algorithm_opportunity_registry_update_v5.json). No future P1d candidate outputs were used, no additional algorithm inference occurred, and no original contribution is claimed.

## Temporal evidence selection

1. **Observed Failure Modes.** Historical P1b/P1c errors motivate separating entity choice, asserted time and requested time. The current development ledger pools permit direct checking of those distinctions.
2. **Existing Methods and Published Prior Art.** BM25, temporal filtering, entity joins and LongMemEval temporal retrieval are mandatory baselines. The local supplied-date filter is not a complete LongMemEval replication.
3. **Potential Algorithmic Improvements.** A fair top-1 diagnostic now replaces arbitrary ID-based tie breaking with exact expected performance under uniform ties. This is a baseline correction, not innovation.
4. **Validation Feasibility.** Across 16 registered development cases, expected target-and-time-valid selections are random 4/16, binary lexical overlap 4.5/16, BM25 8/16, time+BM25 16/16 and entity+time+BM25 16/16. Every method retains one item; structured filters receive privileged author metadata. These are selection results, not generated-answer accuracy. Median measured Python CPU is about 121 microseconds per case-method including pool preparation; wall time can be affected by concurrent calibration. [Exact results and five timing batches](validation/p1d/budget_calibration_v1/offline_retrieval_v1/summary_v1.json) preserve the evidence.
5. **Publication Value.** This negative novelty result shows no unresolved selection gap on this curated test. Free-text extraction, historical questions, conflicting evidence and persona fidelity require independent data before stronger claims.

## History admission and persona/evidence separation

1. **Observed Failure Modes.** Package-level conditioning differences and possible source confusion do not identify a unique internal interference mechanism.
2. **Existing Methods and Published Prior Art.** Compare all-history/removal, lexical/BM25 selection, FC/PS admission, evidence-priority prompts and FPPS activation steering. FPPS is not implemented by merely emphasizing evidence in a prompt.
3. **Potential Algorithmic Improvements.** A bounded CPU adaptation would need a concrete error left unresolved by those baselines while retaining useful persona information. No such gap is established here.
4. **Validation Feasibility.** Keep equal candidate/generation budgets and measure admission decisions separately from downstream reliability, complete delivery and narrow style fidelity. Removing all history is a baseline, not a sufficient solution. Activation instrumentation and full admission-judge costs are not available in the current pinned HTTP workflow.
5. **Publication Value.** An empirical tradeoff study can be valuable without a novel method. Current status is unverified opportunity; no prototype requiring generation is authorized.

## Answer-component verification

1. **Observed Failure Modes.** P1b supported partial replies and the budget study's answer-delivery audit require claims and task completion to remain separate. A promise or question echo is not an answer.
2. **Existing Methods and Published Prior Art.** Structured component checks, CoVe, RARR and DCCD already address related verification/realization problems. Their extra generation/search costs cannot be omitted from comparisons.
3. **Potential Algorithmic Improvements.** The existing asserted-date/requested-date checker remains a known-method engineering adaptation. A useful next falsifiable question is whether uncertainty-aware extraction avoids false task success without discarding correct historical claims.
4. **Validation Feasibility.** Independently annotate claim ownership, dates, negation, delivered values and unsupported additions. Preserve partial correctness, abstention, false rejection and persona style. Authored software fixtures are not independent language accuracy; no free-text checker superiority is established.
5. **Publication Value.** Measurement validity is presently the strongest contribution. A new checklist name or structured schema is insufficient novelty.

## Response-boundary reliability

1. **Observed Failure Modes.** P1c has eight unresolved primary spans. Later text can affect a whole-continuation parser; section headers also create attribution uncertainty even when a role delimiter is recognized.
2. **Existing Methods and Published Prior Art.** Native EOS, conventional stops, role/heading/fence extraction, official templates and grammar-constrained generation are established baselines. Offline cutting cannot estimate the causal effect of generation-time stopping or formatting.
3. **Potential Algorithmic Improvements.** A bounded prefix-locality prototype asks whether hazards strictly after an earlier role boundary should veto that prefix. It uses no answer key or condition labels. It is an engineering adaptation.
4. **Validation Feasibility.** On the 72 saved P1c outputs, the prototype yields 64 candidates and **zero additional recoveries** among the eight ambiguous outputs. Its advantage occurs only in authored software fixtures, not this empirical set. This negative result is retained in [the baseline report](validation/p1d/budget_calibration_v1/offline_baseline_v1/summary_v1.json). Independent span adjudication and answer-loss labels are still required; agreement with the old parser is not accuracy.
5. **Publication Value.** A controlled measurement-robustness study remains justified. Neither this prototype nor a post-hoc heading heuristic establishes a new algorithm. Generation-level format/stop diagnostics require separate authorization.

## Interaction-aware conditioning

1. **Observed Failure Modes.** Existing P1c package estimates are uncertain and boundary-sensitive; a reproducible interaction has not been established.
2. **Existing Methods and Published Prior Art.** Fixed conditioning policies and fully reported factorial comparisons precede any adaptive routing baseline.
3. **Potential Algorithmic Improvements.** No routing prototype is justified from an unstable nonzero estimate. Preserve the idea without tuning to effect signs.
4. **Validation Feasibility.** Require independent speakers and templates, frozen routing rules, matched compute, all registered contrasts and persona-fidelity assessment. Six or eight development clusters cannot establish population adaptation gains.
5. **Publication Value.** Deferred for insufficient evidence. PersonaSLM's original S/F/H programme and empirical publication path remain intact whether or not this optional track succeeds.
