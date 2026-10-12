# P0 Generation Budget Diagnostic

Date: 2026-10-12. Paper: **Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**. Research Protocol v1.1, with its prospective English-language scope addendum. This is an engineering diagnostic, not a Persona comparison study.

**Execution PASS; natural termination remains unresolved.** All 18 new responses reached their assigned limit, including all six at 256 tokens. Increasing the budget alone did not produce natural completion in this frozen subset.

## Frozen design and provenance

The selection was frozen at `2026-10-12T17:39:54.613027+00:00`: the lexicographically first three existing synthetic IDs, `synthetic_001`–`synthetic_003`, under C0 and C3. No case was selected by output quality. Budgets were 96, 192 and 256, in that order, C0 then C3 at each budget. There were no adaptive extensions. The fresh 96-token group supplies the within-session reference; it does not replace any historical run.

The original English dataset SHA-256 is `31b5242c2cc01411f524c2b922086de0ef216105920e723f1270560e0bc1f282`. The original cases, trusted evidence, current questions, applicability and prompt template `transcript_base_v1` were retained. No translation, Chinese dialogue insertion, naturalistic data collection or new Persona algorithm was performed.

Model: third-party Qwen3.5-2B-Base Q4_K_M GGUF, SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; fixed publisher revision `765d2baaa04dbb8d6df3e78af571e6beaa4373d7`. Backend: llama.cpp build 11573 / `0f701c882`, executable SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. Prior provenance limitations remain as documented in the model report.

CPU-only, 4 inference threads / 4 batch threads, context 4096, seed 42, temperature 0, top_p 1, `stop=[]`, `cache_prompt=false`, `ignore_eos=false`. Only `n_predict` and its native budget alias changed. Input IDs were checked against the historical exact prompts and re-tokenized before generation. Git HEAD was `8ffe1fdeb64ccc85182d2ff983b514940ecb6f70`, with dirty state **true** in all six new manifests; exact source/tool snapshots and hashes identify the uncommitted implementation.

Actual command: `tools/p0_capture.py --output results/p0_methodology/20261012T173818/budget_generation_command.json -- .\.venv\Scripts\python.exe tools/p0_methodology.py budgets --session results/p0_methodology/20261012T173818`, invoked with the project virtual-environment Python. UTC start `17:50:19.490471`, finish `17:55:59.646820`; 340.156 seconds wall clock, exit 0. All six managed servers completed and were stopped by the runner.

## Actual results

Each row below contains the same three case IDs. Latencies are measured HTTP response wall times; they exclude server startup. Backend prompt/prediction timings are separately retained for every response. Runs were sequential, not randomized; system load, cache state and temperature were not experimentally controlled. These are observations, not a CPU benchmark or a condition speed comparison.

| Budget | Condition | Actual generated tokens, each | Stop reason | Reported EOS/EOG | Mean latency (s) | Range (s) |
|---:|---|---|---|---:|---:|---|
| 96 | C0 | 96, 96, 96 | limit × 3 | 0 | 8.636 | 8.486–8.799 |
| 96 | C3 | 96, 96, 96 | limit × 3 | 0 | 9.888 | 9.434–10.492 |
| 192 | C0 | 192, 192, 192 | limit × 3 | 0 | 16.648 | 15.902–17.505 |
| 192 | C3 | 192, 192, 192 | limit × 3 | 0 | 16.682 | 16.393–17.049 |
| 256 | C0 | 256, 256, 256 | limit × 3 | 0 | 20.973 | 20.753–21.094 |
| 256 | C3 | 256, 256, 256 | limit × 3 | 0 | 21.335 | 21.244–21.510 |

Raw nonempty: 18/18. Parser classification: preserved 18/18; failures 0. Each response returns exactly its budget in output token IDs. The loaded logs list EOS 248044 and EOG IDs 248044, 248046, 248063, 248064, 248065; none appears in the returned output IDs, and the native stop reason is `limit` in every response. No input-context truncation was reported. Evaluated input counts agree, but evaluated input ID arrays are still not independently returned by the backend.

The six case/condition pairs retain the same prompt hash, input IDs and common configuration at all three budgets. Each 96-token sequence is an exact prefix of both longer sequences in this run. This observation does not establish general deterministic behavior from a seed.

## Completeness and termination interpretation

All 18 initial city answers form recognizable complete first replies and have terminal punctuation. All 18 outputs then generate additional `User:` / `Assistant:` turns. None of the full outputs ends in terminal punctuation; many end in a question fragment, role label or incomplete answer. These structural flags are saved per response, and independent human semantic-completeness fields remain empty. Missing punctuation alone is not proof of semantic incompleteness.

Examples: C0/001 first answers Paris, then invents age, occupation and marital-status turns. C0/003 repeatedly answers Dijon. C3/002 and C3/003 continue to progressively earlier years beyond the supplied fact-validity interval. Longer budgets prolong those continuations. None of these observations is evidence that Persona conditioning causes a reliability change.

The immediate stopping mechanism is established: the native completion API receives a finite token budget, no text stop sequence, and EOS is not disabled. A generated `User:` string is ordinary transcript text, not an automatic stopping boundary for this request. The model continues generating past its initial answer until the numerical limit. The Base model and transcript prompt are consistent with this observed continuation pattern, but this diagnostic does not isolate a causal explanation for why EOS was not selected.

There is no demonstrated budget among 96/192/256 that ensures a single naturally terminated answer here. A future response-boundary or stopping policy would need an explicit, versioned P0 validation and preservation of unfiltered text. No such rule was introduced in this diagnostic, and historical parser behavior was not changed.

## Evidence

- [Frozen design, configuration and language metadata](validation/P0_budget_plan.json).
- [All 18 prompts, input/output IDs, raw/parsed outputs, settings, stop reasons, latencies, hashes and completeness indicators](validation/P0_budget_diagnostic.json).
- [Observed parameter-control checks and summary](validation/P0_methodology_summary.json).
- [Full captured command records, including failures](validation/P0_methodology_commands.json).

Original run directories are under `results/p0_methodology/20261012T173818/budget_runs/`:

| Budget / condition | Exact run ID |
|---|---|
| 96 / C0 | `20261012T175020-abbfd27ab4464f59b47195c130418d3f` |
| 96 / C3 | `20261012T175053-a86e73ac7d2f4b6e85a7cfe565470af9` |
| 192 / C0 | `20261012T175130-e4aa45177cef41fdbcd50e3222f08f56` |
| 192 / C3 | `20261012T175229-391d284949804147b4b3340ca1568ac2` |
| 256 / C0 | `20261012T175339-f6abbafdfd4046b98299d76c1533b98a` |
| 256 / C3 | `20261012T175449-2d3695902beb4fbaa7bb1f53bc062a22` |
