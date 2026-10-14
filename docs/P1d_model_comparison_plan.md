# P1d model comparison — proposed v1

Maintainer: Yaxin ZHENG. No model inference or weight download was performed for this proposal.

## Base anchor and distinct instruction arm

Keep the local Qwen3.5-2B-Base Q4_K_M anchor. Its actual model SHA-256 is `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; llama.cpp b11573 server SHA-256 is `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. Native vocabulary checks verified these identities. Proposed settings retain CPU-only, four threads, four batch threads, context 4,096, temperature 0, seed 42, 96 output tokens, no prompt cache and the existing Base stop policy. No new model result replaces the historical anchor.

The same-family instruction-tuned candidate is officially named [Qwen/Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B), not an invented local `-Instruct` artifact. The prospective upstream revision is `965dcc54bc9c0591873df0e9869c056a54d323d1`. Its [official template](https://huggingface.co/Qwen/Qwen3.5-2B/blob/965dcc54bc9c0591873df0e9869c056a54d323d1/chat_template.jinja) was inspected: use proper role serialization, generation prompt and explicit non-thinking mode for a text-only comparison. Do not paste the Base transcript into an unrelated generic chat template.

Local Instruct GGUF, conversion provenance, tokenizer/template byte hashes, backend compatibility, RAM and latency are **not yet verified**; the machine manifest uses nulls rather than invented values. Before freezing that arm, pin source weights, conversion software/revision, quantization recipe, GGUF bytes, vocabulary/special tokens and native EOS/EOG IDs. Check rendered token IDs against the backend, actual capacity and generated-token accounting. Download/conversion is not a scientific validation of compatibility. No larger model is presently recommended because measurement and identification have higher information value.

## Comparison and stopping policy

Select 24 speaker clusters from the 144-cluster allocation before outputs, balancing family/date/template strata; both cases and all six conditions are paired across models. Compare model differences of within-case E/V contrasts and full outcome distributions, including missingness. This is a secondary 288-call arm, not 288 new independent cases. Model weights, post-training, quantization, templates, token counts and native stop behavior all differ or may differ; the contrast does not identify pure post-training.

Keep 96 tokens as the proposed common primary budget for comparability. A separate development diagnostic can compare 96/192/256 on the same cases without choosing the budget by effect signs, but is not in the proposed 2,016 scope and is not authorized. If 96 tokens leaves the independent task requirements unevaluable, stop the prospective freeze and amend the policy before validation. Never tune on the independent responses. An official template comparison or stop-sequence intervention requires real separately authorized generation; offline clipping cannot answer it.

Compute cost is bounded in the [precision plan](P1d_sample_size_precision_plan.md). Different model-arm generation costs and extra verification calls must be reported, not hidden behind equal request counts. The instruction arm is recommended for coverage and configuration sensitivity, not as an assumed improvement.
