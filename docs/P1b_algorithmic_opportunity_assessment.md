# P1b Algorithmic Opportunity Assessment

Maintainer: Yaxin ZHENG. Empirical PersonaSLM research remains primary. This is an evidence-based assessment, not authorization for algorithm development, training, another model arm or additional inference. Formal Protocol v1.1 and the prospective v1.2 r1 remain unchanged.

## Present evidence and decision

**No new algorithmic direction is currently justified as a demonstrated solution to a PersonaSLM factual or temporal failure.** Wave1 has72/72 researcher-coded factual Correct and48/48 temporal Correct, with79 complete first replies. Its78 CROSS_TURN,17 TRUNCATED and1 AMBIGUOUS labels show a response-unit problem, not72 factual failures. The17 incomplete replies occurred in nonfactual greeting tasks. Automatic factual coverage improved from15 Correct /57 Unverifiable to72 Correct after confirmed human coding. This supports better measurement and bounded task calibration; it does not demonstrate a need to filter history or add a corrective reasoning architecture.

These observations and the assisted annotation provenance are retained in the [Wave1 analysis](P1_wave1_exploratory_factorial_analysis.md) and [structural/semantic comparison](P1_wave1_structural_semantic_comparison.md). The new24-case bank has **no empirical outputs**. Its plausible shortcuts and intended cognitive demands are prospective hypotheses. Lack of observed error is not proof that a mechanism never matters.

## Relevant existing methods

The existing [novelty matrix](related_work_novelty_matrix.md) and [P1b publication assessment](P1b_novelty_and_publication_assessment.md) remain the broader record. The following primary sources were checked for this assessment; abstract-level facts are not presented as reproduced results.

