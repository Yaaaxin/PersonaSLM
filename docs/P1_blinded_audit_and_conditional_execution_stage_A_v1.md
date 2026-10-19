# P1 blinded scientific audit and conditional execution — Stage A v1

Researcher and maintainer: Yaxin ZHENG. Official paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Scientific language: English.

**Stage A complete. New generations:0. Actual researcher ratings:0. No real audit was unblinded. Stage B is inactive and awaits a complete researcher-reviewed sheet and the future explicit message `unblind and proceed`.** This report intentionally omits earlier condition-level success aggregates and scoring suggestions to support the current partial-blinding procedure.

## Governance and scientific purpose

Phase P1, RQ1/RQ2: establish measurable task reliability under fixed sufficient evidence before the core S/F/H pilot. The original C0–C7 programme, separate reliability dimensions and linguistic/behavioral Persona Fidelity remain central. This work does not estimate a new Persona effect. Research Protocol v1.1 remains the frozen research-design baseline; v1.2 remains proposed. The separately registered English-language, P1c and P1d addenda remain valid only within their actual approved scopes. No historical protocol, experiment, annotation or scientific conclusion was overwritten.

P0: frozen; P1: active (P1a–P1d retained, main P1d independent-validation execution still NO-GO); P2/P3/P4: paused; P5: completed diagnostic with prior semantic-adoption limitations preserved; P6: paused with prior ESCP negative evidence preserved. No paused-phase experiment, new algorithm, training or independent-validation generation was launched.

The current researcher instruction prospectively replaces the later pilot/fallback **execution** gates with provisional automatic thresholds. The O/Q **selection** gate still requires actual researcher ratings. This explicit change is recorded in `stage_policy_frozen_v1.json`, preserving earlier human-gate policies as historical versions. The latest fixed eight-case manifests retain every registered family: no outcome-driven family deletion or replacement is performed. A zero-success source family, if later observed in the audited O/Q panel, will be disclosed rather than silently changing these new fixed manifests.

## Partial-blinded researcher audit

Review sheet: `docs/validation/p1/blinded_audit_stage_a_v1/blinded_researcher_audit_v1.csv`.

SHA-256: `5bc9712ef9c5ad0e2a1769e55d99b72f7a4e99ab9e77a4657a605b642bfb1781`.

Exactly32 completed decision records are included. Source request identities are initially sorted, then shuffled once using Python `Random(731951)`; a separate `Random(731952)` produces128-bit opaque review IDs. No grouping or stratification uses condition, family or previous scores. The source records are the32 D0–D3 observations in the earlier56-row audit; the other24 original calibration records are outside this decision sheet.

Only the anonymous ID, exact original question, registered evaluation date, canonical trusted evidence, frozen reference answer, complete raw response, required answer components and blank researcher fields are exposed. There are no condition labels, family columns, automatic/AI scores, success proposals or condition aggregates. All raw responses and question strings are preserved, including contradictory statements, incomplete tails and citations.

The same canonical entity/attribute/date table is used for every record. All facts, entity identities, values and inclusive validity intervals are preserved. Display evidence rows use local E01/E02 identifiers; the separate key maps these losslessly to original source IDs. **Local display IDs are not the raw response's original source identifiers.** A literal citation that cannot be resolved from the displayed substantive facts should be flagged UNCERTAIN with a comment; do not guess a source mapping or open the key to resolve it during review. Original provenance remains recoverable after authorized unblinding. This presentation transformation applies only to the review display, never to experimental prompts.

Blinding is partial, not double-blind. Q0/Q1 question cardinality is recognizable, the same cases repeat, raw citations may reveal case identity, outputs may be familiar, and the researcher already knows earlier aggregate outcomes. The reviewing researcher is not an independent second annotator. No inter-annotator agreement or independent human-validation claim is made.

## How to complete the sheet

Work on a copy, such as `completed_blinded_researcher_audit.csv`, and preserve the original blank snapshot. Fill task, factual and temporal decisions on every row using exactly:

`CORRECT`, `INCORRECT`, `PARTIAL`, `UNVERIFIABLE`, `UNCERTAIN`, `NOT_APPLICABLE`.

