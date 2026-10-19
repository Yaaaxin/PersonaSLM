# Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models

Researcher and intended paper author: Yaxin ZHENG. First submission target: PLOS ONE. Working manuscript sections v2; AI-assisted drafting disclosed in the research record. These sections are prospective where independent validation is incomplete. They do not report invented validation results. The earlier Methods v1 is preserved.

## Introduction and research questions

Personalized dialogue systems must reflect a speaker's linguistic and conversational characteristics while answering the current task from valid evidence. An answer can be stylistically faithful yet false, factually supported yet incomplete, or semantically useful despite subsequent generated dialogue. Treating these outcomes as a single score obscures scientifically different failures.

PersonaSLM asks how linguistic style, supplementary personal facts and dialogue history affect four reliability dimensions under identical, sufficient trusted evidence (RQ1–2); how model and context configurations bound those effects (RQ3); and where observable failures and oracle headroom arise in the processing pipeline (RQ4). Linguistic and Behavioral Fidelity are separate outcomes. CPU deployment is a fixed constraint, not itself a causal intervention. The main study remains the controlled S/F/H programme, supported by focused history and configuration diagnostics.

## Related work and contribution boundary

The [versioned novelty matrix](related_work_novelty_matrix_monitor_v7.md) supplies verified sources and publication status. Existing work already addresses personalization-induced factual errors, memory admission, temporal retrieval, persona persistence, structured response validity and verification. PersonaSLM must therefore demonstrate a precise contribution through independently measured conditional effects, informative limits or a validated reliability–fidelity–cost tradeoff. New dataset names, factorial notation, CPU implementation or combined known filters are not sufficient novelty.

The 2026-10-18 surveillance update further narrows this boundary. Published or current primary work already formalizes stale binding after contextual updates, temporal supersession in conversational memory, non-selective cross-attribute persona effects, deterministic linguistic-fidelity diagnostics, and persona-consistency versus reasoning-stability trade-offs; one close study combines governing persona facts, temporal revisions, quantized small open-weight models and local CPU inference. PersonaSLM therefore cannot claim priority for those broad phenomena or mechanisms. Its remaining empirical hypothesis is the controlled joint decomposition of complete S/F/H conditioning packages under shared sufficient dated evidence, with outdated-value adoption separated from other failures and reliability, fidelity and computational cost reported jointly. This distinction remains untested and is not itself evidence of novelty.

Subsequent full-text review adds three sharper boundaries. Wiki-Talkie already compares
raw comment history with explicit profiles and compressed behavioral descriptions for
population-level persona simulation. ReTurn uses matched direct and conversational views
to separate answerability from selective-history failure and distinguishes cases where
history is required from cases where it competes with current evidence. Memory Echo's
Family-Provenance-Authority framework already groups same-source traces, conditions stale
record eligibility on verified corrections, and constrains answers with authoritative
evidence. Consequently, neither history-versus-profile comparison, the statement that
history can help or hurt, nor generic provenance-guided stale-memory suppression is a
defensible priority claim. These studies instead motivate matched direct controls and
simple restatement, temporal-filtering, authority-only, and FPA-like baselines for any
future mechanism or algorithm study.

Post-restart surveillance identified a further measurement collision. PersEvalBench
prospectively defines whether persona information should persist, transfer, or cease to
apply and evaluates directional appropriate-, under-, over-, and stale/superseded-use
errors with matched responses and a human-reference subset. The paper reports that LLM
judges remain unreliable even with full or highlighted history, while pairwise comparison
is easier but does not identify error direction. PersonaSLM therefore cannot claim the
first persona-use evaluator meta-evaluation or controlled stale-use taxonomy. Its future
semantic endpoint must be validated with condition-blinded human judgments; an LLM judge
or pairwise contrast may be reported only as secondary evidence.

## Experimental design

Track A crosses S/F/H in C0–C7 while fixing evidence, question, evaluation/requested dates, reference answer and dialogue context within case. Token-matched controls are interpreted according to their actual semantic validity. Track B manipulates evidence availability separately. P1c R/T and P1d E/V are text-package diagnostics; name, value, date and salience changes limit mechanistic interpretation. Model comparisons record template, quantization and stop-policy differences rather than attribute everything to post-training.