| Source | Verified overlap and implication |
|---|---|
| Chang Liu and Deliang Ding, *What to Admit and How to Present: Governing Persistent Memory in LLM Agents*, arXiv2610.11188v1, under review | Separates memory admission from rendering; compares whole-entry and typed-unit admission. Reported gains have personalization trade-offs, while rendering comparisons do not survive multiplicity correction. Selection/presentation decomposition is already explicit prior work; PersonaSLM must not claim it as an unprecedented idea. [Primary paper](https://arxiv.org/abs/2610.11188v1) |
| Di Wu et al., *LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory*, ICLR2025 / arXiv2410.10813v2 |500 questions include temporal reasoning, updates and multi-session reasoning. Indexing/retrieval/reading and time-aware query expansion already address memory access. Our short supplied ledger is not a long-term retrieval benchmark. [Primary paper](https://arxiv.org/abs/2410.10813v2) |
| Masaaki Nakatsu and Reno Wang, *Decoupling Logic from Persona: Structural Immunity of Edge LLM Agents to Context Pollution*, arXiv2610.09772v2 | Separates logic and persona paths with adapters and structured state. Same-base ablations cover two models and report substantial structured-output failures, with extra decoding cost and model-dependent robustness. Architectural separation and structural/semantic distinctions are overlapping prior methods, not automatically our novelty. [Primary paper](https://arxiv.org/abs/2610.09772v2) |
| Yuheng Zha et al., *AlignScore: Evaluating Factual Consistency with A Unified Alignment Function*, ACL2023 | A learned alignment metric assesses factual consistency; such scoring must be validated for new tasks rather than treated as oracle truth. [Primary paper](https://aclanthology.org/2023.acl-long.634/) |
| Zhongxiang Sun et al., *When Personalization Misleads: Understanding and Mitigating Hallucinations in Personalized LLMs*, Findings of ACL2026 | Directly addresses personalized factual reliability and mitigation. Persona–truth interference alone is not a new claim. Our proposed independent evidence-grounded factorial questions would need demonstrably different identification/measurement evidence. [Primary paper](https://aclanthology.org/2026.findings-acl.395/) |

No benchmark result from these studies is assumed to transfer to our2B Base transcript. No external code, data, adapter or model was imported.

## A. Historical evidence selection

**Supporting observations:** H changes some Wave1 structural/ordinal outcomes, concentrated in greeting cases; no factual/temporal error to explain. P1b E deliberately includes relevant past residence, while other families use unrelated history. Relevance is currently confounded with task family.

**Existing methods:** Admission/eligibility policies and relevance-based selection already occur in *What to Admit and How to Present*; memory retrieval is central to LongMemEval.

**Unresolved problem:** Whether irrelevant, stale or personally salient material causally interferes with sufficiently discriminative evidence-grounded tasks has not been separated here.

**Possible contribution:** An explicit, auditable selector respecting speaker, evidence source and proposition time could be a candidate only after a reproducible failure boundary exists. A rules-based filter alone is not a novel algorithm.

**Required validation:** A separate authorized relevance/temporal diagnostic with the same cases, content budget, task evidence and interpretation scope; preserve beneficial history use and measure both harm and utility on independent materials. Removing trusted evidence would violate this Track A contract.

**Baselines:** All-history, no-history, random equal-budget selection, query relevance selection, and a transparent deterministic eligibility rule. Control token budget and extra inference cost rather than rewarding shorter context automatically.

**Cost:** Deterministic scanning is linear in the available records under a simple implementation; neural retrieval/reranking adds unmeasured compute. Additional generation arms are not counted into the current192.

**Publication relevance / decision:** Potentially useful empirical boundary evidence, but strong prior overlap and no present model-error motivation. **Do not develop now.**

## B. Temporal validity handling

**Supporting observations:** Wave1 temporal coding is48/48 Correct. P1b sources expose inclusive intervals and both past/current question dates, but have not been tested. Symbolic boundary checks establish key correctness, not model temporal failure.

**Existing methods:** LongMemEval already studies knowledge updates and temporal reasoning and proposes time-aware query expansion.

**Unresolved problem:** Stale claims presented as current versus legitimate past statements; these must not be conflated. Current C3−C0 changes a history package, not only validity.

**Possible contribution:** Proposition-date-aware evidence selection or a temporal consistency checker, only if calibrated observations show a failure that existing methods do not handle. Always-current filtering would itself answer historical questions incorrectly.

**Required validation:** Independently varied relevance and temporal status with true past/current records, explicit time questions, no contradictory ground truth; unchanged task-sufficient Track A evidence. A separate proposal and approval are necessary.

**Baselines:** No filter, date-blind relevance selection, simple interval lookup, latest-only selection and oracle interval selection as a diagnostic upper reference. Latest-only is not an acceptable universal solution.

**Cost:** Interval checks over records are inexpensive; natural-language date/claim extraction or additional neural passes have unknown cost. Test dates and boundaries independently of this bank.

**Publication relevance / decision:** Conditional temporal failures could be informative; temporal checking itself is established. **No temporal algorithm is justified by current results.**

## C. Persona-style and evidence separation

**Supporting observations:** No factual variation in Wave1; structural/relevance changes are task-concentrated. Style effects cannot be inferred from the presence of a profile alone, and fidelity has no validated ground truth in P1b.

**Existing methods:** *Decoupling Logic from Persona* already uses separate logic/persona pathways; the admission paper separately controls what memory is supplied and how it is rendered.

**Unresolved problem:** Whether separating evidence extraction from style rendering improves supported content without destroying persona fidelity, once task, template, model, token and compute differences are controlled.

**Possible contribution:** At most a prospective controlled evaluation of a separation rule under an identified failure boundary. A two-pass “facts then style” architecture is not claimed novel.

**Required validation:** First show a repeatable adverse operational S or S×H effect on independent tasks. Then use a separately authorized arm with raw intermediate state, evidence preservation, style-fidelity references and identical final answer opportunities.

**Baselines:** Single-pass mixed context; simple section separation; no style; two-pass extraction/rendering with matched compute; existing appropriate decoupling methods where compatible. Adapter training is outside current authorization.

**Cost:** Two passes generally add work; exact CPU overhead is unmeasured. A same-token final reply does not equal same total compute.

**Publication relevance / decision:** Useful only if it resolves an identified trade-off beyond existing architectures. **Do not initiate development or training.**

## D. Response boundary control

**Supporting observations:** Structural labels and first-reply completeness disagree markedly in Wave1. Natural stopping was rare, yet many first replies were complete and supported. This is the strongest observed instrumentation issue, not evidence that a particular stopping rule cures it.

**Existing methods:** The repository already has frozen role-transition extraction, stop-marker diagnostics and `response_status_v1`. Prior decoupling work explicitly measures failures to emit required structures; structured-output reliability is not a new phenomenon.

**Unresolved problem:** Whether a model-appropriate boundary method improves usable first-reply coverage without deleting content or changing apparent factual effects. A stop marker can cut a correct clause prematurely.

**Possible contribution:** A reproducible measurement diagnostic distinguishing continuation, semantic completion and extraction error, with independent adjudication. That is more defensible now than claiming a new generation algorithm.

**Required validation:** A separately versioned later comparison on untouched material, freezing markers before outputs; evaluate false cuts, retained meaning, first-reply agreement, all structural categories and latency. Do not repeatedly optimize on the same P0/Wave1 examples.

**Baselines:** Existing no-stop Base transcript and parser; carefully declared role-marker stop; post-generation first-reply extraction; native Instruct template only as a separate configuration arm. Distinguish native termination from semantic completeness.

**Cost:** Parsing existing text is cheap and offline. Stopping/template arms need new authorized generations; shortened outputs may reduce cost but not necessarily improve validity. No such arm is run now.

**Publication relevance / decision:** A worthwhile conditional measurement study if P1b semantic coverage is poor. **Possible diagnostic, no novel algorithm claim.**

## E. Evidence-grounded answer verification

**Supporting observations:** The old automatic checker left57 factual responses Unverifiable that the researcher subsequently confirmed Correct. This is an observed scorer-coverage gap, not57 model errors. P1b has multi-component answers for which the old city checker is unsupported.

**Existing methods:** AlignScore and other claim/evidence alignment approaches already address factuality. The local symbolic oracle checks structured source queries and is not a free-text factual metric.

**Unresolved problem:** Claim segmentation, negation, mixed correct/incorrect claims, past-time attribution, partial answers and uncertainty must be handled without treating unsupported syntax as incorrect.

**Possible contribution:** A calibrated, auditable measurement interface that records source links and explicitly abstains outside coverage. Algorithmic originality would require evidence of improvement against existing verification methods on independent annotations.

**Required validation:** Independently labelled answers with contradictions, unsupported claims, partial replies, date shifts and ambiguous references; compare to human decisions while preserving disagreement. Do not use the same generated errors both to author rules and estimate their held-out accuracy.

**Baselines:** Task-specific exact/normalized matching as a limited baseline; current checker with abstention; claim-level symbolic checks where expressible; an appropriately validated learned alignment method; genuine human reference. No baseline's output is automatically ground truth.

**Cost:** Rules cost little per claim; learned verification adds model calls and may be expensive on CPU. Reviewer effort and verifier latency are unmeasured. Do not substitute an external paid judge or launch extra models.

**Publication relevance / decision:** Necessary evaluation coverage is an engineering priority; a new verifier is **not currently justified as a research algorithm**. Manual scoring with preserved evidence is the planned calibration route.

## Publication strategy and falsifiable next questions

The current preparation improves reference correctness, prospective applicability, input traceability and precision planning. It does not establish novel persona mechanisms, general reliability, a discriminative benchmark or a publishable effect. PLOS ONE expects technically rigorous analyses, adequate evidence and justified conclusions; it accepts negative/null results and requires a scientific rationale for close replication. [Journal criteria](https://journals.plos.org/plosone/s/criteria-for-publication).

The next bounded experiment, if approved, can weaken as well as support the premise that the new bank is more informative: continued ceilings across all families would leave discrimination unresolved; condition-invariant errors would show task difficulty without persona sensitivity; poor semantic coverage would favor a boundary diagnostic over scaling. Any observed interactions require uncertainty and independent material before broader claims. A separate history R/T diagnostic is justified only by a concrete unresolved question, not because those factors sound novel. Presentation must remain separately motivated against existing admission/rendering evidence.

Prioritize this calibration and honest measurement over algorithm invention or larger generation counts. Independent replication and configuration sensitivity may later strengthen a defensible empirical paper, but neither is silently added to this preparation task as a new mandatory experiment.


## Researcher-confirmed P1b calibration addendum

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Target: PLOS ONE. Protocol v1.1 remains formal; v1.2 Revised Proposed r1 is unadopted. Exploratory development evidence only. No new inference.

The original pre-calibration assessment above is preserved as historical context. This addendum uses newly registered 192-response evidence. No algorithm is implemented or claimed original.

### A. Temporal-aware selection and evidence-priority routing

**Observed Failure Modes.**34 adopted temporal contradictions;four occur already at C0. Selecting an old counter/residence/site/desk is observed, but retrieval versus generation responsibility is unresolved because the trusted ledger was fully supplied.

**Existing Methods and Published Prior Art.**[LongMemEval](https://arxiv.org/abs/2410.10813v2) includes temporal updates, indexing/retrieval/reading and time-aware query expansion. [What to Admit and How to Present](https://arxiv.org/abs/2610.11188v1) already separates admission/rendering and compares typed-unit versus whole-memory selection. These records/abstracts were checked; implementations were not reproduced.

**Potential Algorithmic Improvements.**A provenance- and proposition-date-aware admissibility layer is a candidate, not an original contribution. It would need to distinguish current versus requested past states and preserve beneficial old facts. A simple date filter is existing method practice.

**Validation Feasibility.**First identify a residual problem on independent ledger/reference-date material. Compare no-history/all-history, equal-budget random/relevance selection, deterministic interval lookup and established time-aware retrieval; ablate relevance, temporal eligibility and evidence priority separately. Keep trusted evidence constant. Rules cost little local computation; retrieval/extra decode cost must be measured. Removing relevant history can harm fidelity and utility.

**Publication Value.**A new failure boundary or robust negative result could be useful; a renamed filter cannot support originality. No new method is justified until simple baselines fail under an identifying design.

### B. Answer-component verification

**Observed Failure Modes.**27 supported partial outputs, including 20 D-family outputs, show claim consistency is not full task success. Three promises contain a reference string without delivering an answer.

**Existing Methods and Published Prior Art.**[AlignScore](https://aclanthology.org/2023.acl-long.634/) learns information alignment for factual consistency. Existing exact-match/abstention, QA/NLI and component checking address parts of verification; a support metric does not automatically verify task completion.

**Potential Algorithmic Improvements.**A separate coverage-and-commitment checker might help, but the present annotation distinction is not itself a new algorithm. Current component counts sometimes reflect textual coverage, requiring semantic validation.

**Validation Feasibility.**Compare reference exact-match with abstention, human claim/required-component inventory, established alignment/NLI verification and a deterministic component checklist. Use independent prompts with paraphrases, negation, promises and true intermediate facts. Ablate support, coverage and delivery separately. Offline rules are cheap; learned scoring or regenerated answers add measured CPU cost. Do not train and evaluate on these 192 responses.

**Publication Value.**A validated discrepancy between claim support and task success is empirically useful; originality of a new verifier remains UNVERIFIED. Any checker that erases style must be evaluated separately for Persona Fidelity.

### C. Persona/evidence separation and interaction-aware conditioning

**Observed Failure Modes.**The H package has negative descriptive task effects; SxH varies by endpoint and cancels in temporal labels. This is not evidence of representational entanglement.

**Existing Methods and Published Prior Art.**[FPPS](https://aclanthology.org/2026.findings-acl.395/) addresses personalized factual distortion. [AO-DA](https://arxiv.org/abs/2610.09772v2) separates reasoning and persona rendering. Prompt sectioning or two stages are not new by themselves.

**Potential Algorithmic Improvements.**Condition-dependent gating is only a hypothesis. It should not be fitted to the signs in this development table. Current evidence does not justify beginning implementation.

**Validation Feasibility.**Require independent factorial replication, matched-length/compute controls, native-template baselines, established separation/steering comparators and independent fidelity annotation. Ablate sectioning, extra decode and routing decision. One additional decode roughly doubles generation-call count, not necessarily latency; actual cost is unmeasured.

**Publication Value.**Only a replicated benefit beyond existing methods with preserved fidelity could justify a method contribution. This study has not supplied that evidence.

### D. Response-boundary management and recoverable outputs

**Observed Failure Modes.**186 cross-turns include 109 full correct first replies, while one ambiguous span remains. Four truncated outputs are unfinished thinking; one is a supported partial answer.

**Existing Methods and Published Prior Art.**Native chat/EOG templates, stop sequences, role-transition extraction and existing structured-output systems already manage boundaries; AO-DA studies structural failure. These are baselines, not invented methods.

**Potential Algorithmic Improvements.**A conservative extractor with abstention could reduce ambiguous units, but choosing later correct turns would introduce selection bias. A parser change cannot create missing final-answer content.

**Validation Feasibility.**Compare frozen extraction, native template/EOG and predeclared stop rules on independent material. Human unit annotations should measure false cuts, wrong-speaker inclusion, completion retention and semantic distortion. Offline extraction costs no model calls; generation arms require new authorization and matched controls.

**Publication Value.**Measurement sensitivity may support an empirical contribution. Boundary heuristics alone do not establish an original algorithm or solve temporal errors.

### Decision

Prioritize an identifying empirical diagnostic and independent annotation before algorithm work. The above opportunities are prospective; no training, retrieval system, routing algorithm or new decoding experiment was launched. Evidence insufficient for an original algorithm claim is reported as such.
