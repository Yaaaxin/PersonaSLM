> **Implementation status:** The researcher subsequently authorized P1. The [frozen wave-1 plan](P1_experiment_plan.md) and [completed first-wave report](P1_pilot_wave1_report.md) are the current executed scope. The proposal below remains unchanged as historical design material; it is not a claim that P1 is still unstarted.

---

# P1 Controlled Factorial Pilot — Proposal v0.1

2026-10-12. **PROPOSED ONLY. P1 NOT STARTED.** Researcher: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Protocol v1.1 remains frozen. This document requests no automatic amendment and creates no confirmatory test set. Implementation and execution require researcher approval after P0 acceptance.

## Purpose and limits

The pilot should establish whether the manipulations, response units and separate reliability/fidelity measurements work across diverse English synthetic speakers and situations. It should estimate variability and identify design problems, not certify a harmful or beneficial persona effect. The existing P0 uses one style and one speaker ID with repeated city pairs; its scope is engineering validation, not population-level real-speaker modeling.

Retain Track A's identical, correctly dated, sufficient trusted evidence and current question across every within-case condition. Track B separately manipulates missing/correct/stale/conflicting/oracle knowledge and belongs to its own later study. Do not pool the tracks, remove current evidence from Track A, or call an unavailable-evidence failure persona interference. Authorized real-speaker data and chronologically separated evaluation remain future naturalistic validation; no private conversations are introduced here.

## Frozen factors and intended contrasts

| Condition | S: linguistic style | F: additional personal facts | H: dated historical dialogue |
|---|---:|---:|---:|
| C0 | 0 | 0 | 0 |
| C1 | 1 | 0 | 0 |
| C2 | 0 | 1 | 0 |
| C3 | 0 | 0 | 1 |
| C4 | 1 | 1 | 0 |
| C5 | 1 | 0 | 1 |
| C6 | 0 | 1 | 1 |
| C7 | 1 | 1 | 1 |

Retain preliminary primary simple contrasts **C1–C0** and **C3–C0**, plus matched comparisons **C1–N_style** and **C3–N_history**. They remain bundles/replacement effects with explicit residual confounds, not automatically pure style or format mechanisms. Estimate average factorial main effects and interactions separately using equal cell weights and the protocol's formulas. Eight factorial conditions plus two matched controls are ten conditions, not ten factorial cells.

The [control diagnostic](P0_neutral_control_diagnostic.md) identifies the current control limitations. A new control version must be reviewed and exactly token-matched before use. Current development candidates are not accepted interventions. Proposal-only fact-equated prose/dialogue and attribution diagnostics could clarify presentation effects; they would be separately approved supplementary comparisons, not an unannounced redefinition of H.

## Synthetic persona diversity without uncontrolled bundles

Start with an illustrative **12 invented speakers × four situations = 48 paired cases**, subject to feasibility review. This is a planning allocation, not a final sample-size commitment, power claim or generated dataset. Speakers should have explicit, consistent names in evidence, questions and history. Names, cities, profile traits and task templates must be independently counterbalanced; do not map a style to one demographic identity, city or error-prone question.

| Dimension | Proposed development manipulation | Held constant / unavoidable overlap |
|---|---|---|
| Brevity | Short versus expanded phrasing, while requesting the same answer content | Formality and lexical preferences fixed in the initial manipulation check; output length is a measured mediator, not an eligibility filter |
| Formality | Conversational versus formal lexical/syntactic register | Target semantic content held fixed; some sentence length/punctuation changes cannot be fully separated |
| Lexical preferences | Small, predeclared English synonym preferences with equal intended meaning | Avoid required-answer words, dates, city names and repetitive catchphrases; token lengths must be observed |
| Rhythm | One versus several naturally separated clauses/short sentences | Preserve propositional content; rhythm overlaps brevity, so validate one axis at a time before combinations |
| Pragmatic tendencies | Direct answer versus acknowledgment followed by answer | No withholding, guessing or uncertainty preference bundled with factual truth; changes in relevance/completeness must be measured |
| Historical relevance | Same-topic versus unrelated, with matched number/type of assertions | Topic relevance cannot be removed by simply matching role format; use a declared blocking variable or a separate diagnostic |
| Temporal relation | Consistent stable history versus explicitly dated updates / competing past values | Current evidence unchanged and sufficient; factual and temporal errors may overlap; do not label true past facts false |

Begin with independent manipulation checks for each style axis on newly authored development material. A balanced incomplete assignment can spread axes across 12 speakers without claiming a full cross of every dimension. Combine only those dimensions shown to retain intended content. Record overlaps explicitly. Do not silently treat all styles as “short casual haha” or equate lexical imitation with behavioral fidelity.

