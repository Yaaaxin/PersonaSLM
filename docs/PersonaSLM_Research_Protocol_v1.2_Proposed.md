# PersonaSLM — Research Protocol v1.2 (Proposed)

**Working paper title:** Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models  
**Researcher and maintainer:** Yaxin ZHENG  
**Study:** Controlled empirical NLP study, with subsequent authorized real-speaker validation  
**Primary research language:** English (stimuli, generated conversations, annotations, analyses, and paper)  
**Version status:** **PROPOSED AMENDMENT, NOT YET ADOPTED**. Research Protocol v1.1 remains the frozen research-design baseline until the researcher approves this version and records a protocol decision. Neither the already accepted P0 evidence nor historical results may be rewritten. The confirmatory-experiment freeze remains outstanding.

> **Research anchor.** Under the *same sufficient, valid trusted evidence and question*, determine whether and how speaker-specific linguistic style (S), supplementary personal facts (F), and date-stamped dialogue history (H) change distinct reliability outcomes of 0.8B–3B language models. Seek reproducible **conditional patterns, interactions, failure boundaries, and explanations supported by controlled comparisons**—not merely another demonstration that persona prompts can help or hurt. Neither harm nor novelty is assumed in advance.

## 1. What changes relative to v1.1—and what does not

### 1.1 Retained without alteration

- The official working title, real-speaker modeling motivation, English scope, RQ1–RQ4, and the six post-P0 research phases.
- S/F/H and the eight Track A factorial conditions C0–C7; the distinct Track B knowledge-availability experiment.
- Identical, task-sufficient, correctly dated trusted evidence **within every Track A case**.
- Four separate Dialogue Reliability constructs: response relevance, factual consistency, temporal consistency, conversational coherence; independent linguistic and behavioral Persona Fidelity.
- Primary *provisional simple contrasts*: C1–C0 and C3–C0; additional N_style and N_history comparisons with exactly defined estimands. Exploratory average main effects and interactions are not retroactively promoted to confirmatory primary outcomes.
- CPU-only fixed deployment, auditable raw generation/parsed spans, response boundary and evaluation versioning, per-question outcome applicability, privacy, honest missingness, and the two-stage research/confirmatory freeze.

### 1.2 Proposed methodological refinements

1. Make the project's **novelty-sensitive questions** explicit, together with supporting and falsifying patterns and direct prior-work threats.
2. Separate **total added-prompt-package effects**, **length/wrapper-controlled replacement effects**, **factorial interaction effects**, and **additional mechanism probes**. Do not use the same label for different estimands.
3. Introduce a **planned historical-content diagnostic** with relevance (R), temporal status (T), and presentation (P), explicitly outside the original eight cells unless separately approved and versioned.
4. Define **structural response failures independently from substantive answer errors**, and report denominator/coverage sensitivity rather than excluding failed generations after seeing them.
5. Require distinct, counterbalanced speaker and scenario realizations, plus stimulus-level manipulation checks; a prompt-template variation is not automatically a style mechanism.
6. Give **each phase a precise input, experiment, anticipated output artifact, decision gate, and negative-result interpretation**.
7. Make the **literature overlap/novelty audit a prospective gate** before committing to any additional expensive experiment or contribution claim.

These refinements add discipline and priorities; they do not claim that the factorial scheme, exact-token matching, persona interference, or real-speaker simulation were invented by this project.

## 2. Scope, populations, and non-goals

**Scientific population of interest.** Small language models (~0.8B–3B) asked to answer new English dialogue turns while conditioned on a target speaker's characteristics derived from past speech or dialogue. A target speaker is an explicitly identified entity and must not be conflated with the present user or interlocutor.

**Three distinct evidence tiers.** (1) Controlled fictional English personas: isolation and known ground truth; (2) English historical conversations of real speakers supplied under documented permission: naturalistic transfer and fidelity; (3) external public benchmarks such as PersonaChat/MSC: task-specific external comparators. They have different populations and must not be pooled into one accuracy estimate.

**Not central causal treatments.** CPU thread count, RAM, GGUF quantization, server configuration and implementation framework. Measure efficiency and constrain execution; change deployments only as distinct, explicitly controlled experiments. New training methods, adapters or novel decoding are *optional follow-on interventions*, not requirements for this paper.

