# P1 measurement recovery: consolidated O/Q diagnostic report v2

Maintainer: Yaxin ZHENG. Official paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE.

**Engineering complete: 24 new requests succeeded, no failures or retries. Eight archived D0 responses were reused. SCIENTIFIC DECISION PENDING REVIEW. No configuration is selected; fallback and S/F/H inference remain unexecuted.**

## Research scope, governance and amendment

This is P1 development measurement recovery for the original S/F/H programme, not a Persona effect study or independent validation. Research Protocol v1.1 remains the approved historical baseline; v1.2 remains proposed; existing approved addenda retain only their documented scope. No historical protocol, score, raw response or structural classification was rewritten. P0 frozen; P1 active (P1a/P1b/P1c evidence retained and P1d main validation NO-GO); P2/P3/P4 paused; P5 current diagnostic closed with its AI semantic adoption still outstanding; P6 paused, including preserved ESCP negative findings. No work was launched in paused phases.

The researcher prospectively resolved the Q1-v1 tie: choose the first qualifying component in the original frozen reference-component order. Only the four D2/D3 requests for cases04/05 were repaired. They select the assigned bay, B5238/B5284 respectively. Their questions explicitly identify that attribute. All original20 executable request objects, hashes, token records and relative order remain identical. The four repaired requests are appended in their original blocked-inventory order, avoiding reordering the20 frozen objects. The v1 manifest/report remain intact. `Q1_amendment_v2.json` records the actual user instruction, no fabricated human timestamp. This is prospective design authorization, not semantic approval.

Selection remains deterministic: first two lexical case IDs per original task family, cases00–07, without score inputs. These previously observed cases share Alderbrook/schema ancestry and eight-row evidence burden. Outcome-independent selection is not an independently blinded or representative sample. Original factorial candidates were not selected or replaced using their own C0 scores.

## Source audit, D0 reuse and exact intervention

All32 archived C0 request/output/reference records were rechecked with the existing source audit. Eight D0 prompts reconstruct byte for byte; model, backend, tokenizer, template, seed, decoding, identities and original output hashes match. D0 is absent from the24 new-request inventory. Exact per-case original/new prompt diffs and source fingerprints are in `prompt_and_D0_integrity_v2.json`. The 43-file prior recovery seal passed; the preceding large historical suite was not rerun. The original log prefix is preserved.

Original32 proposals remain: task success11/32, complete-answer forms29/32, evidence-supported components29/64; task-family successes4/8 single lookup,2/8 dual component,5/8 relational chain,0/8 dated comparison. Automatic/AI task agreement28/32 and factual agreement21/32 remain observations of agreement, not accuracy. Objective witness checks find unique supported original references, including chain links; no reference correction is adopted. Human scientific review remains necessary. Cases02/22 false unavailability, case07 contradictory March answers, and cases10/30 entity/temporal attribution remain consequential disagreements, preserved in the CSV.

D0=O0Q0; D1=O1Q0; D2=O0Q1; D3=O1Q1. O1 retains the exact fact-line multiset, values, provenance and dates, groups by entity and sorts by validity date, adding entity headings. Q0 question and reference are unchanged across O. O jointly changes position, length, presentation and salience; it is not pure retrieval. Q1 retains the same evidence as its Q0 partner and requests one original answer component. It changes cardinality, complexity and response requirements; it is not pure reasoning or the same task-competence estimand. Archived D0 also differs in execution time from new arms. No literal answer was added to questions as an oracle shortcut.

| Case | Q1 reference | Frozen accepted aliases |
| --- | --- | --- |
| p1_measure_calibration_00 | Bay B5022 | Bay B5022, B5022 |
| p1_measure_calibration_01 | Bay B5096 | Bay B5096, B5096 |
| p1_measure_calibration_02 | Bay B5102 | Bay B5102, B5102 |
| p1_measure_calibration_03 | Bay B5177 | Bay B5177, B5177 |
| p1_measure_calibration_04 | Bay B5238 | Bay B5238, B5238 |
| p1_measure_calibration_05 | Bay B5284 | Bay B5284, B5284 |
| p1_measure_calibration_06 | Bay B5316 | Bay B5316, B5316 |
| p1_measure_calibration_07 | Bay B5361 | Bay B5361, B5361 |