Assess task success from all requested components, not mere presence of a correct token. Assess factual claims against evidence and temporal claims against the requested dates. A historically true fact can be wrong when assigned to the current query date. A complete wrong answer is not a correct task answer; an unfinished explanatory tail does not automatically mean required answers are missing. Do not force ambiguous statements into correctness or incorrectness. Frozen references may themselves be questioned and should then be flagged.

For any non-CORRECT applicable decision, provide one or more failure types separated by semicolons and an explanatory comment. Allowed types: Wrong entity, Outdated value, Wrong date attribution, Contradictory answer, Missing required component, Incomplete answer, Reference-answer ambiguity, Scorer error, Unsupported answer, Other documented failure. NOT_APPLICABLE requires a reason; applicability is not silently changed or removed from the denominator. Keep factual, temporal and task decisions separate. Do not consult previous automatic suggestions to create a scorer-error label during blind review; unresolved scorer questions can be examined after authorized unblinding.

Do not edit IDs, row order, questions, evidence, references or raw responses. The validation tool checks exact column/row inventory, all immutable displayed fields, allowed labels, explanatory fields, duplicate IDs and key hashes. CSV serialization/newline differences alone do not invalidate unchanged parsed content. All current researcher fields remain blank.

The frozen mapping is preserved: CORRECT→Success; INCORRECT→Failure; PARTIAL→Partially correct; UNVERIFIABLE/UNCERTAIN→Uncertain; NOT_APPLICABLE→N/A. Only CORRECT contributes1 to the full-success numerator. For the previously registered **exact-category agreement** gate, PARTIAL remains distinct and does not automatically agree with automatic Failure; uncertain/N/A outcomes are not silently collapsed into incorrect or excluded. The binary full-success numerator and categorical agreement are different summaries.

## Separate key and authorization

Key: `docs/validation/p1/blinded_audit_stage_a_v1/restricted/unblinding_key_v1.json`.

Key SHA-256: `8ab628c1a74a7fbb3f09c0a8f266359ab32d6c9835db39f4afe3406647dc896f`.

It maps anonymous IDs to original case, condition, task family, output identifier, original evidence/response/prompt hashes, canonical-display hash and original evidence provenance. The key is frozen before review and must not be modified. It is separate by file/location, not a security boundary against a researcher who deliberately opens it. Avoid reading it while completing the blinded sheet.

Deterministic tools: `tools/p1_blinded_audit.py` validates and, only with activation, unblinds; `tools/p1_conditional_execution.py` revalidates the authentic review and frozen inputs before bounded execution. The literal phrase quoted inside the present planning instruction is **not** an activation. A future standalone researcher message is required. Tool validation cannot independently prove who typed a CSV or a text file; the operator must use the real researcher submission and actual conversation authorization, never an assistant-authored confirmation.

No completed-review file, activation record, human timestamp, joined human annotation snapshot or real unblinding result was manufactured in Stage A. The initial blank sheet cannot pass completeness validation.

## Frozen mutually exclusive candidate manifests

| Configuration | Planned requests | Exact path | SHA-256 |
| --- | ---: | --- | --- |
| D0 | 80 | `docs/validation/p1/blinded_audit_stage_a_v1/manifests/P1_SFH_measurement_pilot_D0_v2.json` | `157afc1ca2243c58527f41c90cf120cdd215e51c6a17a01a65bf3bf7bd55568a` |
| D1 | 80 | `docs/validation/p1/blinded_audit_stage_a_v1/manifests/P1_SFH_measurement_pilot_D1_v2.json` | `1cba4398e7e63dc2e077648b2a038a767ffb10e5a0444435b07921723d89a920` |
| D2 | 80 | `docs/validation/p1/blinded_audit_stage_a_v1/manifests/P1_SFH_measurement_pilot_D2_v2.json` | `6936bd214e8691786366ecbc80cfb1ae56231f2a1645016dc2e691164e8b6016` |
| D3 | 80 | `docs/validation/p1/blinded_audit_stage_a_v1/manifests/P1_SFH_measurement_pilot_D3_v2.json` | `d0b3e4f45e4abe729899f981f85044140c6cef23e320f25aa0e9e29997ba60c9` |
| minimal_temporal | 80 | `docs/validation/p1/blinded_audit_stage_a_v1/manifests/P1_minimal_temporal_SFH_pilot_v2.json` | `6bc6421823371b9cad6140aad1046a3f9aebc2d4594e277b3601a3f4b6fc849e` |
| fallback_calibration | 8 | `docs/validation/p1/measurement_recovery_2x2_v2/fallback_bank_v1/fallback_calibration_manifest_candidate_v1.json` | `b23b9a35bba1ff9313e71f75759e8107b3d23b54f765c5fe736094263ff17cde` |

