# P1d actual tokenizer evidence — v1

Maintainer: Yaxin ZHENG. No generation or server launch occurred.

All 1,728 current Base prompts were verified against their actual native vocabulary-call logs, complete integer token IDs and hashes. This audit reused the existing native observations only after exact prompt and log hash equality; it did not substitute approximate counts or unnecessarily repeat 1,728 calls. The native utility is llama-tokenize from b11573, with the pinned Qwen3.5-2B-Base Q4_K_M vocabulary. Current model, backend, tokenizer executable and all 29 recorded DLL hashes also match the prior identity.

Input lengths remain **1,946–2,085 tokens**. All 288 cases have exact equality across four active histories and D_procedural. H_none is shorter. At context 4,096 and candidate output cap 256, the tightest remaining capacity is **1,755 tokens**. No context truncation is required by these counts. All six conditions preserve the same evidence-bearing prefix bytes and reference fields, and the original candidate order matches native records. There is no frozen independent-study execution order yet.

The [per-prompt evidence](validation/p1d/scientific_validation_v1/tokenizer_evidence_verification_v1.json) retains native log references and hashes. The [current identity check](validation/p1d/scientific_validation_v1/current_runtime_identity_verification_v1.json) records actual local binary hashes. These checks certify saved vocabulary tokenization of the Base transcript, not Instruct rendering, semantic neutrality or generation quality. Detokenization round-trip and actual generation-time backend token equality remain explicit final-preflight checks. No successful prefill or output inference is claimed.
