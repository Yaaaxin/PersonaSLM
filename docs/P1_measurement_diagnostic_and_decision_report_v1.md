# P1 measurement diagnostic and scientific decision package — consolidated v1

Maintainer: Yaxin ZHENG. Official paper: Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models. First submission target: PLOS ONE.

**Decision: NO-GO for the 80-request S/F/H pilot and for confirmatory freezing.** The current obstacle is scientific measurement readiness, not missing development authorization. The standing 160-request authorization remains valid, with independent category caps. No additional routine batch approval is requested.

## Actual execution and engineering evidence

This milestone executed exactly16 category-C CPU requests on eight previously generated calibration cases, with two instruction packages. 16 successful, 0 failed, zero retries. Native stops {'eos': 16}; 429 output tokens; mean latency 9.380s; observed peak working set 3140472832 bytes. Available RAM exceeded3GiB during full preflight. No memory threshold or model setting was lowered.
Raw run: `results/p1_measurement_pilot/v1/runs/20261015T074907-51b8eb31600149d08743e11afac6cdc4`. Manifest `docs/validation/p1/measurement_pilot_v1/C_DIAGNOSTIC_manifest_v1.json`, SHA-256 `81115f46cbff91cd2512f6038b77079492826a8f0bc5ef862b822e94212220ec`. Actual prompt token range 579–637. Native/official/live token arrays matched for every prompt.
Qwen/Qwen3.5-2B, third-party Q4_K_M GGUF `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`; pinned llama.cpp b11573 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; official nonthinking template `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`. CPU4threads,4096context,96output,seed42,temp0,top-p1,no custom stops,no cache,no warmup. Exact upstream/distributor revisions and the partial conversion-lineage limitation remain in each manifest. No model substitution or confirmatory inference occurred.
The cumulative ledger is32 A_C0 +0 B_FACTORIAL +16 C_DIAGNOSTIC =48/160 attempts. Remaining caps are0/80/32, total112, with no category transfers. The initial32-case calibration is reported once in `P1_C0_measurement_calibration_report_v1.md`; this report is the one engineering/scientific record for the16-request diagnostic and the consolidated P1 checkpoint.

## Research question, design and identification

Can shorter requested-answer instructions or explicit date/slot instructions restore measurement adequacy on the same sufficient evidence? Calibration cases00–07 were selected as the first complete four-family block, not for favorable treatment responses. The factorial bank was frozen before all calibration outputs and remains entirely unexecuted and unchanged. These repeated cases are development comparisons, not independent replication.
Concise adds answer-only/no-explanation instructions. Date-slots adds field order and requested-date interval selection. Evidence, question, references, dates, model, template and decoding remain identical. The diagnostic identifies output-instruction packages, not a pure formatting mechanism, retrieval mechanism, persona effect, or post-training effect. No oracle evidence reduction or additional P5 experiment occurred.

| Matched eight-case configuration | AI task success | Complete form | Supported components |
| --- | ---: | ---: | ---: |
| Original C0 | 1/8 | 6/8 | 5/16 |
| concise | 2/8 | 8/8 | 7/16 |
| date_slots | 1/8 | 8/8 | 4/16 |

Both instruction arms produce8/8 complete forms and identifiable first-response candidates. Neither supplies a correct complete answer in single lookup, dual-component or dated-comparison cases in this eight-case block. Both fail the prospective all-family readiness condition. No arm is selected. The original calibration target80–95% was not a hard gate; the present NO-GO follows the additional predeclared diagnostic criteria and unresolved automatic/fidelity measurement issues.
Concise improves one route case; date-slots improves the same route case but loses the previously correct other route case. Thus cleaner completion is not stable factual improvement. All negative outcomes are retained. The proposed first-response identification is AI-only; original16 AMBIGUOUS parser labels remain unchanged. Native EOS/eog compatibility and separate semantic certification remain documented. No independent boundary-accuracy claim is made.

## Paired uncertainty and failure evidence

concise: paired task-success difference 12.5 percentage points; whole-speaker/case resampling sensitivity95% [0.0, 37.5] points. Eight purposive cases, four shared task ancestors; not guaranteed population coverage or a significance test.
date_slots: paired task-success difference 0.0 percentage points; whole-speaker/case resampling sensitivity95% [-37.5, 37.5] points. Eight purposive cases, four shared task ancestors; not guaranteed population coverage or a significance test.

The pooled16-output iid interval in the initial machine summary is explicitly superseded by `C_DIAGNOSTIC/measurement_v1/summary_v2.json`; the original file remains preserved. Case contributions, both instruction arms, failures and leave-one-case-out diagnostics are retained. Across both milestones there are32 unique calibration cases, not48 independent observations.