Index: `docs/validation/p1/blinded_audit_stage_a_v1/manifest_index_frozen_v1.json`. These are408 **candidate request specifications**, not408 authorized generations. Four O/Q alternatives and one fallback pilot are mutually exclusive. The current remaining budget is88: B_FACTORIAL80 and C_DIAGNOSTIC8. Actual historical use remains A32/B0/C40=72 of160. Stage A consumes0 and reserves no additional inference attempts.

Each80-request pilot contains exactly eight C0 cells first, then the remaining72 C1–C7/N_style/N_history cells. Case IDs are sorted before shuffling, with fixed seeds731960 for the C0 block and731961 for the remainder. Case pairing, conditions and seeds are frozen. D0 pilot prompts are byte-identical to the earlier unexecuted registered factorial candidate prompts, although request namespace and execution order are versioned for the new conditional controller. This future D0 **pilot** must not be confused with the eight archived diagnostic D0 responses, which remain reused and will never be regenerated.

O/Q alternatives use the previously registered `p1_measure_factorial_00`–`07` cases, two per source family. They are disjoint in case/speaker/exact question identity from all32 C0 calibration cases, and none has a current-scope generation attempt. Their construction has already been used for development planning: they are not independent confirmation data. Four template ancestors, repeated given-name patterns and a common Elmbridge lexical block limit independence. Each has12 evidence rows, compared with8 in the selected O/Q diagnostic cases; this fixed workload difference may affect baseline readiness and is not repaired using future results.

D1/D3 apply the frozen organization rule to identical facts. D2/D3 apply the authorized original-reference-order single-component rule. O changes position, formatting, length and salience; Q changes cardinality and task demands. These alternatives do not isolate pure retrieval or pure reasoning. References and questions are identical across S/F/H conditions within each chosen configuration.

## Minimal temporal bank and factorial audit

The existing16-case bank, construction seed731902 and allocation seed731901 are preserved exactly. Eight calibration and eight pilot identities/speakers are disjoint. One case per each of eight authored template families goes to each pool. Every case has4–6 dated facts, explicit nonoverlapping old/current target intervals, a registered query date, unique current and outdated values, frozen aliases and sufficient evidence. Current-value references pass explicit entity/attribute/date witness checks. The original dated H statement is valid at its historical date and outdated at the query date; trusted evidence may correctly contain both values.

All original pilot and fallback cases passed objective reference, interval, identity and answer-leakage checks. Existing fallback inventory checks found no exact prior calibration/OQ/held-out candidate case, speaker or question reuse in the documented sources. This is not proof of semantic or population independence: all fallback tasks share one temporal-lookup schema, and the profiles were AI-authored. No held-out generated answers were read or used for design.

For all five pilots, C0–C7 match the v1.1 S/F/H table. Trusted evidence, question, references, evaluation date, speaker and fixed context are constant within a case. S supplies linguistic instructions and no target facts; F supplies non-answer supplementary facts and no current-value answer; H appears only in C3/C5/C6/C7 and repeats the registered dated old statement. Current and outdated values in the fixed trusted ledger are not mistaken for H contamination. N_style/N_history contain no task-specific entity/value information.

Semantic limitations remain: H uses first-person target attribution and carries discourse features; F may alter entity salience; some style instructions request complete sentences while Q1/minimal questions request one identifier. Thus exact automatic matching may be insensitive to legitimate stylistic realization. Responses outside its frozen grammar remain uncertain, not silently factual errors. This is a measurement limitation to inspect, not a reason to change prompts or scoring after results. No substantive scientific-definition correction was made.

