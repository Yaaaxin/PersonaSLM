# P1b Real-Inference Readiness — Prepared Calibration v1

Maintainer: Yaxin ZHENG. **Preparation only: PARTIAL readiness, 0/192 generations executed.** Protocol v1.1 remains the formal baseline. The prospective v1.2 r1 is unchanged. P0 and P1 Wave 1 retain their original results, policies and annotations.

## Frozen experimental input

The [calibration manifest](validation/p1b/final_v1/calibration_manifest_v1.json) contains the complete 192 prompt strings and hashes, per-case evidence/question/context/reference hashes, factorial assignments, evaluation applicability, model/backend hashes, decoding, source hashes, Git SHA/dirty status, actual preparation timestamp and explicit order. Its status is `PREPARED_NOT_AUTHORIZED`. A planned-request manifest is not an inference run or a claim of tokenizer success.

- Dataset: [p1b_development_proposed_v2](../data/synthetic/p1b_development_proposed_v2.json), SHA-256 `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6`.
- Allocation: all 24 cases, 12 speakers with two cases each, eight families with three cases each; C0–C7 for every case. No neutral requests. No confirmatory set.
- Order seed: **714001**, separate from decoding seed **42**. One shuffle of the 24 case blocks, then an independent sequential shuffle of C0–C7 within each block using the recorded Python RNG/version. The explicit order, not just the seed, is retained.
- Case-block order: C_L1, D_L3, H_L1, C_L3, B_L3, D_L2, H_L2, F_L2, A_L3, E_L2, A_L2, G_L2, A_L1, B_L1, G_L1, F_L1, F_L3, G_L3, E_L1, D_L1, H_L3, C_L2, B_L2, E_L3. Each has its own eight-condition order in the manifest.
- Template: **p1b_transcript_proposed_v1**, unchanged from the P1b proposal. This is an explicitly new evidence-ledger transcript relative to Wave 1, not a silent edit of `transcript_base_v1` or a claim that their difficulty differences are isolated.
- Factor cells: C0=000, C1=100, C2=010, C3=001, C4=110, C5=101, C6=011, C7=111 in S/F/H order. Same evidence, question, context, answer and configuration within each case/arm.

Source identity is HEAD `d5be4380a7939a8d8bbda13b1bc32a36ae5b1665` plus the uncommitted source hashes/snapshot, not that commit alone. The preparation manifest truthfully records dirty state. Future execution must record its own source snapshot and timestamp, link this immutable input plan and retain any changed runner source separately. A later commit or authorized operational adapter is not a reason to overwrite the plan.

## Pinned backend and execution contract

| Component | Pinned value | Current verification |
|---|---|---|
| Model | Qwen3.5-2B-Base, third-party Q4_K_M GGUF | Local file SHA-256 rechecked |
| Model SHA-256 | `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` | Matches the historical pin |
| Backend | llama.cpp b11573, commit `0f701c882` | Historical version identity and current executable hash |
| Executable SHA-256 | `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` | Matches the historical pin |
| CPU configuration | 4 threads, 4 batch threads, 4096 context, 0 GPU layers | Configuration frozen; no new running-process observation |
| Decoding | temperature 0, top_p 1, seed 42, n_predict 96, stop [], stream false, return_tokens true | Exact match with Wave 1 decoding |
| State | cache_prompt false; each request receives only its frozen prompt | No generated text carried between cells |
| Response policy | `response_status_v1` | Source hash preserved |
| Evaluation policy | `separate_axes_policy_v1` | Historical semantics preserved; new task routing below |

The physical CPU/RAM and loaded-model observations remain the P0 evidence. Binary integrity does not independently establish upstream quantization fidelity. No server was launched to claim a new hardware, tokenizer or throughput observation.

Before any generation, an authorized operational preflight must load these exact artifacts, verify CPU settings and tokenizer identity, and call native `/tokenize` on **all 192 complete prompts**, with `add_special=true`, `parse_special=false`, `with_pieces=false`. Persist returned IDs and raw responses; require `actual input count + 96 <= 4096` without truncation. Token counts/IDs are currently null. Characters, symbolic tokens and old Wave 1 counts are not substitutes. Save preflight in a new linked artifact; do not edit the frozen preparation manifest.