Development material is permanently distinguished from independently constructed validation material. Speakers, tasks, templates and construction ancestors are recorded as dependencies. Prospective realization blocks vary legitimate expressions while retaining semantic intervention content. Final sample and endpoint choices require an explicit confirmatory freeze; the already adopted P1d prospective addendum does not provide that freeze.

### Current development-feasibility evidence

The original Stage B minimal temporal calibration yielded 6/8 current-value adoptions against its registered 7/8 gate, so the associated 80-request factorial pilot was not executed. A separately authorized, prospectively frozen two-challenger recovery then tested the smaller configuration on the same development-only cases. SmolLM2-1.7B-Instruct Q4_K_M completed all eight requests with integrity PASS, but the frozen exact/alias endpoint counted only 1/8 current-value adoptions (one current, one outdated and six unverifiable) against the unchanged 7/8 model-screen threshold. A retrospective AI-only semantic reading proposed four current, three outdated and one incomplete answer; it is neither independent nor human annotation, does not replace the frozen endpoint, and still does not meet the gate. The complete two-candidate evidence chain and hashes are indexed by the [post-Candidate-2 research state](validation/p1/model_feasibility_recovery_v1/post_candidate2_research_state_v1.json).

The second frozen configuration, Qwen2.5-3B-Instruct Q4_K_M, was downloaded, hash-verified and native-template materialized. After an earlier 4,901,916,672-byte resource block, materially changed memory availability justified one versioned v4 preflight. It passed at 5,675,884,544 available physical bytes against the unchanged 5,368,709,120-byte gate. Exactly eight frozen requests then completed without retry. The registered automatic endpoint counted 2/8 current-value adoptions, with three outdated-value adoptions and three unverifiable answers, below the unchanged 7/8 selection threshold. Seven outputs ended with native EOS and one unverifiable output reached the 96-token length limit; all three explicit outdated-value outputs ended normally after eight or nine tokens, so truncation cannot explain those failures. Exact/alias classifiable coverage was 5/8, compared with 2/8 for Candidate 1, but two of the three additional classifiable answers adopted outdated values. Replay verified all eight attempts, HTTP records, raw-output hashes and scores. The prospective selection status is therefore `BOUNDED_SCREEN_NEGATIVE`: neither configuration qualified and no model was selected. Autonomous use is 16 generations and 159.95704690001094 recorded completion-inference seconds. This is an actual negative development-screen result for the exact model-plus-native-template configuration, but not independent validation, a broad capability comparison, a human semantic judgment, or evidence about S/F/H effects. No disjoint C0 pilot or factorial request is authorized.

Offline downstream preparation also exposed a controller hazard: the frozen 80-request
minimal-temporal source is case-grouped, so its first eight positions span C0–C7 rather than
the eight C0 cases. A Candidate-2-native materialization now preserves the exact scientific
messages while recording explicit eight-request C0 and 72-request continuation ID sets under
a new autonomous namespace. It used 80 tokenizer calls and zero generations. The prospective
C0-only controller selects the eight registered IDs explicitly, pins the materialization
hash, preserves immutable attempts and raw-response replay, and retains the unchanged 5 GiB
RAM gate. It was validated offline but never executed. Candidate 2 subsequently failed the
frozen 7/8 feasibility screen and was not selected, so the controller now fails closed with
`STATE_REQUIRES_REVALIDATION`; neither its C0 action nor any continuation action is authorized.
The controller deliberately implements no continuation action, and all 72 other requests
also remain blocked by semantic endpoint validity and separate-controller requirements.

### Synthetic persona-dialogue development evidence

