# P1b Discriminative Task Design — Proposed v1

Maintainer: Yaxin ZHENG. Target: PLOS ONE. Official title: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Formal baseline: Protocol v1.1. The v1.2 Revised Proposed r1 document remains unchanged and unadopted.

## Decision requested

Approve human validation of a **24-case development bank**, followed only under separate inference authorization by one bounded **24 cases × eight S/F/H cells = 192-request Base calibration**. Do not authorize a large expansion yet. Use the pinned model to test whether better evidence-grounded measurement is possible without simultaneously changing the model. An Instruct arm is conditional, separately versioned and not launched. This proposal authorizes no model execution.

The immediate information target is **task and measurement discrimination**, not a favorable persona effect. Offline checks demonstrate explicit evidence dependence and distinct reasoning operations. They **cannot demonstrate empirical model difficulty or a reduced ceiling without new observations**. No large inference recommendation is warranted until that missing evidence exists.

## What Wave 1 does and does not establish

The [fresh source inspection](validation/p1b/historical_inspection_v1.json) reads all 48 original development cases, 96 confirmed annotations and 972 case/metric/contrast records. The executed wave has nine factual case units and six temporal units, not 72/48 independent speakers. Their 72/72 and 48/48 labels are Correct. All nonzero relevance/coherence contrasts occur in the nonfactual C family. The existing empirical bootstrap cannot generate unobserved factual errors.

| Property inspected | Actual Wave 1 material | Plausible measurement limit; not an established mechanism |
|---|---|---|
| Question complexity | Current city, membership name, or current delivery city; greeting is factual N/A | Mostly one fact lookup; little evidence integration |
| Evidence sufficiency | Two explicit current statements, including the answer, repeated across cells | Necessary Track A protection; remove neither correct evidence nor answerability to make errors |
| Evidence presentation | Short prose, direct current-state wording, repeated predicate templates | Easy alignment is plausible; no presentation intervention was randomized |
| Temporal reasoning | A/D ask about now following a move; dated old residence in H | Selecting an explicitly current fact differs from boundary dates, interval comparison or dated joins |
| Competing facts | One old residence; one current residence; membership and unrelated possession | Limited same-attribute competition; genuine old truth is not a simultaneous contradiction |
| Entity ambiguity | Named target consistently supplied | Almost no need to resolve equal first names, roles or references |
| History relevance | Residence history matches A/D topic; less relevant to B/C | Relevance varies with family; a history main effect does not isolate it |
| Persona strength | Twelve style descriptions, six categories with nested realizations; unrelated possession in F | No independent fidelity manipulation check proves realization in outputs; do not strengthen cues until a harmful effect appears |
| Response unit | 72 factual answers are CROSS_TURN and human-confirmed correct; 17 incomplete greetings are factual N/A | Structural continuation is not factual error. First-reply and full-continuation outcomes differ |
| Statistical information | Twelve purposive speakers, three per family; nine/six eligible case units | Low precision and low task discrimination are distinct problems. More copies of ceiling tasks address neither generality nor sensitivity adequately |

## Development bank and complexity

The [versioned dataset](../data/synthetic/p1b_development_proposed_v1.json) contains 24 English fictional prototypes: eight task families × three **designed complexity levels**, twelve new speaker IDs, two cases per speaker. All 24 are factual-eligible; eleven are temporal-eligible. Other cases remain temporal N/A. Relevance/coherence apply to all; Persona Fidelity remains unmeasured. These are proposed eligibility assignments for new cases, not changes to historical eligibility.

| Family | Level 1 | Level 2 | Level 3 | Information gained beyond repeating Wave 1 |
|---|---|---|---|---|
| A: retrieval anchor | One archive-box location | Same lookup among two boxes | Same lookup among three boxes | Search-load anchor; still one-hop, not a claim of deep reasoning |
| B: related personal facts | Workshop plus role | Also join workshop to place | Also join place to entrance | Multiple answer components and connected evidence |
| C: validity intervals | Date inside an interval | Exact transition date | Transition date and preceding day | Inclusive boundary discrimination; two formerly valid values remain explicit |
| D: multi-step reasoning | Person → crate → locker | Add room | Add building | Two-, three-, four-fact chains; the final answer is not adjacent to the queried person |
| E: relevant history | Current residence with true old residence | Current residence → collection hub | Current residence → hub → opening day | Dated relevant history competes with the current lookup path; no knowingly false historical assertion |
| F: disambiguation | Full name and unique ID | Role identifies one of two Morgans | Role → folder → shelf | Explicit solvable attribution, not ambiguous ground truth |
| G: current/past distinction | Current pickup site | Site at a past date | Past and current sites separately | A historical answer can be correct when the question asks for that time |
| H: fixed-context follow-up | Resolve “it” to a named parcel | Recipient join and dated desk | Two parcels, explicit focus and transition date | Prior context has a necessary reference-binding role |

