# P1b Model Arm Comparison — Proposed v1

Maintainer: Yaxin ZHENG. No model launched or downloaded. Protocol v1.1 and all historical settings/results remain unchanged. The v1.2 r1 proposal is not adopted.

## Recommended sequencing

**First assess the new task bank with human evidence checks; if approved for inference, use the pinned Base model for the bounded calibration. Do not initially double the experiment by default.** The observed problem is a factual/temporal ceiling, not an inability to score all factual first replies:72/72 factual and48/48 temporal eligible outputs received confirmed judgments. Therefore, changing both model and task set now would obscure whether discrimination improved because of task design or model configuration.

This recommendation does not privilege Base accuracy, require natural EOS on every reply, or assert that Instruct is unnecessary for eventual generalization. It chooses the least confounded next feasibility question. Instruct may be more informative than adding more Base cases **if new supported tasks become semantically unassessable owing to incomplete/ambiguous replies**, or when testing an independently justified configuration-boundary hypothesis after task calibration.

## Arm comparison

| Option | Information gained | Required controls and limitations | Cost / current readiness |
|---|---|---|---|
| Base only, new24 cases | Whether controlled evidence reasoning yields measurable variation under the established configuration | P1b evidence is a new ledger format; no pure difficulty claim from old/new accuracy. Same model, decoding and policies; no answer-based prompt revisions |192 requests only if later approved; historical-rate proxy30.2minutes, new latency unknown |
| Instruct only | Whether a dialogue-trained configuration permits more usable response units | Cannot isolate task redesign from model/template differences; lacks paired new-material Base baseline | New artifact/provenance/template/context validation required; CPU cost unmeasured |
| Both on the same new cases | Paired configuration sensitivity while preserving all eight cells per arm | Model, post-training, template, special tokens and possibly training lineage differ; not a pure post-training experiment |384 total requests, not authorized; second-arm latency cannot be assumed equal |
| Same Base, separately varied boundary/template | Whether measurement-unit behavior depends on presentation | Requires a separate frozen arm; no tuning to the same scored outputs; may duplicate earlier diagnostics | Additional cases/arms only if a clear unresolved measurement question warrants them |

## Pinned Base reference

Qwen3.5-2B-Base, third-party Q4_K_M GGUF; SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`.

llama.cpp b11573, commit `0f701c882`; executable SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`.

Historical CPU settings:4 threads,4 batch threads,4096 context capacity, zero GPU layers,96 output tokens, seed42, temperature0, top_p1, no custom stop list, reset/cache policy as recorded in Wave1. File integrity was rechecked offline. Binary identity does not independently prove faithful quantization of official upstream weights. The original P0 hardware observations and model lineage report remain the evidence; no new CPU inference measurement occurred.

Future Base prompts would use the explicitly versioned `p1b_transcript_proposed_v1` construction, not overwrite `transcript_base_v1`. Exact input token counts and context fit are pending. Keep96 output tokens unless the researcher approves a separately frozen budget rationale before generation; do not raise the cap until the desired persona result appears. A concise requested answer does not guarantee the Base model will avoid deliberation or continuation.

## Instruct arm requirements, if later authorized

Select a publicly documented same-family, comparable-size artifact only after confirming actual availability, upstream lineage, license, tokenizer, quantization and template. **No exact Instruct binary, revision, hash or performance is invented here.** Pin them before execution. Use its documented native chat template and special-token policy, recording rendered prompt bytes/IDs, output budget and inference settings. Do not apply the Base transcript automatically.

Within each arm keep the shared evidence/question/context and S/F/H routing identical by case. Across arms hold underlying semantic messages and answer keys constant, report rendered token lengths, and treat template as part of the configuration package. New neutral matching is per-arm; Base token equality does not transfer. The eight-cell responses remain paired within case and repeated across arms, requiring speaker-clustered analysis with an arm interaction, not independent96/192-observation tests.

A Base/Instruct difference could reflect post-training, altered original weights/data, reasoning policy, template, special tokens or quantization. Native-template performance is a **configuration comparison**, not isolated post-training causality. A template cross-over is an optional later test only if both renderings are valid for the models and the information gain justifies the extra arm. Do not launch a broad model-size/post-training phase under this P1 proposal.

## Measurement and publication gate

Retain the original structural policy even if native EOS names differ; record any compatibility diagnostic separately. Report raw continuations, first-reply semantic completeness, four reliability dimensions and coverage. A lower CROSS_TURN count alone does not mean better factuality. Instruct could still exhibit ceiling effects, uncertainty or instruction violations; no improvement is assumed.

For a narrowly scoped single-configuration empirical claim, two arms are not automatically a journal requirement. Broader claims about small-model reliability or post-training require evidence beyond one configuration. The [publication assessment](P1b_novelty_and_publication_assessment.md) separates that claim-dependent need from an immediate generation quota. The researcher should authorize a second arm only after reviewing the calibrated task/coverage results and the exact question it would resolve.
