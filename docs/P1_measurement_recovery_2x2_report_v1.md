# P1 measurement recovery: consolidated O/Q diagnostic record v1

Maintainer: Yaxin ZHENG. Official paper: Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models. First submission target: PLOS ONE.

**Execution blocked by the unchanged physical-memory gate. New generations: 0. Scientific decision: SCIENTIFIC DECISION PENDING REVIEW.** No configuration is selected, and no S/F/H pilot v2 is generated or executed as a qualified design.

## Scientific scope and original source audit

This P1-only development intervention tests measurement feasibility for the original S/F/H programme. It estimates neither Persona effects nor population mechanisms. Protocol v1.1 is retained; v1.2 remains proposed. The adopted P1d addendum is preserved within its existing scope, not replaced. P0 is frozen; P1 active; P2/P3/P4 paused; P5 diagnostic closed with semantic adoption outstanding; P6 paused, including the prior null ESCP contribution.

All32 original C0 raw outputs, questions, trusted facts, timestamps, component references, automatic scores and AI proposals were inspected. The complete original HTTP/request/result inventory reconstructed. All32 references passed explicit unique entity/attribute/date witness checks, including relational chain links. The audit found no reference-answer error or non-unique original answer. This is objective checking plus AI-assisted source review, not human scientific certification.

Original scores remain untouched: task Success11/32; complete-answer forms29/32; supported components29/64. The new audit retains the original task recommendations pending human review. False unavailability in cases02/22 can count as delivered but wrong answers; treating it as missing component delivery is a preserved alternative. Case07 supplies incompatible March answers. Cases10/30 conflate wrong entity with temporal scope; case30's Incorrect temporal alternative is especially plausible because the wrong entity's cited value also expires before September. No disputed label was silently revised.

| Task family | All original C0 AI success | Selected D0 AI success |
| --- | ---: | ---: |
| dated_comparison | 0/8 | 0/2 |
| dual_component | 2/8 | 0/2 |
| relational_chain | 5/8 | 1/2 |
| single_lookup | 4/8 | 0/2 |

Failure tags are descriptive, can overlap, and do not prove an internal reasoning mechanism:

- AUTOMATIC_DATE_ATTACHMENT_COVERAGE_LIMIT: 8
- EVALUATOR_DISAGREEMENT_NOT_PROOF_OF_SCORER_ERROR: 11
- EXPLICIT_INTERVAL_REASONING_ERROR: 1
- FALSE_UNAVAILABILITY: 2
- INCOMPLETE_ANSWER_COMPONENTS: 3
- INCOMPLETE_CITATION_WITH_COMPLETE_ANSWER: 1
- INCOMPLETE_REASONING_TAIL: 7
- NOT_YET_VALID_VALUE_SELECTED: 3
- OUTDATED_COMPONENT_SELECTED: 1
- OUTDATED_VALUE_SELECTED: 7
- REVERSED_DATE_ATTACHMENTS: 3
- SELF_CONTRADICTION: 2
- TEMPORAL_INTERPRETATION_UNCERTAIN: 2
- WRONG_DATE_ATTACHMENT: 3
- WRONG_ENTITY: 2

## Frozen case selection and D0 reuse

Selection uses the first two lexically sorted calibration case IDs within each of the four fixed task families. It reads no performance field. The chosen IDs are p1_measure_calibration_00 through07. These were previously observed development cases; an outcome-independent selector is not an independently blinded sample. All have eight evidence rows and shared Alderbrook/block ancestry, limiting representativeness. The factorial pool remains disjoint and unexecuted; no factorial case was selected by its C0 result.

For every selected case, reconstructed true-C0 prompt UTF-8 bytes equal the archived original request exactly. The original request SHA, prompt SHA, token array, model, template, context, seed and decoding are retained. D0 reuses the eight original outputs and never appears in the new completion inventory. D0 AI task success1/8; complete forms6/8; supported components5/16. These are existing observations, not a new experiment.

## Prespecified O/Q intervention and component eligibility

D0=O0Q0 (archived); D1=O1Q0; D2=O0Q1; D3=O1Q1. O1 groups the exact original fact lines by entity and sorts by validity date, with entity headings. The fact multiset, provenance IDs, intervals and values remain identical. Questions/references are unchanged across O. Position, length, format and salience change, so O is an organization package, not pure retrieval.

