# P1c Authorized Development Calibration: Execution and Measurement v1

Maintainer: Yaxin ZHENG.

Paper: Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models.

First submission target: PLOS ONE. This is exploratory development evidence, not independent confirmation or publication readiness.

## Researcher decisions and scientific scope

The original 77-entry supplied review bundle was preserved. The compatibility registration verified 74 existing scoped confirmations, including 48 original `ACCEPT_WITH_LIMITATIONS` history decisions. Their original label, explanation, limitations, confirmation and source hashes remain intact. A derived operational category restricts use to the already approved text-package estimand; it does not claim that the researcher independently selected a new label. There were no unresolved compatibility mappings and no repeated approval of those 74 items.

The researcher subsequently explicitly approved the evaluation/statistical policy, the P1c addendum and exactly 72 real CPU requests. [Separate approval registration](validation/p1c/authorization_v2/researcher_consolidated_approval_v1.json) binds the original review registration and exact policy documents. [Provenance](validation/p1c/authorization_v2/approval_provenance_v1.json) preserves the actual user statement and distinguishes software registration time from an unavailable human approval timestamp. Source proposal files and the earlier pending packet retain their historical status; they are not current gate failures.

| Approved object | SHA-256 |
|---|---|
| Frozen 72-request manifest | `b0cf330d9dd5f7b59a186dc298c477a97bd86e06a29209805989a9f399fde02b` |
| P1c addendum proposed v2 | `51d1987e2e91e2f4e72735304380e3f4442f418b731e972828677d24b7b96f55` |
| Explicit three-item approval registration | `aa1cf2a59a9fea995a3aa3300952bdd16b89bd4ed745d5567e5e7a18e4d0faca` |

All R/T contrasts concern the implemented historical text packages. R also changes topic, predicates, lexical/entity cues; T changes dates, intervals and attribute values. No pure relevance, temporal mechanism, stale-answer competition or internal mechanism is identified. N_history is **LENGTH_MATCHED_DIAGNOSTIC_CONTROL / DIAGNOSTIC_ONLY**, not validated semantic neutrality. H_none is shorter. Protocol v1.1, the unadopted v1.2 proposal, earlier observations and annotations remain unchanged.

## Execution and preflight

The authorized inventory was executed once: **72 attempts, 72 successful raw responses and normalized results, zero failed requests**, in one append-only run. No retry, resume, parameter change, extra completion or new wave occurred. The run is `results/p1c_calibration/development_v1/runs/20261014T062351-c6724f67d31c4f7e83341957adcc42a4`.

Model: pinned Qwen3.5-2B-Base Q4_K_M. Backend: llama.cpp b11573 (`0f701c882`), CPU only, four threads, context 4096, output cap 96, temperature 0, top-p 1, decoding seed 42, original condition-order seed 715001. Exact prompts and token arrays were supplied from the frozen manifest; the existing transport configuration did not re-render them. Original order, 12 cases, six speakers, six cells and answer references were retained.

The final preflight verified explicit authorization, all 45 source pins, model/backend/tokenizer/DLL hashes, evidence/reference equality, routing, source snapshots and context capacity. There were 10,780,135,424 free bytes at the recorded preflight, exceeding the 1 GiB raw-log reserve. On the owned pinned server, all 72 complete prompts were tokenized and their actual arrays matched the frozen arrays **before any completion**. Postflight model/backend identity was unchanged.

The run preserves exact HTTP response bytes, decoded text, input/output token IDs, native stopping, latency, failures, prompt hashes, complete prompts, parser traces, excluded tails, code snapshots, Git SHA and dirty status. The immutable claim limits total attempts to 72; an uncertain attempted send cannot be retried automatically. Resume supports only the original unattempted suffix under the identical claim.

There were 6,898 generated tokens. Summed request latency was 1,156.563682 seconds (19.28 minutes); the captured execution command took 1,167.763955 seconds including setup and shutdown. These are actual local observations, not clean CPU benchmarking: light repository/documentation work ran concurrently. Peak RAM was not measured.

## Integrity reconstruction

[Machine-readable reconstruction](validation/p1c/calibration_v1/measurement_v1/execution_integrity_v1.json) binds every request to its raw response and frozen structural result. Two independent offline reconstructions agreed exactly. All 72 ordered completion payloads, raw HTTP bodies and tokenizer arrays reconciled. Current execution source and saved source snapshots match their claim hashes. Dataset, model, backend and tokenizer checks passed. No historical response was regenerated or rescored.

An initial offline audit invocation stopped because a historical tokenizer-only helper deliberately rejects journals containing completion requests. No analysis files were produced in that attempt. The adapter now passes that helper only the tokenizer-route view while separately checking every authorized completion payload and raw body. The complete immutable journal and helper were unchanged. The failed diagnostic and corrected successful command are retained; this was an offline audit integration issue, not a generation or scientific-input failure.

## Frozen response structure and termination

