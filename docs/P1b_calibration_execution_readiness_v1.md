# P1b Calibration Execution Readiness — Adapter v1

Maintainer: Yaxin ZHENG. Formal baseline: Protocol v1.1. Proposed v1.2 r1 remains unadopted. This report describes non-generation preparation, not an executed calibration or a new scientific result.

## Decision and evidence

**TECHNICAL READINESS = PASS; SCIENTIFIC REVIEW = PENDING; INFERENCE AUTHORIZATION = PENDING. Overall launch decision: NO-GO until explicit researcher review and execution authorization.** The narrow manifest-consuming adapter requested in the prior readiness report is implemented and tested. No dataset or experimental manifest was revised. Earlier reports remain historical records of their then-pending adapter/tokenizer work.

Actual [offline preflight](validation/p1b/authorization_v1/execution_preflight_v1/preflight.json) rechecks model/backend file SHA-256, 24 cases, all 192 frozen prompts/order/factors/applicability and the saved native GGUF tokenizer event chain. It reconciles all 192 recorded input-ID arrays, with input range 150–434 and input-plus-output budget at most 530, under 4096 context. It performs **zero server launches, zero new tokenizations and zero generation requests**. This reuses actual native evidence with unchanged inputs and binaries; it is not a new loaded-process observation or a claim of real end-to-end P1b generation.

After authorization, the adapter must again verify the owned loaded model/build and **all 192 complete prompt token-ID arrays before the first generation in each segment**. Any mismatch stops execution. The earlier actual tokenizer log reports CPU 4/4 threads and zero offloaded layers. Future runs retain their own server command, logs, process/memory observations and pre/post artifact checks. No independent new physical CPU/RAM inventory is claimed by this offline task.

## Immutable experiment