## Metric variance and automatic evaluation

| Metric | Diagnostic AI distribution | Scored | Variance | Automatic v2 agreement |
| --- | --- | ---: | ---: | --- |
| behavioral_fidelity | {} | 0 | None | 0/0 |
| coherence | {"5": 16} | 16 | 0 | 8/8 |
| delivered | {"1": 4, "2": 8, "3": 4} | 16 | 0.5333333333333333 | 16/16 |
| factual | {"Correct": 3, "Incorrect": 13} | 16 | None | 8/16 |
| linguistic_fidelity | {"3": 5, "4": 7} | 12 | 0.26515151515151514 | 4/10 |
| relevance | {"5": 16} | 16 | 0 | 8/8 |
| semantic_completeness | {"YES": 16} | 16 | None | 16/16 |
| stale_adoption | {} | 0 | None | 16/16 |
| supported | {"0": 11, "1": 2, "3": 3} | 16 | 1.4291666666666667 | 16/16 |
| task_success | {"Failure": 13, "Success": 3} | 16 | None | 14/16 |
| temporal | {"Correct": 3, "Incorrect": 13} | 16 | None | 8/16 |

All16 diagnostic relevance and coherence scores are5, and all16 complete forms areYES: these outcomes have zero observable discrimination here, not proven zero treatment effects. Factual and task-success labels still coincide in these actual data; the constructs remain separate, as shown by complete wrong answers and the pre-existing correct-history-only counterexample. LF has some narrow surface variation but its heuristic agreement is poor. BF has zero scored opportunities; it is not a measured zero score.
The conservative automatic scorer is insufficient for unattended confirmatory scoring. Date-bearing prose/slot forms can remain Unverifiable automatically despite an interpretable AI judgment. Full per-category confusion matrices, unscored coverage, disagreements, canonical syntax views and original-parser sensitivities remain machine-readable. Agreement is computed on common proposed text views; shared references, deterministic keys and AI boundary assumptions preclude independent accuracy or human inter-rater reliability claims.

## Persona Fidelity construct audit

Reuse the existing eight authored counterexamples and separate blank fidelity/quality panels. They include correct facts/wrong style, wrong facts/right persona, truthful history/wrong behavior, promise-with-persona/no answer, and improved delivery with erased persona. These intended distinctions are not independently rated outcomes. The current BF order-only rule treats absent acknowledgment or absent final answer as insufficient opportunity; older authored keys sometimes treat these as compliance/noncompliance. The mismatch is explicitly recorded, not silently rescored.
Before confirmatory freezing, review separate acknowledgment occurrence, response-act ordering and unsolicited-advice opportunity. A promise can express persona while failing the task. Absence of a target feature may be observable noncompliance even when ordering is undefined. These alternatives require a prospective rubric decision; current BF values stay unscored. Short-code length heuristics are not validated fidelity thresholds.

## Core S/F/H readiness and final checkpoint

C0 baseline:11/32 AI successes (34.4%; descriptive Wilson95%20.4–51.7), with task-family success4/8 single,2/8 dual,5/8 chain,0/8 date comparison. The eight-case C0–C7+N_style+N_history bank is intact, native-token checked and unexecuted. Trusted evidence, questions, references, dates, speaker and fixed context are identical within each pair. Sixteen active/control pairs are token-matched; the controls remain diagnostic, not semantically neutral.
Unexecuted pilot manifest: `docs/validation/p1/measurement_pilot_v1/B_FACTORIAL_manifest_v1.json`, SHA-256 `1fd7ef2d4365119755ca4301779d37c1276c53107d121d0df8dd732aaca6c77b`. Principal C3−C0 outdated-answer adoption endpoint has eight prospectively eligible cases. **Observed factorial requests:0; primary estimate:NOT_ESTIMATED.** Other S/F/H main effects, interactions and diagnostic contrasts likewise have no empirical estimates. Prepared paired estimators have only synthetic software tests; no synthetic result is presented as a model finding.
Scientific case proposals remain VALID_WITH_LIMITATIONS, not researcher confirmations. There are four construction ancestors, five normalized question forms and two linguistic profile specifications. Fixed source roles and target/distractor code prefixes provide shortcuts. Exact-name separation is not linguistic or template independence. No case, question, answer or prompt was replaced using its own factorial outcome.

## Exact remaining decisions and validation requirements