**No anticipated result is assumed.** A well-estimated zero effect, an effect that disappears after semantic matching, a style-history interaction that fails to replicate, or a finding limited to Base models is informative if measurement quality and uncertainty are reported.

## 3. Research questions and falsifiable novelty-oriented hypotheses

### 3.1 Frozen RQs (v1.1)

- **RQ1 — Reliability:** How does persona conditioning affect relevance, factual consistency, temporal consistency and conversational coherence?
- **RQ2 — Conditioning factors:** What are the independently manipulated and combined effects of linguistic style, supplementary personal facts and historical dialogue?
- **RQ3 — Model/context sensitivity:** How do effects differ by parameter scale, post-training stage and actual context budget?
- **RQ4 — Observable failure localization:** Where do errors appear in retrieval, generation, selection or post-processing, and what headroom is suggested by controlled oracle interventions? No purely log-based causal blame assignment.

### 3.2 Prioritized *prospective exploratory* hypotheses

| ID | Question / hypothesis (no assumed direction) | Comparison and observables | Evidence supporting a nontrivial pattern | Falsifier or narrowing result | Existing-work threat |
|---|---|---|---|---|---|
| **H1: S×H interaction** | Does a style prompt change the effect of adding history? | At fixed F=0: [Y(C5)-Y(C3)]-[Y(C1)-Y(C0)], separately for each outcome and structural-status prevalence; repeat for F=1 as exploratory | Consistent, suitably precise interaction in independent personas/templates; mechanism probes rule out simple length/format accounts | Near-zero interactions with sufficiently informative uncertainty, or collapse after realization/control checks | Factorial prompts and persona effects are established; interaction *finding* and validity are the potential contribution |
| **H2: history mechanism** | Do historical relevance, temporal validity and presentation have distinguishable associations under fixed correct evidence? | Separately controlled R/T/P diagnostics, not inference solely from C3−N_history | Replicated contrasts with matched facts/topic/format where needed, plus cross-conditions specificity | Apparent effect disappears under fact-/topic-matched controls | Personal-memory errors and temporal memory have prior literature |
| **H3: failure-mode divergence** | Are changes in response boundaries/format distinguishable from semantic/factual changes? | Structural status distributions **and** four reliability outcomes with explicit coverage/unverifiability | Some interventions disproportionately shift specific failure categories; same result across held-out cases | Only missingness/format artifacts, or indistinguishable changes after coverage analysis | Context pollution already linked to format failures |
| **H4: realization sensitivity** | How dependent are estimated effects on different natural prompt expressions of the *same intended factor*? | Multiple pre-validated lexical realizations, counterbalanced independently of question/persona | Large, reproducible between-template heterogeneity or robust invariance with confidence bounds | Differences explained by unbalanced task difficulty or unvalidated semantic changes | Cue wording/format robustness has direct published precedents |
| **H5: generalization boundary** | Which results persist across model status, task type, and eventually authorized real speakers? | Reproduced matched contrasts across held-out scenarios, model families/post-training arms, naturalistic tier | Stable scoped pattern or a well-characterized failure boundary | Only one toy template / single model effect | Small-model work, persona simulation and long-dialogue evaluation already exist |

A pilot can *reject the feasibility of testing* a hypothesis without rejecting the hypothesis itself. Hypothesis selection for confirmatory claims follows the pilot and the later confirmatory freeze; it must not be retrofitted to whichever exploratory result happens to look largest.

## 4. Design and estimands

### 4.1 Track A: shared correct evidence, 2×2×2 intervention

For a case i, define fixed evidence Eᵢ, time reference tᵢ, question Qᵢ, target speaker identity Iᵢ, and fixed preceding conversational context Kᵢ. All conditions for i must receive the **same Eᵢ, tᵢ, Qᵢ and Kᵢ**; additions S, F and H are separate, versioned blocks with stable insertion policies.

| Cell | S | F | H | Operationalized input |
|---|---:|---:|---:|---|
| C0 | 0 | 0 | 0 | evidence/question only, with shared fixed context |
| C1 | 1 | 0 | 0 | plus style profile |
| C2 | 0 | 1 | 0 | plus supplementary, answer-independent facts |
| C3 | 0 | 0 | 1 | plus date-stamped historical dialogue |
| C4 | 1 | 1 | 0 | plus style and facts |
| C5 | 1 | 0 | 1 | plus style and history |
| C6 | 0 | 1 | 1 | plus facts and history |
| C7 | 1 | 1 | 1 | all three additional blocks |