| Item | Frozen value |
|---|---|
| Dataset | `p1b_development_proposed_v2`; 24 cases, 12 fictional speakers, 8 families |
| Dataset SHA-256 | `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6` |
| Existing manifest | `docs/validation/p1b/final_review_v1/calibration_manifest_v2.json` |
| Manifest SHA-256 | `d73ceb403148b01f7b2c83a51a20165fdd625658e50c04a7ce0caa118ab22869` |
| Planned requests | 24 × C0–C7 = 192; no neutral-control or additional model requests |
| Model | Qwen3.5-2B-Base Q4_K_M |
| Model SHA-256 | `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` |
| Backend | llama.cpp b11573 / `0f701c882` |
| Executable SHA-256 | `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| CPU/context | 4 generation threads, 4 batch threads, 4096 context, 0 GPU layers |
| Output/decoding | 96 tokens; seed 42; temperature 0; top_p 1; stop []; stream false; return_tokens true |
| Order | Existing explicit case-block and within-case condition order; seed 714001 |
| State | Exact saved input IDs; cache_prompt false; no generated history carried forward |
| Prompt | `p1b_transcript_proposed_v1`, used verbatim; legacy transport template field does not render text |
| Policies | `response_status_v1`; `separate_axes_policy_v1`; `p1b_manual_semantic_routing_proposed_v1` |

The existing manifest still records `execution_authorized=false`. It is not edited to grant permission. A separate authorization record binds its exact hash, the approved review-registration hash, adapter version/source preflight and the 192-attempt bound. File equality is not independent proof of upstream quantization fidelity; that known limitation remains unchanged.

## Adapter behavior and interruption policy

Implementation: [core adapter](../src/personaslm/p1b_calibration.py) and [command tool](../tools/p1b_calibration.py), using existing `ManagedServer`, native `LlamaClient`, immutable `RunJournal`, token validation and frozen response classification.

1. Refuse missing, unconfirmed or mismatched review/authorization records before any server launch. Validate every official review record, the limited-interpretation/scoring confirmations, exact plan/preflight hashes, current source hashes and pinned binary identities.
2. Acquire an exclusive local writer lock. Bind a wave claim to the exact authorization, review, source inventory and original manifest. A stale lock after a hard kill is not automatically removed; first verify the prior process has stopped. No unrelated server is attached to or terminated.
3. Create a new immutable segment under `results/p1b_calibration/development_v1/runs/`, with explicit segment index, links/hashes to all earlier segments, Git SHA/dirty state, source byte snapshots, configuration, plan and approval provenance. UUID filenames alone do not define segment order.
4. Verify native tokenizer IDs for the whole plan before any completion. Send saved ID arrays in the original request order. No input is truncated or re-rendered, and no decoding option is adapted to output quality.
5. Journal each attempt before sending it. Preserve native HTTP response bytes before JSON validation, the full raw reply before parsing, native termination evidence, generated count/IDs when available, timings, first-reply spans and excluded continuation. Token/count/context mismatches stop the segment with raw evidence retained.
6. On interruption, close only the owned server and retain failures. `--resume` requires the same wave binding and source hashes and loads every prior segment. It continues unattempted IDs in the original order. Successful outputs are never regenerated.

**No automatic retries:** the maximum remains 192 total attempts. A write-ahead attempt without a received raw response is conservatively uncertain and is not silently retried. It remains in the eligible denominator. If raw data exists but the parser result was not persisted, the offline audit reconstructs a separate derived record without another model call. A future explicit retry would require a separately documented researcher decision and attempt-budget policy; it is not implemented or implicitly authorized here. This conservative behavior satisfies continuation without overwriting or selecting better answers.

The `audit` action checks journal integrity and frozen parser reconstruction and returns all 192 planned rows, including unattempted, attempted-without-response, invalid-raw and recoverable-raw records. A segment execution PASS is not full-wave measurement acceptance. Missing backend output IDs remain absent, never reconstructed by guessing.

## Evaluation readiness

The unchanged [routing contract](validation/p1b/final_v1/evaluation_routing_v1.json) and [applicability matrix](validation/p1b/final_v1/evaluation_applicability_v1.csv) precede responses. Manual task-specific scoring uses the ledger, requested components and proposition dates; neither the P0 city scorer nor the symbolic source oracle scores free text.

| Axis | Eligible planned outputs | N/A | Pending assessment |
|---|---:|---:|---|
| Response relevance | 192 | 0 | Human 1–5, considering requested information and explicit constraints |
| Factual consistency | 192 | 0 | Correct / Incorrect / Unverifiable / Not Applicable under the source-based rules |
| Temporal consistency | 88 | 104 | Eleven cases; judge the time asserted, including valid past answers |
| Conversational coherence | 192 | 0 | Human 1–5 for the fixed question/context and identified reply |
| Structural status | 192 planned observations | 0 | Frozen COMPLETE / TRUNCATED / CROSS_TURN / AMBIGUOUS when raw output exists |

`PENDING` in adapter records is annotation workflow state, explicitly not a fifth factual outcome. A failed request has no observed model structural status; retain missingness rather than fabricating AMBIGUOUS. Empty actual output is handled by the frozen boundary policy. Supported partial content need not be Incorrect; Unverifiable is not Incorrect; CROSS_TURN is not factual error. Semantic completeness remains an independent human judgment. Ambiguous extraction stays marked, with raw text for adjudication. All planned eligible rows remain in denominators, without filtering on C0 correctness. Fidelity is unscored and no composite metric is constructed.

Calibration success concerns credible measurement coverage and informative variation, not error production or a preferred S/F/H direction. Report family-specific coverage, structural/semantic disagreement, unchanged ceilings if present, paired case outcomes and uncertainty with speaker clustering. These 24 development cases are not independent confirmatory data; history relevance/family and style/speaker confounds remain.

## Researcher confirmation and future commands

The [final review packet](P1b_final_review_confirmation.md) contains the 312 proposed judgments, limitations and confirmation procedure. The [authorization template](validation/p1b/authorization_v1/execution_preflight_v1/authorization_PENDING.json) is deliberately false, with no researcher identity or decision source filled. It cannot launch inference. Importing confirmed case reviews does not change it.

Only after explicit researcher authorization may a **separate new** authorization record contain the actual decision source, `researcher_id=Yaxin_ZHENG`, `final_decision_authority=researcher`, `authorized=true`, confirmed review-registration hash and the already pinned plan/preflight hashes. Do not invent a review or authorization timestamp. The code validates bound records; it cannot independently authenticate a person's identity, so truthful recording of the actual researcher instruction remains required.

Future execution command, **not executed in this task**:

```powershell
.\.venv\Scripts\python.exe tools/p1b_calibration.py run --authorization docs/validation/p1b/researcher_authorization_v1.json --review-registration docs/validation/p1b/researcher_confirmation_v1/registration.json --preflight docs/validation/p1b/authorization_v1/execution_preflight_v1/preflight.json
```

Use the same command plus `--resume` only for a preserved partial run. If code changes after preflight, prepare a new offline preflight record rather than altering the old one or the experimental manifest. Offline reconstruction uses `tools/p1b_calibration.py audit --output <new-project-local-json>`; it sends no model requests.

## Actual validation and reproducibility

Commands executed during this preparation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_p1b_authorization.py
.\.venv\Scripts\python.exe tools/p1b_review_proposal.py build
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/p1b_calibration.py preflight --output docs/validation/p1b/authorization_v1/execution_preflight_v1
```

