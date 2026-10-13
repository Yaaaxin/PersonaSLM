# P1 Wave 1 Publication Readiness

Maintainer: Yaxin ZHENG. First submission target: PLOS ONE. Official title: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Protocol v1.1 remains the executed baseline; v1.2 Revised Proposed r1 remains prospective and unchanged.

## Current assessment

**A reproducible exploratory pilot is available; a submission-ready empirical study is not yet established.** Researcher confirmation closes the missing-label stage for these 96 outputs. It does not supply independent rater reliability, discriminative factual tasks, representative sampling, confirmed interactions, valid unreviewed controls or real-speaker generalization.

The defensible current contribution is a bounded empirical measurement observation: transcript continuation and first-reply semantic validity diverge in this one model/template configuration, and using structural labels as factual-error labels would misdescribe the saved data. This distinction is scientifically useful, but its novelty and generality are not established merely by documenting it.

## Observation, hypothesis and claim boundary

| Evidence level | Current statement | Claim not supported |
|---|---|---|
| Observed and reconstructible | 96 real outputs; confirmed 79 complete first replies; 72/72 factual and 48/48 temporal applicable labels Correct | General model accuracy or absence of persona-related factual effects |
| Supported within-sample comparison | Complete eight-cell paired observations; small relevance/coherence/structure differences concentrated in family C | Population interaction, significance, practical importance or a causal mechanism |
| Measurement observation | All 72 factual responses are CROSS_TURN yet have correct first replies; MR069 remains structurally AMBIGUOUS and semantically complete | Full continuations are factually correct or safe, or a termination intervention would improve them |
| Exploratory hypothesis | More demanding evidence reasoning, independent wording and different configurations may expose meaningful variation | Those future effects exist, or an Instruct model will necessarily improve reliability |
| Unresolved mechanism | H adds dated residence dialogue while holding current evidence fixed | Isolated historical relevance, temporal conflict or presentation effects |
| External validity | English fictional development cases, one quantized Base model | Authentic speaker fidelity, multilingual transfer, a size law or post-training effect |

## Nearest literature and novelty risk

The existing [novelty matrix](related_work_novelty_matrix.md) and [P1 assessment](P1_novelty_assessment.md) remain historical records. Official source records/abstracts were rechecked for the comparisons below; Wiki-Talkie's versioned HTML was available. This is not a new replication or a claim that every prior study's full method was re-audited. Previously verified full-text details are retained in the earlier assessment.