One consolidated review index links48 new item-level AI proposals and the eight existing P5 paired records. Human decision/correction/time fields remain blank. Review the full metric-specific proposals, prioritizing AM004/AM031 negative-answer completeness, AM017 conflicting support, AM020/AM024 entity/temporal attribution, and date-comparison outputs. The record must remain researcher-adopted AI assistance if adopted; no independent reviewer or inter-rater agreement may be inferred.
The smallest useful next step is independent condition/AI-key-masked annotation of the existing48 outputs and the authored construct challenges, with separate quality and fidelity panels. No new model request is needed for this step. If an independent reviewer is unavailable, disclose that limitation; researcher adoption alone cannot validate automatic accuracy. Do not change this scientific status merely because software tests pass.
A new independent inference sample size is not yet scientifically justified by these failed readiness checks. Before selecting it, establish usable outcome/fidelity opportunity, independently authored and counterbalanced templates, a defined speaker/template sampling frame, prespecified primary estimands and practical precision, and dependence/missingness simulations. The adopted144-speaker E/V target does not automatically justify a different core S/F/H sample. Retain the previous E/V plan and all historical precision work.
Remaining GO requirements: resolve the task-family floor without outcome-based case selection; settle the prospective BF rubric and automatic claim/date-scope coverage; obtain genuine independent measurement evidence where feasible; pass the registered scientific readiness check and fresh technical preflight. Confirmatory protocol/material freezing and confirmatory execution still require explicit researcher decisions. Existing development authorization is not revoked and need not be requested again, but no further batch is scheduled merely to consume the unused112 requests.

## P5 closeout, work tree and publication

P5 is administratively/scientifically closed as a completed development diagnostic with pending semantic adoption: existing2/8 versus8/8 AI proposals remain unchanged. Eight paired source records contain exact request/output hashes and evidence. The reference-aware oracle package altered evidence content/length/position/salience/literal answer exposure; it identifies no pure retrieval/sufficiency/persona effect. No additional P5 run occurred.
P0 PASS/frozen; P1 ACTIVE but factorial measurement execution NO-GO; P2 knowledge utilization PAUSED; P3 model/context PAUSED; P4 real-speaker PAUSED; P5 current diagnostic COMPLETED with human semantic review pending; P6 PAUSED. No new paused-phase designs, algorithms, training or literature expansion were undertaken. The negative ESCP baseline result remains unchanged. PLOS ONE remains the first target; no originality, confirmatory finding, equivalence or publication readiness is claimed.

## Validation and reproduction

Targeted regression evidence: 71 passed, exit code0; command and complete output in `docs/validation/p1/measurement_pilot_v1/targeted_regression_v1.json`. Original48 request/HTTP/result inventories reconstruct exactly. All earlier source observations and frozen artifacts are preserved; the research log is append-only.
Generation command used: `.venv/Scripts/python.exe tools/p1_measurement_run.py run --category C_DIAGNOSTIC --preflight docs/validation/p1/measurement_pilot_v1/C_DIAGNOSTIC_preflight_v1.json`. The completed batch cannot be repeated by that command. Read-only audit: `.venv/Scripts/python.exe tools/p1_measurement_run.py audit --category C_DIAGNOSTIC --output <new-workspace-path.json>`. Original native stdout/stderr, input/output IDs, seed/order, raw HTTP, exact source snapshots and reproducibility hashes remain linked. Latencies are observed development timings; light local documentation/analysis occurred, so they are not controlled hardware comparisons.

## Hash-bound review sources

| Source | SHA-256 |
| --- | --- |
| `docs/validation/p1/measurement_pilot_v1/A_C0/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv` | `d6b07183ab5f53612a176d177d74d4fc684bf16a98ca8688b12dcc25f605f653` |
| `docs/validation/p1/measurement_pilot_v1/C_DIAGNOSTIC/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv` | `e74a4f1df234dc13d128e30700b32a3e5f7e1bd8d1ff988da7e21a8e2da3eb23` |
| `docs/validation/p1/measurement_pilot_v1/consolidated_researcher_review_index_v1.csv` | `3960f1c345db5ccce91361648dfaba2013c031211ce0a917ee4b49036b1e1b49` |
| `docs/validation/p1/measurement_pilot_v1/fidelity_construct_audit_v1.json` | `6dd947f5789bf3fefdc70e35766fd1ba0d949721a2ce13e182449c4cfe23731c` |
| `docs/validation/p1/measurement_pilot_v1/calibration_measurement_gate_v1.json` | `406e3ba639285c3d47ed2a898b5eedf2e7b6684f2b4faaa2b28ff82df7c6477c` |
| `docs/validation/p5/oracle_diagnostic_v1/measurement_v1/paired_historical_comparison_v1.csv` | `fc2bcda607b1b7312f801c3e719f0199ba1a9d0ff6c1eb2393b547e9b757fa03` |