**F** contains personal facts not needed to answer Qᵢ; it must not conditionally supply the ground-truth answer. **H** is controlled dialogue with source, speaker roles, dates and potential factual content. In natural language, H will sometimes also carry style or facts: experimental orthogonality is operational, not semantic independence. No condition may be dropped because the baseline answered correctly/incorrectly.

### 4.2 Distinguish four families of comparisons

1. **Simple prompt-package contrasts** (v1.1 provisional primary): C1−C0 and C3−C0 with other factor switches off. These measure *total intervention packages*, including changed length and wording. They are **not** pure style or pure temporal mechanisms.
2. **Matched replacement controls:** C1−N_style and C3−N_history. Use **exact full-prompt token matching (tolerance = 0)** with the loaded model tokenizer, shared evidence, identical question, proper wrapper and insertion position. The P0-accepted N_style represents an *explicit absence-of-style statement*, not equivalence to C0. The P0-accepted History A compares *dated residence history* with an unrelated coherent dated dialogue, not a pure stale-fact or pure format effect. Future P1 stimuli require their **own** matching and semantic review.
3. **Factorial contrasts:** report equal-weight main effects and two-way/three-way interactions as exploratory. For fixed F=0, the proposed S×H contrast is `Y(C5) − Y(C3) − Y(C1) + Y(C0)`. This is an *interaction of the operationalized packages* and cannot on its own identify an internal neural mechanism. Full factorial average S effect is `1/4 Σ(f,h)[Y(S=1,f,h)-Y(S=0,f,h)]`; analogous for F and H. Averaging/reporting rules depend on complete paired coverage and endpoint definition.
4. **Targeted R/T/P diagnostic contrasts:** content-equated prose versus dialogue (P), same-topic versus unrelated material with balanced assertions (R), and dated consistent versus outdated/conflicting historical information with fixed current trusted evidence (T). Each family needs its own manipulation checks, neutral replacements and *specified estimand*. These are proposals for a later P1 diagnostic or subsequent focused study, not retroactive modifications of C3, N_history, or Track B.

**Critical boundary:** Track A's historic information always accompanies *correct current evidence*. **Track B** is the separate experiment that intentionally alters the *availability or correctness of necessary evidence*. Track A and Track B cannot be combined into one undifferentiated effect estimate.

### 4.3 Allocation, position, and nuisance factors

Within each case, freeze evidence bytes and validity intervals, question bytes, context, model settings, initial prompt-template family and response policy. Record evidence start/end token positions, overall token lengths, headers, neighboring segments and IDs. Exact length does **not** hold lexical tokens, semantics, attention or recency constant. For P1, balance persona style axes, history topic types, fact properties, speaker identity/name, scenario family and realization wording; avoid associating any style with a single question template, city or demographic label.

Randomize the order of case-condition executions using a saved seed, with consistent stateless service/cache policy. Primary fixed-context multi-turn inputs are written before inference. Generated free-running dialogue is a separate exploratory protocol. Repeated deterministic runs do not create independent sampling units.

## 5. Data, stimulus quality, and controlled pilot scale

**Synthetic development tier.** The prospective design is **12 distinct fictional speakers × 4 scenario families = 48 paired cases**: current-state update; stable supported personal fact; nonfactual conversational request; time-sensitive follow-up with fixed context. The allocation is a *pilot planning target*, not a power calculation or a confirmatory dataset. Each speaker must have a stable identifier, multiple verified English style traits/realizations, non-answer F data and chronologically consistent H, along with dated trusted evidence.

For every case maintain: persona_id, case_id, scenario_family, evaluation reference, speaker name and role, fact IDs/validity intervals, trusted evidence, question, fixed preceding dialogue, intended S/F/H interventions, optional control IDs, expected factual answer if applicable, evaluation-applicability matrix, prompt/dataset/template hashes, leakage/manipulation checklist, and provenance. For nonfactual tasks, do not fabricate a factual answer or declare factual consistency applicable by default.