Each ran under `tools/p0_capture.py`; exact arguments, timestamps, stdout/stderr and exit codes remain in `results/p1b_authorization/v1/engineering/`. The first targeted run passed 44 tests in 20.55 seconds. An additional adversarial segment-order test and explicit sequence-number handling followed code review; the final complete suite passed **631 tests in 35.79 seconds**, zero failures, no warnings reported, exit 0; captured process duration 36.5016855 seconds. No assertion or acceptance threshold was weakened.

Tests use clearly labelled local doubles only. The interruption integration test exercises the 192-position plan with fake HTTP/model behavior and preserves a failed request rather than retrying it. It is not real inference evidence. Actual tokenizer evidence comes solely from the preceding preserved native run, whose input IDs and raw event chain were reconstructed by the new offline preflight.

Starting HEAD: `64f5f1a120289df9f4b866687c65bb4e7be4e4af`; the working tree already contained the previous uncommitted review work. This task preserves it. The task baseline inventories 371 existing repository source/supplied files and 3,909 previous local Wave 1/tokenizer/review files. Only an append to the development log is intended among those source files. New files and their hashes, exact source copies, test records and preservation results are registered in the [delivery verification](validation/p1b/authorization_v1/delivery_verification_v1.json). Historical reports, raw outputs, annotations, policies and supplied reviews remain unchanged. All changes remain uncommitted.

## Algorithmic opportunity and publication assessment

| Aspect | Assessment |
|---|---|
| Observed failure modes | P1b remains unexecuted. Historical continuation/scorer-coverage limitations justify measurement safeguards, not a factual-error correction algorithm |
| Existing methods | The [existing assessment](P1b_algorithmic_opportunity_assessment.md) and [novelty matrix](related_work_novelty_matrix.md) cover direct persona/factuality, memory and boundary-method overlap; not newly reverified here |
| Potential improvements | None implemented. A later response-boundary, temporal-validity or evidence-selection diagnostic requires a concrete observed failure and separate authorization |
| Validation feasibility | Freeze methods on separate development material, compare appropriate baselines and test independent material; never optimize on desired persona effects |
| Publication value | This adapter supplies traceable empirical measurement. Neither CPU execution nor factorial engineering constitutes a novel scientific contribution |

The next action is researcher confirmation of the prepared judgments and qualified interpretation, followed by a separate execution decision. No new scientific objective, dataset expansion, algorithm, model arm or phase is added as an acceptance gate.
