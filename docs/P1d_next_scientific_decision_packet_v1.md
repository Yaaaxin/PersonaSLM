# P1d next scientific decision packet — v1

Maintainer: Yaxin ZHENG. Official paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Status: **main validation NO-GO; one bounded development decision is ready**. No new researcher decision is registered in this packet.

## Completed evidence and scientific decision

The authorized manifest `docs/validation/p1d/final_preparation_v1/format_diagnostic_manifest_proposed_v1.json`, SHA-256 `3f0e68b0fbe4cf5abfeab3bef9f6fbc39460b9219d118500ccc10d6fda121523`, produced exactly 16 successful Base CPU requests, with no failed request or retry. The [engineering report](P1d_format_diagnostic_engineering_report_v1.md), [scientific report](P1d_format_diagnostic_scientific_report_v1.md) and [reproducibility manifest](validation/p1d/format_calibration_v1/reproducibility_manifest_v1.json) retain the evidence and its limitations.

Both arms add the same current-question `User:` marker. Only the registered stop strings differ between the new arms. All eight no-stop outputs reach 96 tokens and are CROSS_TURN. All eight stopped outputs terminate at a registered string after 15–23 tokens; their frozen AMBIGUOUS classification means bounded-reply semantics are uncertified, while a first span is identifiable. Native EOG occurs in neither arm. First-response content is unchanged within all eight pairs after whitespace normalization. No requested answer component is delivered in either arm (AI assessment, unconfirmed). Conventional offline stops reproduce the actual stopped outputs exactly; agreement is not independent boundary accuracy.

This supports continuation control without improved answer delivery, closest to Case B. Operationally it also satisfies the Case C reason **not to expand the current Base configuration**. No format qualified under the predeclared 8/8 complete-identifiable-answer criterion. The previous 144-budget result and its negative hypothesis remain unchanged. No further Base budget or format sweep is proposed here.

## One immediate authorization decision

**Recommended choice: AUTHORIZE_8_INSTRUCT_DEVELOPMENT_REQUESTS_WITH_DOCUMENTED_LIMITATIONS.** Alternative: **DEFER_INSTRUCT_GENERATION**. Neither option adopts a new P1d primary model or authorizes any independent-validation request.

The exact proposed scope is:

| Item | Bound value |
| --- | --- |
| Manifest | `docs/validation/p1d/instruct_preparation_v3/minimal_instruct_smoke_manifest_proposed_v1.json` |
| Manifest SHA-256 | `ba63c30a9868b94b47f8f79dd774ac0627d56113810ffd4db08eb63af0374b91` |
| Data | The same eight previously inspected development cases, H_none only; no independent P1d cases |
| Requests | Eight maximum attempts; no retries; 96 tokens each; maximum 768 generated tokens |
| Model | Qwen/Qwen3.5-2B Instruct candidate, Q4_K_M; distributor `lmstudio-community/Qwen3.5-2B-GGUF`, revision `bb84e11355a036e28f080c7793fa6d22b7c4e344` |
| Local artifact | `models/gguf/instruct_candidates/lmstudio-bb84e113/Qwen3.5-2B-Q4_K_M.gguf` |
| Model SHA-256 | `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc` |
| Backend | Pinned llama.cpp b11573, CPU-only, 4 threads, context 4096; server SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| Decoding | Seed 42, temperature 0, top_p 1, cache_prompt false, native EOG, no custom stops, no warmup, no vision or MTP |
| Template | Pinned official template, SHA-256 `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`, thinking disabled; explicit one-user rendering |
| Input tokens | 1642–1765; all eight native token arrays match the official tokenizer |
| Time bound | 45 minutes; stop on integrity failure or material runtime/OOM failure; preserve partial attempts |

**Material limitation requiring an informed execution decision:** local bytes match the distributor's LFS digest, the official token IDs/merges match, and b11573 reads the vocabulary. The distributor reports quantizer build b8185 but does not bind its conversion to an exact source-weight revision or complete conversion/calibration recipe. Conversion lineage is therefore PARTIALLY_VERIFIED. Tensor execution, actual EOG, RAM, latency and answer delivery are unmeasured. Authorizing this eight-request feasibility test accepts that limited provenance for development only; it does not certify the artifact for confirmatory inference. Full reconstruction from pinned official weights remains an alternative if that limitation is unacceptable.