**Partitioning.** Split at the speaker and question-template family level before generation into *development*, *independent confirmation*, and *future locked confirmatory* inventories. The locked confirmatory set is generated/frozen only after this pilot and a separate researcher decision. P0's historical city tests and control search examples are not fresh external validation material. Do not revise a held-out item in response to its model output while continuing to call it held-out.

**Pilot Wave 1, explicitly authorized:** after preflight and stimulus-manipulation validation, take **12 cases: one per fictional speaker, 3 per scenario family**, and run 8 cells per case = **96 real local CPU generations**. This is the first exploratory factorial wave; no matched controls are run until P1-specific controls have independently passed the required semantic checks. Do not assume the earlier accepted six P0 items validate new questions. Do not start the remaining 36 cases or a second model arm without reviewing Wave 1.

**Planning scale for later Wave 2:** if approved and corrected, 48 cases × (8 factorial cells + 2 neutral controls) = up to **480 generations per model**, excluding repeats and supplementary R/T/P diagnostics. Not all 480 are automatically authorized or necessarily scientifically informative. Record realized inference cost rather than relying on token arithmetic.

## 6. Measurement, response validity, and statistical analysis

### 6.1 Separate endpoints; predeclare applicability

For each case and each axis, lock applicability *before generation*:

- **Response Relevance:** adequate response to the latest request.
- **Factual Consistency:** support/contradiction of claims under trusted evidence valid at tᵢ.
- **Temporal Consistency:** correct distinction among formerly true, currently true, superseded and conflicting dates/claims.
- **Conversational Coherence:** alignment with fixed preceding turns and discourse obligations.
- **Persona Fidelity — Linguistic:** resemblance to a target speaker's lexical, punctuation, rhythm and register preferences.
- **Persona Fidelity — Behavioral:** resemblance to speaker choices across distinct conversational situations.

Each construct is a separate variable. Do not merge the four reliability axes into an arbitrary composite or absorb Fidelity into Reliability. Fidelity in invented speaker fixtures measures conformity to *specified synthetic targets*, not actual fidelity to a human. Real-person fidelity claims require separately authorized data and independent blinded evaluation.

### 6.2 Structural versus semantic outcomes

Retain frozen `response_status_v1`: `COMPLETE`, `TRUNCATED`, `CROSS_TURN`, `AMBIGUOUS`. Store server stop/EOS separately; status is not a proxy for factual correctness. Record raw bytes, native output tokens where supported, first-reply extractable span, excluded continuation, postprocessing, output cap, and failure cause. Report structural outcomes for **all pre-eligible requests**, not only easy-to-score completions.

Retain frozen `separate_axes_policy_v1`: `Correct`, `Incorrect`, `Unverifiable`, `Not Applicable` for bounded factual scoring; annotate other endpoints independently. A truncated answer may be factually supported, contradicted or indeterminate, depending on what is actually observable. `Unverifiable` and `AMBIGUOUS` must not silently be coded as a success/failure or discarded. For each endpoint report denominator, applicability, assessable coverage, uncertain cases, raw missingness, and conditional descriptive figures. A secondary complete-only analysis is subject to selection bias and must be labeled as such.

**Open-ended outputs:** the P0 city-specific scorer is not a general factuality or coherence judge. Prepare blind outcome-rating materials with versioned rubrics and genuine independent ratings where required. Report actual reviewer count and agreement only when computed from real independent ratings. Retain disputed judgments and abstention decisions. Any automated grading extensions require held-out validation of negation, contradictory extra claims, speaker mix-ups, temporal updates and inability to answer.

### 6.3 Estimation and uncertainty

All conditions of a case are paired. Estimate within-case differences; account for questions clustered within speaker and templates in later analyses. **Twelve speakers are not enough to claim population-level generality.** Pilot summaries emphasize per-condition category counts, paired transitions, heterogeneity, false/negative results, wide uncertainty, and assessment coverage. Exploratory confidence intervals may be reported with method and instability caveats; do not select only C0-correct cases for the main comparison. No confirmatory significance claim or post-hoc selection of the largest interaction is permitted.