The current `tools/p1_wave.py` execution path is specific to the Wave 1 schema and routing. **It is not a valid P1b run command.** Before execution, a narrowly scoped adapter must consume this manifest and the existing validated CPU backend, preserve IDs/prompts/decoding, perform token preflight and route semantics to the new manual review contract. It must not invoke the old city-only checker on this bank. Offline preparation and import/reconstruction commands are implemented in `tools/p1b_readiness.py`; there is deliberately no execute action in this task. This is an explicit operational readiness gap, not a failed model experiment.

Use new P1b run IDs and immutable segments. Preserve raw response bytes, native reason, generated count, returned output IDs if available, latency, prompt IDs, errors and all attempts. If interrupted, keep the partial segment and resume only uncompleted planned request IDs in the frozen order. A failed attempt is retained alongside a later authorized retry, never replaced. A successful output must not be rerun merely for answer quality. Missing backend output IDs remain missing, with count/response evidence retained.

## Predeclared evaluation applicability and units

The [192-row applicability CSV](validation/p1b/final_v1/evaluation_applicability_v1.csv) and [routing contract](validation/p1b/final_v1/evaluation_routing_v1.json) precede all model outputs. The prospective routing version is **p1b_manual_semantic_routing_proposed_v1**, awaiting researcher approval. The symbolic solver validates stimulus references, not arbitrary generated English.

| Outcome | Eligible cases per condition | Eligible outputs | N/A outputs | Planned assessment |
|---|---:|---:|---:|---|
| Response relevance | 24 | 192 | 0 | Human 1–5, anchors 1 irrelevant, 3 partial, 5 responsive |
| Factual consistency | 24 | 192 | 0 | Human Correct / Incorrect / Unverifiable |
| Temporal consistency | 11 | 88 | 104 | Human Correct / Incorrect / Unverifiable at proposition-specific dates |
| Conversational coherence | 24 | 192 | 0 | Human 1–5 for fixed context; 1 fails continuity/reference, 3 partial, 5 coherent |
| Structural response status | 24 | 192 | 0 | Frozen COMPLETE / TRUNCATED / CROSS_TURN / AMBIGUOUS |
| First-reply semantic completeness diagnostic | 24 | 192 | 0 | Human COMPLETE / INCOMPLETE / UNCERTAIN, separate from structural label |
| Persona fidelity | 0 | 0 | 192 per fidelity axis | No invented reference ground truth; do not score |

There are 11 temporal cases from **nine speakers**, not twelve independent temporal clusters. A_L1–3, B_L1–3, D_L1–3, F_L1–3 and H_L1 are temporal N/A. For past questions, assess whether the claim is valid **at the date it asserts**. The global April 15 reference does not make a correct March statement false. Date selection and reference chains are explicitly supplied to reviewers; arbitrary string overlap is insufficient.

| Observed future response type | Prospective handling |
|---|---|
| Explicit wrong final value or incompatible factual assertion | Incorrect only when contradicted by the applicable supplied evidence; retain cited claim and fact |
| Unsupported value or assertion absent from evidence | Unverifiable, not necessarily false |
| Supported but partial answer | Factual support may be Correct; semantic completeness INCOMPLETE and relevance reduced as appropriate |
| Unfinished reasoning with no assessable answer | Do not infer Incorrect; factual Unverifiable if no supported assessable claim; preserve absence/completeness and rubric notes |
| Correct claims plus an explicit contradictory claim | Incorrect within that factual unit; report mixed claims, rather than scoring only the matching phrase |
| CROSS_TURN with an identifiable first reply | Score the frozen first reply, retain excluded continuation and structural label; continuation alone does not make the reply wrong |
| AMBIGUOUS boundary | Preserve label and unit uncertainty; manual diagnostic/adjudication must not silently replace the frozen extraction |
| Failed request, empty output, unreadable unit or scorer limitation | Keep the eligible row; missing/unknown score with an explicit reason and coverage flag; do not relabel N/A |
| Automatic city grammar cannot score an answer | Scorer coverage failure, not evidence of model failure; manual task-specific scoring required |

