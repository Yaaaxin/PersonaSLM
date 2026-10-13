# P1 Controlled Factorial Pilot - First-Wave Report

Maintainer: Yaxin ZHENG. Paper: **Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**. Research Protocol v1.1 is unchanged. P0 remains accepted. P1 is authorized exploratory development; P2-P6 have not started.

## Execution decision and scope

**The first bounded wave completed 96/96 real CPU generations: 12 cases x eight factorial cells.** No mock responses, external inference service, neutral-control generations, retries or remaining-case expansion were used. Execution/instrumentation pass; semantic outcome coverage is partial and new control review is OPEN. This is not confirmatory evidence of persona benefit, harm, interactions or novelty.

The [frozen plan](P1_experiment_plan.md), [manipulation report](P1_manipulation_validation.md), [design snapshot](validation/p1/wave1_design_v1.json) and [wave manifest](validation/p1/wave1_manifest_v1.json) predate the first response. Full source and dataset bytes, Git dirty state, randomized order and prompt hashes are retained. The starting and frozen Git commit is `ded2ab28af9b9b7b5afd303221672424350c5106`; the wave ran with explicit uncommitted P1 development changes, not the clean commit alone. The frozen plan was not changed after outputs.

## Dataset and experimental units

Author 12 fictional English speakers with six style categories and two same-intent realizations each, and four scenarios per speaker: current residence update, stable membership fact, nonfactual welcome, and time-sensitive residence follow-up. The material contains 48 development cases; this wave selects one per speaker and three per family before generation. Eight responses from a speaker are correlated repeated observations. This is 12 speaker-case units, not 96 independent people or a confirmatory sample.

All C0-C7 cells preserve trusted evidence, current question, fixed preceding context, evidence location, decoding and evaluation. S/F/H additions are correctly routed across all 384 planned prompts. History contains a true old residence with a closed validity interval, while current evidence contains the new residence. Supplementary possession facts contain neither the required city nor membership answer. No private or real-speaker conversations were used. Style remains nested in speaker, and historical relevance co-varies with task family; these limits prevent isolated wording/relevance mechanisms.

## Model, tokenizer and CPU evidence

