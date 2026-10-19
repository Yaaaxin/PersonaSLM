# P1 C0 difficulty calibration — consolidated milestone v1

Maintainer: Yaxin ZHENG. Phase: P1 measurement development only. All semantic judgments are AI-assisted proposals; zero researcher confirmations and zero independent human ratings.

## Research purpose and prospective design

Establish true C0 difficulty, answer measurement coverage and evaluator limitations before the core S/F/H pilot. Thirty-two distinct synthetic development speakers/cases cross four task families, four ledger sizes (8/12/16/20 rows) and two replications. C0 contains no S/F/H optional blocks. It is not the previous H_none condition. The eight-case factorial pool was fixed before these outputs and has disjoint speakers, questions, answer-code inventory and evidence records. The pools share four construction ancestors and two style specifications; names are not evidence of independent linguistic populations.

No cases were removed to reach the provisional 80–95% target. The target was not a hard gate. All 32 cases remain; v1.1 and the adopted P1d E/V addendum remain unchanged, while v1.2 remains proposed. This P1 development bank does not replace or freeze the formal P1d bank.

## Engineering evidence

Manifest: `docs/validation/p1/measurement_pilot_v1/A_C0_manifest_v1.json`, SHA-256 `d32b0f10edb7dbbc16e0cad5f282f3aa7b3d808e9d9a819b27e2b723b3a6e8cb`.
Raw run: `results/p1_measurement_pilot/v1/runs/20261015T073025-41204876184c408c912f020459d700f5`. 32 attempts, 32 successful, 0 failed, zero retries. Native stops: {'eos': 21, 'length': 11}; output tokens: 1439; mean latency 14.285 seconds; observed peak process working set 4281438208 bytes. These are observations, not independent hardware benchmarks.
Model `models/gguf/instruct_candidates/lmstudio-bb84e113/Qwen3.5-2B-Q4_K_M.gguf` SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`; backend b11573 SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. CPU only, four threads, context 4096, seed42, temperature0, top-p1,96 output tokens, no custom stops/cache/warmup/retries. Official nonthinking template SHA-256 `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`. Partial third-party conversion lineage remains a development-only limitation.
All native input arrays matched the official tokenizer and the live server. Actual input range: 553–1251 tokens. Full prompts, token IDs, native outputs, base64 HTTP bodies, source snapshots, effective server properties, memory observations, errors and hashes remain in the journal. Available RAM passed the unchanged 3 GiB preflight. No external process was stopped.

## Scientific observations

AI-proposed task success: **11/32 (34.38%)**. Descriptive Wilson95% interval: [20.41%, 51.69%]. This iid approximation does not guarantee population coverage for shared synthetic templates.
Complete requested-answer forms: 29/32; delivered components: 61/64; supported components: 29/64. An explicit but false unavailability answer is treated as delivered answer content, not supported content (AM004/AM031); the opposite completeness interpretation is retained for human review. AM017 contains a supported March assertion and a conflicting March assertion; its supported component is not successful final delivery.
Original parser statuses remain {'AMBIGUOUS': 21, 'TRUNCATED': 11}. All 32 first-response candidates are AI-proposed identifiable. Attribute headings triggered parser ambiguity; EOS alias incompatibility and semantic certification are distinct. The 11 budget-ended continuations must not be automatically marked factually wrong or incomplete. No original label or raw text was changed.

| Task family | Success | Complete form | Supported components |
| --- | ---: | ---: | ---: |
| dated_comparison | 0/8 | 5/8 | 3/16 |
| dual_component | 2/8 | 8/8 | 7/16 |
| relational_chain | 5/8 | 8/8 | 15/24 |
| single_lookup | 4/8 | 8/8 | 4/8 |

The dated-comparison family has a task-success floor (0/8). Errors include expired or not-yet-valid values, reversed date assignments, a wrong entity, false unavailability and incomplete explanations. This is a measurement/model adequacy concern, not a persona effect; C0 has no persona treatment.

## Metric discrimination and evaluator audit

| Metric | AI distribution | Scored | Numeric variance | Auto v2 / AI agreement |
| --- | --- | ---: | ---: | --- |
| factual | {"Incorrect": 21, "Correct": 11} | 32 | None | 21/32 |
| temporal | {"Incorrect": 19, "Correct": 11, "Unverifiable": 2} | 32 | None | 23/32 |
| task_success | {"Failure": 21, "Success": 11} | 32 | None | 28/32 |
| semantic_completeness | {"YES": 29, "NO": 3} | 32 | None | 30/32 |
| relevance | {"5": 21, "4": 8, "3": 3} | 32 | 0.4475806451612903 | 21/21 |
| coherence | {"5": 21, "4": 8, "2": 2, "3": 1} | 32 | 0.7096774193548387 | 21/21 |
| linguistic_fidelity | {"4": 11, "3": 7, "2": 6} | 24 | 0.6938405797101449 | 4/19 |
| behavioral_fidelity | {} | 0 | None | 0/0 |
| delivered | {"1": 11, "2": 13, "3": 8} | 32 | 0.6038306451612904 | 29/32 |
| supported | {"0": 15, "3": 5, "1": 10, "2": 2} | 32 | 1.184475806451613 | 32/32 |
| stale_adoption | {} | 0 | None | 32/32 |

FC Correct and task Success coincide item by item in this observed calibration (100%); separate human-readable construct judgments and authored counterexamples are retained. Complete wrong answers occur, so completeness and correctness discriminate. RR/CC exact concordance is 93.75%; their ceiling concentration limits resolution. LF is narrow, AI-proposed and not independently validated; BF has no answer/acknowledgment ordering opportunity and therefore no scores, not zero fidelity.
The frozen v1 automatic scorer had shared FC/TC assignment in its restricted grammar and missed explicitly labeled code syntax. Its source and every score remain preserved. Version2 separates temporal scope and recognizes declared type labels without changing any output. Both versions are compared on the identical AI-proposed evaluation spans; a separate v1 original-parser view exposes extraction dependency. Shared reference answers and shared proposed spans mean this is system agreement, not independent evaluation accuracy. Prose/date attachment still requires semantic review. AM020/AM024 retain temporal Unverifiable due to entity/time attribution uncertainty.

## Decision and next bounded diagnostic

Do not start the 80-request pilot yet. A single 16-request category-C diagnostic is prospectively registered on calibration indices00–07, with unchanged evidence/question/references: concise output and date-slot output instruction packages. No pilot cases are selected or removed. Selection rules are fixed before diagnostic outputs; if neither arm qualifies, preserve NO-GO rather than optimize until an accuracy target is reached.

## P5 closeout and research tree

P5 engineering is completed: the existing eight oracle outputs are not rerun. Existing AI task proposals remain 2/8 historical Instruct versus8/8 oracle, unconfirmed. Full/reduced evidence were both sufficient; content, length, position, salience and literal answer exposure changed. No pure retrieval, sufficiency or Persona effect is identified. The existing eight-item paired comparison and semantic evidence package are reused for researcher review; no new P5 inference or algorithm work occurs.
P0 PASS/frozen; P1 ACTIVE; P2/P3/P4 PAUSED; P5 diagnostic completed with semantic confirmation outstanding; P6 PAUSED. The negative ESCP result is preserved; no new algorithm is developed. The central S/F/H question, separate reliability/fidelity dimensions and future constrained P6 objective remain recorded.

## Limitations and reproduction

Evidence source numbering and B-versus-D value prefixes can reveal target/distractor structure; only four shared administrative-task ancestors exist. Burden changes jointly with generated record content, so a pure context-length effect is not identified. These materials are development-only and unsuitable for independent validation claims. Future independent work needs independently authored/counterbalanced templates, target-value coding, requested-date balance, independent metric-specific annotation and precision planning with speaker/template dependencies.
Reproduce without inference: `.venv/Scripts/python.exe tools/p1_measurement_run.py audit --category A_C0 --output <new-workspace-path.json>`. The generation command was `.venv/Scripts/python.exe tools/p1_measurement_run.py run --category A_C0 --preflight docs/validation/p1/measurement_pilot_v1/A_C0_preflight_v1.json`; replay is prohibited because the32-request allocation is spent. Scores, witnesses, alternatives and blank human fields are in `docs/validation/p1/measurement_pilot_v1/A_C0/measurement_v1/`. Targeted tests:38 passed after scoring independence and syntax corrections;39 passed after adding the category-C scientific-invariance check. Earlier failures are preserved in the final development record.
