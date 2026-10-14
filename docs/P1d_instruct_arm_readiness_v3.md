# P1d Instruct preparation — v3

Maintainer: Yaxin ZHENG. **Local candidate prepared; generation remains unauthorized.** This supplements v2 without replacing the Base model or adopting a new primary model policy.

## Verified artifact and remaining provenance limits

The intended official model remains [Qwen/Qwen3.5-2B at 965dcc54bc9c0591873df0e9869c056a54d323d1](https://huggingface.co/Qwen/Qwen3.5-2B/tree/965dcc54bc9c0591873df0e9869c056a54d323d1). A current metadata fetch found a newer repository revision15852e8c16360a2fea060d615a32b45270f8a8fc; it is not silently adopted. The API lists the same weight LFS digest at both revisions (`aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1`, 4548221488 bytes). This is remote metadata equality, not a locally reproduced conversion.

Three public quantization repositories were checked at fixed revisions. The prepared candidate is [lmstudio-community/Qwen3.5-2B-GGUF](https://huggingface.co/lmstudio-community/Qwen3.5-2B-GGUF/tree/bb84e11355a036e28f080c7793fa6d22b7c4e344), revision `bb84e11355a036e28f080c7793fa6d22b7c4e344`, file `Qwen3.5-2B-Q4_K_M.gguf`, **1270808032 bytes**, SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`. Local bytes match the distributor's LFS digest. Location: `models/gguf/instruct_candidates/lmstudio-bb84e113/Qwen3.5-2B-Q4_K_M.gguf` (ignored model directory; no weights enter Git).

The distributor reports llama.cpp b8185 quantization, but not its exact source-weight revision, complete conversion command or calibration provenance. Therefore **conversion lineage is PARTIALLY_VERIFIED**, not fully certified. It was chosen for a standard non-MTP-advertised Q4_K_M candidate with explicit quantizer build and size comparable to Base, before any Instruct response was observed. Bartowski's checked candidate advertises MTP addition and b9222; the checked Unsloth card does not supply an exact quantizer revision. No outcome-based model selection occurred. An exact local reconstruction from official weights remains an alternative if full conversion lineage is required.

## Tokenizer, template and runtime

All248070 official shared token IDs and247587 merges match the local candidate. Its architecture is qwen35 with24 layers; stored native context262144, proposed runtime4096. EOS metadata248046 corresponds to `<|im_end|>`. Native EOG behavior under generation remains **unmeasured**.

The embedded template bytes differ from the pinned official template; all eight proposed single-user development renderings nevertheless agree exactly. The proposal explicitly binds the official template file (`0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`), enable_thinking=false, and does not rely on implicit embedded-template precedence. Fixed dialogue remains quoted task content inside one user message; this differs from Base plain completion formatting.

The pinned b11573 vocabulary-only utility processed all eight prompts successfully, **1642–1765 tokens**, with special-token parsing enabled. Every full native token array equals the pinned official tokenizer result. These are eight development checks, not new native certification of all288 future Instruct prompts. No server, tensor evaluation, warmup or Instruct generation occurred. The original288 offline rendering/tokenizer checks remain separate evidence.

The local model is about1.184GiB; actual Instruct RAM/latency and tensor execution compatibility remain unknown. The Base process peaked at2.431GiB. A later post-run system-memory observation is retained; transient free RAM is not an Instruct measurement. The eventual smoke preflight should reserve memory headroom and run without concurrent model/tokenizer workloads. Official recommended sampled decoding differs from the proposed greedy comparability diagnostic; no claim of official benchmark reproduction is made.

## Exact prospective scope

[minimal_instruct_smoke_manifest_proposed_v1.json](validation/p1d/instruct_preparation_v3/minimal_instruct_smoke_manifest_proposed_v1.json), SHA-256 **`ba63c30a9868b94b47f8f79dd774ac0627d56113810ffd4db08eb63af0374b91`**, proposes only **8 H_none development requests**, same eight cases, 96 tokens, seed42, CPU4, ctx4096, native EOG, no custom stops, no retries, maximum768 generated tokens. No generation is authorized. Acceptance requires8/8 identifiable complete answers with separately reported correctness, components and fidelity; success only supports further separately authorized all-condition measurement validation. Failure retains NO-GO.

The registered288 Instruct validation target remains24 speakers×2 cases×6 conditions, paired to a subset of1728 Base requests. This is a limited model-plus-template/quantization comparison, not pure post-training or full-cohort model interactions. An Instruct-first or replacement primary arm would require a prospective amendment; none is adopted here.