A separate, prospectively frozen development programme used Qwen3.5-2B Q4_K_M on four
explicitly synthetic personas and twelve new controlled next-turn choice cases. It executed
all eight S/F/H cells once per case (96 generations). The narrow phrase-level style contract
showed a registered S effect of +0.9375, but this is template compliance rather than broad
Linguistic or Behavioral Persona Fidelity. The frozen strict choice scorer resolved 44/48
H=0 responses but only 2/48 H=1 responses, leaving every registered content factorial
contrast without a complete-case point estimate. Raw-output inspection found that 44/48 H=1
responses repeated the archived assistant frame `I recommend the ...`; this was a preserved
negative measurement result, not zero reliability. The complete report is the
[independent synthetic S/F/H replication](validation/p1/persona_dialogue_independent_replication_v2/scientific_report_v1.md).

Two prospectively frozen mechanism studies then produced 90 further observations. A
30-request arm comparison showed that neutralizing the archived recommendation surface
eliminated literal frame recurrence but did not improve the registered task-success endpoint.
A position-balanced 60-request semantics-by-surface design independently reproduced the
surface association: declarative minus raw history was +0.1667 for preferred-current choice,
+0.1250 for current-target selection, -0.1667 for exact archived-target intrusion, -1.0000
for raw-frame recurrence and +0.8750 for strict-format adherence. Averaged history arms still
had lower values than no history on the registered preferred-current endpoint (-0.2917). Aligned history also did not
outperform conflicting history in this small bank. These are conditional, synthetic,
single-model development estimates; the strict format rule structurally overlaps the raw
article-bearing frame, exact-name intrusion is an incomplete stale-use measure, and no human
semantic or Persona Fidelity outcome was collected. Evidence is in the
[template-mechanism report](validation/p1/persona_dialogue_history_template_mechanism_v1/scientific_report_v1.md)
and [position-balanced mechanism report](validation/p1/persona_dialogue_history_semantics_surface_factorial_v2/scientific_report_v2.md).

An output-informed simple baseline subsequently changed only the archived assistant's first
sentence to `My choice was <same archived target>.` for the 48 H=1 cells and reused the 48
frozen H=0 observations without regeneration. Strict selection resolution increased from
2/48 to 42/48 and raw-frame recurrence fell from 44/48 to 2/48. These are coupled
surface/measurement outcomes because the strict selector rejects the raw recommendation
frame; they did not identify a paired semantic-content benefit because only two
raw/declarative pairs were jointly resolved. In the hybrid cross-batch descriptive
reconstruction, complete-case preferred-choice
estimates were S -0.225, F +0.125, H -0.125 and F×H -0.250; logical missing-outcome bounds
excluded zero only for S and H, while F reached zero and higher interactions generally
spanned both directions. The two incomplete cases were both in the irrelevant-history
stratum, so the logical bounds take precedence over the reweighted complete-case points.
H is exactly aliased with execution batch and declarative rendering.
These estimates are output-informed and execution-batch-confounded,
so they are hypotheses for a disjoint validation bank, not causal factor effects or
independent validation. A separate read-only reconstruction reproduced the raw journals,
scores, estimates and resource accounting with zero differences. The full evidence is in the
[declarative-history repair report](validation/p1/persona_dialogue_independent_replication_declarative_repair_v1/scientific_report_v1.md).

A prospective disjoint-case validation then collected 168 responses from the same
Qwen3.5-2B Q4_K_M configuration on 24 new controlled synthetic cases (12 personas,
three task families, seven within-case arms). The registered pooled declarative-minus-
raw estimate was 0.0000 for preferred-current selection and +0.0139 for any-current
selection, so the earlier same-bank surface association did not reproduce as a stable
pooled declarative advantage. Aligned-minus-irrelevant and conflict-minus-irrelevant
preferred estimates were +0.0417 and +0.0208; aligned-minus-conflict was +0.0208 and
zero on any-current selection. The registered irrelevant-H-minus-no-H estimate was
-0.1875 on both automatic endpoints, but an explicitly post-hoc raw-output audit found
that 24/144 History-conditioned responses copied the literal format placeholder
`<exact A anchor>` or `<exact B anchor>` (versus 0/24 without History). Of the 24,
23 were scored `NONE`; all 23 nevertheless named the preferred canonical option in
the first sentence and none named the nonpreferred option. This makes the automatic
-0.1875 contrast uninterpretable as demonstrated semantic reliability loss and instead
identifies a reproducible response-realization/evaluator interaction. Independent local
analysis code reconstructed 1,557 hash-chained events, all 168 scores, all 14 registered
estimates, task strata, leave-one-persona-out ranges, resources, and cumulative budgets
with zero differences. These remain synthetic, single-model, constrained-selection
results; blinded human relevance, evidence consistency, coherence, completeness, and
Persona Fidelity judgments are pending. The complete evidence is in the
[disjoint validation report](validation/p1/persona_dialogue_disjoint_surface_validation_v3/scientific_report_v3.md).

