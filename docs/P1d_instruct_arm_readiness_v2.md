# P1d Instruct preparation — v2

Maintainer: Yaxin ZHENG. This supplements v1 with offline tokenizer evidence. **Instruct execution remains NO-GO. No Instruct generation or weight download occurred.**

The intended source remains [Qwen/Qwen3.5-2B, revision 965dcc54bc9c0591873df0e9869c056a54d323d1](https://huggingface.co/Qwen/Qwen3.5-2B/blob/965dcc54bc9c0591873df0e9869c056a54d323d1/README.md). The official tokenizer JSON was retrieved from that revision, with SHA-256 `5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42`. Only tokenizer metadata and a small isolated tokenizers 0.22.2 runtime were added; no model inference was used.

## Actual completed checks

The [metadata comparison](validation/p1d/final_preparation_v1/instruct_tokenizer_metadata_comparison_v1.json) reads the pinned Base GGUF vocabulary without loading tensors. All **248,070 IDs defined by the official tokenizer** have identical strings in the Base vocabulary; **247,587 merges** agree. The Base GGUF has 250 additional audio/padding IDs not defined in that official JSON. The comparison's `id_string_mismatch_count=250` denotes these extra entries, not 250 conflicting shared text-token definitions. This does not establish full Base/Instruct tokenizer equivalence.

The [288-record official-tokenizer check](validation/p1d/final_preparation_v1/instruct_official_tokenizer_check_v1.json) uses the already rendered, unmodified official-template candidate strings. Every string encodes and decodes exactly with special tokens retained. Counts are **1,965–2,083**, leaving at least **1,757** context positions after a hypothetical 256-token completion in a 4,096-token window. On the corresponding unchanged Base task bodies, all 288 upstream-JSON token-ID hashes agree with the previously recorded native Base hashes. Full IDs are in [tokenizer records](validation/p1d/final_preparation_v1/instruct_official_tokenizer_records_v1.json).

The runtime was installed into an ignored project-local results directory, without changing the research Python environment. Initial restricted-network attempts failed with Windows socket error 10013; explicit tool-level network approval allowed the same bounded fetch/install. Download and runtime byte hashes are preserved. Tokenization is vocabulary processing, not model generation.

## Still required before execution

A traceable local Instruct GGUF is absent. Source-weight revision, quantizer/converter provenance and local file hash must be verified before selecting an artifact. The final GGUF's native tokenizer, official-template rendering in the pinned backend, end-of-generation behavior, CPU compatibility, actual RAM and latency remain unmeasured. Upstream JSON checks must not be substituted for those tests or copied into a supposedly executable Instruct manifest. No third-party model has been silently selected.

The approved comparison is **24 selected speakers × 2 cases × 6 conditions = 288 Instruct requests**, paired to 288 requests already included in the 1,728 Base allocation. It supports model-configuration comparisons on that subset only. Weights, quantization, chat rendering and stopping can differ; this is not a pure post-training effect or a complete 144-speaker model interaction.

A Base-only route can be separately authorized after Base measurement adequacy and all other scientific gates are satisfied. It must explicitly defer the adopted Instruct comparison, not erase it. Current output-budget diagnostic results do not automatically authorize either route or freeze the independent bank.