| Study / primary source | Relevant prior coverage | Implication for this pilot |
|---|---|---|
| [Principled Personas](https://aclanthology.org/2025.emnlp-main.1364/), EMNLP 2025 | Distinguishes intended persona advantages, robustness to irrelevant attributes and fidelity; effects vary across tasks/models | Persona sensitivity and separating constructs are established. Our within-case shared evidence differs operationally, but needs informative outcome variation |
| [When Personalization Misleads](https://aclanthology.org/2026.findings-acl.395/), Findings ACL 2026 | Studies history-aligned factual distortion and a factuality-preserving personalization intervention | Generic persona-induced hallucination is already covered. Our ceiling is neither replication nor falsification of their claim; tasks and interventions differ |
| [One Persona, Many Cues, Different Results](https://aclanthology.org/2026.acl-long.2079/), ACL 2026 | Tests six cue forms across seven models and four tasks, warning that cue choice changes conclusions | Our style wording is partly nested in speaker/task; an independent within-speaker realization test is needed before a new wording-robustness claim |
| [Decoupling Logic from Persona](https://arxiv.org/abs/2610.09772), arXiv v2 | Reports structured-output failures under context pollution and separates logic/persona inference paths in controlled model ablations | Structural versus semantic separation is not unprecedented. Our free-form first-reply audit is a different measurement setting, not a new architecture or proven mechanism |
| [What to Admit and How to Present](https://arxiv.org/abs/2610.11188v1), arXiv v1 | Separates memory admission and presentation; reports admission benefits with tradeoffs and no corrected difference between the two tested shared-content renderings | History content-versus-format decomposition overlaps directly. Our existing H package cannot isolate those mechanisms; broad novelty claims would be redundant |
| [Wiki-Talkie](https://arxiv.org/html/2610.08513v1), arXiv v1 | Real-user next-turn simulation with profile, behavior and history cues; population behavior and text similarity evaluation | Persona/history conditioning and real-user behavior are already studied. Our source-supported reliability questions differ, but fictional speakers provide no authentic-speaker validation |
| [TwinVoice](https://aclanthology.org/2026.findings-acl.981/), Findings ACL 2026 | Separates memory, reasoning and linguistic/persona capabilities across multiple real-world contexts | Multiple metrics and real-person simulation are not new. We have not measured Persona Fidelity or demonstrated transfer |
| [Persistent Personas?](https://aclanthology.org/2026.eacl-long.246/), EACL 2026 | Evaluates persona fidelity and instruction following over extended interactions | Our fixed short context is a different setting; generated transcript turns are not an executed long interactive trajectory |

The initially requested versioned Decoupling abstract and Wiki-Talkie abstract returned cache errors; the Decoupling main record (identifying v2) and Wiki-Talkie v1 HTML succeeded. These access failures are retained in the log. No paper findings or citations were invented and no paper data, adapters or code were imported.

## What could become a defensible contribution

| Candidate | Supporting future evidence | Falsifying / weakening evidence | Present limit |
|---|---|---|---|
| Independent and interactive S/F/H effects | Replicable, adequately precise paired effects on independent material after valid semantic scoring and controls | Informative near-zero effects, or apparent differences explained by wording, length or measurement choices | Current factual/temporal ceiling; ordinal differences largely involve three greeting speakers |
| A measurement boundary changes scientific interpretation | Independent first-reply/full-continuation assessment consistently changes an otherwise apparent conditioning effect | No material reinterpretation, or only a known enum/parser defect with no reproducible scientific consequence | Confirmed first replies only; full continuations were not independently scored |
| History relevance/temporal validity dissociate | Separate, justified manipulations under identical sufficient evidence and controlled presentation | Differences disappear after matching content/format or fail on independent cases | Current H combines these properties; future design requires approval |
| A configuration-specific robustness boundary | A separately frozen model/template arm yields a repeatable, scoped structural/semantic distinction | No meaningful difference, or differences entirely explained by changed template/budget | One configuration; post-training and template cannot be casually conflated |
| Generalization beyond synthetic speakers | Authorized independent English real-speaker material supports or bounds the controlled observation | Failure to transfer establishes a narrower synthetic boundary | No real-speaker data or fidelity ground truth here |

These are hypotheses, not discoveries. A rigorous justified replication or informative null may be publishable; a factorial layout, small model, CPU execution, many responses or high CROSS_TURN prevalence alone is not a scientific contribution.

## PLOS ONE relevance and remaining work

PLOS ONE's [official criteria](https://journals.plos.org/plosone/s/criteria-for-publication) emphasize original research, high technical standards, adequately supported conclusions, clear English reporting and data availability; they explicitly consider negative and null results. They do not require a favorable persona effect, and do not guarantee acceptance of this pilot. Our prospective cross-configuration or real-speaker requirements must be tied to the claims attempted, rather than presented as universal journal rules.

Before a confirmatory or broad publication claim, specify a defensible question/replication rationale; independent evaluation material; sample/precision and clustering justification; validated rating anchors and independent annotation/adjudication where required; a locked analysis/missingness/multiplicity plan; and a release package retaining all failed and null observations. Recover the original uncoded PDF if available and disclose any unresolved provenance gap. The current single-researcher assisted coding has no inter-annotator agreement; none can be calculated by treating AI coding as a second human.

The 24 P1 controls remain OPEN and must pass their own semantic review before matched-control comparisons. Their lack of review does not invalidate the existing factual labels or authorize changing controls based on observed performance. P0 remains accepted; no new P0 acceptance criterion is introduced. The next step is a researcher decision on [independent discriminative material](P1_wave1_next_experiment_recommendation.md), not automatic expansion or adoption of v1.2.