Preserve parsed text, first reply, full continuation, native stop reason, parser operations and excluded spans. Neither a stop sequence nor EOS proves semantic completeness. A 96-token stop does not prove factual error. Two/4 ratings represent intermediate cases with notes; freeze any further rubric clarification before reviewing calibration outcomes. Human ratings are absent now. Future annotation must disclose assistance, retain original narratives, hide condition/model labels where possible and avoid invented independence or agreement.

For each axis report eligible, assessed, unknown, missing and N/A counts per condition. **No C0-correct filter; no exclusion of CROSS_TURN/AMBIGUOUS from primary denominators.** Present category proportions over all eligible rows and assessed-only summaries separately. For binary support summaries, keep Unverifiable/missing as unknown: success is bounded by Correct/N and (Correct+unknown)/N. Propagate unknown paired cells through contrast bounds before aggregation. An incomplete response with assessable supported content is not automatically missing. Full ordinal distributions accompany descriptive score differences. No composite reliability/fidelity score.

## Prospective precision, not observed results

The [new precision grid](validation/p1b/final_v1/precision_v1.json) explicitly separates nine contrasts. Simple C1−C0 and C3−C0 use weights +1/−1. S/F/H average four on-minus-off pairs (weights ±1/4). S×F/S×H/F×H average two differences-in-differences (±1/2). S×F×H is the third difference (±1). The interaction conventions are not silently normalized into main effects.

For planning only, let within-case binary outcomes have variance 0.25 and exchangeable correlation r. For a zero-sum contrast w, `sigma_D^2 = 0.25*(1-r)*sum(w^2)`. If case contrasts have speaker ICC rho and eligible cluster sizes m_i, `n_eff = N^2 / [(1-rho)*N + rho*sum(m_i^2)]`; the normal half-width is `z*sigma_D/sqrt(n_eff)`. These are assumptions, **not measured covariance, confidence intervals or power**. The grid varies r=0.2/0.5/0.8, rho=0/0.2/0.5 and unadjusted versus nine-contrast critical values within an endpoint. Nine is a sensitivity illustration, not adoption of a confirmatory testing family. It differs from the old plan's illustrative eight tests (two simple contrasts × four axes), which remains unchanged.

Middle scenario r=0.5, rho=0.2, individual 95% normal planning intervals:

| Contrast | Factual half-width, 24 cases / 12 speakers | Temporal half-width, 11 cases / 9 speakers |
|---|---:|---:|
| C1−C0 | 21.91 percentage points | 30.60 percentage points |
| C3−C0 | 21.91 pp | 30.60 pp |
| Average S | 10.96 pp | 15.30 pp |
| Average F | 10.96 pp | 15.30 pp |
| Average H | 10.96 pp | 15.30 pp |
| S×H | 21.91 pp | 30.60 pp |
| S×F | 21.91 pp | 30.60 pp |
| F×H | 21.91 pp | 30.60 pp |
| S×F×H | 43.83 pp | 61.21 pp |

Factual cluster sizes are twelve twos; temporal cluster sizes are seven ones and two twos. Normal approximations with so few clusters can be optimistic. The r=0.5 example implies simple-contrast variance 0.25; it is not the old plan's discordance q=0.30 assumption. Both are illustrative sensitivities, not conflicting empirical estimates. Ordinal score intervals require a separate score-contrast variance assumption; do not apply the binary table to 1–5 scores.

Each family has only three cases, with one prototype per designed level. Family and level subgroup precision cannot be established from this allocation. Preserve speaker blocks when estimating uncertainty; independently resampling family rows would break clusters because speakers span families. For future balanced data, use a predeclared family-adjusted, speaker-clustered analysis with small-cluster sensitivity or cluster simulation. Structural censoring may depend on treatment and invalidate random-missingness approximations. Report unknown-cell bounds and rater uncertainty separately; increasing sample size cannot repair an invalid rubric.

