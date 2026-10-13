# P1c Model Sensitivity Proposal — Proposed v1

Maintainer: Yaxin ZHENG. No model inference, download or new model arm is authorized by this document.

## Recommended initial scope

Use the already pinned **Base model only** for the first approved narrow R/T development diagnostic. This keeps model/backend status comparable to the motivating P1b observations and avoids doubling a small feasibility bank before its manipulation is accepted. It is not a claim that Base is intrinsically preferable. Persistent continuation failures remain a reason to evaluate a separate post-trained arm later.

P1b preserved 186 CROSS_TURN, five TRUNCATED and one AMBIGUOUS output, with 191/192 identifiable first replies. Confirmed semantic completeness and factual judgments are separate. Thus high continuation frequency alone does not prove that Base responses are unusable, nor that changing models would solve semantic measurement.

## Candidate separate arm

The official [Qwen/Qwen3.5-2B model card](https://huggingface.co/Qwen/Qwen3.5-2B) identifies a 2B language model with pre-training and post-training, and documents instruct/non-thinking use. Do not invent a repository named `Qwen3.5-2B-Instruct`. The official [chat template](https://huggingface.co/Qwen/Qwen3.5-2B/blob/main/chat_template.jinja) must be pinned to an immutable revision before use; the present moving links establish availability, not an approved artifact or frozen configuration.

Required preflight: official model revision and license; third-party GGUF publisher/conversion lineage if used; quantization and model file SHA-256; tokenizer metadata/hash; exact chat-template bytes/hash; explicit thinking-mode setting; compatibility with the selected backend; context and memory fit; CPU-only execution; native token accounting and endpoint stop behavior. No suitable local Instruct GGUF has been certified in this task. Binary integrity does not prove faithful upstream quantization.

Start from four threads, 4096 context and the same 96-token visible generation budget only if the official template/mode and backend support it. A budget including reasoning tokens is not equivalent to a visible-answer budget; record the exact accounting. Any budget or backend revision is a separately approved arm. Do not silently apply the Base transcript wrapper or reuse Base token matches. Match histories separately after each arm's actual template/tokenizer, holding semantic evidence and question constant within arm.

## Comparability and cost

A later limited paired model comparison could repeat the 12 cases × six cells (72 additional requests), separately frozen and approved. It would evaluate configuration sensitivity, not isolated post-training: weights, training lineage, chat template, token accounting and possibly quantization differ. Analyze within-arm R/T contrasts first, then their paired difference across configurations with speaker clustering. Keep native stops, structural status and annotation coverage alongside semantic outcomes. Do not pool independent-looking 144 outputs into 144 cases.

The Base workload proxy for 72 calls is 13.10 response minutes, with a .5×–2× sensitivity range of 6.55–26.20 minutes. It is not an Instruct runtime estimate; actual latency, load time and memory are unavailable. Review effort can dominate compute. Instruct-only would abandon the immediate same-configuration diagnostic; both arms now would spend more resources before resolving the relevance operationalization and neutral semantics. Consequently Base-only is the proposed first step, with the separate model arm contingent on measurement feasibility and researcher approval.

No claim about the new model's accuracy, response termination or persona fidelity follows from its model card. Its usefulness must be tested on frozen material and valid annotation, not assumed from post-training status.