The four planned situation families are: a current-state update; a stable supported personal fact; a nonfactual conversational request with a fixed previous turn; and a time-sensitive follow-up in fixed multi-turn context. Applicability must be specified before generation, separately for relevance, factual consistency, temporal consistency, coherence, linguistic fidelity and behavioral fidelity. These are families, not authored final items. The narrow city evaluator applies only where its grammar and truth reference are supported; new task families require human procedures or separately developed and validated evaluators.

## Input controls and allocation

Use the same evidence bytes, question bytes, fixed recent conversation, evidence location and response request within each case. Record fact IDs, validity intervals, topic, attribution and source-language provenance. Keep persona text separate from trusted evidence. Use C0 as the unconditioned anchor; declare that other conditions add tokens and move the question relative to evidence.

For matched pairs, count the complete final prompt with the actual loaded model tokenizer, special-token policy and template; tolerance remains **0**. Seal the candidate pool and search order before tokenization. Include all candidates and failures. Choose by predeclared matching and semantic criteria, never by downstream answer quality. Match section placement, role/date structure, adjacency type and information type where feasible; otherwise state exactly what changes. Do not pad with repetitive formatting instructions to achieve length parity. Failed matches remain failed engineering items and cannot be dropped retrospectively from a scientific denominator.

Freeze development/confirmation partitions by speaker and scenario template before outputs. The independent confirmation partition must not be the three control-development cases or the four earlier termination-development examples. No confirmatory inventory is generated here. Randomize condition execution order with a recorded allocation seed, reset prompt caching/state consistently and block any resource/time drift. Keep CPU deployment fixed, rather than treating hardware as a causal factor.

## Measurement and analysis rules

Retain `response_status_v1` and `separate_axes_policy_v1` unless a separately approved, developed and held-out version supersedes them. Preserve raw generation and excluded continuations, backend termination, first-span extraction and semantic-completeness uncertainty. A cap is not a factual error and a stop string is not proof of completion. Route ambiguous response units for the declared annotation procedure and report their frequency; do not select only naturally terminated outputs.

Report **Correct / Incorrect / Unverifiable / Not Applicable** separately. Use all pre-eligible paired cases as the primary denominator and report coverage/uncertainty alongside conditional statistics. No automatic conversion of Unverifiable to a success or failure. Keep factual support, temporal consistency, relevance, coherence and completeness separate. Persona Fidelity must remain an independent linguistic/behavioral construct, without a default composite reliability score.

For open-ended outcomes, use the protocol's blinded independent annotation and adjudication plan, disclose any exposure to preliminary judgments, and compute agreement only from genuinely independently supplied ratings. The current single-researcher control review cannot serve as an inter-annotator agreement estimate or model-output ground truth.

Pilot analyses should emphasize paired distributions, errors, null/mixed findings and uncertainty. Questions within a speaker are clustered; 48 cases are not 48 people. With only 12 proposed speakers, hierarchical/cluster-bootstrap estimates are exploratory and may be unstable. Use pilot variability for a later explicit power/sample-size decision. The confirmatory freeze must settle primary endpoints, contrast family, multiplicity policy such as Holm, exclusions, weighting and annotation thresholds before locked testing. Neither this proposal nor P0 is a preregistered confirmatory result.

## Resources, gates and artifacts

The illustrative single-model allocation costs **48 × 10 = 480 generations**. At a predeclared 96-token cap this is an upper bound of **46,080 generated tokens**, excluding prompt evaluation, startup and any separately authorized diagnostics. This is arithmetic, not measured runtime. Repeated seeds at deterministic decoding must not be presented as independent stochastic samples. Any stochastic repeat design needs explicit parameters, rationale and a multiplied budget before execution.

Start, if approved, with the pinned 2B Q4_K_M artifact/build and fixed CPU 4/4 threads, context 4096; comparisons across 0.8B–3B, post-training, quantization or context remain separately controlled studies. No LoRA is proposed as a P0 remedy.

Before execution: close or explicitly resolve the methodological control blocker without rewriting Protocol v1.1; obtain researcher approval; freeze pilot inputs/applicability/control validity/evaluation versions; verify tokenizer and context; create a new run manifest with Git SHA/dirty state, exact source/dataset/model/backend hashes, timestamps and all errors. Preserve every raw result. Stop for instrumentation/evidence failures, not for inconvenient outcomes. No experiment in this document has been run.