The [existing larger-allocation plan](P1b_sample_size_and_precision_plan.md) remains prospective. At its separate q=0.30/rho=0.20 assumptions, 24 speakers × eight new cases gives roughly ±12.00pp factual / ±13.86pp temporal simple-contrast half-widths; 48 speakers gives ±8.49/±9.80pp before multiplicity and missingness. These plans require **new independent speakers, names, evidence realizations, answer templates and task materials**, with counterbalanced styles and no promotion of this calibration bank to a confirmatory test. Agree a useful margin and a narrow endpoint/contrast hierarchy before choosing either allocation. Do not scale merely to obtain nonzero persona effects.

## Scientific value and next gates

The bounded calibration asks whether evidence-grounded retrieval, integration, dates, entity references and context can yield assessable variation under one established configuration. A continued ceiling, lower scores, mixed family patterns or structural censoring are all admissible outcomes. Report all 24; do not tune against these outputs and then reuse them as independent validation. Human reference correctness is testable now; actual discrimination is not.

Retain the pinned Base arm first to avoid changing tasks and model simultaneously. A separately versioned Instruct arm becomes useful if meaningful answers cannot be assessed or if a specific configuration-sensitivity question is justified. Base/Instruct differences include template, special tokens, weight lineage and post-training; they do not isolate post-training alone. No second arm is prepared or launched here. The historical latency proxy gives about 30.2 minutes for192 requests, with a declared 1–3× scenario of30.2–90.5 minutes; P1b latency is unmeasured, excluding startup/tokenization/failures and human review.

Actual blockers before real inference are narrowly defined:

1. Researcher validation of the24 stimuli, three revisions and the prospective task-specific scoring/routing contract; resolve any substantive failed checks.
2. A reviewed manifest-consuming execution adapter that preserves the existing backend and policies while bypassing the unsupported city scorer for these tasks.
3. Real pinned-tokenizer/context preflight for all192 prompts, with current loaded-model/CPU verification and saved IDs; stop on any failure.
4. Explicit researcher authorization for this exact bounded192-request run after the above evidence is reviewable. The current request explicitly prohibits inference.

Old neutral-control review is OPEN but does not block this factorial-only calibration. Independent confirmatory data, a new algorithm, perfect EOS, P2–P6 and a new model arm are not additional gates for this task. PLOS ONE requires rigorous methods and supported conclusions and considers null/negative results; this preparation improves those prerequisites, not publication certainty. See [the journal's criteria](https://journals.plos.org/plosone/s/criteria-for-publication).

## Reproducibility evidence

Offline reconstruction verified192 prompts, the dataset, corrections, ordered requests and precision grid; current binary hashes match their pins. Both original Wave1 journals verify (2,278 and909 events),720 saved native tokenizations reconcile,24 old exact matches persist, and3,192 original run files are unchanged. Original96 annotations retain72 factual Correct,48 temporal Correct,79 complete first replies,17 incomplete; frozen structural labels remain78 CROSS_TURN,17 TRUNCATED,1 AMBIGUOUS and0 COMPLETE. These counts are historical, not P1b results.

The [hash inventory](validation/p1b/final_v1/hash_inventory_v1.json) binds prepared artifacts and source files. A local source snapshot and exact command/test capture records are under `results/p1b_readiness/v1/`, intentionally ignored by Git. Public delivery checks record hashes and summaries without exposing local absolute paths or binaries. Archive the local logs/snapshot separately if sharing a reproducibility bundle. A copied source hash list is not evidence of new inference.

Full project test command: `.\.venv\Scripts\python.exe -m pytest -q`. Actual result: **556 passed, 0 failed, 0 warnings reported, exit0; pytest19.71 seconds, captured process20.477073 seconds**. The46 new tests cover independent answers, changed/ambiguous sources, historical dates, factorial order, review tampering/incomplete labels and distinct contrast/precision conventions. The existing510 tests remain. Targeted readiness tests first passed46/46 in1.20 seconds. Full structured captures preserve actual timestamps and stdout/stderr; no generation was launched by these validations.