Q1 retains a single original entity/date answer valid at the query date, with no answer inserted outside the unchanged evidence. The eligible six cases select Bay B5022, B5096, B5102, B5177, B5316 and B5361 respectively. The comparison-family cases select the September component under their existing requested_date. Q changes cardinality, complexity and competence; it is not pure reasoning and cannot share an identical task-success estimand with Q0.

**Prospective eligibility issue:** cases04/05 each have three valid entity components (bay/zone/gate). The user's rule does not explicitly order these multiple qualifying components. Under the instruction to stop affected Q1 requests, four D2/D3 requests are blocked before inference, not replaced or charged. A clarification was requested before any new output. No silence is recorded as approval. The remaining20 requests have valid frozen inputs: D1 eight, D2 six, D3 six. This partial inventory cannot establish a complete32-record decision panel; it does not redefine the requested 2x2 experiment.

Frozen Q1 aliases are full bay label and bare bay code. Normalization is Unicode NFKC, whitespace collapse, casefold, and at most one terminal period removal. The entire normalized response must equal an alias. Negation, contradictory extra answers, prose or markdown are never stripped to manufacture a match; unhandled forms remain Uncertain/Unverifiable for human review. A wrong exact bay is Failure/Incorrect; an absent record, observed empty answer, N/A and uncertain answer remain distinct. No aliases were adapted to new outputs. Q0 retains the original criteria and automatic v2 limitations.

## Engineering preflight and authorization

Frozen eligible manifest: `docs/validation/p1/measurement_recovery_2x2_v1/diagnostic_manifest_frozen_v1.json`. SHA-256: `d5aa221311660d272d4a9235da5746d60921aad56e1ef2e1e4c34bc587b5e0a5`. All20 inputs passed actual pinned GGUF/native tokenizer checks against the official tokenizer, including full prompt reconstruction. Input range 559–652 tokens, with96 output tokens within4096 context. Original/native token logs are preserved. The live server/tokenizer gate was not attempted after failed RAM preflight.