## Measurement framework

Measure Response Relevance, Factual Consistency, Temporal Consistency and Conversational Coherence independently. Separately retain Task Success, supported/present components, semantic completeness, boundaries, empty/repetition rates, Linguistic/Behavioral Fidelity and CPU/RAM. Correct, Incorrect, Unverifiable, N/A and Missing remain distinct; uncertain evidence, unresolved boundaries and ambiguous interpretation have separate state fields. A complete wrong answer is not an incomplete answer; native stopping is not correctness.

The [fidelity proposal](PersonaSLM_persona_fidelity_measurement_v1.md) separates profile/reference-conditioned judgments from the evidence-quality panel. Independent reviewers score before seeing AI proposals or other ratings. Where the researcher adopts AI suggestions, report that provenance without implying independently produced human labels. Store raw and extracted text with boundary sensitivity rather than overwriting inconvenient spans.

The aggregate evaluator-validity audit places a narrower boundary on current automatic measures. In the 32-record O/Q audit, automatic and single-researcher exact categories agreed for 31 records (96.88%; descriptive record-level Wilson 95% interval 84.26%–99.45%), and both sources contained 16 task successes. Those marginals do not identify the confusion matrix, sensitivity, specificity, kappa, or independent validity of factual and temporal axes. In Wave 1, the automatic factual scorer produced a conclusive label for only 15/72 eligible replies (20.83%); researcher-confirmed AI-assisted coding, rather than an independent second rating, supplied the broader semantic labels. Structural status was also not a semantic proxy: 78/78 `CROSS_TURN` first replies in Wave 1 and 142/186 in the P1b aggregate were semantically complete. For Candidate 1, the frozen whole-answer alias endpoint recognized a current or outdated value in 2/8 outputs and in only 2/7 outputs that a post-hoc AI-only diagnostic considered semantically classifiable. This does not estimate semantic accuracy, but it is sufficient to reject that endpoint as the sole future semantic outcome, particularly because Style can change answer wrappers. The historical 1/8 model-selection result and 7/8 gate remain unchanged. The machine-readable aggregate and source hashes are in [evaluator_validity_v1.json](validation/p1/model_feasibility_recovery_v1/evaluator_validity_v1.json).

PersEvalBench independently reinforces this prospective restriction but does not validate
PersonaSLM's endpoint. Its paper reports an 83.5% exact human agreement rate (Cohen's
kappa 0.72) on a 100-scenario subset and large human–LLM-judge gaps for directional
persona-use errors. Future PersonaSLM review must therefore retain independent pointwise
judgments, error direction, false alarms, abstention or unverifiable coverage, and genuine
human agreement. Side-by-side pairwise review is reserved for sensitivity analysis because
the explicit contrast makes the task easier and cannot recover direction.