| Outcome | Count / 72 | Percentage |
|---|---:|---:|
| COMPLETE | 0 | 0.00% |
| TRUNCATED | 0 | 0.00% |
| CROSS_TURN | 64 | 88.89% |
| AMBIGUOUS | 8 | 11.11% |
| Identifiable first reply under the frozen policy | 64 | 88.89% |
| Native token-budget termination | 70 | 97.22% |
| Native EOS termination | 2 | 2.78% |

All eight AMBIGUOUS records contain an unrecognized section heading in the candidate first span: PC010, PC023, PC033, PC039, PC042, PC044, PC054 and PC063. Their labels and spans remain frozen. PC010 and PC023 ended with native EOS; the other six reached the token budget. Examples include `USER QUESTION:` and `RECENT CONVERSATION:`. These are observable continuation/boundary hazards, not automatic factual errors. No alternate parser has been applied.

All 64 CROSS_TURN outputs contain an identifiable first span followed by generated dialogue. The high budget-saturation rate does not show that all first replies are incomplete: the cap frequently terminates the additional continuation. Conversely, zero TRUNCATED classifications does not certify semantic completion. Native `truncated=false` is an input/context transport flag, not a semantic completeness judgment.

| Condition | CROSS_TURN | AMBIGUOUS | Denominator |
|---|---:|---:|---:|
| R0T0 | 11 | 1 | 12 |
| R0T1 | 11 | 1 | 12 |
| R1T0 | 9 | 3 | 12 |
| R1T1 | 10 | 2 | 12 |
| N_history | 11 | 1 | 12 |
| H_none | 12 | 0 | 12 |

Single retrieval contributed 24 CROSS_TURN and no AMBIGUOUS records; multiple components contributed 18 and 6; route integration contributed 22 and 2. Each family has four cases from only two speakers. All eight ambiguous spans are concentrated in Elian Moss and Nora Finch. Family, speaker, content and wording are not independently separated by this distribution.

## Exploratory structural comparisons

The [full structural analysis](validation/p1c/calibration_v1/measurement_v1/structural_contrasts_v1.json) reports all 16 registered contrasts for six separate structural/transport indicators. [Case-level tables](validation/p1c/calibration_v1/measurement_v1/structural_case_contrasts_v1.csv) retain every case. Whole-speaker bootstrap uses 10,000 draws and seed 715004; all calculations were repeated with exact agreement. These are structural observations only, not semantic condition effects.

The table below uses the AMBIGUOUS indicator. Positive values mean more frozen ambiguity, not more factual errors. Fixed-factor comparisons lead the interpretation.

| Contrast | Paired estimate, pp | Exploratory cluster percentile interval, pp |
|---|---:|---:|
| R1T0 − R0T0 | +16.67 | [0.00, 50.00] |
| R1T1 − R0T1 | +8.33 | [0.00, 25.00] |
| R0T1 − R0T0 | 0.00 | [0.00, 0.00] |
| R1T1 − R1T0 | −8.33 | [−50.00, 25.00] |
| R average package effect | +12.50 | [0.00, 29.17] |
| T average package effect | −4.17 | [−25.00, 12.50] |
| R×T unscaled difference in differences | −8.33 | [−50.00, 25.00] |
| N_history − H_none | +8.33 | [0.00, 25.00] |

All comparisons have 12 structurally evaluated cases and six clusters; structural ambiguity itself is observed rather than omitted. R×T leave-one-speaker-out estimates range from −20 to +10 pp, reversing sign. R estimates range from +5 to +15 pp. Such sensitivity and only six purposive clusters prohibit population significance claims. Degenerate intervals reflect observed constant contributions, not proof of zero population uncertainty. All diagnostic/transport endpoints and comparisons are disclosed rather than significance-selected. No empirical ICC was estimated.

## Semantic review and analysis readiness

The [review guide](P1c_calibration_semantic_review_guide_v1.md) links separate Stage A and Stage B files. Original prospective IDs PC001–PC072 and presentation order/seed 715005 are retained. Stage A hides conditions, factor assignments, structural status, full continuation and automatic correctness predictions; its human fields are blank. Stage B exposes boundary evidence only for the subsequent audit. The separate analyst mapping is not encryption. Textual cues and prior analyst knowledge limit blinding.

All 72 records remain eligible for factual, temporal, relevance, coherence, task success, component coverage and semantic completeness; structural status also applies to all 72. Persona Fidelity is N/A for all 72. **Official semantic judgments: zero; missing judgments: 72 for each semantic axis.** The 64 identifiable spans are an extraction-coverage count, not a factual evaluation count. The eight ambiguous spans remain in the denominator and require explicit disposition, not fabricated replacement replies.

[Optional AI-assisted observations](validation/p1c/calibration_v1/review_support_v1/AI_review_observations_UNCONFIRMED_v1.csv) cover all 72 items with exact model quotations and trusted fact references. They flag candidate date/entity mismatches, attribute wording and boundary issues. They supply no formal endpoint ratings, no human decisions and no semantic condition estimates. Their provenance explicitly discloses access to wider design/run information; this is not independently blinded annotation. Preserve initial Stage A work before opening assistance.