Model GGUF SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`; backend SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; template SHA-256 `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`. Same Qwen/Qwen3.5-2B Q4_K_M, llama.cpp b11573, CPU-only four threads, context4096, output96, seed42, temperature0, top-p1, no custom stops/cache/warmup/retries. Partial third-party conversion lineage remains development-only. No model or configuration substitution occurred.

Most recent full preflight: `docs/validation/p1/measurement_recovery_2x2_v1/preflight_v2.json`; failure: RAM preflight failed: 2676510720; unchanged requirement 3221225472 bytes. The3GiB threshold is unchanged. Earlier memory availability was sufficient at an initial observation, but this does not override a failed pre-generation check. No server was started, no request claim/attempt consumed, and no new latency, stop reason, output tokens or model RAM measurements exist. Missing telemetry is not fabricated. Exact preflight observations remain machine-readable.

Cumulative attempted: A_C032, B_FACTORIAL0, C_DIAGNOSTIC16 =48. Actual remaining: A0/B80/C32 =112. The authorized24-request recovery scope is unspent. If all24 are eventually completed, the remaining allocation would be80 factorial+8 diagnostic=88; this is not the current count. Factorial execution is explicitly excluded by the latest instruction even though its standing allocation remains unused.

## Measurement and reviewer package

| Endpoint | Original32 automatic/AI agreement | Selected D0 agreement |
| --- | ---: | ---: |
| coherence | 21/21 | 5/5 |
| delivered | 29/32 | 6/8 |
| factual | 21/32 | 5/8 |
| relevance | 21/21 | 5/5 |
| semantic_completeness | 30/32 | 7/8 |
| supported | 32/32 | 8/8 |
| task_success | 28/32 | 7/8 |
| temporal | 23/32 | 5/8 |

These rates measure system agreement, not accuracy or independent inter-rater reliability. Original automatic v1 coupled FC/TC; its record is preserved, while existing v2 independently checks temporal scope. V2 still defers prose and date attachment. Conservative abstention is not automatically an error. The actual disagreement rows and rationales are first in the consolidated CSV.

`docs/validation/p1/measurement_recovery_2x2_v1/consolidated_researcher_review_v1.csv` contains56 uniquely identified rows:32 actual archived observations (eight marked D0,24 audit-only), plus24 clearly marked unexecuted inventory rows. Exactly32 rows belong to the intended D0–D3 decision panel;24 of these have no new output. Human decisions/notes/metric corrections remain blank. No unexecuted row is counted as an actual model failure or semantic observation. Full evidence, raw text, original labels, hashes and source locations are supplied.

| Condition | Output availability | AI task success | Audited task success |
| --- | --- | --- | --- |
| D0 | 8 archived | 1/8 | Not available |
| D1 | 0/8 new | Not measured | Not available |
| D2 | 0/8 new;2 Q1-blocked | Not measured | Not available |
| D3 | 0/8 new;2 Q1-blocked | Not measured | Not available |

No O/Q effect estimate, confidence interval or family-level new result is calculated without outputs. Original family/metric distributions remain machine-readable. Original structural labels21 AMBIGUOUS/11 TRUNCATED are unchanged; native EOS alias compatibility and AI first-response interpretation are separate. Truncation is not factual failure. No independent boundary ground truth exists.

## Decision rule, fidelity and next action

Only researcher-audited labels for the complete32-record panel can trigger the gate: success >=6/8 AND automatic exact agreement >=7/8, fixed priority D0,D1,D2,D3. Unknown or missing labels cannot be silently excluded or counted as agreements. No configuration is recommended on the basis of the AI proposals. A selected family's0/2 outcome would justify only the specified disclosed prospective development restriction, not a permanent scope change. The subsequent80-request pilot requires separate authorization and its own eight-C0 audited >=6/8 continuation gate.

Q1 reduces already limited linguistic and behavioral opportunity. A correct bay code is not Persona Fidelity; unavailable fidelity opportunities are not zero. This diagnostic does not validate either fidelity construct. The main S/F/H programme and separate reliability/fidelity endpoints remain unchanged.

Next action: resolve the two chain-case Q1 component priorities prospectively, retain all versions, then repeat the unchanged full resource preflight when memory is available. The existing inference authorization does not need to be requested again for the bounded eligible diagnostic. Do not run the80-request pilot, introduce another prompt variant, substitute a model, or optimize additional tasks. The final scientific configuration decision still requires real researcher review; current status is **SCIENTIFIC DECISION PENDING REVIEW**.

## Verification and reproduction

Targeted regression: 59 passed in 6.69s. Complete command/output are in `docs/validation/p1/measurement_recovery_2x2_v1/targeted_regression_v1.json`. One initial preparation error (undefined OLD alias) was fixed before any inference; partial registration files were preserved and checked before preparation resumed. A later recording command had a shell-quoting SyntaxError before execution and was corrected. Both errors and the resource failures are retained in `development_failures_v1.json`. No model request failed or was retried. Detailed model/backend/DLL/D0 checks are in `static_integrity_verification_v1.json`; its static PASS does not bypass the failed RAM or unattempted live gates.

Read-only validation: `.venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'tools'); import p1_recovery_run as r; r.validate()"`.
Fresh preflight: `.venv/Scripts/python.exe tools/p1_recovery_run.py preflight --output <new-workspace-json-path>`.
Eligible execution command, only with a successful fresh preflight: `.venv/Scripts/python.exe tools/p1_recovery_run.py run --preflight <successful-preflight-path>`.
The runner rejects existing batch claims and reserves every attempt before HTTP, uses the cumulative category ledger, verifies live token arrays, records raw response bodies/IDs, and cannot generate D0 or factorial cells. This report does not claim that the unexecuted runner has been empirically validated by new inference.

Reproducibility manifest: `docs/validation/p1/measurement_recovery_2x2_v1/reproducibility_manifest_v1.json`. The previous944-file milestone is preserved; research log updates are append-only. Git HEAD/dirty state, source hashes, test evidence, all candidate inputs and memory failures are recorded. No commit/push, training, paused-phase work, originality claim, independent validation claim or submission-readiness claim.
