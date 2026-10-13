# P1 Controlled Factorial Development Pilot - Wave 1

Maintainer: Yaxin ZHENG. Paper: **Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**. Research Protocol v1.1 remains unchanged. This is authorized exploratory P1 development, not a confirmatory test or authorization for P2-P6.

## Purpose and allocation

Investigate independent and interactive S/F/H prompt-package effects without assuming harm, benefit or interactions. Author 12 fictional English-speaking personas and four scenario families per persona: A current residence update, B stable supported reading-group membership, C nonfactual welcome request, D current residence follow-up after a dated move. These 48 cases are development material, not 48 independent speakers or a power calculation. No real conversations, translated persona data or demographic ground truth are used.

Six style categories each have two distinct same-intent realizations: brevity, formal register, conversational register, plain lexical preferences, separated sentence rhythm and acknowledgment before answering. These cover five requested axes without combining them into a generic persona. Allocation seed 713019 independently permutes names, current cities, old cities, clubs and supplementary possessions. The full material crosses each speaker with all four task families. Style remains nested in speaker; two realizations across different speakers cannot isolate a within-speaker paraphrase effect.

Wave 1 selection is fixed before outputs: for speaker index i=0..11 choose family ABCD[i mod 4]. This selects one case per speaker, exactly three cases per family. Condition-order seed 713042 shuffles speaker/case blocks and independently shuffles the eight cells within each block. This reduces order bias but does not perfectly counterbalance every run position or eliminate thermal drift. No later 36-case expansion is automatic.

## Factor construction and chronology

| Cell | S | F | H |
|---|---:|---:|---:|
| C0 |0|0|0|
| C1 |1|0|0|
| C2 |0|1|0|
| C3 |0|0|1|
| C4 |1|1|0|
| C5 |1|0|1|
| C6 |0|1|1|
| C7 |1|1|1|

S is the named speaker's linguistic description; F is a stable possession unrelated to any required answer; H is an explicitly dated two-turn old-residence exchange. Current residence is valid from the fictional October move onward; the old residence ends the previous day. Membership and possession have separate validity intervals. The dated history is genuinely true in its past interval, not an unannounced simultaneous contradiction. All conditions share the same task-sufficient trusted current evidence, question, recent dialogue, evaluation date and evidence location. Old facts remain source facts but do not replace the current trusted record. History is directly task-relevant in A/D and less relevant in B/C; this overlap between family and historical relevance is a declared confound.

Use unchanged `transcript_base_v1`. Every case includes explicit identity, source language, fact IDs/intervals, expected answer or null, fixed context and endpoint eligibility. Validate all 384 factorial prompts before selecting the frozen 96-request wave. Check exact factor routing, evidence/question/context identity, nonoverlapping incompatible fact intervals, named history speaker and absence of the current expected answer from S/F/H additions. Scripted validation establishes construction invariants; it is not a human manipulation judgment or evidence that a model actually adopts the style.

## Estimands and neutral controls

| Comparison | Permitted interpretation | Residual confounds |
|---|---|---|
| C1-C0 | Total operationalized style package with F=H=0 | Added length, heading, wording and positions; not a pure style mechanism |
| C3-C0 | Total dated-history package with S=F=0 | Length, dialogue format, residence topic, factual content and past time; not isolated temporal conflict |
| C1-N_style | Specific style information versus explicit absence of style information, matched final length and wrapper | Lexical/register and absence-priming differences; not equivalence to C0 |
| C3-N_history | Residence history versus unrelated coherent dialogue, matched length and format | Topic relevance, facts and temporal factual information differ |

Prepare controls for the 12 selected cases only. Freeze 36 single-sentence absence-of-style candidates and 16 two-turn unrelated conversation definitions per case before tokenizer access. Preserve header, insertion position, speaker labels and history date. Select the first zero-difference final-prompt match in fixed order; preserve every attempt and best difference on failure. Do not extend the pool, pad with repeated sentences or inspect model answer quality. Token equality is an engineering check, not semantic approval. New human review remains OPEN. No neutral generation or adjusted contrast may run until the new exact texts receive the required semantic review. Original P0 approvals do not transfer.

## Predeclared exploratory hypotheses

| Hypothesis | Independent variables / contrast | Dependent variables | Support and potential falsification | Coverage, confounds and prior overlap |
|---|---|---|---|---|
| H1: Style effects may depend on history | S x H difference-in-differences, averaged equally over F | Each structural category; factual/temporal categories only where measured | Consistent nonzero interaction supports further study; near-zero estimates weaken it, but low precision does not prove equivalence | All eight cells per speaker; 12 speakers, semantic coverage limited. Length/wording and H content co-vary. Principled Personas; When Personalization Misleads |
| H2: History may affect factual and temporal reliability differently | H contrasts on separately eligible endpoints | Separate factual and temporal judgments | Different paired changes after independent assessment support; similar precise changes would contradict meaningful dissociation | A/D provide six temporally eligible speakers. Temporal annotation required; no automatic temporal labels from city accuracy. When Personalization Misleads; Persistent Personas? |
| H3: Some effects may primarily concern structure | S/F/H simple and factorial contrasts, separate first-span and raw status | COMPLETE/TRUNCATED/CROSS_TURN/AMBIGUOUS; factual categories separately | Structural changes with stable measured content support; only content changes or no robust changes weaken | All 96 responses retained; cap and parser coverage are confounds. Decoupling Logic from Persona directly overlaps |
| H4: Same-category style realizations may differ | Descriptive comparison of the two realizations per category | Paired style changes on each measured endpoint | Divergent changes motivate an independent paraphrase arm; equivalent changes would weaken sensitivity | Two different speakers per category; speaker/task confounding prevents an isolated wording claim in this wave. One Persona, Many Cues, Different Results |
| H5: Effects may vary by task family | Family-stratified within-case contrasts | Structural and applicable reliability outcomes | Heterogeneous paired changes motivate follow-up; uniformly similar changes weaken the hypothesis | Three speakers per family; family, speaker and history relevance are partially confounded. Principled Personas; TwinVoice and REALTALK cover related persona constructs |

