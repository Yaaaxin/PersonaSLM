# P1c History Mechanism Design — Proposed v1

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Target: PLOS ONE. This is prospective development design, **not an authorized experiment**. Protocol v1.1 remains formal; v1.2 Revised Proposed r1 remains unadopted.

## Evidence motivating the questions

The [independent recheck](validation/p1c/proposed_v1/p1b_evidence_recheck_v1.json) reconstructs 480 case-level contrasts from the registered P1b annotations and verifies their agreement with the original analysis. It retains 24 cases, 12 speakers and 192 outputs. Under the original confirmed-span sensitivity interpretation, the average H contrast is −11.46 percentage points for factual Correct-label incidence, −18.18 for temporal Correct-label incidence and −18.75 for full task success. The corresponding inherited speaker-bootstrap intervals are [−20.83, −3.13], [−44.44, 0.00] and [−31.25, −9.38] points. These are exploratory intervals from a small development population, not new significance findings.

Correct-label incidence includes Unverifiable in a separate observed category. It is not Correct-versus-Incorrect accuracy. On the assessed-only, complete-cell sensitivity subset, H is −5.56 points for factual correctness (18/24 cases) and −12.50 for temporal correctness (8/11 eligible cases). All-eligible binary uncertainty bounds allowing unknown outcomes to vary are [−18.75, +3.13] and [−29.55, +2.27] points respectively. The selection mechanism can depend on condition. These bounds are not confidence intervals. The temporal S×H mean is zero; nonzero case contributions cancel. Four P1b temporal errors occurred at C0, so added history cannot be presumed necessary for the observed failures.

The labels retain their actual provenance: condition-masked AI-assisted proposals followed by Yaxin ZHENG's explicit confirmation. This is not two-rater agreement or proof of perfect blinding. The response-unit sensitivity and original structural labels remain unchanged.

## Candidate research questions requiring approval

| Question | Prospective observable | Supporting versus narrowing observations |
|---|---|---|
| RQ-H1: Does history relevance alter reliability? | Paired R contrast under fixed sufficient evidence | Reproducible nonzero R contrast; a precise near-zero result narrows the relevance hypothesis |
| RQ-H2: Does temporal status alter reliability? | Paired T contrast relative to the date requested in the question | Nonzero valid-versus-expired contrast; errors equally present without history favor a ledger/template account |
| RQ-H3: Do R and T interact? | Averaged case-level difference in differences | Stable interaction on independent material; opposite contributions or imprecision preclude a general claim |
| RQ-H4: Are effects robust to content controls? | Each active history versus separately reviewed neutral history | Differences survive the specified length/format replacement; disappearance weakens a content-specific interpretation |
| RQ-H5: Do effects generalize? | Independently frozen task/template and model-arm replications | Replication with informative intervals; configuration dependence defines scope rather than invalidating null results |

None was a preregistered P1b mechanism hypothesis. RQ-H5 is not answered by this development bank.

## A narrower cross that preserves answer availability

Directly crossing answer-relevant history with valid/expired status creates a problem: the valid relevant cell repeats the requested answer while an irrelevant cell does not. That changes answer disclosure. We therefore prepare a **narrow auxiliary-history cross**, pending researcher agreement that it is useful:

| Cell | R: topical auxiliary relation | T: status at requested date |
|---|---|---|
| R0T0 | Unrelated music-label record | Expired before the requested date |
| R0T1 | Unrelated music-label record | Valid on the requested date |
| R1T0 | Parcel-label record related to the collection topic | Expired before the requested date |
| R1T1 | Parcel-label record related to the collection topic | Valid on the requested date |
| N_history | Coherent procedural archive exchange | No personal validity claim; semantic approval OPEN |
| H_none | Empty additional-history slot | No added history; intentionally shorter |

All four R/T statements are true within their stated intervals. T0 means inapplicable to the requested date, not false. For historical questions, T1 selects a historical interval rather than the newest interval. The archive timestamp is constant and explicitly distinct from the fact's validity dates. The ledger describes scheduled assignments, so later validity does not imply unavailable evidence.

R measures **topical relation of non-answer auxiliary information**, not whether history supplies the answer. It cannot identify direct stale-answer competition. A narrower alternative for that latter question would compare an expired target-property record against an expired unrelated record, holding T0 fixed. It would estimate the added stale-target-content package, not a complete R×T mechanism. No such alternative stimuli or requests have been added to the executable proposal. The researcher must choose the scientific target before an experiment is authorized.

## Independent development material

[The versioned dataset](../data/synthetic/p1c_development_proposed_v1.json) contains six new fictional speakers and two requested-date cases per speaker: 12 cases, three task families, six proposed cells, **72 proposed requests**. This replaces no historical allocation; the earlier 60-request example was illustrative, not a frozen P1c experiment. The present allocation adds a reviewed-neutral arm and paired current/historical questions while limiting independent speakers to six.

Each family has two speaker realizations and two question wordings. The families are direct single-field retrieval, two-component retrieval and a route-to-room relation. Multiple candidate routes and rooms prevent a unique-terminal-entity answer from being sufficient by itself. Explicit foil entities test basic identification, not difficult coreference. Required facts, quotations and derivations are in [ground_truth_v1.json](validation/p1c/proposed_v1/ground_truth_v1.json). Removing a required fact fails the reference solver; this is an offline stimulus check, never a Track A treatment. Such a check demonstrates formal dependency, not a model's reasoning process.

All new cases are selected by the construction rule before any model response: all speakers, both requested-date strata and every family are retained. No P1b case is reused as independent evidence. Development material will never become the confirmatory test. Lexical reuse, few templates, synthetic schedules and family nested within speaker remain limitations. More text is not a difficulty label; empirical discrimination remains unknown.

## Fixed experimental inputs and scope

Every cell preserves evidence bytes, question, requested date, evaluation date, recent context, reference answer and outcome applicability. Evidence is before the history slot. Matched histories share the archive wrapper, two turns, named speaker and insertion point. H_none keeps the wrapper but has no added dialogue, so its total-length contrast is not controlled. S=F=0 throughout this diagnostic; it does not re-estimate S/F/H interactions or replace C0–C7.

The proposed Base configuration is Qwen3.5-2B-Base Q4_K_M, llama.cpp b11573, four CPU threads and batch threads, zero GPU layers, context 4096, output budget 96, temperature 0, decoding seed 42. [Configuration proposal](validation/p1c/proposed_v1/configuration_proposal_v1.json) records an explicit shuffled 72-cell order with seed 715001. It is a proposal, not a frozen execution manifest. No generations have been requested. Final approval must pin selected prompts, source hashes, runtime identities, annotation policy and resume policy before creating a new execution manifest.

The unchanged 96-token budget preserves a documented starting configuration; it may censor complex replies. A separately authorized budget or template arm would be a new configuration, not a repair to these hypothetical outcomes.

## Presentation and subsequent research

Keep natural archived dialogue fixed initially. A records-versus-dialogue comparison would need identical admitted fact units, dates, order, speaker references and independently matched token length. It is not a free extra R/T factor. Adding one alternate rendering to four R/T cells would add 48 development requests, about 8.73 Base-equivalent response minutes, before setup and annotation. Existing admission/presentation work makes this secondary arm a replication or narrowly justified extension, not inherently novel. It is not included or authorized.

See [identifiability](P1c_identifiability_assessment.md), [precision](P1c_statistical_precision_plan.md), [review gates](P1c_neutral_control_review.md) and [researcher decisions](P1c_researcher_decision_packet.md). The proposed study is useful only if its narrower estimand is explicitly accepted; an observed error rate alone would not establish scientific value.
