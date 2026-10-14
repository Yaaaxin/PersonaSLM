# P1d independent measurement validation — proposed v1

Maintainer: Yaxin ZHENG. No second reviewer has been recruited, no human decisions are filled, and no agreement statistic has been measured.

## Independent review and sampling

P1c's researcher-adopted AI-assisted labels remain valid within their recorded provenance; they are not independent human ratings. A genuinely independent reviewer should first assess the 72 existing P1c raw outputs without prior spans/scores as a measurement audit. This does not turn P1c into an independent empirical replication. Use separate authored rubric examples for training, not the evaluated records. If an independent reviewer is unavailable, report that fact; do not substitute a second AI pass and call it inter-rater reliability.

For future P1d, prospectively sample 36 of 144 speaker clusters with fixed seed 716401, stratified over allocation blocks. Include both cases/all six conditions: 432 Base outputs, with all corresponding Instruct outputs if those speakers are in that arm. Allocate one independent human pass and one separate researcher pass before either sees AI suggestions. The remaining material may use AI assistance plus researcher adoption with that provenance explicitly retained. Select a separate enriched boundary-ambiguity diagnostic sample after generation using structure-only strata; report its inclusion probabilities and do not use it to estimate prevalence without weights.

Stage A uses anonymous response IDs, question, complete trusted evidence, requested/evaluation dates, required components and fixed context. Hide conditions, history packages, source model, parser status, automated predictions and previous score comparisons. Separate relevance/coherence and claim/component passes to avoid shared assignment. Responses may reveal treatment/style cues, so perfect blinding is not claimed. Randomize view order with seed 716402, preserve mapping in a protected file and freeze ratings before unblinding.

## Boundary ground truth

Stage B presents unchanged full raw continuations and prompt suffixes, with optional token/termination diagnostics only after initial span decisions. A first assistant response is the attributable assistant utterance immediately following the supplied final user request. A role transition begins a newly generated dialogue speaker; a section heading within the same utterance is not automatically a role transition. Answer completion concerns delivered requirements, not the presence of EOS. Continuation may belong to the same reply or a new turn. Ambiguity allows multiple defensible spans; no-recoverable-answer is distinct from an identifiable empty/promise reply.

Annotators mark exact character offsets, quote supporting boundary cues, record candidate spans and explain uncertainty. A response may be human-adjudicable yet parser-ambiguous. The parser is a comparator, never independent ground truth. Each reviewer must be able to abstain. Adjudicate disagreements with the researcher or a genuinely independent third human if available; preserve pre-adjudication labels and identities. Do not fabricate a third reviewer. Record actual submission times only when real submissions occur.

## Metrics and acceptance

For factual/temporal categories report raw agreement, confusion tables and nominal Cohen kappa, retaining Unverifiable and uncertainty. For ordinal ratings report weighted kappa with fixed linear weights and full score distributions. For components report per-component agreement; do not count components as independent participants. Use whole-speaker resampling for uncertainty. With extreme prevalence, kappa can be unstable or undefined; report observed agreement and ceiling frequencies without invented precision. Do not calculate agreement between an AI suggestion and its adopted copy as human reliability.

Boundary endpoints are exact/accepted-span match, over-extraction, under-extraction, false turn transitions, answer loss, abstention and unresolved cases. Multiple accepted spans are not forced into one gold. Semantic answer loss requires content review; character overlap alone cannot establish it. Existing `p1c_offline` baselines remain development comparisons. `tools/p1d_analysis.py::boundary_errors` implements comparison to independently adjudicated spans and refuses to report accuracy for unadjudicated ground truth.

Before confirmatory freeze, independently resolve all material ground-truth/leakage problems and all known rubric implementation conflicts. Predeclare a measurement-readiness target: at least 90% direct categorical agreement, no unresolved systematic rubric disagreement, and at most 5% boundary-unresolved records in a separate measurement pilot. These are proposed operational targets, not universal psychometric laws or guaranteed agreement. Failure triggers rubric/prompt revision on development material, not exclusion of difficult validation outputs. Even 5% missingness can leave substantial interaction bounds. Never remove a zero-variance metric retrospectively.

## Baseline comparison protocol

Compare native EOS/EOG, literal stops, deterministic first-turn extraction, anchored roles, headings and fence-aware parsing on identical saved text. Include quoted roles, document headings and code blocks in development challenges. Evaluate native templates and constrained output only in separately authorized generation studies. Freeze parser rules before future held-out outputs, report failures of simple and complex methods, and include runtime excluding I/O versus total runtime explicitly.
