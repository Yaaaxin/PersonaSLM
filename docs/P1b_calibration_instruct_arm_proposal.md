# Prospective P1b Instruct Configuration Arm

Maintainer: Yaxin ZHENG. Formal experimental baseline: Protocol v1.1. Protocol v1.2 Revised Proposed r1 remains prospective and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Development evidence only; no new inference.

## Decision

**Scientifically plausible, not authorized or launched. First finish the current semantic review.** Persistent transcript continuation and 190/192 budget stops justify asking whether a native dialogue configuration yields more usable first replies. They do not establish semantic failure on all those outputs. No new model artifact was downloaded, tokenized or executed.

## Candidate and provenance gate

Candidate: the official **Qwen/Qwen3.5-2B** post-trained model, not an invented `-Instruct` repository name. The official card describes 2B language-model parameters and a post-trained checkpoint, with non-thinking mode the default. [Official model card](https://huggingface.co/Qwen/Qwen3.5-2B).

Use its official `chat_template.jinja`, which renders role delimiters and handles thinking configuration; the inspected template inserts a closed empty thinking block by default when adding the assistant generation prefix. [Official template](https://huggingface.co/Qwen/Qwen3.5-2B/blob/main/chat_template.jinja). This source was inspected on a moving main branch for planning; **no arm revision, converted GGUF hash or tokenizer hash is frozen yet**.

Before approval, pin upstream model/config/tokenizer/template revisions, selected quantized artifact publisher and conversion provenance, GGUF SHA-256 and metadata, executable/build hashes, native chat rendering and special-token behavior. Verify text-only operation, CPU/context support on the chosen backend; do not silently upgrade b11573 if unsupported. Quantization identity does not prove upstream training equivalence. Missing provenance is a preparation gate, not filled with the Base model's hash.

## Prospective comparison contract

Preserve all 24 case contents, evidence/questions/reference dates, S/F/H routing, predeclared metric applicability, seeds and within-arm randomized order. Evaluate every C0–C7 cell. Neutral controls remain excluded while semantic review is OPEN. Compare the same cases across configurations with paired, speaker-clustered reporting and masked review using the same four axes and separate answer-delivery/structure measures.

Proposed resource-matched starting point: 4 CPU threads, context4096, temperature0, seed42, output96. The candidate's native non-thinking configuration is explicit; Base has no equivalent guaranteed switch. Native template, special tokens and checkpoint/post-training differ jointly. This is an **operational configuration-sensitivity comparison**, not identification of a pure post-training effect. Temperature0 is a deliberate comparability proposal, not a claim that it is the vendor's recommended benchmark setting. A different budget/decoding regime needs a separately approved arm; do not change it after viewing results.

Native chat stop/EOG markers must be logged separately from semantic completeness. Preserve response_status_v1 results as historical measurements; validate any chat-specific delimiter adapter on independent fixtures and version any additional structural diagnostic. Do not force rendered chat output through a transcript interpretation without checking false cuts and excluded text.

## Scientific value, cost and limits

Measure semantic scoring coverage, first-reply completeness, instruction relevance, factual/temporal category distributions and structural continuations independently. Support for the feasibility hypothesis would be improved usable-answer coverage without hiding unknowns, backed by unit verification; unchanged or worse coverage would weaken it. Correctness improvement is not a required or assumed direction. Shared-case findings are developmental; independent material is still necessary for confirmation.

A full paired arm would require 192 additional calls **only after authorization**. Observed Base summed request latency was 2096.152s, mean 10.917s/request, about 34.94minutes. A planning range of 1–3 times that cost is roughly35–105minutes, excluding setup, artifact preparation, failures and annotation; it is not measured Instruct performance. Quantization, tokenization and actual reply lengths can change cost. Do not expand case counts to spend a budget.

If current review instead finds that first replies already support reliable semantic measurement, prioritize independent discriminative cases and precision over a new model. If extraction errors dominate, a small independently designed boundary diagnostic may provide more information than all192 new calls. The researcher selects the next experiment after review; no automatic launch is permitted.

## Algorithmic Opportunity Assessment

Native template/EOG handling is an established configuration baseline. Demonstrating that it changes an S/F/H interpretation could support a measurement study; using it is not an algorithmic novelty. No new architecture, training, response selection or post-processing optimization is proposed for immediate implementation.
