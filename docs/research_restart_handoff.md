# PersonaSLM planned Windows-restart handoff

**Checkpoint status:** `READY_FOR_PLANNED_WINDOWS_RESTART`  
**Recorded:** 2026-10-18T12:30:24.3183698Z  
**Purpose:** recovery after a researcher-initiated Windows/BIOS memory-allocation restart. This is not a research closeout. No inference was run while preparing this checkpoint.

## A. Repository identity

- Working root: `E:\DEVOIRS\Research\PersonaSLM-Lab\PersonaSLM-Lab-P0-v1.1\PersonaSLM-Lab`
- Branch: `research/autonomous-personaslm`
- HEAD: `c40667ad266082481b1850453f67784b593f3723`
- `main`, `origin/main`, and HEAD were all at that commit when checked. The research branch has no upstream.
- Remote: `origin = https://github.com/Yaaaxin/PersonaSLM.git`

## B. Uncommitted checkpoint

- Staged paths: 0.
- Tracked unstaged paths before this handoff: `.gitignore`, `docs/P1_novelty_assessment.md`, and `docs/research_development_log.md`.
- The repository contains a large retrospective untracked research archive. Before this handoff there were 910 visible non-ignored untracked files; this handoff adds one. Important additions include the P0-P1 cumulative checkpoint, manuscript draft, feasibility freeze/receipts/state, evaluator and reproduction artifacts, literature ledger/workflow, tools, and tests.
- Model weights, raw feasibility outputs, private data, credentials, unblinding keys, researcher comments, and restricted mappings remain excluded by ignore policy. Do not use `git add .` or `git add -A`.

## C. Latest verified milestone

`P1_ANALYSIS_REPRODUCTION_AND_NOVELTY_COLLISION_V1` is `COMPLETE_AND_VERIFIED_NO_INFERENCE`:

- Candidate 1 private-archive replay passed integrity for all 8 requests and reproduced its frozen 1/8 result.
- An isolated `python -I -B` reconstruction reproduced the public-safe evaluator aggregate exactly from an explicit eight-file allowlist.
- Full public clone-only reproduction remains partial because raw results and model weights are local/ignored.
- Literature review identified Memory Echo/FPA as a direct collision with broad provenance-guided stale-memory-suppression claims, and ReTurn as a stronger prospective matched-history design.

This milestone is reproducibility and novelty evidence, not an S/F/H result, independent validation, or algorithmic contribution.

## D. Current P0-P6 status

| Phase | Status | Boundary |
|---|---|---|
| P0 | `FROZEN` | Infrastructure accepted and historical evidence preserved. |
| P1 | `ACTIVE` | Model/measurement feasibility recovery; Candidate 2 resource-blocked. |
| P2 | `PAUSED` | No new knowledge-utilization execution. |
| P3 | `PAUSED` | Bounded P1 challengers do not activate full model scaling. |
| P4 | `PAUSED` | No naturalistic participant work or fabricated human review. |
| P5 | `DIAGNOSTIC_COMPLETED` | Historical diagnostic only; no new causal claim. |
| P6 | `PAUSED` | Prior ESCP negative result preserved; FPA collision prevents a renamed provenance/suppression claim. |

The authority for exact research design is `docs/research_protocol_v1.1.md`; v1.2 files remain proposals.

## E. Inference authorization balances

- Historical P1 ledger: 160 authorized, 80 attempted, 80 remaining. It is separate and must not be transferred automatically.
- Autonomous recovery ledger `P1_AUTONOMOUS_MODEL_FEASIBILITY_20261017_V1`: 1,200 generations / 72,000 actual inference seconds authorized; 8 generations / `65.87628550000954` seconds used; 1,192 generations / `71934.12371449999` seconds remain.
- Candidate attempts: Candidate 1 = 8; Candidate 2 = 0.
- Unresolved in-flight completion requests: 0.

## F. Candidate 1 finding

- Configuration: `smollm2_1_7b_instruct_q4_k_m`.
- Archive: one terminal run, 8 starts, 8 completion HTTP records, 8 raw records, 8 scored results, integrity `PASS`.
- Frozen score: 1/8 current-value adoption against the unchanged 7/8 developmental gate; it did not qualify.
- Frozen states: 1 current, 1 outdated, 6 unverifiable.
- A post-hoc AI-only reading proposed 4 current, 3 outdated, and 1 incomplete response. It is not human annotation, does not alter the frozen gate, and is not independent validation.

## G. Candidate 2 frozen configuration