Approval permits only a final exact-hash/environment preflight and the eight listed completions. Rejection/deferment permits continued offline preparation, including provenance resolution, but no Instruct generation. Do not treat a completed form, download permission or this recommendation as execution authorization. This gate follows the user's explicit reservation of Instruct inference and the existing P1d execution process; it is not an extra software-schema approval.

## Prespecified interpretation after the proposed test

Require 8/8 recoverable, semantically complete task answers with no demonstrated answer-losing cut for the narrow feasibility criterion. Separately report factual/temporal labels, required components, persona fidelity and uncertainty; do not choose a format using favorable history effects. AI proposals remain distinct from human confirmation. Passing this criterion supports further independently authorized all-condition measurement validation only. Failing preserves NO-GO and localizes the problem without spending the main cohort. Eight previously examined cases cannot establish independent model suitability or reliability.

## Prospective model-policy alternative — not adopted

The adopted target remains 144 speakers, 288 paired cases, 1728 Base requests and 288 matched Instruct requests. The latter covers 24 speakers × two cases × six conditions; it cannot estimate full-cohort model-by-factor interactions. No new primary execution manifest is frozen because adequacy is unresolved.

If an Instruct configuration subsequently passes development measurement checks, a separately specified amendment could propose an Instruct primary six-condition cohort on the same approved case allocation. A matched Base comparison would remain a separately justified configuration study, potentially deferred if its outputs cannot measure the intended endpoints. This is a conditional alternative, not an adopted reversal of the current 1728/288 allocation. An exact model/template, budget, baseline scope, estimand treatment and renewed precision assessment must precede that amendment. Model, template and quantization differences must be interpreted jointly, not as pure post-training effects. The original S/F/H programme remains the central research programme.

## Remaining main-validation GO conditions

| Domain | Current status and exact resolution | Mandatory human decision |
| --- | --- | --- |
| Model/output adequacy | NO-GO: Base format arms both deliver zero complete answers provisionally; Instruct has no generation evidence. Establish a scientifically measurable configuration on development data. | Any new primary model/output policy amendment and exact execution scope |
| Material and controls | 288 AI VALID_WITH_LIMITATIONS proposals; 288 token-matched procedural controls remain diagnostic. Use the existing stratified 64-case/64-control review packet; version any consequential defect. | Scientific adoption/corrections, not duplicate engineering approvals |
| Measurement | Separate metric contracts and blank independent forms exist. Sixteen new and 144 previous semantic proposals remain unconfirmed; independent human reliability is unestablished. Complete prospective measurement validation and retain uncertainty. | Genuine semantic adoption/adjudication where required; no fabricated second reviewer |
| Independence and statistics | 144 nominal speakers, 16 abstract templates, four shared construction ancestors. Retain registered contrasts and simulations; define fixed-template generalization or prospectively diversify templates. | Any substantive sampling/estimand amendment |
| Reproducibility | Existing sources preserved; main input tokens and controls already checked. Final selected model/template/policy and final request manifest are not yet frozen. | None for ordinary integrity checks; exact frozen inputs must precede authorization |
| Inference | All 16 authorized format attempts consumed. Main 2016 and proposed eight Instruct requests remain unauthorized. | Explicit authorization bound to the exact relevant manifest |

The [material/measurement follow-up](P1d_material_measurement_followup_v1.md) and [Instruct readiness report](P1d_instruct_arm_readiness_v3.md) supply the details. Do not reopen the previously approved P1d design merely to restate its limitations. Full validation authorization is not being requested now.

## Algorithmic Opportunity Assessment

1. **Observed Failure Modes:** continuation suppression leaves promises rather than answers; supported generic policy echoes can coexist with task failure.
2. **Existing Methods and Published Prior Art:** conventional stops/extraction, structured component checking, LongMemEval temporal retrieval, FPPS, CoVe, RARR and memory-admission controls are relevant baselines; see the [verified primary-source update](related_work_novelty_matrix_monitor_v6.md).
3. **Potential Algorithmic Improvements:** no demonstrated new computational distinction survives the strong simple baselines yet. Claim/date/component states are a testable engineering adaptation, not an original algorithm.
4. **Validation Feasibility:** retain the implemented offline comparison and negative fixtures; obtain independent boundary/semantic truth before accuracy claims. Generation-based verification methods need separate authorization and matched compute/fidelity controls.
5. **Publication Value:** the credible contribution is rigorous identification and measurement of persona-conditioning effects after configuration adequacy, including negative results. This development diagnostic alone is not publication readiness.

Researcher decision: **blank / pending**. Researcher decision timestamp: **not supplied**. AI-assisted scientific recommendations are not human judgments.