Levels are **family-specific complexity bundles**, not a calibrated equal-interval difficulty scale. A3 still uses one support fact; H3 adds reference competition without a longer fact chain than H2. Facts, entities, response components and length vary between cases; none is a pure difficulty manipulation. Each family/level cell currently has one prototype, so difficulty, identity and wording cannot be disentangled statistically in this bank.

Every item has a structured source ledger, inclusive validity intervals, fixed reference, English question/context, symbolic answer path, answer components, hashes and proposed applicability. No external knowledge, private chats or real-person biography is required. Names and evaluation dates are synthetic. The source-reference date is not an execution timestamp.

## S/F/H identification remains intact

C0=000, C1=100, C2=010, C3=001, C4=110, C5=101, C6=011, C7=111, ordered S/F/H. Across all eight cells of a case, the evidence bytes and prefix position, question, reference date, recent conversation, answer key and eligibility are identical. Model/decoding must be constant within each future arm. The active additions remain separate blocks in S, F, H order.

S describes one main linguistic tendency per speaker, spanning brevity, formality, lexical choice, rhythm and pragmatic opening. No style is an instruction to change truth. Realizations are still nested in speaker; category-specific causality is not identifiable here. F is a stable, answer-independent bookmark possession. This intentionally weak/simple F limits generalization about all personal facts; expanding its content needs a new prospective stimulus version. H is one genuine past residence statement, valid when uttered. It is topic-relevant in E and unrelated to the answer domains elsewhere; no unplanned false history is introduced.

| Contrast | Measured package | Controlled | Remaining confounds / prohibited claim |
|---|---|---|---|
| C1−C0 | Adding the specified style profile at F=H=0 | Evidence, question, context, model settings | Length, wording, recency; not pure linguistic style or proven fidelity |
| C3−C0 | Adding dated residence dialogue at S=F=0 | Same common inputs | Topic, factual content, date content, length and format; not isolated temporal interference |
| Average S/F/H; interactions | Paired on/off averages and differences-in-differences of the operational packages | Eight-cell pairing | Not neural mechanisms; task/speaker/template heterogeneity remains |
| C1−N_style, if separately validated | Style information versus explicit absence of style information | Exact full-prompt length, wrapper and common input | Absence wording is an intervention, not C0; new prompts need new tokenizer and semantic checks |
| C3−N_history, if separately validated | Residence history versus unrelated coherent dialogue | Exact full-prompt length and history format | Topic, factual content and temporal information remain different; no isolated temporal-conflict claim |

The 24 old P1 control approvals are still OPEN, and would not transfer to P1b. No control-adjusted estimate or new matched candidate is generated here.

## Selection, separation and prospective calibration gates

**Selection rule before any output:** include all 24 listed IDs, all eight cells, with the existing level/family allocation. No C0-correct filter, no removal of failures, no selection based on effect sign or size. Proposed execution-order seed 714001 must be recorded in an approved future run manifest; it has not been used to run a model. Human ambiguity/incorrect-key corrections happen before inference, are logged and versioned, and must preserve the planned strata. There is no inference authorization embedded in the builder.