Before the *confirmatory* study, the researcher must lock primary endpoints, contrast hierarchy, sample size/precision rationale, multiplicity procedure (e.g., Holm), randomization, model set, exclusions, missing/uncertain handling, reviewer independence and adjudication, and final test inventory. Structural-failure rates should be reported as their own outcomes; do not silently redefine the reliability score to make the result appear stronger.

## 7. Model and execution rules

**Wave 1 baseline:** pinned local Qwen3.5-2B-Base Q4_K_M GGUF and pinned llama.cpp CPU executable verified in P0; nominal baseline 4 CPU threads, context **capacity** 4096 (not a claim that each prompt uses 4096 tokens), 96-token output budget unless a **separately frozen pre-generation** setting is approved, and the previously documented decoding/stop policy. Capture actual config and check model-specific template correctness. Preserve third-party GGUF lineage caveat; pinned bytes do not establish official-weight quantization equivalence.

No silent switch of Base to Instruct, template, budget, family, prompt wording or model size during a paired experiment. If structural feasibility is poor, first report the actual coverage pattern and then propose a **separate versioned arm** for a post-trained model or output-boundary strategy. A second arm is not used to replace inconvenient Base results. A seed is not a cross-platform determinism guarantee.

Before each inferential wave, freeze: dataset/case roster, full prompt versions, run order, applicability, selection rules, model/back-end artifact SHA-256, decoding and hardware parameters, boundary/scoring policies and their hashes. Keep original outputs/errors, journal chain, Git SHA + dirty state, local raw snapshot and publicly shareable derived evidence. Do not reconstruct unavailable historical telemetry by guesswork.

## 8. Staged work plan: priority, experiment, expected evidence, and gate

The following are **expected deliverables / observation types, not predicted positive effects**.

| Stage | Research priority & experiment | Expected output regardless of result | Gate to next stage |
|---|---|---|---|
| **P0 — Accepted** | Validate input schema, prompt routing, real CPU inference, tokenizer matching, response boundaries, separated scoring, human control checks, logs and provenance | Auditable infrastructure and explicitly qualified controls; **no scientific effect finding** | Completed: 15/15 scoped mandatory checks; 365 tests reported at acceptance. Do not revise P0 findings retroactively |
| **P1a — Initial factorial feasibility wave** | Diverse fictional speakers, four scenario families, C0–C7 across 12 paired cases; prioritize S×H interaction, distinct failure types and manipulation integrity | Actual raw 96 generations *if preflight passes*; response-status/coverage tables, four reliability axes where evaluable, case-level comparisons, failure examples, falsified and feasible hypotheses | Researcher reviews whether structural coverage and manipulation quality permit informative larger experiments. No automatic expansion |
| **P1b — Controlled factorial development pilot** | Expand only after Wave 1; counterbalanced style realizations, F information independence, history placement; new N_style/N_history independently checked; test all eight cells and controls | Paired contrasts; exploratory main/interaction-effect estimates with uncertainty; control-family sensitivity and task heterogeneity; validated annotation set | Decide which estimands, tasks, models and control designs are fit for confirmatory freezing. Results remain exploratory |
| **P1c — Optional focused history/realization diagnostics** | Controlled R (relevance), T (temporal status) and P (presentation) plus explicit-absence vs other vetted style realization controls; freeze **new** treatment IDs | Separate results identifying which alternative explanations survive; may show no separable mechanism or contradictory findings | Only pursue if a pilot signal is robust enough and new manipulations are valid; no rebranding of C3 as causal temporal effect |
| **P2 — Knowledge utilization / Track B** | Independently manipulate missing, correct, stale, contradictory, and oracle *necessary evidence*, with retrieval baselines where practical | Evidence Recall@K and coverage, valid evidence use, abstention/errors, contrasts under availability changes, oracle diagnostic bounds | Do not combine with Track A totals; identify whether a knowledge-use failure warrants further work |
| **P3 — Model/post-training/context sensitivity** | Repeat selected validated contrasts on other ~0.8B–3B sizes/families, Base vs Instruct with model-appropriate templates, predefined actual input budgets; CPU secondary cost | Heterogeneity and boundary conditions, plus latency, generated tokens/s, RAM; separate template and model confounds | Decide scope of generalization; no claim of general model-size law from one family or artifact |
| **P4 — Authorized real-speaker validation** | Reconstruct English speaker profiles/history from consenting participants, chronological splits, disjoint evaluation, independent linguistic and behavioral fidelity plus reliability | Transfer/replication or failure of controlled patterns, privacy-preserving examples, reviewer agreement when available; limits of real-world relevance | No inference about all speakers; maintain lawful permission and avoid future-information leakage |
| **P5 — Pipeline/Oracle diagnostics** | Retain retrieval, candidate generation, selection and parser traces; Oracle Retrieval/Selection with shared candidate pools, equalized candidate/CPU budgets | Failure-location *observations*, candidate coverage, selection regret and potential headroom; structural vs semantic bottleneck audit | Decide if a limited intervention is justified; no unsupported causal decomposition from logs |
| **P6 — Optional remedy** | Only if P1–P5 identify a reproducible bottleneck: e.g., evidence-gated selection, constrained response rendering, or separately justified adaptation | Same-budget comparison with strong baselines, fidelity/reliability tradeoffs, CPU overhead, null results and ablations | A method is never required for a valid empirical paper; no premature training |