To operationalize that restriction without changing a historical gate, a deterministic
local review package now randomizes the eight archived Stage B responses together with the
eight archived Candidate 1 responses. Its pointwise form exposes the complete evidence,
question, and raw answer while masking model, run, case, condition, automatic score, and
prior AI interpretation; the identifying mapping is stored separately. The form requests
current-value, outdated-value, other-supported, unsupported, contradictory, missing-value,
or uncertain answer state plus semantic completeness, answer span, rationale, confidence,
and reviewer provenance. At this checkpoint all 16 label rows are blank. The package is a
measurement instrument, not human evidence, and a single completed review would still not
establish inter-rater reliability. Its public receipt is
[semantic_review_package_v1.json](validation/p1/model_feasibility_recovery_v1/semantic_review_package_v1.json).
The corresponding intake validator rejects changes to anonymous IDs, evaluation material,
or raw responses and requires a hash-bound reviewer provenance record before producing an
aggregate. It has been tested only with synthetic labels and has not unblinded or analyzed
the real package.

An additive two-rater calibration package now closes the instrument's mechanical
single-reviewer limitation without supplying any human result. Two independently ordered,
local-only copies share the same 16 development responses while masking the protected
mapping, automatic labels, condition identity and the other review. Both remain unassigned
and blank. The prospective intake requires two distinct external humans, immutable initial
locks, explicit blindness/no-AI-assistance provenance, and separation of unavailable review
from a completed `UNCERTAIN` judgment. A hash-bound aggregate analyzer is ready to report
coverage, full 7×7 and 3×3 matrices, raw agreement and nominal Cohen kappa, including honest
undefined states, without exposing record-level material. There is no post-hoc acceptance
threshold. Even a completed analysis would remain a small development calibration rather
than independent endpoint validation or Persona Fidelity evidence. The zero-label records
are [the calibration plan](validation/p1/model_feasibility_recovery_v1/semantic_interrater_calibration_plan_v1.json)
and [analysis readiness receipt](validation/p1/model_feasibility_recovery_v1/semantic_interrater_analysis_readiness_v1.json).

## Statistical analysis plan

Estimate paired case contributions using exact registered contrasts and outcome-specific denominators. Cluster by speaker and examine template/ancestor and task-family sensitivity; never treat generations as independent participants. Report categorical incidence, assessable-case correctness and supported-task success as different estimands. Unknown-outcome bounds, leave-one-speaker-out diagnostics and boundary sensitivity complement intervals. Small purposive development clusters do not yield guaranteed population coverage. Confirmatory multiplicity and practically meaningful precision targets must be declared before generation; null findings are retained and do not automatically establish equivalence.

An offline resource and precision audit identifies 48 new speakers with two ancestry-disjoint cases each as a potentially feasible minimum independent design. Retaining C0–C7 plus both diagnostic controls would require 960 generations. A subsequent deterministic 2,000-replicate simulation crossed those 96 cases over eight balanced new template ancestors and declared a central median two-way clustered 95% half-width target of at most 15 percentage points with at least 93% conditional-template coverage before execution. Under the central assumptions, the median half-width was 11.89 points and simulated coverage was 95.95%; a higher-template-dependence sensitivity yielded 13.11 points and 97.15%. Outcome-dependent missingness reduced median complete-pair coverage to 88.54%, biased the complete-pair estimate downward by 2.48 points, and reduced interval coverage to 92.5%; logical missing-outcome bounds averaged 11.89 points wide. These are assumed-data planning results, not fitted power, a frozen cohort, or authorization. Eight template ancestors do not establish broad new-template generalization, and high-order interactions can remain much less precise. Execution still requires a viable development configuration, an interpretable factorial pilot, an adopted missingness policy, and researcher-blinded semantic review of the primary C0/C3 outputs. The exact simulation, source hash, assumptions, and reproduction test are in [independent_validation_precision_v1.json](validation/p1/model_feasibility_recovery_v1/independent_validation_precision_v1.json).

A prospective missing-outcome policy now reuses the registered S/F/H weights and the tested
signed-bound engine. Every frozen eligible request remains in the primary denominator.
Infrastructure loss, invalid raw evidence, unavailable review, semantic uncertainty, valid
model nonanswers, and prospectively declared inapplicability are distinct states. Unknown
binary semantic outcomes contribute sign-aware logical bounds without dropping cells or
renormalizing factorial weights. Complete-pair estimates are secondary sensitivities with
explicit condition, speaker, and template coverage; bounds are identification regions, not
confidence intervals. This policy is synthetic-tested and pending researcher adoption, so it
does not yet constitute the confirmatory freeze. The machine-readable candidate is
[independent_validation_missingness_policy_v1.json](validation/p1/model_feasibility_recovery_v1/independent_validation_missingness_policy_v1.json).

