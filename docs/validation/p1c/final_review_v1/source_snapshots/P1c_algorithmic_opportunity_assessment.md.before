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