- Candidate ID: `qwen2_5_3b_instruct_q4_k_m`.
- Model: `Qwen/Qwen2.5-3B-Instruct-GGUF`, revision `af75b7aaf5bb163ce4c5dab4e6b84d844e96265d`.
- Weight: Q4_K_M; SHA-256 `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`; local ignored path `models/gguf/feasibility_candidates/qwen2.5-3b-instruct-af75b7aa/qwen2.5-3b-instruct-q4_k_m.gguf`.
- License: Qwen Research License; redistribution requires separate review.
- Backend: `llama.cpp b11573-0f701c882`, CPU-only, 4 threads, 4,096 context tokens.
- Generation: max 96 new tokens, temperature 0, top-p 1, seed 42, no stop strings.
- Native template SHA-256: `d5495a1e5db0611132a97e46a65dbb64a642a499421228b9c8b93229097fa9a4`.
- State: materialized, 0 attempts, 0 outputs, scientifically unevaluated.

## H. Candidate 2 frozen materials

- Prospective freeze: `docs/validation/p1/model_feasibility_recovery_v1/prospective_freeze_v1.json`, SHA-256 `5ce53ae8fba0cd5acb4fe303b7bd1b5a81600de68230d770a53e497fdb6483a9`.
- Eight-request materialization: `docs/validation/p1/model_feasibility_recovery_v1/materialized_qwen2_5_3b_instruct_q4_k_m_v1.json`, SHA-256 `591dadd21a2b893a6c327d4d8737da3159a380a5f921049f9d5364a5bc849c43`.
- Materialization receipt: `docs/validation/p1/model_feasibility_recovery_v1/candidate2_materialization_receipt_v1.json`.
- Latest blocked preflight: `docs/validation/p1/model_feasibility_recovery_v1/candidate2_preflight_attempt_v2.json`, SHA-256 `686f92690681b69911643840ff5a30b8b7b07015bc55a293cc0b283b1908d5d9`.
- V2 observed `4,595,142,656` available bytes against the `5,368,709,120`-byte gate, a `773,566,464`-byte deficit. This is a resource result, not a model-performance failure.

## I. First post-restart preflight

After reading this handoff, verifying Git/state/ledgers, and confirming that the V3 receipt does not already exist, run exactly once:

```powershell
.venv/Scripts/python.exe -B tools/p1_model_feasibility_recovery.py preflight --candidate qwen2_5_3b_instruct_q4_k_m --output docs/validation/p1/model_feasibility_recovery_v1/candidate2_preflight_attempt_v3.json
```

Do not lower the 5 GiB threshold, terminate unrelated applications, or retry in a loop. If a V3 receipt already exists after interruption, inspect it and use the next unused version rather than overwriting it.

## J. Conditional resume command

Only if V3 is `PASS`, all frozen hashes and authorization checks still pass, and no Candidate 2 attempt exists, run the eight-request screen once:

```powershell
.venv/Scripts/python.exe -B tools/p1_model_feasibility_recovery.py run --candidate qwen2_5_3b_instruct_q4_k_m --preflight docs/validation/p1/model_feasibility_recovery_v1/candidate2_preflight_attempt_v3.json --output docs/validation/p1/model_feasibility_recovery_v1/candidate2_run_receipt_v1.json
```

Then audit before selection:

```powershell
.venv/Scripts/python.exe -B tools/p1_model_feasibility_recovery.py audit --candidate qwen2_5_3b_instruct_q4_k_m --output docs/validation/p1/model_feasibility_recovery_v1/candidate2_audit_v1.json
.venv/Scripts/python.exe -B tools/p1_model_feasibility_recovery.py selection --output docs/validation/p1/model_feasibility_recovery_v1/selection_after_candidate2_v1.json
```

## K. Scientific stop rules

- Preserve the 7/8 Candidate 2 screen threshold and the 6/8 later disjoint-C0 threshold.
- Do not rerun Candidate 1, the original Stage B model, completed requests, or failed calibration cases.
- Preserve partial, failed, interrupted, missing, and negative records; never retry to obtain a favorable answer.
- Candidate 2 preflight failure keeps it `BLOCKED_RESOURCE`; it is not a model failure.
- Candidate 2 below 7/8 ends the bounded two-challenger screen. Do not add a third model or change prompts/scorer/aliases/thresholds.
- Candidate 2 at or above 7/8 does not directly authorize the old pilot controller. First build and validate a Candidate-2-native 80-request manifest/controller, namespace, and autonomous sub-ledger. Select C0 explicitly by condition; never positionally slice the legacy manifest.
- Execute only 8 disjoint C0 requests next. Run the remaining 72 S/F/H and neutral-control requests only after the frozen C0 gate passes and semantic-endpoint validity is adequate.
- Keep developmental, exploratory, and independent-validation evidence separate.

## L. Evaluator and analysis limitations