A subsequent registry audit found that the current nine factorial/simple contrasts omit two
preliminary Protocol v1.1 comparisons, C1−N_style and C3−N_history. A prospective candidate
restores them rather than silently narrowing the protocol and places all four simple
comparisons plus the seven balanced main/interaction contrasts in one 11-hypothesis,
two-sided Holm family for blinded-human outdated-value adoption. C3−C0 is the lead planning
contrast but has no unadjusted-alpha privilege. Missing or invalid marginal tests stay in
the family as non-rejections. Other reliability, semantic, fidelity, and cost endpoints are
estimation outcomes unless the later confirmatory freeze explicitly expands the testing
family. This candidate remains unadopted: exact neutral controls need semantic approval, the
missingness policy needs those two contrasts, and the two-way speaker/template marginal test
needs prospective calibration. The machine-readable record is
[independent_validation_multiplicity_candidate_v1.json](validation/p1/model_feasibility_recovery_v1/independent_validation_multiplicity_candidate_v1.json).

That calibration has now produced two retained negative planning results. The original
two-way sandwich with t(7) exceeded its declared global-null Holm FWER criterion (worst
3,000-replicate fraction 7.7%; Wilson upper 8.71% versus a 6% ceiling). A separately
versioned speaker-cluster t(47) alternative for a finite-eight-template target kept the Holm
FWER upper limit below 6% but exceeded the mandatory marginal type-I upper-limit criterion
(6.98% versus 6.5%). Neither procedure is adopted, and no threshold was relaxed. Thus the
current plan has no calibrated confirmatory test: effects, category distributions,
missingness and logical bounds remain estimable, but dichotomous hypothesis-test claims are
blocked pending a prospectively justified alternative or an explicit estimation-first
freeze. The signed-bound policy now covers all 11 candidate contrasts without activating
unreviewed neutral controls. Evidence is retained in
[test calibration v1](validation/p1/model_feasibility_recovery_v1/independent_validation_test_calibration_v1.json),
[test calibration v2](validation/p1/model_feasibility_recovery_v1/independent_validation_test_calibration_v2.json),
and [missingness policy v2](validation/p1/model_feasibility_recovery_v1/independent_validation_missingness_policy_v2.json).

An outcome-blind estimation-first candidate now supplies a narrower alternative to further
test searching. It preserves all 11 contrast definitions, designates C3−C0 only as the lead
reporting estimand, and targets the eventual finite realized 96-case/eight-template cohort
only if its exact inventory and policy are prospectively adopted. Signed case-level points
or bounds are averaged across both cases within speaker and then equally across all 48
speakers; missing speakers fail closed. Reports would retain every denominator, missingness
reason and semantic category. Complete-pair estimates and template leave-one-ancestor-out
ranges are sensitivities only. No p-values, dichotomous decisions, calibrated confidence
intervals or broad population claims are authorized. This remains an unadopted candidate,
not the confirmatory freeze, and is recorded in
[independent_validation_estimation_candidate_v1.json](validation/p1/model_feasibility_recovery_v1/independent_validation_estimation_candidate_v1.json).

## Reproducibility and limitations

Bind prompts, native token IDs, input/reference versions, source code, model/backend/template files, seed/order, parameters, raw HTTP output, stops and telemetry by hashes. Preserve failed attempts and prohibit silent reruns. Researcher authorization, AI proposals, adopted annotations and independent human judgments are distinct records. No historical protocol or raw experiment is rewritten. Third-party quantization lineage, synthetic linguistic dependence and incomplete independent annotation presently limit inference.

## Publication evidence roadmap