| Item | Actual setting or evidence |
|---|---|
| Model | Qwen3.5-2B-Base Q4_K_M; third-party GGUF, same accepted P0 artifact |
| Model SHA-256 | `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` |
| Backend | llama.cpp b11573 / 0f701c882 |
| Executable SHA-256 | `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| CPU observation | AMD Ryzen 7 PRO 5850U, 8 physical cores / 16 logical processors, independent CIM query |
| OS observation | Windows 10 Professionnel, 10.0.19045, 64-bit |
| Memory observation | OS-visible total 12,698,714,112 bytes; free 2,050,208 KiB at the recorded query. Physical DIMM installed capacity was not independently measured |
| Runtime | Inference/batch threads 4/4, context 4096, offloaded 0/25 layers; observed server log agrees with configuration |
| Decoding | temperature 0, top_p 1, seed 42, n_predict 96, stop [], cache_prompt false, stream false, return_tokens true |
| Prompt / policies | transcript_base_v1; response_status_v1; separate_axes_policy_v1; p1_endpoint_routing_v1 |
| Tokenizer | Loaded GGUF native `/tokenize`; add_special true, parse_special false, with_pieces false |
| Inputs | 129-217 tokens; all 96 re-tokenized arrays match the frozen arrays; evaluated counts agree; context truncation false throughout |
| Returned IDs | Output IDs available for all 96 responses and agree with output counts. Evaluated input IDs are not echoed; their array equality cannot be independently asserted from counts |

One owned server slot receives complete prompt-ID arrays; prompt cache reuse is disabled consistently. The process is not restarted per condition. Exact seeds are not a guarantee of identical outputs on other hardware/builds. Pinned binary identity does not independently establish faithful equivalence of the third-party quantization to upstream weights; the accepted provenance limitation remains.

## Raw output and response structure

| Structural status | Count | Share of all 96 |
|---|---:|---:|
| COMPLETE | 0 | 0.00% |
| TRUNCATED | 17 | 17.71% |
| CROSS_TURN | 78 | 81.25% |
| AMBIGUOUS | 1 | 1.04% |

All 96 raw outputs are nonempty. Native termination is length limit for 95 and EOS for one; generated tokens total 9,148. The EOS response has 28 tokens; the other 95 have 96. Backend termination is separate from the research response-status classification. COMPLETE requires independent completeness evidence under the frozen policy; zero COMPLETE labels do not prove that all first replies are semantically incomplete.

All 96 first-reply/prefix spans are mechanically identifiable, with offsets and excluded continuations saved. Every A/B/D response (72/72) is CROSS_TURN. Family C has six CROSS_TURN, 17 TRUNCATED and one AMBIGUOUS response. The 17 TRUNCATED outputs visibly start a `<think>` segment without a closing marker. These are generated raw text observations, not proof of the model's training identity or internal reasoning mechanism. The parser did not silently remove them or extract an imagined final answer.

For example, `p1_speaker_11_C__C1` reaches EOS after a welcome mentioning Chester; its completeness and adherence to the no-biographical-claims request require review. `p1_speaker_04_D__C3` begins with a supported-looking residence sentence, then invents a street address in an additional generated turn. The continuation is preserved but not silently promoted into the fixed primary reply unit. No contact/address strings in these fictional generated continuations are verified real-person data. The [96-item response packet](validation/p1/output_review_v1.csv) enables independent assessment without condition/model/automated-score columns; a separate administrator key exists. No human review or agreement is yet recorded.

Observed response latency: minimum 3.743 s, median 9.418 s, mean 9.428 s, maximum 10.914 s. These are actual client-observed latencies from a shared workstation with concurrent documentation work, not an isolated hardware benchmark or causal condition timing comparison. Native backend timings are retained per response.

## Reliability coverage and frozen scores

Each condition has 12 received responses, nine factually eligible cases, six in the bounded residence-grammar scope, three stable-fact cases requiring human review, and three factual Not Applicable cases. Temporal eligibility is six per condition; relevance/coherence eligibility is 12 each. No C0-correct filtering or structural-status exclusion was applied.

| Condition | CROSS_TURN | TRUNCATED | AMBIGUOUS | Correct | Incorrect | Unverifiable | Not Applicable |
|---|---:|---:|---:|---:|---:|---:|---:|
| C0 | 10 | 2 | 0 | 0 | 0 | 9 | 3 |
| C1 | 9 | 2 | 1 | 1 | 0 | 8 | 3 |
| C2 | 10 | 2 | 0 | 0 | 0 | 9 | 3 |
| C3 | 9 | 3 | 0 | 2 | 0 | 7 | 3 |
| C4 | 10 | 2 | 0 | 1 | 0 | 8 | 3 |
| C5 | 10 | 2 | 0 | 3 | 0 | 6 | 3 |
| C6 | 11 | 1 | 0 | 4 | 0 | 5 | 3 |
| C7 | 9 | 3 | 0 | 4 | 0 | 5 | 3 |

Across 72 factually eligible responses, the frozen outputs are 15 Correct, zero Incorrect and 57 Unverifiable. Of the latter, 24 are B-family responses deliberately awaiting human evaluation; 33 arise within the 48 A/D residence responses. Temporal: 48 eligible, zero human-evaluated, 48 pending. Relevance/coherence: 96 eligible each, zero human-evaluated, 96 pending each. These are unavailable effect estimates, not null semantic effects. Persona Fidelity remains separate and unscored.

**A central measurement limitation is condition-dependent grammar coverage.** The [additive lexical diagnostic](validation/p1/measurement_coverage_diagnostic_v1.json) preserves all 48 A/D spans and original labels. Fifteen exactly follow the simple current-city sentence; 33 append the source's valid-from date. The latter remain Unverifiable in the frozen `english_residence_claim_audit_v3` grammar. For example, the C0 first reply for `p1_speaker_01_A` includes the valid-from suffix and receives Unverifiable, whereas C1 omits the suffix and receives Correct. Both visibly name the source's expected city. This post-output string inventory is not an independent human judgment, new score or revised evaluator. Original scores and applicability remain intact.

Therefore zero detected Incorrect responses is not perfect factual accuracy; the apparent increase in recognizable Correct labels is not established factual improvement. Unverifiable is neither incorrect nor correct. B membership responses were never sent to the residence checker. Nonfactual C outputs remain factual Not Applicable even when the model inserts biographical material; adherence belongs in the predeclared relevance/coherence review rather than an output-dependent eligibility change.

## Paired and factorial descriptive contrasts

The primary structural denominator is all 12 paired speaker-cases. Difference units below are percentage points for binary structural indicators. All COMPLETE contrasts are zero under the current absence of semantic-completeness judgments.

| Simple contrast | CROSS_TURN | TRUNCATED | AMBIGUOUS | Mean generated-token difference |
|---|---:|---:|---:|---:|
| C1-C0 | -8.33 | 0.00 | +8.33 | -5.67 |
| C3-C0 | -8.33 | +8.33 | 0.00 | 0.00 |

Both nonzero simple structural changes are confined to `p1_speaker_11_C`. C1 changes a cross-turn reply into the EOS/AMBIGUOUS reply; C3 changes it into a length-censored reply. These are not uniformly beneficial or harmful changes. Across A/B/D the observed structural categories are saturated CROSS_TURN in every cell, yielding zero within-family structural contrasts; this does not establish equivalent semantic quality.

| Structural outcome | Average S | Average F | Average H | S x F | S x H | F x H | S x F x H |
|---|---:|---:|---:|---:|---:|---:|---:|
| CROSS_TURN | -4.17 | +4.17 | 0.00 | -8.33 | 0.00 | 0.00 | -33.33 |
| TRUNCATED | +2.08 | -2.08 | +2.08 | +12.50 | +4.17 | -4.17 | +25.00 |
| AMBIGUOUS | +2.08 | -2.08 | -2.08 | -4.17 | -4.17 | +4.17 | +8.33 |

Average main effects equally average four opposite-factor comparisons; two-way entries are differences-in-differences averaged over the third factor, and the three-way entry is their difference. They are not simple C1-C0/C3-C0 contrasts. Large high-order values here reflect sparse category changes in only three family-C speakers; they do not establish population interactions. [Analysis JSON](validation/p1/wave1_analysis_v1.json) retains all paired values, observed ranges, family strata and denominators. No significance test, equivalence claim or causal-mechanism inference was performed.

Factual transitions are preserved separately: C1-C0 has one Unverifiable-to-Correct transition; C3-C0 has two, among nine eligible paired cases. Grammar coverage prevents interpreting these as accuracy effects. No temporal, relevance or coherence effect is estimated without annotations. C1-N_style and C3-N_history were not executed. H1 has mixed sparse structural observations; H2 cannot be evaluated semantically; H3 motivates measurement diagnosis; H4 is confounded with speaker/task; H5 has descriptive family differences but insufficient separation of family and historical relevance. None is confirmed.

## Neutral controls and scientific identification

All 24 prepared comparisons have exact final-prompt token equality, selected from the bounded predeclared pools without output-based optimization. [Review materials](validation/p1/control_review_v1.csv) remain blank. N_style compares style information to explicit absence of style information under matched wrapper/length; it is not C0-equivalent. N_history compares old residence dialogue to unrelated coherent dialogue under matched format/length; topic relevance, factual content and temporal relationships remain different. Neither comparison identifies a pure mechanism. Human semantic review and any necessary resolution are required before neutral generation.

C1-C0/C3-C0 measure total operationalized context packages. Shared task-sufficient trusted evidence distinguishes Track A from knowledge-utilization experiments; Track B was not executed. The wave cannot separately manipulate historical relevance, temporal status and presentation, nor prove target-speaker style adoption. Synthetic template simplicity, one small Base model, one seed, quantization, output cap, shared workstation and partially confounded speaker/style/family allocation limit generalization.

## Reproducibility, errors and engineering verification

Exact commands and actual UTC timestamps are retained in the engineering capture directory `results/p1_wave1/development_v1/engineering`; immutable run journals are separate. Preparation journal: `results/p1_wave1/development_v1/runs/20261013T065000-5b7eb2b7a3d64b29945f557bdf2abb59`. Generation journal: `results/p1_wave1/development_v1/runs/20261013T065228-971f93c4c1434254a5298dde72dd9061`.

Each actual response retains raw native HTTP bytes, text, token arrays/counts, prompt/source/data hashes, native stop/timing fields, first-span/excluded-tail operations, separate-axis labels and error status. The 909-event generation chain and all 96 native inputs/completions were audited; saved inputs and evaluation outputs reconstruct twice identically. The preparation journal binds all 720 native tokenizations. Existing P0 journal inventories are byte-checked separately, not overwritten. [Verification](validation/p1/verification_v1.json) and [delivery evidence](validation/p1/delivery_v1.json) record preservation, pinned hash checks, tests, file inventory and command outputs.

Full suite: **401 passed, zero failed, zero warnings reported; exit 0; pytest 18.08 s**, captured process 18.663 s. Before generation, 384 tests passed twice; the second check followed preflight/snapshot hardening. The final suite includes 36 new P1 tests covering dataset/routing invariants, scope-aware evaluation, factorial formulas, resume safety, review validation and descriptive analysis. Existing policies/tests were not weakened.

Recorded engineering issues: a malformed initial file-add patch was rejected before writing and corrected; the first hardware CIM query was denied by sandbox permissions, then succeeded through approved read-only execution; the blank review master was intentionally rejected by the importer. No inference failure, retries or adaptive model/template change occurred. Additional final offline verification records any separate audit-tool issue without rewriting successful experimental evidence. Frozen native artifacts retain original machine-recorded paths where present; narrative links use project-relative paths. No credentials, private chat dataset or model binaries are added to source control.

## Novelty and next-wave recommendation

The [verified literature assessment](P1_novelty_assessment.md) documents direct overlap with persona robustness, personalized hallucination, cue variation, structural context interference, digital twins and long-term conversation studies. Factorial terminology, a 2B model or CPU execution are not original contributions. This wave establishes a reproducible feasibility observation and exposes a measurement-coverage boundary; it does not establish an unprecedented phenomenon or a persona reliability mechanism.

**Recommend option D first: investigate structural/measurement failures and complete outcome review before expansion.** Use the existing 96-item packet to assess first-reply completeness, supported meaning, temporal handling and task adherence, preserving frozen scores. If extending automatic grammar, develop a new version on independent examples and validate a separate holdout; do not tune and silently rescore this wave. Complete the 24 control reviews before any matched-control requests. Resolve intended style-adoption/third-person task interpretation before stronger fidelity claims. An alternative model/template requires a separately frozen later arm and researcher decision.

Do not automatically execute the remaining 36 cases. This recommendation does not authorize another arm or later phase. The current delivery is a completed bounded inference wave with usable structural measurements, partial semantic measurement, documented negative/null observations and open human review.
