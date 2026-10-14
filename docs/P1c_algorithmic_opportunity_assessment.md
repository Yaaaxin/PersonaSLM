# P1c Algorithmic Opportunity Assessment

Maintainer: Yaxin ZHENG. The empirical study remains primary. **No new algorithm is implemented, trained or established as original.** Prior-art details and verification limits are centralized in the [literature audit](P1c_related_work_novelty_audit.md).

## A. Temporal-aware evidence selection

**Observed Failure Modes.** P1b adopted labels contain 34 temporal errors under sufficient dated evidence, including errors without added H. They do not isolate retrieval failure or an H mechanism.

**Existing Methods and Published Prior Art.** [LongMemEval](https://arxiv.org/html/2410.10813v2) already includes time-aware retrieval. [When Facts Change](https://aclanthology.org/2026.findings-acl.103.pdf) probes temporal conflict. Date filtering is established engineering.

**Potential Algorithmic Improvements.** Requested-date interval selection with explicit provenance could be useful, but a date filter is not original. A genuinely new claim would require a demonstrated residual failure beyond these baselines.

**Validation Feasibility.** First identify current-versus-historical selection failures on independent material. Future baselines: full evidence, simple date filter, query/time-aware retrieval and oracle validity lookup. Ablate requested-date parsing, interval resolution and provenance. Keep the full trusted ledger fixed in Track A; deleting evidence is a separate Track B diagnostic. Rule cost is small; model-based retrieval cost unmeasured. Check loss of valid historical facts and persona fidelity separately.

**Publication Value.** A well-controlled negative or conditional result is valuable; a new retrieval algorithm is presently unjustified.

## B. History relevance gating

**Observed Failure Modes.** H changes several endpoints, but topic relevance is not isolated. No P1c outcome exists.

**Existing Methods and Published Prior Art.** [What to Admit and How to Present](https://arxiv.org/html/2610.11188v1) compares admission and rendering, including relevance/random controls. Simple relevance gating is not new.

**Potential Algorithmic Improvements.** A future gate might distinguish topical relevance from authority and date applicability. This is a candidate decomposition, not an originality claim.

**Validation Feasibility.** Require independently identified R/T sensitivity. Compare all-history, token-budget-matched random/relevance selection, declared authority/date rules and published admission baselines. Ablate each criterion. Preserve trusted evidence. One model-adjudication pass could add substantial cost; exact CPU overhead is unknown. Gating may remove useful persona information, requiring separate fidelity/beneficial-use evaluation.

**Publication Value.** Strong direct prior-art overlap; implement only if a concrete gap survives fair baselines and independent cases.

## C. Evidence-priority routing

**Observed Failure Modes.** Sufficient trusted records do not guarantee correct requested-date selection. Existing effects are package-level observations.

**Existing Methods and Published Prior Art.** [FPPS](https://aclanthology.org/2026.findings-acl.395.pdf) steers factual/personalization representations; instruction hierarchy and source labeling are familiar controls.

**Potential Algorithmic Improvements.** A future explicit authority-and-time routing policy could be evaluated. Merely adding a stronger prompt or renaming a gate is not a new algorithm.

**Validation Feasibility.** Compare identical prompts with/without source-priority instructions, simple rule routing, no-history and a feasible published steering baseline. Hidden-state methods may require infrastructure/training beyond the current GGUF endpoint; no such work is authorized. Record facts retained, extra passes and fidelity costs. Independent contradictory and nonconflicting cases must both be included.

**Publication Value.** A robust failure boundary may justify incremental work; the present data do not identify an internal routing mechanism.

## D. Answer-component verification

**Observed Failure Modes.** P1b separates 137 Correct-label outputs from 110 full task successes; partial supported claims need not answer every component.

**Existing Methods and Published Prior Art.** Evidence extraction, checklist verification, structured answering and verify-then-revise are established method families. LongMemEval's reading strategies are relevant; a comprehensive verifier-method survey is **NOT FULLY VERIFIED** here.

**Potential Algorithmic Improvements.** A component-evidence coverage check might detect incomplete delivery. Detection alone is not a new reasoning algorithm.

**Validation Feasibility.** First independently validate component labels. Future baselines: no verifier, deterministic required-field checklist, structured answer schema, existing evidence-grounded verifier and oracle component audit. Separate detection from regeneration effects; retain false alarms, unsupported additions and latency. A deterministic check is cheap; a second pass adds approximately another response workload, not a measured runtime. Test on new task templates with frozen references, and measure any style loss separately.

**Publication Value.** Potential practical measurement improvement, but originality and generalization remain unverified. No implementation recommended now.

## E. Response-boundary management

**Observed Failure Modes.** P1b has 186 CROSS_TURN, five TRUNCATED and one AMBIGUOUS output. These do not map one-to-one onto factual error.

**Existing Methods and Published Prior Art.** EOS handling, native templates, stop sequences and parser span extraction are established engineering; [Decoupling Logic from Persona](https://arxiv.org/html/2610.09772v2) already distinguishes structural and raw-text failures.

**Potential Algorithmic Improvements.** The immediate opportunity is measuring unit-selection bias, not inventing a stop rule against these outputs.

**Validation Feasibility.** Independent human unit review first, then a separately frozen template/boundary diagnostic on unseen material if needed. Compare native template, frozen parser, explicit stops and human span oracle while preserving raw text. Stops may remove legitimate multi-paragraph content. Parsing is low cost; extra generation is not currently authorized. Check semantic coverage and fidelity before judging improvement.

**Publication Value.** Reproducible measurement findings can be useful; a stop sequence is not an original algorithm.

## F. Persona-evidence separation

**Observed Failure Modes.** Existing S/F/H and H observations do not distinguish representations, attentional competition or formatting. S×H heterogeneity includes cancellation.

**Existing Methods and Published Prior Art.** AO-DA separates logic/persona paths; FPPS addresses interference through steering. These directly limit originality claims.

**Potential Algorithmic Improvements.** An interaction-aware separation policy remains a hypothesis. Evidence does not currently justify designing it.

**Validation Feasibility.** Require an independently replicated interaction beyond length/topic/unit effects. Future baselines: shared-context generation, static evidence-first template, published two-stage separation, oracle fact preservation and an appropriate steering method. Ablate extra compute, source isolation and persona rendering. Multi-pass cost exceeds one decode; fidelity may weaken. Use independently frozen personas and task templates with separate fidelity raters; no training or adapter development is authorized.

**Publication Value.** High overlap and current identification gaps make implementation premature. The empirical R/T measurement study has priority.

## Decision

Proceed with stimulus/control review and independent measurement validation. None of the six opportunities currently warrants algorithm implementation. A separate proposal must name the failure, primary baselines, independent validation population, ablations, compute budget and fidelity tradeoff before approval. An algorithm is optional for PLOS ONE; sound empirical evidence is mandatory for the intended paper.


## Scientific-identification review addendum

The unchanged bank and [new counterfactual audit](P1c_counterfactual_pair_audit.md) provide no new model failure observations. They show that R/T switch auxiliary predicates, colors and intervals, with cyclic lexical cues. None supplies a stale target answer. Consequently the present bank cannot validate a remedy for direct outdated-answer competition, even if a future package interaction is observed.

The six five-part assessments above remain in force. The following update links each direction to the newly clarified identification boundary and the [verified prior-art check](P1c_scientific_prior_art_review.md).

| Direction | Observed Failure Modes | Existing Methods and Published Prior Art | Potential Algorithmic Improvements | Validation Feasibility | Publication Value |
|---|---|---|---|---|---|
| Temporal handling | P1b dated errors; P1c date/value coupling, no new outcomes | Time-aware retrieval/interval filtering; LongMemEval | Requested-date handling is a candidate engineering baseline, not an original method | Independent current/historical tasks; full ledger versus reviewed auxiliary selection; ablate date/value cues without deleting trusted evidence | No algorithmic claim until a residual beyond simple rules is identified |
| Relevance gating | H package differences do not establish relevance failure | Admission, random and relevance controls in the admission/presentation study | A future topic/authority distinction must improve on existing gates | Use independent lexical assignments; all-history, no-history, matched random and query-relevance baselines; measure beneficial-memory/fidelity loss | High overlap; present work is identification, not a gate invention |
| Evidence-priority routing | Sufficient evidence coexists with errors, including at C0 | FPPS and source-priority engineering | Explicit provenance routing remains hypothetical | Compare evidence-first and source-label baselines; hidden-state steering requires separately approved infrastructure; test both conflicting and nonconflicting records | Unresolved causal target; no implementation justified |
| Component verification | P1b 137 supported-claim labels versus 110 full answers | Checklists, structured answering and evidence-grounded reading; comprehensive verifier survey incomplete | Detect missing required components without falsely treating them as contradictions | Independent task templates; deterministic checklist, no verifier, published verifier and oracle component labels; separate detection from regeneration | Potential measurement contribution, originality UNVERIFIED |
| Persona/evidence separation | No isolated persona mechanism follows from current R/T bank; S/F held off | AO-DA and FPPS directly overlap | Interaction-aware routing is only a hypothesis | Needs independently replicated S/F/H effects; equal-compute mixed/separated/steered baselines and separate fidelity scoring | Not justified by this auxiliary-history design alone |
| Boundary management | P1b continuation and first-reply success diverge | Native templates, EOS/stops, extraction and structural/raw-text analyses | First establish unit-selection bias; a stop rule is not inherently novel | Independent blinded unit review; frozen parser/native-template/stop and human-span-oracle comparisons; no selection of later answers | Useful validity evidence if reproducible; no new algorithm established |

Implementation complexity and CPU cost remain unmeasured for prospective methods. Deterministic interval/checklist rules are plausible low-cost baselines, while model adjudication, verification/regeneration or two-pass separation add work; no timing claim is made. Fair ablations must separate extra compute, source exclusion, temporal parsing and formatting. Any method must use separate development material and independent evaluation, retain errors/null results, and measure potential persona-fidelity loss independently. No method is approved for implementation or training.

## Final-review opportunity assessment

The [final identification decision](P1c_final_identification_decision.md) preserves the distinction between an implemented history package and a latent mechanism. No P1c inference exists. The empirical track remains primary; **no strong original algorithmic contribution is currently demonstrated, and no algorithm implementation is justified by this preparation**. The following six-part assessments specify the additional evidence and mandatory baselines for any later proposal.

### Temporal-aware evidence management

1. **Observed Failure Modes.** P1b contains temporal errors under sufficient evidence, including some no-history baseline errors. P1c repeats auxiliary label facts, not outdated target answers.
2. **Existing Published Methods.** [LongMemEval](https://arxiv.org/html/2410.10813v2), ICLR 2025, includes temporal memory evaluation and time-aware retrieval. [When Facts Change](https://aclanthology.org/2026.findings-acl.103.pdf), Findings ACL 2026, studies temporal knowledge conflict. Interval filtering and newest-record heuristics are established baselines, not inventions.
3. **Remaining Methodological Gap.** Requested-date errors must be separated from retrieval availability, target-answer competition and lexical cues. Current package comparisons cannot settle those alternatives.
4. **Potential Algorithmic Improvement.** A provenance-aware requested-date selector is only a candidate incremental technique; no distinct algorithm beyond existing filtering has been specified.
5. **Validation Feasibility.** Mandatory baselines: all-history, no-history, requested-interval filter, newest-record heuristic, feasible published time-aware retrieval and an oracle. Hold trusted evidence fixed; evaluate current and historical queries on independent entities/values. Ablate time parsing and source authority separately. Measure selection errors, latency and lost personalization. Deterministic rules are expected to be cheap, but CPU cost is unmeasured.
6. **Publication Value.** An independently reproduced failure boundary could be useful. A novel temporal selector is not an established contribution here.

### History relevance selection

1. **Observed Failure Modes.** P1b's negative H package estimates motivate testing content effects, but do not prove relevance failure. P1c's R changes attribute and color together.
2. **Existing Published Methods.** [What to Admit and How to Present](https://arxiv.org/html/2610.11188v1) is a preprint studying memory admission and rendering, with query-relevance, random/admission-count and typed-unit controls. Filtering and reranking are existing methods.
3. **Remaining Methodological Gap.** Whether benefit comes from relevance, reduced exposure, authority or changed token volume remains unresolved in the present evidence.
4. **Potential Algorithmic Improvement.** A gate that distinguishes answer support from merely topical material might be testable, but its originality is unverified.
5. **Validation Feasibility.** Mandatory baselines: full history, no history, equal-count random admission, query-relevance selection and an appropriate published admission policy. Preserve common trusted evidence, equalize retained length where feasible and measure beneficial-memory loss. Independent lexical/template assignments and answer-bearing versus auxiliary histories are needed. Compare extra adjudication compute fairly; record CPU cost and fidelity separately.
6. **Publication Value.** High direct prior-art overlap. Identification evidence is more defensible than announcing a new gate.

### Evidence-priority routing

1. **Observed Failure Modes.** Supported evidence and incorrect delivered answers coexist in P1b; this does not locate an internal routing defect.
2. **Existing Published Methods.** [When Personalization Misleads](https://aclanthology.org/2026.findings-acl.395.pdf), Findings ACL 2026, proposes FPPS steering. Source labels and instruction priorities are standard engineering controls.
3. **Remaining Methodological Gap.** The evidence does not show that an authority-routing policy improves on simple evidence-first instructions under equal compute.
4. **Potential Algorithmic Improvement.** Explicit provenance routing remains a prospective hypothesis, not a specified new method.
5. **Validation Feasibility.** Mandatory baselines: existing evidence-first prompt, source-priority instruction, simple rule routing, no-history and a feasible FPPS comparison. Hidden-state steering requires different infrastructure; its absence must be disclosed rather than mislabeled as an implemented baseline. Test conflict/nonconflict records on independent materials, ablate instructions versus actual routing, and measure compute and fidelity loss.
6. **Publication Value.** Potential incremental reliability work only after a residual failure is identified and independently replicated.

### Answer-component verification

1. **Observed Failure Modes.** P1b has 137 factual Correct labels but only 110 full task successes. Missing components need separate detection from false claims.
2. **Existing Published Methods.** [Chain-of-Verification Reduces Hallucination in Large Language Models](https://aclanthology.org/2024.findings-acl.212/), Findings ACL 2024, separates draft, verification questions, their answers and revision; factored verification avoids conditioning on the original answer. [RARR: Researching and Revising What Language Models Say, Using Language Models](https://aclanthology.org/2023.acl-long.910/), ACL 2023, retrieves support and revises unsupported content while considering preservation. Attribution is not identical to factual truth. Method sections were inspected; implementations were not executed.
3. **Remaining Methodological Gap.** Claim verification alone need not ensure that every requested component was delivered; the benefit of an explicit requirement-to-evidence coverage check beyond existing methods remains untested.
4. **Potential Algorithmic Improvement.** A component-completeness audit is a candidate measurement extension, not yet a novel generation algorithm.
5. **Validation Feasibility.** Mandatory baselines: no verifier, deterministic required-field checklist, structured answer, CoVe, and a RARR-style evidence/revision baseline. Restrict any adapted retrieval to the shared trusted ledger to retain Track A; label that adaptation. Compare detection and regeneration separately with equal-compute controls and independent task templates. Record false alarms, added false claims, missing components, CPU latency and fidelity changes. Multi-call costs must be measured, not assumed to match one decode.
6. **Publication Value.** A reproducible coverage finding may be useful, but novelty requires a demonstrated residual beyond these published approaches. The full verifier literature is not exhaustively verified.

### Persona-evidence separation

1. **Observed Failure Modes.** P1b S/F/H differences and heterogeneous interactions do not identify attention or representational interference. P1c holds S/F off.
2. **Existing Published Methods.** [Decoupling Logic from Persona](https://arxiv.org/html/2610.09772v2), a preprint, already evaluates separated logic/persona paths and structural versus raw-text behavior. FPPS supplies a distinct published steering approach.
3. **Remaining Methodological Gap.** Whether adaptive separation exceeds static separation under equal evidence, compute and fidelity constraints is unknown.
4. **Potential Algorithmic Improvement.** Interaction-aware routing is an unverified idea; current R/T cases cannot validate its persona mechanism.
5. **Validation Feasibility.** Mandatory baselines: mixed context, evidence-first static prompt, published two-stage separation, feasible steering and oracle factual preservation. Use separately reviewed S/F/H stimuli and independent fidelity judgments. Ablate extra passes, source separation and final rendering; preserve all failure categories and measure CPU overhead.
6. **Publication Value.** Direct overlap makes implementation premature. A rigorous empirical comparison would precede an originality claim.

### Response-boundary management

1. **Observed Failure Modes.** P1b's 186 CROSS_TURN outputs coexist with successful and unsuccessful first replies; five TRUNCATED and one AMBIGUOUS output remain preserved.
2. **Existing Published Methods.** Native chat templates, EOS, stop strings, structured decoding and first-reply extraction are established techniques. The separation preprint above already examines structural/raw-text distinctions.
3. **Remaining Methodological Gap.** The magnitude and direction of unit-selection bias under independent human span judgments are not established.
4. **Potential Algorithmic Improvement.** No original boundary algorithm is specified. The immediate candidate is an independent measurement diagnostic.
5. **Validation Feasibility.** Mandatory baselines: frozen parser, official model template, predeclared stops and human-span oracle. Use unseen material, preserve raw outputs, and measure loss of valid multiline replies. Additional budgets/templates require separate arms. Parsing cost is low in principle; decode and reviewer cost must be recorded. A style may legitimately be long or multi-paragraph, so fidelity must be checked separately.
6. **Publication Value.** Well-supported measurement bias can strengthen an empirical paper; a high continuation rate or new stop string alone is not a scientific innovation.

## Publication and model sensitivity decision

Preserve Base for the scoped development candidate if approved. A later same-family Instruct arm should pin the official template, tokenizer/model revision, quantization and thinking configuration, and repeat paired inputs under a separately declared configuration. This tests sensitivity to a model/template package, not pure post-training. Neither algorithm development nor an additional model is a prerequisite manufactured for this offline review. For PLOS ONE, independent validation, sound measurement, uncertainty, data/code availability and accurate AI-assistance provenance remain substantive needs; the current calibration proposal alone is not publication-ready.
