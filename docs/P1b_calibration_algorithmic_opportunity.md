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
