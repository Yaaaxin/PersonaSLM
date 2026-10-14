# P1c Output Budget and Model Configuration Risk

Maintainer: Yaxin ZHENG. Prospective only. The existing configuration remains 96 output tokens; no budget, template or model change was applied.

## Actual motivation and unmeasured quantities

P1b retained 190/192 token-budget stops, 186 CROSS_TURN, five TRUNCATED and one AMBIGUOUS output. It nevertheless had 191 identifiable first replies and 143 researcher-confirmed complete replies. These are different outcomes: a continued transcript can follow a usable answer; a length stop can censor an unfinished answer. No controlled inference from those observations establishes the effect of a larger budget on P1c.

P1c requests one or two short answer components. A concise valid answer can fit in 96 tokens, but this does not establish model completion under that cap. Route explanation, repetition or continuation can consume it. No P1c output exists. Increasing the cap could merely generate more turns, with little improvement to the first reply.

All current inputs fit: maximum 938 + 96 = 1,034 tokens, leaving 3,062 of the configured 4,096. Hypothetical 192 and 256 caps also fit (1,130 and 1,194). Capacity does not prove adequate or comparable semantic coverage.

## Optional bounded sensitivity proposal

[Machine proposal](validation/p1c/scientific_review_v1/output_budget_sensitivity_proposal_v1.json): three existing cases selected before outcomes—p1c_01_historical, p1c_03_current, p1c_05_historical—one per family, first speaker in each family with alternating requested-date mode. Six original conditions × three caps (96/192/256) would be **54 separately authorized requests**. It is not added to the 72-request proposal and is not a new mandatory gate. Mode and family are not balanced in this tiny subset; it cannot choose a universally adequate cap.

If authorized, pin the same prompt bytes, model, decoding seed/temperature, response policies and a separate randomized arm order (proposed seed 715006). Keep all six conditions at each cap. Preserve raw continuations, native termination, input/output IDs where available, extraction boundaries, delivered components, human completeness and latency. Evaluate the first reply with the frozen policy; retain full continuations separately. Do not take a later correct turn or alter the cap only for unfavorable cells.

The decision criterion is improved measurement coverage/completeness at an acceptable cost without concealing boundary changes, **not a desired sign of R, T or R×T**. Any adopted cap belongs to a newly versioned whole arm, never retroactively to the original configuration. If no coverage benefit is observed, retain that negative finding. No P1c outcome-based prompt tuning is proposed.

At the prior mean 10.917 seconds/request, linear cap scaling gives roughly 18.56 response minutes for the full optional design. This is a workload illustration, not measured P1c throughput or an upper bound; longer prefill, early stopping and generated length can invalidate linear scaling. Original 72-call Base proxy remains 13.10 minutes (6.55–26.20 under a .5×–2× sensitivity), excluding loading, review and retries.

## Model recommendation

Retain the pinned Qwen3.5-2B-Base Q4_K_M / llama.cpp b11573, CPU threads/batch threads 4, GPU layers 0, context 4096, temperature 0 and seed 42 for a first **approved** scoped calibration. This preserves the motivating configuration; it does not imply that Base is universally suitable. Native tokenizer matching is verified, whereas future generation latency, memory and semantic coverage are unobserved.

A separate post-trained [Qwen/Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) arm may then test response-unit and semantic-coverage sensitivity. Pin official chat-template bytes/revision, thinking mode, tokenizer, quantization publisher/lineage and backend compatibility before any use. The official repository describes post-trained 2B weights; it does not establish a verified local GGUF. Base/Instruct differences would combine weights, template and token accounting, not identify pure post-training. A further 72 calls would have the 13.10-minute **Base-equivalent** reference, with actual Instruct cost unknown. No model download, execution or arm expansion occurs here.