**Phase semantics:** P1 is a *pilot* and can refine new development stimuli using properly separated development data. The **confirmatory freeze** is a distinct decision following sufficient pilot evidence; it is not automatically P1b, nor any retrospective relabeling of P1a data. P4 may run only when permission and sampling conditions are met, even if earlier phases are complete. Negative results and infeasible measures lead to redesigned *future* tests, not edited historical claims.

## 9. Deliverables for the first authorized P1 wave

**Before generating any answers:**

1. `docs/P1_experiment_plan.md` — hypotheses/estimands/alternatives, 12-case roster, run settings, stopping and exclusion policy, planned analyses and checks.
2. `data/synthetic/p1_development/...` — 48 case candidates (or a clearly marked partial preparation), with 12 Wave 1 cases selected and source-sealed before outcome inspection.
3. `docs/P1_manipulation_validation.md` — per-condition evidence/question byte equality, speaker IDs, style/fact/history checks, leak/counterbalance checks, tokenizer and context verification.
4. Versioned run manifest — model/backend/tokenizer hashes, frozen case IDs, templates, seed/order, per-axis applicability and policy versions.
5. P1-specific neutral controls plus an **unfilled**, human-readable review form; do not treat their generation as acceptance or run them ahead of approval.

**If preflight passes:** execute precisely the 96-cell bounded Wave 1 with real CPU, preserving raw results and failures. Produce `docs/P1_pilot_wave1_report.md`: counts by condition and scenario, structural coverage, individually measured reliability axes, possible fidelity descriptors where valid, case-paired distributions, exploratory interactions, uncertainty, reproducibility and discarded hypotheses. If preflight fails, report **0 executed** and the precise validation failure instead of inventing runs.

**After Wave 1:** prepare a **researcher decision memo**, *not an automatic Wave 2 launch*: whether to expand, improve new stimuli, allocate a separate post-trained model arm, or investigate response boundaries. Connect each proposed next test to a clear novelty-relevant question and observed feasibility limit.

## 10. Novelty review and literature decision rules

The field already studies: factual distortion under personalization; sensitivity to irrelevant persona properties; effects of persona cue wording; long-dialogue fidelity and memory recall; real-person simulation; persona/context pollution and structural output failure. The project **will not** claim any of these broad phenomena, the 2×2×2 framework itself, or exact-token matching as original without stronger verified grounds.

The novelty audit is updated **before each expensive expansion and before the confirmatory freeze**. For each nearest study, log versioned primary PDF/DOI, overlapping RQ, models/task populations, manipulations and matched controls, evaluation denominators, factual/structural distinction, result, and what is still an actual open question. A new preprint is a threat to a broad claim but does not automatically invalidate a narrower well-controlled empirical contribution. Verify methods, not only paper titles or abstracts.

**Novelty gates:**

- **N0 — Already covered:** a general replication of persona interference or factuality drop: report as replication, not a new mechanism.
- **N1 — Conditional finding:** a validated, nontrivial interaction or failure boundary under shared evidence with uncertainty, independent speakers/tasks, and honest alternative explanations.
- **N2 — Explanatory discrimination:** a result surviving targeted R/T/P or matched-control alternatives, including informative null/equivalence outcomes.
- **N3 — External validity/method:** transfer (or documented failure to transfer) to authorized real-speaker data, or a validated distinct remedy/assessment procedure relative to prior baselines.