1. Researcher reviews every English question against the ledger/oracle and intended style/history scope, using the blank [stimulus form](validation/p1b/stimulus_review_v1.csv). No human approval is claimed now.
2. After approval, pin full prompts, roster, source hashes, scoring guide and arm settings. Perform real GGUF tokenizer/context preflight before any completion. No character-based token estimate substitutes for this gate.
3. If inference is separately authorized, run the single 192-request calibration. Condition-masked first-reply assessment must preserve all structural categories and missing/uncertain labels. Proposed coverage gate: at least 95% of eligible replies assessable in **each condition and metric**, with exact small-sample counts shown. This is a proposed feasibility threshold, not a retrospective Wave 1 requirement; researcher approval is required.
4. Inspect ceiling/floor and coverage by family/level with treatment labels masked during the task-discrimination decision. Keep all outcomes. Do not delete items, choose a “best” persona difference, or repeatedly tune these prompts. A whole-family ceiling is a measurement finding; any later development revision uses new IDs and a recorded defect/complexity rationale. No fixed error quota is a target.
5. Larger inference remains gated on meaningful outcome variation **or a justified scoped ceiling-bound question**, adequate scoring coverage, a chosen precision target, and researcher approval. The 24 cases cannot establish population interactions. If the calibration remains at ceiling, merely repeating it at scale is not recommended.

The current 24 items are permanently development-only. Neither they nor Wave 1 may become an untouched confirmatory test. Future independent evaluation must use new speakers, names, fact values and separately authored question/context realizations; reserve template realizations as well as personas. Task operation families may remain common to test replication, with that dependence disclosed. Do not create the final confirmatory inventory now. Freeze confirmatory hypotheses, endpoints, clustering, multiplicity, applicability and sample allocation before its collection.

## Separate historical R/T/P proposal — not part of these eight cells

R/T are potential explanations, not demonstrated effects. For a later authorized diagnostic, propose a new case-specific history ledger with **R: same queried domain vs an unrelated domain**, and **T: formerly valid vs still valid at reference**. Keep correct task-sufficient evidence, question, speaker, number of assertions, dialogue roles/position and presentation fixed. Pair content realizations across cases. Ground every historical assertion at its utterance time; do not silently substitute fabricated contradictions for outdated truths.

R changes semantic topic by definition; lexical content cannot be fully equated. T changes dates/validity and often answer reinforcement: a currently valid target fact may repeat the correct answer whereas a stale one cannot. Such a contrast measures *stale competition versus current reinforcement*, not pure timestamp processing. If leakage-free current histories are needed, use a related non-answer attribute in **both** T levels and explicitly narrow the estimand. Do not pretend these two designs identify the same effect. Shared trusted ledgers must contain all needed current facts regardless of history injection; this remains Track A, not knowledge withholding in Track B.

Prioritize one R×T diagnostic only if an interpretable history pattern or a clearly justified replication question survives calibration. Do not automatically cross it with the full S/F/H grid. P (same propositions/dates/identity rendered as dialogue vs prose) would be an additional hypothesis with a fixed content ledger and actual token/position checks; only add it for a prediction not already answered by the admission/presentation literature. [What to Admit and How to Present](https://arxiv.org/html/2610.11188v1) directly motivates this caution. None of R/T/P is adopted by this document.

## Measurement rules and approval boundary

Retain `response_status_v1` and `separate_axes_policy_v1`. Preserve native stop reason, first span and excluded continuation. An incomplete supported assertion may be factually Correct; omission belongs to relevance/completeness, not automatic factual Incorrect. Unsupported or absent claims remain Unverifiable. Factual and temporal labels require separate evidence quotations, including attribution and date. Do not use the city grammar to score folders, joins or interval reasoning. The symbolic oracle is an answer-key check, **not an English response evaluator**.

Use the existing separate relevance/coherence scales, with new task-specific anchors approved before inference. Report requested-component delivery separately as a **prospective descriptive diagnostic** if approved; it is not a new composite reliability score and must not change primary categories. Report applicability, assessment coverage and uncertainty; do not silently drop structural failures. All model-scored rubric extensions need independent challenge examples for negation, partial support, additional contradictions, role confusion and abstention.

Required researcher decisions: approve the new development scope/ledger template and rating anchors; confirm all ground truths; choose precision and practical effect margins; authorize or decline the 192-request Base calibration; decide later whether a distinct Instruct or R/T arm is warranted. None requires altering v1.1 automatically. Any formal protocol amendment requires a separate recorded decision. See the [sample plan](P1b_sample_size_and_precision_plan.md), [model assessment](P1b_model_arm_comparison.md), and [novelty assessment](P1b_novelty_and_publication_assessment.md).