| Pilot | Actual input-token range | Matched control pairs | Tokenizer record provenance |
| --- | ---: | ---: | --- |
| D0 | 786–903 | 16/16 | {'REUSED_EXACT_NATIVE_PROMPT_RECORD': 80} |
| D1 | 888–1019 | 16/16 | {'NEW_OFFLINE_NATIVE_TOKENIZATION_NO_GENERATION': 80} |
| D2 | 784–890 | 16/16 | {'NEW_OFFLINE_NATIVE_TOKENIZATION_NO_GENERATION': 80} |
| D3 | 888–1001 | 16/16 | {'NEW_OFFLINE_NATIVE_TOKENIZATION_NO_GENERATION': 80} |
| minimal_temporal | 353–592 | 16/16 | {'REUSED_EXACT_NATIVE_PROMPT_RECORD': 80} |

All400 pilot requests and the8 fallback calibration candidates have actual native-token records.240 changed prompts were newly tokenized offline;160 pilot records and8 calibration records reused exact matching native records with verified prompt/token hashes. Full prompt reconstruction and official/native tokenizer agreement are preserved. Context4096/output96 capacity checks pass. N_style matches C1 and N_history matches C3 per case in every package. These80 matched candidate pairs are not80 independent controls; they reuse cases/texts across mutually exclusive packages.

The controls remain **LENGTH_MATCHED_DIAGNOSTIC_ONLY**. Generic document descriptions can change instructions, discourse or topic; token equality is not semantic neutrality. No human control certification was invented. Material corrections affecting definitions would need a prospective registered amendment; no such correction was performed here.

## Future conditional execution (not performed)

After the researcher supplies the completed sheet and writes `unblind and proceed`, validate all32 labels, row fingerprints, key, manifests, model and source hashes. Apply audited success>=6/8 AND frozen automatic exact agreement>=7/8, fixed priority D0,D1,D2,D3. Do not select by maximum accuracy. Unknown/partial/N/A labels stay in the eight-request denominator.

Branch A: load only the first qualifying package. Generate its eight C0 pilot cells. Automatic success>=6/8 permits the other72; otherwise stop, preserve all outputs and mark AUTOMATIC DEVELOPMENT GATE NOT PASSED. Diagnostic8 remains unused. Maximum80 new requests.

Branch B: if no O/Q configuration qualifies, generate the already frozen eight fallback calibration C0 cells using C_DIAGNOSTIC. Exact/alias automatic success>=7/8 permits the already frozen temporal pilot. Its eight C0 cells must reach automatic>=6/8 before the remaining72. Failures stop generation without replacement, new variants, family exclusion or model switch. Maximum88 new requests. Failure of the first fallback gate warrants model-feasibility review, not automatic P3 execution.

Each automatic gate records all eight case scores, raw output hash, scorer/source version, threshold, decision, actual software time and pending human-review status. Unknown/missing responses never disappear from denominators. Later researcher disagreement must be a new sidecar, preserving the original gate and conditional-sampling consequences. No gate demonstrates model incapability, independent accuracy or confirmatory validity.

The future runner uses exclusive global claims/attempt files, category caps, one attempt per ID, no retries and no implicit resume. It checks the exact selected branch before loading the model and verifies all live prompt token arrays before generation. An infrastructure failure preserves attempts and stops; no silent request replacement. The runner has been unit-tested with synthetic data and rejection paths, **not empirically tested by new model inference in Stage A**.

## Model, measurements and statistical readiness