The minimum credible empirical submission needs an adequate model/task regime; validated persona manipulations and independent linguistic/behavioral measurements; a prospective core S/F/H confirmatory design with useful precision; independent cases and meaningful template variation; transparent clustering/missingness/multiplicity; fair method/configuration baselines; and a reproducible data/code availability plan. A new algorithm is optional. Results must remain useful if effects are null or known baselines match proposed remedies.

[PLOS ONE's publication criteria](https://journals.plos.org/plosone/s/criteria-for-publication) require original research, technically sound methods and conclusions supported by data, with ethical/reporting/data standards. Technical reproducibility alone does not establish readiness or acceptance. No independent validation, manuscript submission or public release is claimed here. An algorithm paper would additionally need a distinct method, strong comparisons, ablations, fidelity/cost accounting and independent evaluation.

## Real-speaker S/F/H development pilot: observed evidence, 19 October 2026

A separate prospective development pilot has now collected 64 actual Japanese dialogue
continuations using RealPersonaChat v1.0.0, revision
`28d0b6b3865b29cabc26c230a2db37cdf315e937`. Eight eligible speakers were selected
deterministically from the frozen 76-speaker development cohort, with one later dialogue
context and all eight C0–C7 conditions per speaker. The existing speaker partition was
retained; the 58 independent-validation speakers remain unused. Participant-authored
persona statements and dialogue are genuine corpus records. The corpus's documented
license and research restrictions are preserved in the
[intake and privacy boundary](validation/p1/real_persona_chat_intake_v1/data_governance_and_study_boundary_v1.md).
A [narrow governance amendment](validation/p1/real_persona_chat_sfh_pilot_v1/data_governance_amendment_v1.json)
authorized this development-only generation batch with automatic proxy outcomes before
human semantic review. Participant text, prompts, references, outputs, and mappings remain
local; only aggregate evidence is reported here.

S supplied numeric surface descriptors derived from two earlier dialogues with distinct
partners. F supplied the participant's ten self-authored persona statements, whose temporal
truth is unknown. H supplied six chronological turns immediately preceding the fixed
partner query in a later dialogue with another partner. The next human continuation was
withheld from every prompt. Parseable timestamps, partner separation, and conservative
lexical leakage checks were required. All conditions used the same system instruction,
section headers, and query; disabled factor sections were empty. An XOR Latin schedule
balanced condition position across speakers and each factor within each execution block.
Natural history carries both content and style, so these comparisons estimate incremental
prompt-package effects rather than orthogonal psychological constructs. These decisions
were frozen in the [prospective design](validation/p1/real_persona_chat_sfh_pilot_v1/prospective_design_v1.json).

The model was Qwen3.5-2B with third-party Q4_K_M weights (SHA-256
`0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`), run through
llama.cpp `b11573-0f701c882` on four CPU threads, with context 4,096, maximum 96 new
tokens, temperature 0, top-p 1, seed 42, and thinking disabled. No retries were made.
The quantization's upstream conversion lineage remains partially verified. Repository
HEAD was `c40667ad266082481b1850453f67784b593f3723`; the pilot's uncommitted source
versions, tokenizer, template, weights, prompts, native token arrays, authorization, and
integrity amendment are bound separately by hashes in the
[execution registration](validation/p1/real_persona_chat_sfh_pilot_v1/prospective_execution_registration_v1_1.json).
The source commit alone therefore does not reconstruct this execution.

All 64 requests returned responses without native API failure. Sixty ended with the
backend's native `eos` reason; four reached the 96-token limit, one each in C0, C2, C3,
and C6, affecting three speakers. The frozen analysis provides text-derived proxy values
for 60 responses and complete eight-condition text contrasts for five speakers. Token and
latency contrasts retain all eight speakers. The shared boundary parser recognizes `eog`
but does not normalize this backend's `eos` label; consequently it records 60 boundaries
as `AMBIGUOUS` and four as `TRUNCATED`. Numerical proxy availability does not resolve
that boundary ambiguity or demonstrate semantic completeness. Neither the raw stopping
records nor the frozen analysis has been relabeled retrospectively.

The registered speaker-paired main effects are shown below. A main effect is the mean
within-speaker difference between factor-present and factor-absent conditions, averaged
over the other two factors. The complete analysis retains all seven main and interaction
contrasts, condition summaries, missingness, and descriptive influence ranges.

| Outcome | Complete speakers | S effect | F effect | H effect |
|---|---:|---:|---:|---:|
| Generated tokens | 8 | -18.937500 | +9.437500 | -2.875000 |
| Completion latency, seconds | 8 | -0.293696 | +1.948556 | +0.753629 |
| Six-coordinate source-style distance, lower is closer | 5 | -0.104083 | +0.035680 | +0.026409 |
| Character-trigram F1 against one withheld continuation | 5 | +0.048791 | +0.009045 | -0.016897 |

S reduced generated length in this finite development cohort; its leave-one-speaker-out
token-effect means ranged from -23.642857 to -16.107143. F and H increased observed
completion latency, including the cost of their longer input packages. These estimates
describe this hardware, model, and execution schedule. The single withheld human response
is one possible continuation, so reference overlap cannot be interpreted as correctness.
The text estimates exclude three speakers with limit-censored outputs; this
condition-dependent missingness can distort complete-case contrasts. See the
[frozen aggregate analysis](validation/p1/real_persona_chat_sfh_pilot_v1/analysis_v1_1.json).

The apparent S improvement in source-style distance needs a narrower interpretation.
Earlier [development validity controls](validation/p1/real_persona_chat_style_signal_validity_v1/scientific_report_v1.md)
found a mixed stylometric signal that survived finite length, lexical-overlap, repetition,
and partner controls, but did not establish topic-independent speaker identity. In the
generated pilot, a separately labeled
[post-hoc coordinate decomposition](validation/p1/real_persona_chat_sfh_pilot_v1/posthoc_style_coordinate_decomposition_v1.json)
shows that -0.082165 of the -0.104083 S distance effect comes arithmetically from the
length coordinate (78.9422% of the signed total). The remaining five-marker mean distance
effect is -0.026301, with leave-one-speaker-out means from -0.031667 to -0.018710, on the
same five complete speakers. This ratio is neither causal mediation nor variance
explained. Because S explicitly instructs length and marker rates, the observations
support descriptor conformity, predominantly length conformity, with a smaller marker
component. They do not establish distinctive generative Persona Fidelity or a
reliability–fidelity improvement.

Completion inference consumed 342.591495 seconds (mean 5.352992 per response), bringing
cumulative autonomous use to 572/1,200 generations and 3,514.136104/72,000 inference
seconds. Peak observed server working set was 2,581,692,416 bytes; minimum observed
available physical memory was 2,332,139,520 bytes. A separate AI analyst independently
implemented the numerical metrics and effect arithmetic, reproducing 64 raw responses,
1,024 row-metric values, 128 condition summaries, 112 factorial summaries, and resource
accounting without differences. The
[analysis reproduction receipt](validation/p1/real_persona_chat_sfh_pilot_v1/independent_analysis_reproduction_v1.json)
explicitly retains the shared boundary-parser dependency. This is independent numerical
analysis reproduction, not independent boundary validation, human semantic validation,
generation repeatability, or independent experimental validation. Private artifacts are
required; public clone-only reproducibility remains partial.

Human judgments for these 64 outputs remain uncollected. The separate
[condition-masked review protocol](validation/p1/real_persona_chat_sfh_pilot_v1/human_review_protocol_v1.json)
requires a qualified Japanese-reading human, exact reviewer-exposure provenance, and all
64 record dispositions. It preserves the earlier 168-record and 16-record review
requirements. Relevance, coherence, linguistic resemblance, supported personal claims,
history consistency, and completeness therefore remain unestablished. No p-values or
calibrated confidence intervals are claimed; leave-one-speaker-out ranges are influence
diagnostics. The pilot supplies real-speaker conditioning and resource observations, but
neither an independently validated general effect nor a validated novel algorithm. Semantic
claims require genuine review; further experiments require prospectively applicable
measurements, while the reserved speakers remain protected from development choices.
