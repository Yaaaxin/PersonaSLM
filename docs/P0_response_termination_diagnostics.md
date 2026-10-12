# P0 Response Termination Diagnostics

Date: 2026-10-12. Overall single-turn methodological validation: **PARTIAL**. A usable explicit boundary does not require natural EOS, but the tested rules do not reliably delimit every tested development response.

## Question and frozen design

Can one complete dialogue response be identified under a finite token budget? Here, a **structurally complete turn** is a nonempty assistant reply ended by an observed declared delimiter, a backend-acknowledged declared stop, or EOS/EOG, with no unintended extra role turns and no reserved-delimiter collision with requested content. A token cap or terminal punctuation alone does not establish completeness. **Semantic completeness** additionally requires answering the actual requested components and preserving valid multiline content; it is assessed separately from the structural boundary and factual correctness.

The prior 118 outputs remain unchanged, including the 18 budget diagnostics. Four new English development cases are versioned in `tests/fixtures/p0_boundary_dev_v1.json`: Maya (one sentence), Noah (two requested sentences), Iris (two bullets), and Evan (literal `User:` text). They use new IDs, speakers and tasks. All four were selected before generation; no factual-quality filtering occurred. The literal-role challenge is an explicit predeclared stratum, not a post-hoc exclusion.

Freeze: `2026-10-12T18:24:13.295251+00:00`. Exactly 16 requests, case order then T0/T1/T2/T3, all at 96 tokens, seed 42, temperature 0, top_p1, CPU 4/4, context 4096. Model/backend and hashes are unchanged from the pinned GGUF/build 11573 setup. Prompts are identical within each stop/no-stop pair; only the stop list changes. The two formats preserve the same task evidence and question. Tokenization of all 16 prompts completed before any generation.

| Variant | Prompt version | Native stop strings |
|---|---|---|
| T0 | `transcript_base_v1` | none |
| T1 | `transcript_base_v1` | `\nUser:`, `\nAssistant:` |
| T2 | `explicit_end_reply_v1` | none |
| T3 | `explicit_end_reply_v1` | `\n<END_OF_REPLY>` |

The explicit format asks for exactly one answer, preserves requested line breaks, and requests a separate `<END_OF_REPLY>` line. No stop or prompt rule was adapted during generation. These are controlled development diagnostics, not new Persona treatments or a P1 comparison.

## Observed outputs and failure modes

Exact run ID: `20261012T182432-ea39ea100d8c449ab05b04cf80e6b78c`, under `results/p0_methodological_final/20261012T181718/experiments/runs/`. All raw HTTP bytes, native JSON, output IDs, latency, legacy parse, boundary parse and excluded tails remain saved. The full public derived evidence is [P0_response_termination_evidence.json](validation/P0_response_termination_evidence.json); machine paths are redacted there, not in the local originals.

| Variant | Generated tokens per case, 001–004 | Native stop | Structural v1 | Supplementary review |
|---|---|---|---|---|
| T0 | 96, 96, 96, 96 | limit × 4 | 3 PASS / 1 PARTIAL | 2 PASS / 2 PARTIAL |
| T1 | 9, 23, 9, 11 | word × 4 | 3 PASS / 1 PARTIAL | 2 PASS / 2 PARTIAL |
| T2 | 96, 96, 96, 96 | limit × 4 | 0 PASS / 4 PARTIAL | 0 PASS / 4 PARTIAL |
| T3 | 96, 96, 96, 96 | limit × 4 | 0 PASS / 4 PARTIAL | 0 PASS / 4 PARTIAL |

No EOS/EOG was reported. T0's PASS means a first boundary was recoverable in its saved 96-token continuation, not that the native generation stopped there. T1 terminated using a string stop; this is a recorded inference intervention, not spontaneous model EOS.

- **Maya:** a complete first city sentence precedes invented subsequent questions. T1 retains that sentence and ends at the next declared role boundary.
- **Noah:** the first sentence contains both requested facts, but does not satisfy the requested two-sentence format. T0 and T1 also retain `USER: Use the supplied record.` before the next mixed-case `User:`. The frozen v1 parser/stop list missed this uppercase role label. A separately versioned case-insensitive review flags both false structural PASS values; neither raw text nor v1 classifications were overwritten.
- **Iris:** the first reply contains both bullets on separate lines. T1 preserves both; a first-newline parser would have risked losing valid multiline content. The legacy parser was not configured to stop at the first newline.
- **Evan:** T0/T1 omit the requested two-line label and return its explanation only. The input contains a reserved role delimiter, so the role-delimited contract is ambiguous regardless of that output. This run does **not** prove the stop string cut off a correctly generated label. Unit tests demonstrate the collision on a constructed correct literal-label response. T2/T3 include the label and explanation, then keep generating more dialogue without the end marker.

All eight stop/no-stop pairs have identical prompt IDs and request parameters apart from `stop`; the actual stopped body equals the corresponding shadow extraction. This equality alone does not certify the extraction: the Noah pair shares the same uppercase-role error. For T2/T3, both full continuations match because the sentinel stop was never reached. Shadows are separate actual generations; the unseen continuation after a backend stop is never fabricated.

## Model, prompt and parser interpretation

The observed Base-model behavior is consistent with continuing a transcript, including after it has already supplied an adequate initial answer. This is an observation for this binary, prompt family, seed and development set, not a causal comparison of Base versus Instruct models.

The original prompt establishes who speaks next with `Assistant:` but provides no enforced end-of-turn delimiter. Native `stop=[]` permits further transcript text. Adding an instruction and unfamiliar literal sentinel did not make the model produce that sentinel within the fixed budget. Raising the token limit is not the proposed solution.

The historical parser strips surrounding whitespace and an optional speaker prefix; it does not identify the first assistant turn. It therefore preserves extra turns. Its configurable first-newline truncation option was **not used** in these experiments and would not be a safe general solution for multiline answers. The new boundary extraction preserves the original payload, exact slice position and excluded tail; it does not silently replace historical parsing.

## Decision and scope

No tested format passes all four predeclared cases after supplemental inspection. The exact role-stop implementation works for two observed ordinary tasks but misses uppercase role labels, and literal role text makes its contract ambiguous. The sentinel format fails to provide a boundary in all four cases. A case-insensitive extraction or escaped/reserved-delimiter policy is a candidate for a separately frozen diagnostic; it has **not** been adopted or validated online here.

Natural EOS absence is not independently a P1 blocker if a response-boundary policy is otherwise validated. The present blocker is the lack of a validated response-unit contract over the intended tasks, including format variation and legitimate quoted/literal content. Independent human semantic-completeness judgments remain zero; the case descriptions above are agent inspections, explicitly not human evaluation.

## Engineering failure and recovery

The generation command ran from `18:24:32.068339` to `18:26:28.312076` UTC (116.244s) and completed all 16 requests. The journal's execution terminal state is PASS. The enclosing command nevertheless exited 1 during its subsequent audit: the initial audit erroneously demanded HTTP 200 from startup `/health` requests. Fourteen HTTP 503 loading responses are preserved in the journal; actual tokenizer/completion calls succeeded.

The offline auditor now separates health responses from inference pairs, retains all health statuses, and still rejects failed completion responses. Dedicated regression tests cover both cases. Two corrected CLI replays at `18:27:54`–`18:27:55` UTC passed without model generation. The original failed command and all generated records remain. Subsequent all-run verification uses the corrected audit; its exact source hash is recorded separately from the generation-time tool snapshot.