Pinned model: Qwen/Qwen3.5-2B Instruct Q4_K_M, GGUF SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`; llama.cpp b11573-0f701c882 server SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; template SHA-256 `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`. Exact tokenizer and29 DLL hashes reverified. Partial third-party conversion lineage remains a development limitation. CPU4 threads, context4096, output96, seed42, temperature0, top-p1, no GPU/custom stop/cache/warmup or model substitution.

Stage A verified offline artifact identity and candidate inputs. A fresh **full inference preflight**, including the unchanged3GiB available physical RAM before loading and live runtime/token checks, remains required in Stage B. No current generation latency, model-resident RAM, native stopping behavior or new output exists to report. Tokenization is not generation and consumes no inference quota.

Frozen statistics retain all12 registered S/F/H descriptions: four simple/control comparisons, three average main effects, three two-factor interactions, one three-factor interaction and H1 S×H at F=0. C3−C0 outdated-answer adoption is the prospective primary developmental comparison on the full eligible case denominator; correct-answer rate, full task success, outdated adoption, structure and fidelity remain separate. Unknown outcomes retain signed identification bounds and explicit coverage; no missing-cell renormalization. Preserve case pairing, speaker IDs and template ancestry; any bootstrap is descriptive whole-speaker sensitivity, not guaranteed population coverage or significance.

Conditional generation can stop with only8 or16 new outputs, leaving factorial cells genuinely ungenerated. It cannot then support complete-factorial estimates. No outcome-based case substitution, exclusion, favorable-result selection or confirmatory relabeling is permitted. The resulting pilot is conditional development data.

Linguistic and behavioral fidelity remain distinct opportunity-dependent constructs. Single-answer tasks may supply no valid opportunity, which is explicitly insufficient/N/A rather than0. The restricted temporal bank cannot validate general dialogue reliability, coherence, full Persona Fidelity or real-speaker external validity. The full original research scope remains for later independent validation.

## Verification, artifacts and next action

Actual relevant tests: **27 passed in3.77s**, no failures/skips. Command/output: `targeted_regression_v1.json`. Tests cover blinded-field/raw-content integrity, deterministic row shuffle, blank-review rejection, label/missingness rules, immutable-field tampering, fixed-priority selection, quoted-activation rejection before model service access, full-denominator thresholds, mutually exclusive88-request budget, factorial/token/control integrity and existing paired estimators. Any authored reviewer decisions used in tests were synthetic TEST_ONLY fixtures in temporary directories, never real labels or a real audit unblinding.

All558 artifacts from the immediately preceding milestone were verified before the append-only log update. Previous records, the16-case bank, original20+4 O/Q inputs and raw responses are unchanged. No broad historical engineering suite was rerun. There were no new inference or preparation failures in this Stage A run. Git changes remain uncommitted.

New code: `tools/p1_blinded_audit.py`, `tools/p1_conditional_materials.py`, `tools/p1_conditional_execution.py`, `tools/p1_blinded_stage_a_closeout.py`, `tests/test_p1_blinded_stage_a.py`. Artifacts: `docs/validation/p1/blinded_audit_stage_a_v1` (blind CSV, restricted key, source/policy bindings, material audit, five pilot manifests, existing calibration reference,240 new native logs, budget record, tests and reproducibility). Existing `docs/research_development_log.md` is appended; no duplicate decision packet is created.

Read-only candidate validation: `.venv/Scripts/python.exe tools/p1_conditional_materials.py validate`.
Review-content validation without unblinding: `.venv/Scripts/python.exe tools/p1_blinded_audit.py validate_review --review <researcher-completed-copy.csv>`.
Future authorized unblinding: `tools/p1_blinded_audit.py unblind --review <completed-copy.csv> --activation <actual-future-researcher-message.txt> --output <new-unblinding-record.json>`.
Future execution: `tools/p1_conditional_execution.py run --review <completed-copy.csv> --activation <actual-future-researcher-message.txt>` using the repository Python. **Do not invoke the last two commands in Stage A.** Preparation/write-once commands refuse overwrites; do not regenerate a key or manifests once review begins.

Reproducibility manifest: `docs/validation/p1/blinded_audit_stage_a_v1/reproducibility_manifest_stage_A_v1.json`. Current next action: the researcher completes the32-row blind sheet, returns its unchanged-content completed copy, and explicitly sends `unblind and proceed` when ready. No repeated protocol approval or separate ordinary batch approval is requested. Stage B remains inactive until both the genuine review and activation exist. No confirmatory discovery, validated fidelity, algorithm novelty or PLOS ONE submission readiness is claimed.