A manuscript's Contribution statements are chosen **after** observing replicated evidence, not predetermined at N2 or N3. Lack of support for a favored hypothesis is not an instruction to keep changing inputs until it appears.

**High-overlap primary reference checkpoints (verify paper revisions):**

- Luz de Araujo et al., *Principled Personas* (EMNLP 2025), https://aclanthology.org/2025.emnlp-main.1364/
- Sun et al., *When Personalization Misleads* (Findings of ACL 2026), https://aclanthology.org/2026.findings-acl.395/
- Weeber et al., *One Persona, Many Cues, Different Results* (ACL 2026), https://aclanthology.org/2026.acl-long.2079/
- Nakatsu & Wang, *Decoupling Logic from Persona* (arXiv:2610.09772v2), https://arxiv.org/abs/2610.09772
- Du et al., *TwinVoice* (Findings of ACL 2026), https://aclanthology.org/2026.findings-acl.981/
- Luz de Araujo et al., *Persistent Personas?* (EACL 2026), https://aclanthology.org/2026.eacl-long.246/
- *REALTALK* (2025), https://arxiv.org/abs/2502.13270

These papers limit claims of originality; this document does not assert the above research gaps are uniquely unstudied.

## 11. Reproducibility, ethics and governance

Use exact input hashes, native tokenizer IDs/counts and special-token rules, model GGUF/backend hashes, prompt/source/data IDs, runtime config, Git SHA + dirty state, output tokens/raw spans, errors/stop reasons and versions of scoring/annotation. Store times in machine-readable raw run records, but **organize the consolidated human-readable technical report by methods and stages, not calendar timelines**. Do not fabricate missing timestamps, identities, independent annotators or model behavior.

For real-speaker data, document consent/permission, speaker and third-party message scope, privacy risk, pseudonymization, retention, encryption/access controls, chronological evaluation split and whether/how example passages may be shared. Synthetic/control text can be released when valid, while private raw conversations are never assumed to be public research assets. Maintain an explicit publishable artifact inventory and limitations for restricted replication.

The researcher alone approves phase launches, protocol revisions, confirmatory freezing, and Git submissions. Scientific documents identify Yaxin ZHENG as researcher/maintainer, while preserving truthful provenance of code, commands, annotations, and prior suggestions. No historical Git rewrite, falsified authorship or automatic commits/pushes.

## 12. Decision ledger and project navigation rule

| Decision | Current state | Who decides next |
|---|---|---|
| P0 infrastructure and scoped control acceptance | **PASS; completed and committed** | Keep immutable; reproducibility defects are separately recorded |
| P1 Wave 1 bounded real inference | **Authorized; execution status must be read from actual run manifest** | Researcher reviews results and next-wave scope |
| P1-specific N_style/N_history controls | **Not yet accepted for new cases** | Genuine new human semantic check before use |
| History R/T/P focused diagnostics | **Proposed, not yet launched** | Researcher approves only after feasibility/evidence review |
| Confirmatory experiment freeze | **Not performed** | Researcher locks hypotheses, contrasts, models, data, sample size, analysis and independent scoring |
| Track B P2 and later stages | **Not started** | Separate phase authorization |
| Protocol v1.2 | **Proposed; v1.1 remains authoritative until adoption** | Researcher records explicit adoption/amendment decision |

**Before any future intervention, ask:** (i) Which RQ and falsifiable hypothesis? (ii) Which exactly measured estimand and held-constant evidence? (iii) Which earlier paper already does the closest experiment? (iv) What distinct output will refute/support the claim? (v) Which measurement/provenance and privacy conditions apply? (vi) Does this require a prospective amendment rather than overwriting prior data? If these cannot be answered, do not launch the experiment.

**One-sentence abstract:** We use controlled S/F/H interventions under identical sufficient trusted evidence to characterize how small language models' dialogue reliability varies across personas and contexts, separating structural from semantic failures and evaluating candidate interactions and historical-content mechanisms with explicitly scoped controls, followed by model and authorized real-speaker validation.