Prior-study links and source-verification scope are maintained in the [existing matrix](related_work_novelty_matrix.md) and the subsequent P1 novelty assessment. These are falsifiable exploratory questions, not asserted findings. Adequately precise equivalence would be needed to rule out a meaningful effect; this small wave is not powered for that claim.

## Inference and pre-generation gates

Use local Qwen3.5-2B-Base Q4_K_M, SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; llama.cpp b11573/0f701c882 executable SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. CPU threads/batch threads 4/4, context 4096, zero GPU offload. Native decoding remains temperature 0, top_p 1, seed 42, n_predict 96, stop [], cache_prompt false, stream false, return_tokens true. Seeds specify inputs, not cross-platform determinism.

Before any generation: pass software tests and manipulation checks; freeze dataset/order/all prompts/pool/source/config/plan hashes; verify pinned artifacts and owned backend identity; tokenize using that backend with add_special=true, parse_special=false, with_pieces=false; verify each input plus 96 fits context. Save the immutable wave manifest with exact token IDs. The generation process rechecks every pending prompt/ID before its first completion. Requests are stateless full-prompt submissions, one server slot, cache disabled; this is not a claim that the process is restarted per condition. Input-evaluated counts and truncation flags must agree on every response.

Maximum authorized factorial attempts: 96. No external inference API, model substitution or better-answer reruns. For interruption, preserve the old run and create a new immutable segment using the same frozen manifest. Skip every previously attempted request, even if no response was received; no automatic retry of an uncertain request. Essential instrumentation failure stops the segment and is reported. Outcomes or imperfect style adoption alone do not justify changing stimuli.

## Evaluation and denominators

Keep `response_status_v1` and `separate_axes_policy_v1`. Preserve native response bytes, stop reason, generated IDs where supported, count, raw text, first span, removed prefix and excluded continuation. COMPLETE requires its existing separately supplied completeness evidence; punctuation or a stop marker is insufficient. TRUNCATED is boundary censoring, not automatically a factual error. CROSS_TURN and AMBIGUOUS remain in denominators.

Routing extension `p1_endpoint_routing_v1` is frozen before outputs. A/D use the existing bounded English residence audit on the identifiable first response/prefix, with the explicit display name mapped to the evaluator subject. B membership is never sent to that city checker: eligible factuality is Unverifiable / human review pending. C factuality is predeclared Not Applicable. Temporal consistency is eligible only for A/D and remains awaiting independent semantic annotation. Relevance and coherence are eligible for all and retain blank 1-5 ratings. Correct, Incorrect, Unverifiable and Not Applicable remain separate. Distinguish pending review from evaluated uncertainty using assessment provenance. Fidelity is separate and currently inapplicable because no independent reference behavior/ground truth exists.

Per condition:12 structural/relevance/coherence cases;9 factually eligible cases (6 in bounded automatic scope,3 manual);6 temporally eligible cases. Export shuffled review materials with condition/model/automatic labels hidden and a separate administrator key. Blinding describes packet preparation, not completed blind annotation. No human identities, judgments, times or agreement are invented.

## Exploratory analysis and stopping

Report all four structural-category indicators separately, all factual categories and coverage, response-token counts and latency. Calculate paired C1-C0 and C3-C0 differences per case, retain transitions and full denominators. Average factorial main effects use equal weighting over four opposite-factor combinations. Two-way interactions are difference-in-differences averaged over the third factor; three-way interaction is the difference of those interactions. Do not confuse them with simple contrasts.

Report means, raw paired values and observed ranges without p-values, significance claims or pilot confidence interpreted as confirmatory evidence. Structural contrasts are measurable across12 speakers; factual category-distribution contrasts can describe all9 eligible cases but are not semantic accuracy effects when outcomes are unresolved. Provide the6-case automatic-scope subset separately. Temporal/relevance/coherence effects remain unavailable until annotation. Do not remove cases based on C0 correctness. No clustering-based precision is asserted; one selected case per speaker still has eight correlated cell responses.

After 96 attempts, audit all results and measurement coverage. If structural ambiguity/cross-turn output dominates or semantics remain unresolved, recommend targeted diagnosis and review before expansion. Do not tune the same prompts, automatically add the remaining36 cases, or switch to an Instruct arm. The researcher chooses the next wave. Historical P0 files, frozen evaluations and Research Protocol v1.1 remain unchanged.