The scalar analysis engine already implements original signed weights, equal case averaging within speaker, whole-speaker resampling, leave-one-speaker-out diagnostics, assessed-only sensitivity and unknown-outcome bounds. Unknown cells are never silently dropped or reweighted. Formal semantic effects require validated annotations, an immutable annotation snapshot and only then the treatment join. Keep Correct, Incorrect, Unverifiable, N/A, Missing, delivery and completeness distinct. Preserve the original four endpoints and ordinal distributions; do not substitute a component-matching success score.

## Algorithmic Opportunity Assessment

### 1. Observed Failure Modes

The reproducible P1c technical evidence shows persistent cross-turn continuation and eight header-related extraction hazards. Optional item notes point to potentially wrong dates/entities and semantically recoverable content inside ambiguous spans; those semantic suggestions remain unconfirmed. Existing P1b researcher-confirmed development labels and the separate literal-component diagnostic show that mentioning a reference value can coexist with a promise, alternative list or incomplete answer. None identifies a causal history-selection mechanism by itself.

### 2. Existing Methods and Published Prior Art

The [updated primary-source comparison](related_work_novelty_matrix_monitor_v1.md) records direct overlap with LongMemEval time-aware retrieval/structured reading, What to Admit and How to Present admission/rendering decomposition, FPPS persona–factuality steering, AO-DA separation, MemConflict and STALE/CUPMem validity/conflict handling. CoVe and RARR are applicable verifier/revision baselines. Turn templates, native stopping, stop sequences and first-span extraction are known engineering, not new algorithms. Preprints remain distinguished from verified conference publications; unverified appendix/implementation details are marked.

### 3. Potential Algorithmic Improvements

Boundary detection that handles section-heading continuations is an incremental diagnostic candidate, not an authorized replacement for response_status_v1. A candidate answer-act/component verifier must distinguish an assertion from a promise and multi-entity alternatives. Time-aware evidence selection must preserve historical-query answerability rather than always selecting the newest fact. Evidence-priority/persona-separation methods need a fidelity measurement and applicable published baselines. No original algorithm has been established.

The bounded offline component baseline on all 192 P1b outputs produced 110 true positives, 5 false positives, 0 false negatives and 77 true negatives against the existing FULL_ANSWER coding. Five false positives span three cases: two partial replies and three promises without final answers. Gold answer strings are oracle information, not a deployable verifier. No exception was fitted to fix these failures. This remains Level 0 engineering evidence; details and all adverse cases are in the [nongated research report](P1c_nongated_research_progress_v1.md).

### 4. Validation Feasibility

First obtain valid semantic and boundary dispositions for this run. Any revised parser must be a separately versioned sensitivity analysis, preserve raw spans and show false splits as well as recoveries. A generation-level boundary or Instruct comparison needs its own frozen configuration and authorization; it cannot silently replace this Base run. A verifier prototype requires separate development templates and independent labels, comparison with simple/structured/published baselines, ablation, latency and fidelity accounting. The six-cluster R/T calibration cannot validate an interaction-aware algorithm.

### 5. Publication Value

The present contribution is an auditable development measurement package and restricted structural comparison, not a new memory mechanism or validated algorithm. PLOS ONE submission still requires a defensible common estimand, credible annotation, independent cases, useful precision and appropriately scoped model sensitivity. AI-assisted researcher confirmation does not create inter-annotator reliability. Independently reviewed material would strengthen measurement evidence. Null and adverse outcomes remain valuable; neither execution success nor a higher error count establishes publishability.

## Next scientific action and limits

The next dependent action is the 72-item semantic review with separate disposition of the eight ambiguous units. Existing experiment approvals are complete and will not be reopened. No additional inference is authorized by completion of this run. After valid ratings are frozen, compute the approved package contrasts and assess whether condition-specific missingness changes interpretation. Keep all cases and conditions, including failed or unscorable semantic outcomes.

Prioritize measurement validity before sample expansion. A subsequent independently configured Instruct or boundary comparison may be useful if semantic coverage remains materially affected; Base/Instruct differences include template/configuration as well as post-training. A stale-answer-competition experiment remains a separate prospective question. No new wave, held-out dataset tuning, training, algorithmic generation or public release occurred.

## Verification records

The full automated suite and preservation audit are recorded in [final verification](validation/p1c/calibration_v1/closeout_v1/verification_v1.json). Execution, initial offline diagnostic failure, corrected reconstruction and all test command outputs are preserved there as engineering evidence. The original runtime records retain actual timestamps; no human review times were invented. Git HEAD remains `ab588dd973dfbb3743279d15bf1f72b8909efa6b`. All changes remain in the working tree for researcher review; no commit, push or author-identity change was performed.