- O/Q exact-category agreement is 31/32 and task-success aggregates are 16/32 for both automatic and one genuine researcher review, but this is narrow agreement, not general evaluator accuracy or independent inter-rater reliability.
- Candidate 1 exact/alias coverage is only 2/8. Post-hoc AI semantic labels are diagnostic only.
- Wave-1 automatic factual conclusiveness was 15/72.
- The aggregate artifacts cannot recover a full confusion matrix, sensitivity, specificity, kappa, independent factual/temporal validity, or Candidate 1 semantic accuracy.
- Style can change answer wrappers, so exact/alias scoring cannot be the sole future S/F/H semantic endpoint.
- Minimal temporal QA does not measure general dialogue reliability or Persona Fidelity.

## M. Reproducibility status

- Local Candidate 1 private-archive analysis: `PASS`.
- Isolated public-safe aggregate reconstruction: `PASS` and exactly equal to the archived evaluator result.
- Generation reproduction: not run; Candidate 2 remains resource-blocked.
- Public clone-only full reproduction: `PARTIAL`; raw model records and model weights remain local/ignored.
- Legacy `tools/p1_conditional_execution_v2.py` is prohibited for Candidate 2 because it binds the old model, historical ledger, restricted activation, and existing run.

## N. Literature monitoring

- Last verified scheduled collection: `2026-10-18T09:28:51Z`.
- Latest private snapshot: 196 records; 12/13 source requests succeeded; one failed.
- Reviewed ledger: 14 records; primary-source addendum: 3 records.
- Current sandbox identity could not observe the researcher-account Windows task (`TASK_NOT_FOUND`). The GitHub Actions workflow is untracked and absent from HEAD/origin, so continued daily scheduling is not currently verified.
- After restart, verify the Windows task under the researcher account. Do not claim persistence until that check passes.

## O. Governance and Git

The repository does not contain a standalone copy of the full chat-supplied autonomous charter. This handoff therefore preserves its operative mandate: continue publication-oriented autonomous research; protect scientific integrity, frozen protocols, provenance, hashes, budgets, privacy, negative results, independent validation, reproducibility, literature surveillance, and evidence-driven algorithm work; never fabricate results or retroactively manipulate gates.

There is an explicit governance conflict. Chat instructions granted autonomous commits/pushes, but the current repository-local `AGENTS.md` says the human researcher exclusively commits and pushes and forbids automated staging/commit/push. No adopted repository amendment resolves this conflict. Follow `AGENTS.md`: keep this checkpoint uncommitted and unstaged for researcher review; do not replace `AGENTS.md`.

## P. Next scientifically justified tasks

1. Recover from this file and the machine-readable state; validate freeze, ledgers, Candidate 1 audit, and Candidate 2 zero-attempt status.
2. Run the one fresh V3 RAM preflight after the BIOS change; conditionally run only Candidate 2's eight frozen requests.
3. If Candidate 2 qualifies, implement the Candidate-2-native downstream controller before any pilot inference.
4. Obtain genuine blinded researcher semantic adjudication for Stage B/Candidate 1 without changing historical gates.
5. Validate semantic and Persona Fidelity endpoints, then plan an ancestry-disjoint independent cohort with crossed speaker/template precision simulation.
6. Re-verify literature scheduling and keep FPA/ReTurn/Wiki-Talkie constraints in any prospective design. Keep P6 paused until a replicated residual mechanism and strong-baseline comparison justify activation.

## Q. Evidence index

- Authoritative state: `docs/validation/p1/model_feasibility_recovery_v1/research_state_v1.json`
- Development log: `docs/research_development_log.md`
- Cumulative checkpoint: `docs/P0_P1_cumulative_research_checkpoint_and_model_feasibility_assessment_v1.md`
- Candidate 1 audit: `docs/validation/p1/model_feasibility_recovery_v1/candidate1_audit_v1.json`
- Selection snapshot: `docs/validation/p1/model_feasibility_recovery_v1/selection_after_candidate1_v1.json`
- Autonomous ledger: `docs/validation/p1/model_feasibility_recovery_v1/autonomous_authorization_ledger_v1.json`
- Historical ledger: `docs/validation/p1/measurement_recovery_2x2_v2/authorization_ledger_v2.json`
- Evaluator validity: `docs/validation/p1/model_feasibility_recovery_v1/evaluator_validity_v1.json`
- Analysis reproduction: `docs/validation/p1/model_feasibility_recovery_v1/analysis_reproduction_v1.json`
- Literature checkpoint: `docs/validation/literature_monitor_v1/literature_checkpoint_2026-10-18_v1.json`
- Primary-source review: `docs/validation/literature_monitor_v1/primary_source_review_addendum_2026-10-18_v1.json`
- Manuscript draft: `docs/PersonaSLM_manuscript_working_v2.md`

On shutdown, no interactive agent continues running. The next session must reconstruct state from these files before taking any scientific action.
