# P1b Calibration Algorithmic Opportunity Assessment

Maintainer: Yaxin ZHENG. Version 1. Formal Protocol v1.1; proposed v1.2 r1 remains unchanged and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE.

## Observed Failure Modes

The observed structural distribution is **COMPLETE: 0, TRUNCATED: 5, CROSS_TURN: 186, AMBIGUOUS: 1**. Native termination is `{"eos": 2, "length": 190}`. These observations support examining continuation and first-reply extraction; they do not establish factual errors or semantic incompleteness. The initial source/output discrepancy documented in [measurement](P1b_calibration_measurement_report.md) is a review target, not a validated causal mechanism. Human semantic outcome coverage is currently zero. The empirical research remains primary.

## Existing Methods

The repository already provides frozen role-transition extraction and separate semantic applicability. Prior work covers persona robustness and personalized factual distortion. Memory selection and presentation are explicitly separated in *What to Admit and How to Present*, which also reports personalization trade-offs; this is direct overlap, not a new decomposition invented here. [Primary abstract](https://arxiv.org/abs/2610.11188v1). LongMemEval already includes temporal reasoning and knowledge-update evaluation in long-term conversational memory. [Primary record](https://arxiv.org/abs/2410.10813).

The earlier [algorithmic assessment](P1b_algorithmic_opportunity_assessment.md) records additional overlap with Decoupling Logic from Persona and AlignScore. The attempted new fetch of Decoupling v2 returned a browser cache miss; no fresh verification or reproduction is claimed. All literature checks here are record/abstract scope, not a systematic full-text review.

## Potential Algorithmic Improvements

| Direction | Actual support and unresolved question | Necessary baselines and validation | Cost / publication value |
|---|---|---|---|
| Historical evidence selection | History is an operational factor; relevance is entangled with task family. No reviewed harmful-history effect yet | All-history, no-history, equal-budget random and relevance selection; preserve trusted evidence and independently measure memory utility | Rules are cheap; neural retrieval costs unmeasured. No novel selector justified now |
| Temporal validity handling | Tasks expose explicit intervals; the first observed reference mismatch motivates review, not a causal diagnosis | Date-aware lookup versus supplied-ledger baseline, paired date/reference controls, independent cases | Offline rules versus new generation arms have different costs; useful only if reviewed temporal failures reproduce |
| Style/evidence separation | No valid semantic S or S×H estimate yet; repeated style/persona realizations constrain scope | Single-pass sectioning, no style, matched-compute multi-pass baselines and independent fidelity evaluation | Extra passes cost additional inference. Architecture alone has strong prior overlap |
| Response boundary control | Repeated cross-turn continuation is directly observed | Frozen no-stop transcript, post-extraction, predeclared stop rules and a separately pinned native Instruct configuration; test false cuts and complete-answer retention | Offline parsing is cheap; new arms need authorization. Measurement validity is a plausible contribution, not a claimed new algorithm |
| Evidence-grounded verification | General semantic scoring is deliberately unimplemented; source queries are not free-text judges | Human-referenced claim-level evaluation, exact-match-with-abstention and suitable existing factuality metrics on held-out answers | Rules cheap, learned verification adds unmeasured compute. Do not fit a scorer to these outputs and report held-out accuracy on the same items |

## Validation Feasibility

First annotate and integrity-register the existing packet. Distinguish unsupported assertions, verified contradictions, incomplete answers, date confusion, speaker ambiguity and extraction errors. A prospective method becomes justified only if it targets a reproducible unresolved pattern and is compared on independent material with appropriate compute, evidence and fidelity controls. No algorithm code, new model, extra prompt arm or training is executed in this task.

## Publication Value

The strongest current deliverable is auditable measurement infrastructure and a bounded development observation set. Increased error counts would not themselves establish novelty. Supported conditional effects or changed conclusions under valid structural/semantic measurement could motivate a contribution, but must survive independent validation and direct prior-work comparison. Exact tokenization, CPU deployment, a factorial table and a larger generation count are insufficient originality claims.


## Measurement-audit addendum — v2 (original v1 retained)

### Observed Failure Modes

The [192-response measurement audit](P1b_calibration_measurement_audit.md) reproduces every native output and frozen parser result. Beyond the earlier execution summary, it distinguishes four unclosed thinking blocks, one unfinished date clause with no parser-deleted tail, one unrecognized-label ambiguity, and17 literal prospective-check openings. The latter are text-pattern observations, not17 human-confirmed missing answers. Supported intermediate facts can fail to answer a requested room/building question. All semantic judgments remain pending.

### Existing Methods

Role-transition extraction already exists in this repository; the official post-trained Qwen template supplies native turn delimiters. LongMemEval covers temporal retrieval/updates; memory admission/presentation and factual personalization mitigation already appear in the [novelty assessment](P1b_calibration_novelty_assessment.md). A date filter, prompt section or response verifier is not inherently novel. No existing algorithm has been rerun or claimed reproduced in this audit.

### Potential Algorithmic Improvements

| Candidate | Current support / unresolved problem | Required baselines and independent validation | Cost and publication value |
|---|---|---|---|
| Evidence-aware response selection | Intermediate-fact and promise openings show answer-delivery review targets; no validated selector target yet | No selection, first-unit extraction, evidence-aware selection; human true-unit/claim annotations and false-selection rate on independent outputs | Offline rules inexpensive; extra sampled generations cost new inference. Useful only if valid units improve without cherry-picking |
| Temporal-aware historical retrieval | Concrete date/site discrepancies require confirmation; all trusted facts were already supplied | All-history/no-history, date filtering, relevance filtering, matched-budget random selection; crossed relevance/time and preserved evidence | Retrieval rules cheap; causal generation tests new cost. Strong prior overlap; no current method claim |
| Persona/evidence separation | S/F/H packages and length differ; no semantic interaction estimated | Existing sectioned prompt, native chat, compute-matched multi-stage baseline and independent fidelity review | Extra stages add calls. Cannot infer representational entanglement from these outputs |
| Response boundary management |186 cross-turns and one ambiguous boundary are observed; five prefixes end at96tokens | Frozen parser, native chat/EOG, predeclared stop strings; complete-answer retention, false cuts and full raw preservation on independent examples | Offline audit cheap, controlled new arms require approval. Instrument validity is more immediate than algorithm novelty |
| Structured factual verification | Source oracle validates stimuli but is not a free-text semantic judge | Exact-match with abstention, existing factuality/NLI tools, human claim-level references; negation/date/multiple-claim tests and held-out validation | Learned scoring cost unmeasured. Do not train/test on this same reviewed bank and claim independent accuracy |

### Validation Feasibility

First score the existing bank and quantify boundary agreement, missing answer delivery, contradictions, uncertainty and temporal misattribution. Retain unscorable cases and protected assignments until review is frozen. A new method is justified only if a reproducible unresolved failure persists beyond established baselines and a separate development/evaluation allocation can test it. No algorithm implementation, new inference or training is authorized by this assessment.

### Publication Value

Current value is a truthful measurement package. A replicated difference between raw-structure conclusions and valid semantic-unit conclusions could support an empirical contribution; a high continuation count or more errors alone cannot. Independent validation, useful precision and literature comparison remain necessary. This addendum preserves every earlier observation and does not retroactively change the empirical study's primary track.
