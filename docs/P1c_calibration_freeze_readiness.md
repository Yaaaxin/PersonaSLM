# P1c Calibration Freeze Readiness — Candidate v1

Maintainer: Yaxin ZHENG. **Offline candidate prepared; execution is not authorized.** Historical protocols, datasets and all outputs remain unchanged.

## Frozen candidate

[Complete 72-request manifest](validation/p1c/final_review_v1/calibration_manifest_candidate_v1.json). [External hash receipt](validation/p1c/final_review_v1/calibration_manifest_sha256_v1.json).

Manifest SHA-256: `b0cf330d9dd5f7b59a186dc298c477a97bd86e06a29209805989a9f399fde02b`.

Dataset SHA-256: `f0f35d796197263527b444ae2d593648ba8181f4f2ba388453fd8a6f7a6c5d77`.

Selected-prompts SHA-256: `49e3ad50b70c0689aa0a427e2877fd2e134265328ba4335cf8e3373ab25f8dd2`.

Original-order canonical SHA-256: `3a352d9778b5d39aef80df5064dd3a64ede2657b382718731de371894e9ce4be`.

Entry Git HEAD: `24ff0bef076aae412e58f62d77746a306962aae1`; entry working tree was clean. Changes from this preparation remain uncommitted. The previous review's HEAD is historical, not assumed to remain current.

The original source has `(case_id, condition)` request identities, not separate request-ID strings. All 72 tuples and their order are retained, with a zero-based sequence index. No new assignment or randomization occurred. All original selected-prompt fields, full prompts, token IDs, hashes, dates, references and applicability are copied exactly. The candidate is exclusively created and hash-protected; it is not claimed to be filesystem WORM storage.

## Configuration

| Setting | Preserved value |
|---|---|
| Model | Qwen3.5-2B-Base Q4_K_M |
| Backend | llama.cpp b11573, native version commit 0f701c882 |
| CPU / GPU | 4 threads; 4 batch threads; zero GPU layers |
| Context / output cap | 4096 / 96 tokens |
| Decoding | temperature 0, top_p 1, seed 42, no stop strings |
| Execution-order seed | 715001; original explicit order retained |
| Prompt | p1c_evidence_first_transcript_proposed_v1 |
| Requests | 12 cases × 6 original conditions = 72 |
| Policies | response_status_v1; separate_axes_policy_v1; proposed P1c task application |
| State | cache_prompt=false; no previous generated text enters later requests |

Model SHA-256: `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`.

Backend SHA-256: `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`.

Tokenizer executable SHA-256: `e05dbdef761e577b3d56f3daea7b205a07f68e5d87242ea4e2544382ffdd358e`.

## Tokenizer and source verification

This preparation reuses the previous **72 actual native tokenizer calls**, checks their raw log hashes, prompt text, complete token-ID arrays and current model/backend/tokenizer/DLL hashes, and reconstructs every prompt. It does not describe cached evidence as newly executed tokenization. No generation or server was launched. Native vocabulary-only settings and special-token behavior remain pinned in the manifest.

All 12 active/neutral sets have zero full-prompt token difference. Active/neutral lengths are 766–938 tokens. Maximum context use is 938+96=1034, below 4096. H_none is shorter by 65 tokens in ten cases and 66 in two. Evidence precedes the history and remains at the same location; question offsets differ for H_none. Token equality establishes neither information equivalence nor human approval.

Original candidate failures and repairs, prior review forms, raw runs, annotations and protocols remain preserved. New provenance records retain both original append-only document prefixes and current versions, so previous report hashes can still be interpreted rather than silently replaced.

## Logging, interruption and execution gate

The candidate records the established stateless/native request and immutable-segment resume policies from validated P1b infrastructure. A future execution must create a new P1c run directory, log raw bytes, native responses and stop reasons, input IDs, output IDs where available, parser operations, excluded continuations, latency/errors and actual runtime source/Git identities. Never overwrite or silently replay successful requests. An uncertain in-flight attempt must be retained and resolved under the approved resume policy before another call.

This is a manifest preparation, not a claim that a P1c execution adapter has already completed runtime preflight. After authorization, bind this exact manifest to the existing execution infrastructure and recheck disk capacity, output logging, runtime token identity, context limits and resume state. Any mandatory failure or substantive input change stops execution; no fallback model/configuration is authorized.

## Output-budget decision

Retain 96 for this bounded calibration if approved. The questions need one or two answer components, so the cap does not logically make the task impossible. It may censor reasoning/final delivery in practice. Report unknown/incomplete outcomes and structural categories separately; do not equate truncation with Incorrect or adjust the cap to favor effect signs.

The separately versioned [96/192/256 sensitivity proposal](validation/p1c/scientific_review_v1/output_budget_sensitivity_proposal_v1.json) remains optional and unexecuted. Its three cases × six cells × three budgets would add 54 calls only after separate approval. It is not inserted into this manifest, and it is not an extra mandatory gate for the present decision.

## Readiness result

Technical candidate checks are recorded in [verification](validation/p1c/final_review_v1/verification_v1.json) and [provenance](validation/p1c/final_review_v1/reproducibility_manifest_v1.json). The complete test result is linked there with exact command output.

Full automated suite: **796 passed in 32.01s**, exit 0; the captured process took 32.504 seconds and reported no pytest warnings. The new packet guards account for 15 tests. Original experiments were not executed by these tests. The engineering capture retains the exact `.venv\Scripts\python.exe -m pytest -q` command and full output.

**TECHNICAL CANDIDATE READINESS: PASS. SCIENTIFIC REVIEW: PENDING. INFERENCE AUTHORIZATION: PENDING. EXECUTION: NO-GO.** The remaining decisions are precisely the 72 reviewed items and five explicit global decisions in the final packet; no broad redesign is requested.