Normalization is frozen Unicode NFKC, whitespace collapse, casefold, and removal of at most one final period. Success requires the entire normalized output to match an alias. No substring, negation removal, markdown stripping or post-output alias additions. Wrong exact bay identifiers are Incorrect/Failure; unsupported prose is Unverifiable/Uncertain; absent records, observed empty answers and N/A remain distinct. Q1 automatic factual output is the strict answer-state classification, coupled to its task matcher; it is not a second independent factual evaluator. No original two-date scorer is misapplied to a single-date Q1 request.

## Engineering record and budget

Manifest: `docs/validation/p1/measurement_recovery_2x2_v2/diagnostic_manifest_frozen_v2.json`; SHA-256 `c235e309a3726952fc1edc2f96a9259d537293bd4e61ce0a24e9234abfdb5404`. Same Qwen/Qwen3.5-2B Q4_K_M third-party development GGUF, SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`. Backend llama.cpp b11573-0f701c882, SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. Template SHA-256 `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`. Native tokenizer and all DLL identities are bound in the manifest. The accepted partially verified conversion lineage remains unsuitable as fully established confirmatory provenance.

CPU-only, four threads,4096 context,96 output-token cap, seed42, temperature0, top-p1, no custom stops, no cache, no warmup generation, no retry. All24 prompts passed native and official tokenizer equality, live token-array equality and CPU configuration checks before completion requests; inputs range 551–652 tokens. The20 earlier logs remain unchanged and four new logs bind the repaired prompts. Input and returned output token IDs and native termination are preserved; native-minus-returned-token differences are zero for all24.

The first v2 resource preflight was blocked and preserved. After the researcher freed RAM, full `preflight_v2.json` passed at 2026-10-15T11:27:01.118761+00:00 with 5,017,251,840 available bytes. A fresh in-run preflight also passed. The existing minimum3GiB (3,221,225,472bytes) was not lowered. This gate checks available RAM before model loading; it is not a continuous post-load reserve. During model residence, 49 observations recorded minimum available physical RAM 1,994,698,752bytes, maximum sampled working set 3,134,148,608bytes and OS-reported peak working set 3,201,662,976bytes. No unrelated application was closed. These are available OS observations, not an isolated RAM causal estimate.

Run: `results/p1_measurement_recovery/v1/runs/20261015T112741-aed4976fcefe4553923380003fb63eab`. Its event journal preserves actual order, request IDs, prompts, full HTTP payloads/raw response bodies, token arrays, stop reasons, timestamps, CPU latency, RAM, source snapshots and server log. New generation count24, received/results24, failures0, retries0. Native stops22 `eos`,2 `length`; output lengths18×7,1×48,1×26,2×27,2×96 tokens. Summed completion latency 197.415s, mean 8.226s; total runner time 211.476s. Background OS activity was not experimentally controlled; latency is descriptive. Native EOS/EOG compatibility caveat remains.

Global authorization ledger: A_C0=32/32, B_FACTORIAL=0/80, C_DIAGNOSTIC=40/48; total72/160 attempted,88 remaining (B80+C8). The24 new generations are charged to diagnostics. No unused allocation transfers, D0 repeats, fallback generations, factorial generations, training or independent-validation requests occurred. Remaining8 diagnostics are conditionally reserved for the fixed fallback, not arbitrary prompt variants. B80 still needs the separately required pilot authorization.

## Unconfirmed semantic results

| Condition | AI task success | Automatic success | Task agreement | AI complete answer form | AI supported components | Audited success |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| D0 | 1/8 | 1/8 | 7/8 | 6/8 | 5/16 | Pending |
| D1 | 5/8 | 5/8 | 8/8 | 8/8 | 10/16 | Pending |
| D2 | 5/8 | 5/8 | 8/8 | 8/8 | 5/8 | Pending |
| D3 | 5/8 | 5/8 | 8/8 | 8/8 | 5/8 | Pending |

AI factual/temporal Correct counts are1/8,5/8,5/8,5/8 for D0–D3, with all other observed answers proposed Incorrect. There are no missing or empty outputs and no AI-proposed Unverifiable primary task/factual/temporal labels in this32-item panel. This does not eliminate evaluator uncertainty or the automatic scorer's Unverifiable categories. All24 new first-response candidates are AI-recoverable; this is not independently adjudicated boundary accuracy.

Original parser labels are preserved: new22 AMBIGUOUS and2 TRUNCATED; D0 five AMBIGUOUS and three TRUNCATED. Bare bay answers and attribute labels can trigger parser uncertainty/native EOS alias limitations even when human-readable candidates are clear. No new structural label replaces them. D1 cases06/07 deliver both correct date-bound answers before unfinished explanatory tails: task and answer-form completeness proposals are positive while structural status remains TRUNCATED. A stricter whole-utterance syntactic rubric is an explicitly recorded alternative, not silently adopted. Complete wrong answers in other cases remain task failures.

| Original scenario family | D0 | D1 | D2 | D3 |
| --- | ---: | ---: | ---: | ---: |
| dated_comparison | 0/2 | 2/2 | 2/2 | 2/2 |
| dual_component | 0/2 | 1/2 | 2/2 | 1/2 |
| relational_chain | 1/2 | 1/2 | 0/2 | 1/2 |
| single_lookup | 0/2 | 1/2 | 1/2 | 1/2 |

Each cell has two cases. Under Q1, these are ancestry strata, not retained dual-component/chain/comparison tasks: all Q1 requests ask one bay. In Q0, the paired AI organization description improves four cases and worsens none (difference4/8), while in Q1 two improve and two worsen (net0/8). Case-level contributions are retained in `descriptive_analysis_UNCONFIRMED_v2.json`. These are unconfirmed descriptive package comparisons; no significance, population mechanism or common Q0/Q1 competence effect is claimed. Eight paired purposive cases and shared construction ancestors cannot support precise population inference. Equal group means do not imply absence of case heterogeneity.

## Evaluator audit and measurement limits

| Endpoint automatic/AI agreement | D0 | D1 | D2 | D3 |
| --- | ---: | ---: | ---: | ---: |
| task_success | 7/8 | 8/8 | 8/8 | 8/8 |
| factual | 5/8 | 5/8 | 8/8 | 8/8 |
| temporal | 5/8 | 5/8 | 0/0 | 0/0 |
| semantic_completeness | 7/8 | 8/8 | 0/0 | 0/0 |

0/0 means the automatic secondary endpoint was not implemented for Q1, not perfect agreement or scientific N/A. Overall task agreement31/32; factual26/32; temporal10/16 covered; completeness15/16 covered. Task disagreement is D0 case07 (automatic Uncertain, original AI Failure). Q0 factual/temporal discrepancies concern case02 and cases06/07 in both organizations: conservative automatic abstention and date-attachment coverage versus semantic interpretation. Neither scorer is human ground truth. Confusion matrices and exact disagreeing identities are machine-readable. Matching task decisions on all24 new outputs do not independently validate the evaluator.

AI task success and factual/temporal correctness coincide item by item in this panel; separate constructs have limited empirical discrimination in these tasks. Q1 automatic task/factual outputs share a matcher by design. Completeness does discriminate from correctness: all24 new answers have proposed complete answer forms while only15 succeed. These relationships are reported rather than fabricated into score differences.

| Condition | Relevance distribution | Descriptive variance | Coherence distribution | Descriptive variance |
| --- | --- | ---: | --- | ---: |
| D0 | {'3': 2, '4': 1, '5': 5} | 0.734375 | {'2': 2, '4': 1, '5': 5} | 1.609375 |
| D1 | {'5': 8} | 0.0 | {'4': 2, '5': 6} | 0.1875 |
| D2 | {'5': 8} | 0.0 | {'5': 8} | 0.0 |
| D3 | {'5': 8} | 0.0 | {'5': 8} | 0.0 |

These variances summarize the observed ordinal codes, not interval-scale population parameters. New relevance is at ceiling; Q1 coherence is at ceiling. Zero variation cannot establish a zero conditioning effect. The simple answers provide little pragmatic/behavioral range. D0 source proposals remain unchanged. Fresh masked reinspection suggested relevance4/coherence3 rather than original3/2 for cases06/07; all four ordinal alternatives remain separately recorded, unadopted, in the analysis file. This is intra-assistant scoring instability, not independent inter-rater evidence. Human review should resolve it without changing the registered rubric to create variation.

The masked32-item review was frozen before joining protected condition IDs or calculating new automatic scores. Question cardinality and familiar prior D0 outputs still allow assignment inference; the same assistant previously constructed/read stimuli. This is not fully blind or independent annotation. Raw response hashes, evidence references, reasons, uncertainty, alternatives and blank human fields are preserved. No reviewer identity, human score, human timestamp or inter-rater agreement was invented.

Persona Fidelity is not validated here. C0/OQ provides no matched persona intervention; one bay code has little linguistic or behavioral opportunity. Unavailable fidelity is not zero. Q1 may facilitate exact matching while reducing construct coverage. Keep linguistic/behavioral fidelity and all reliability dimensions separate in the future main S/F/H study.

## Reviewer file and decision status

`docs/validation/p1/measurement_recovery_2x2_v2/consolidated_researcher_review_v2.csv` contains56 unique actual observations: original32 C0 (eight D0 and24 audit-only) plus24 new requests. Exactly32 D0–D3 rows form the decision panel. All researcher fields are blank. Original factual disagreements come first, then original task disagreements, failed single lookups, other disagreements and remaining records. Each row supplies full question, evaluation/request date, trusted evidence, references, raw output, automatic/AI scores, provenance, uncertainty and separate human task/factual/temporal/completeness/failure fields.

The final decision requires researcher-confirmed labels on those32 rows: success>=6/8 AND automatic exact agreement>=7/8, fixed priority D0,D1,D2,D3. Partial, Unverifiable, Missing and N/A remain explicit full-denominator categories. No configuration is selected from AI scores. The AI counts are all below6/8, but **the formal negative branch is not activated without the required audit**. Current status: **SCIENTIFIC DECISION PENDING REVIEW**. The researcher need not reauthorize the already completed24 requests or repeat the Q1 tie decision.

If a configuration qualifies after audit, prepare its disjoint eight-case S/F/H pilot; do not execute80. A qualifying configuration with a0/2 family invokes only the disclosed prospective development restriction, not permanent scope deletion. If no condition qualifies, the already authorized fixed fallback can activate after fresh full preflight; no additional prompt design is proposed. Its eight C0 labels then require real audit: >=7/8 permits pilot preparation; below7/8 stops for formal model feasibility review. Later80-pilot execution requires separate authorization and eight C0 first, audited>=6/8 before the remaining72. No case substitution or outcome-based reallocation is allowed.

## Fixed fallback preparation (no inference)

Sixteen new synthetic English cases are frozen, each with a unique target persona,4–6 dated statements, explicit old/current intervals, one uniquely supported query-date answer, frozen aliases and distinct old answer. Eight separately authored task-wording/domain templates each contribute two scenarios. They still share one single-attribute temporal schema and AI construction provenance; different names are not proof of independent linguistic sampling.

Construction seed731902 and allocation seed731901 are frozen. Within each template pair, sorted case IDs are shuffled using recorded Python Random; first goes to calibration and second to pilot. Eight calibration and eight pilot cases are disjoint. Inventory checks found no exact prior case/speaker/name/question overlap against documented prior development and P1d candidate sources; this is not proof of complete semantic independence. No held-out model outputs were accessed. The bank was frozen before the O/Q run, and no output was used for construction, revision, allocation or replacement.

Candidate calibration manifest: `docs/validation/p1/measurement_recovery_2x2_v2/fallback_bank_v1/fallback_calibration_manifest_candidate_v1.json`; SHA-256 `b23b9a35bba1ff9313e71f75759e8107b3d23b54f765c5fe736094263ff17cde`. Eight C0 candidates, conditional authorization **not activated**.

Candidate pilot manifest: `docs/validation/p1/measurement_recovery_2x2_v2/fallback_bank_v1/fallback_pilot_manifest_candidate_v1.json`; SHA-256 `4be7b1959779371502a0e562a589c942676644ef86897196912677978d4da382`. Eight disjoint cases×C0–C7/N_style/N_history=80 planned requests, **not qualified and not authorized to execute**. It is not a qualified `P1_SFH_measurement_pilot_manifest_v2`.

All88 candidate prompts passed actual pinned GGUF/official tokenizer validation. Sixteen active/diagnostic control pairs match full prompt token length. Trusted evidence, question, reference, date, speaker and context remain fixed within each paired pilot case. S adds style without task facts; F adds nonconflicting supplementary facts; H supplies the dated old target value. Speaker attribution in “My …” history relies on the target-persona context and remains a manipulation assumption. Procedural controls remain LENGTH_MATCHED_DIAGNOSTIC_ONLY: token equality does not establish semantic neutrality.

The prospective C3−C0 endpoint is outdated-answer adoption among all eight eligible temporal pilot cases, with separate current, outdated, wrong-entity, contradictory, Unverifiable, empty and missing outcomes. Missing/unknown are not observed outdated adoption; full-denominator incidence and identification bounds are retained. This restricted fallback cannot independently validate general dialogue reliability, coherence, persona fidelity or real-speaker generalization, and cannot replace the full original programme. Fallback calibration results: **not generated**.

## Validation, reproduction and limitations

Recorded relevant regression command: `-m pytest tests/test_p1_recovery_v2.py tests/test_p1_recovery_measurement_v2.py tests/test_p1_recovery_2x2.py tests/test_p1d_instruct_smoke.py tests/test_response_status.py -q` using the repository virtual environment. Result: **75 passed,1 skipped in18.18s**. The skipped legacy test expects an unexecuted v1 reviewer template; new v2 tests verify all56 actual rows, original labels, actual24 raw outputs, masked annotation binding, strict Q1 scoring, human-gate provenance/priority, nonbinary denominators and fallback token/control integrity. Earlier pre-inference subset40 passed. No broad historical test sweep was repeated. Automated tests establish implementation properties, not valid human measurement.

Actual development failures/corrections are retained in `development_events_v2.json`: first RAM block; a pre-freeze fallback control-length search failure repaired without outputs; an optional process query denied; and a failed empty patch at an erroneous path before correction to relative workspace paths. No outside file was created and no model attempt failed. Old reports, sources and failed hypotheses remain intact.

Read-only reproduction: `.venv/Scripts/python.exe tools/p1_recovery_v2.py audit` validates the24-run inventory and raw HTTP reconstruction; source snapshots preserve exact execution code. Analysis/review outputs are immutable snapshots with linked inputs and code. Do not rerun `prepare`, `run` or write-once export commands merely to reproduce a report: the global claim/attempt ledger rejects duplicates and all24 attempts are already consumed. Future conditional execution requires its separate bound manifest and gate, not this old run command. `tools/p1_recovery_gate_v2.py` prepares review imports without inventing confirmation.

Changed implementation: `tools/p1_recovery_v2.py`, `tools/p1_temporal_fallback.py`, `tools/p1_recovery_gate_v2.py`, `tools/p1_recovery_measurement_v2.py`, `tools/p1_recovery_annotation_v2.py`, `tools/p1_recovery_analysis_v2.py`, `tools/p1_recovery_closeout_v2.py`, `tests/test_p1_recovery_v2.py`, `tests/test_p1_recovery_measurement_v2.py`. Added evidence is under `docs/validation/p1/measurement_recovery_2x2_v2`, with this single consolidated report and an append-only research-log entry. Reproducibility manifest: `docs/validation/p1/measurement_recovery_2x2_v2/reproducibility_manifest_v2.json`. It binds source/report/test hashes, original lineage, exact input/output files, allocation ledger, Git HEAD/dirty state and truthful software recording times. No Git commit, push or author change. No claim of confirmatory results, validated persona fidelity, algorithm originality or PLOS ONE submission readiness.
