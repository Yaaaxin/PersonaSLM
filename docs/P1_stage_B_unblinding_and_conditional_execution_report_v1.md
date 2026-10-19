# PersonaSLM P1 Stage B Unblinding and Conditional Execution Report v1

Project: PersonaSLM  
Researcher: Yaxin ZHENG  
Paper title: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*  
Research phase: P1 active developmental measurement  
Software record date: 2026-10-17  
Protocol baseline: Research Protocol v1.1 and approved addenda; v1.2 remains proposed

## 1. Scope and scientific conclusion

The researcher's explicit `unblind and proceed` instruction authorized the previously frozen P1 Stage B conditional workflow, with at most 88 additional CPU generations. The repository and scientific inputs were rechecked before unblinding. The 32 researcher judgments formed a complete 32-to-32 bijection with the original O/Q diagnostic records. Applying the frozen rule found no qualifying D0-D3 configuration, so the deterministic decision selected Branch B and the frozen minimal-temporal fallback calibration.

The registered pre-inference checks passed. Exactly eight calibration generations were then executed, once each and without retry. The frozen exact/alias endpoint scored 6/8 current-value adoptions and 2/8 outdated-value adoptions. This did not meet the registered fallback-calibration threshold of 7/8. Execution therefore stopped as prescribed. None of the 80 conditional minimal-temporal S/F/H pilot requests was generated, and no factorial contrast is estimable.

This is a developmental engineering and measurement checkpoint. It is not a confirmatory result, independent validation, double-blind validation, evidence of general model incapability, algorithmic novelty, or publication readiness.

## 2. Repository and recovery state

- Branch: `main`.
- HEAD: `c40667ad266082481b1850453f67784b593f3723`.
- The working tree was already non-clean and contained many prior untracked P0-P6 research artifacts. It was not reset, cleaned, staged, committed, or pushed.
- The recovery report, annotation integration, temporal scorer audit, candidate manifests, authorization ledger, and frozen decision policy were present before Stage B.
- The original Stage A execution binding referenced the pre-recovery hash of a test that was subsequently made safer so it no longer parsed the real restricted key. The frozen v1 binding and controller were preserved. A versioned reconciliation and wrapper were added; they accepted only that documented test-hash replacement and rechecked the model, backend, scorer, prompt, manifest, budget, decision, and unblinding bindings.
- No pre-existing Stage B run or applied condition selection was found before the authorized operation.

## 3. Researcher annotation and unblinding integrity

The authoritative submitted human-review record contains 32 records, 32 unique anonymous review IDs, and complete task-success, factual, and temporal decisions. The researcher identity is Yaxin ZHENG. The shuffled blinded file, original questions, trusted evidence, required components, reference answers, model responses, researcher comments, and explicit failure types were preserved.

Key provenance values:

- Researcher-completed v3 CSV SHA-256: `b0e8cff9b80bdb6055d81333fc0a42a3117e1d5a3bc043f7dcce4cd9aa8ecb84`.
- Validated compatibility view SHA-256: `b7b6c40900d42b03643808db4aa74d57f1f776e651b21dfb512f328586211cad`.
- Original automatic-score source SHA-256: `3a298818a2fc76d5590d80d05267c46c268bf5eeb812b2d369038616196c894a`.
- Restricted-key SHA-256: `8ab628c1a74a7fbb3f09c0a8f266359ab32d6c9835db39f4afe3406647dc896f`.
- Authorization source SHA-256: `d2ab66b1f3f45c8d0ef953e7433c0873888f9d83eb3ba3a54109f97e25d8a1de`.
- Versioned unblinding record SHA-256: `27875cb4830d6a82b2ae4b561a1ad3cc651ab5c675777c26b6b8bcdfdf9225ee`.
- Software-recorded unblinding time: `2026-10-16T21:15:45.831354+00:00`; no human review timestamp was fabricated.

Every anonymous ID mapped to exactly one original output, every original output mapped to exactly one anonymous ID, and each of D0-D3 contained exactly eight records. The unblinding artifact is separate from the original blinded review CSV. Earlier AI proposals remain in `PersonaSLM_six_proposals_NOT_APPLIED_v3.csv` and were not applied. Original automatic labels, researcher labels, and proposal layers remain separate.

The recovery audit previously disclosed that a legacy interrupted-session test process parsed the real restricted key after the researcher review had already been frozen. No mapping was printed, no condition-level result was calculated, and the key bytes were unchanged. This is retained as a procedural audit event; it is not treated as evidence of reviewer contamination without evidence. Current tests use synthetic mappings and inspect only the real key's existence and hash where unblinding is not authorized.

This process preserves a partially blinded researcher review history. It is not independent second-human or double-blind validation.

## 4. Frozen O/Q decision rule and result

The rule was applied without changing labels or thresholds: a configuration qualifies only if researcher-audited task success is at least 6/8 and original-automatic agreement with researcher task success is at least 7/8. If several qualify, the priority is D0, then D1, D2, and D3.

| Configuration | Researcher success | Original automatic success | Exact agreement | Disagreements | Qualified |
|---|---:|---:|---:|---:|---|
| D0 | 1/8 | 1/8 | 7/8 | 1 | No |
| D1 | 5/8 | 5/8 | 8/8 | 0 | No |
| D2 | 5/8 | 5/8 | 8/8 | 0 | No |
| D3 | 5/8 | 5/8 | 8/8 | 0 | No |

Across all 32 records, researcher success was 16/32, original automatic success was 16/32, and exact agreement was 31/32. No D0-D3 configuration reached the required 6/8 audited-success threshold. The priority order was therefore not invoked. The deterministic decision is Branch B.

Decision record: `docs/validation/p1/stage_b_v1/stage_b_decision_record_v1.json`, SHA-256 `6f02889248239d866f166e40aa65ac59d074996ed8b5d08d21cdb1816a4a321b`.

## 5. Selected frozen materials

First executable material:

- Identifier: `fallback_calibration`.
- Path: `docs/validation/p1/measurement_recovery_2x2_v2/fallback_bank_v1/fallback_calibration_manifest_candidate_v1.json`.
- SHA-256: `b23b9a35bba1ff9313e71f75759e8107b3d23b54f765c5fe736094263ff17cde`.
- Registered requests: eight C0 calibration cases.

Conditional material, usable only after a 7/8 calibration pass:

- Identifier: `P1_minimal_temporal_SFH_pilot_v2`.
- Path: `docs/validation/p1/blinded_audit_stage_a_v1/manifests/P1_minimal_temporal_SFH_pilot_v2.json`.
- SHA-256: `6bc6421823371b9cad6140aad1046a3f9aebc2d4594e277b3601a3f4b6fc849e`.
- Registered requests: eight cases across C0-C7, N_style, and N_history, for 80 total requests.

The cases, evidence, reference answers, accepted aliases, date intervals, prompts, tokenizer records, model settings, and allocation were not recreated or altered.

## 6. Preflight and execution integrity

The saved inference preflight passed at `2026-10-16T21:18:41.137272+00:00`:

- Available physical RAM: 4,431,568,896 bytes.
- Required physical RAM: 3,221,225,472 bytes (3 GiB).
- Deficit: 0 bytes.
- Model SHA-256: `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`.
- Backend SHA-256: `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`.
- Live runtime build: `b11573-0f701c882`.
- Live prompt-token arrays verified before the first completion: 88/88 Branch B candidate requests.

The model, backend, quantization, tokenizer, CPU thread count, context length, prompt bytes, generation parameters, reference answers, aliases, and stopping rules matched the frozen records. No substitution, retry, training, or LoRA occurred.

Run identifier: `20261016T211841-ca844dad54ba434e87904cffed817a43`. The append-only journal contains 372 hash-chained events and passed integrity reconstruction. It records eight starts, eight raw generations, eight results, eight provisional scores, zero failures, and zero retries. Sixty-six source snapshots matched current bound sources. The run manifest SHA-256 is `ef432b23a98660a8dbf91d439839d448182484d33fec88237c9238f2076d1b57`; the run summary SHA-256 is `5f9a9f76117404478a32d470ea6e8adbee1b363e8de2815732ba0a64c935bebc`.

During model residence, 17 memory observations were recorded. The minimum available physical memory was 2,022,965,248 bytes, maximum sampled process working set was 2,408,230,912 bytes, and maximum reported peak working set was 2,408,235,008 bytes. The registered 3 GiB rule is a pre-load gate; the lower in-residence observation is recorded, not reinterpreted as a preflight violation.

## 7. Fallback calibration result and stop decision

The frozen endpoint `p1_temporal_fallback.endpoint` accepts an exact frozen current alias as Success. It produced:

- Current-value adoption: 6/8.
- Outdated-value adoption: 2/8.
- Missing or empty outputs: 0/8.
- Wrong-entity, unsupported, or contradictory endpoint classifications: 0/8.
- Automatic task success: 6/8.
- Registered fallback-calibration threshold: at least 7/8.
- Gate decision: `AUTOMATIC DEVELOPMENT GATE NOT PASSED`.

Successful cases were `p1_fallback_temporal_00`, `03`, `05`, `11`, `13`, and `15`. The two failures were:

- `p1_fallback_temporal_06`: emitted `Plot 78467` rather than the current `Plot 77722` for 2054-09-18. The emitted identifier is a trusted old value for the same entity and attribute, valid in an earlier interval. Raw-output SHA-256: `d3174afc336bae564f1ca049eed8ee1848fae2ebd94e766990877006454f40f0`.
- `p1_fallback_temporal_09`: emitted `Cabinet 94622` rather than the current `Cabinet 81170` for 2054-10-22. This is also a trusted old value for the same entity and attribute. Raw-output SHA-256: `fa3e137a68a246d80b7217cc198e27d1118cb822953c93083707cf50a4d9a003`.

These are provisional automatic outdated-value-adoption findings. Researcher review of the eight new outputs is pending. The later pilot-C0 threshold of 6/8 is not applicable to calibration and was not substituted for the registered 7/8 calibration threshold.

All eight outputs were nonempty, contained one identifiable answer unit, ended with native EOS, and were marked `truncated=false`. All eight retain frozen structural status `AMBIGUOUS` because no independent boundary/budget evidence certifies completeness; semantic completeness remains `UNCERTAIN`. EOS alone is not treated as proof of semantic completeness.

## 8. Budget, missingness, and analysis status

Before Stage B, the authoritative ledger was 72/160 attempted with 88 remaining. This task consumed exactly eight authorized C_DIAGNOSTIC generations. The post-run ledger is:

| Allocation | Attempted | Remaining |
|---|---:|---:|
| A_C0 | 32 | 0 |
| B_FACTORIAL | 0 | 80 |
| C_DIAGNOSTIC | 48 | 0 |
| Total | 80 | 80 |

The remaining 80-request B_FACTORIAL allocation is unused but blocked by the failed registered calibration gate. It is not automatically executable. No calibration output is missing, while all 80 minimal-temporal pilot outputs are intentionally ungenerated under the stop rule and are not scored as failures.

The total request latency for the eight calibration generations was 38.860041 seconds: mean 4.857505, median 4.611950, minimum 4.132808, and maximum 5.856622 seconds. Input-token total was 3,162; generated-token total was 68; all eight native stop reasons were EOS.

Because the S/F/H pilot did not begin, simple contrasts, main effects, two-way interactions, the three-way interaction, paired case-level condition comparisons, and speaker-cluster summaries are `NOT_ESTIMABLE`.

## 9. Measurement status and limitations

- Temporal consistency and task success: provisional frozen exact/alias endpoint, 6 current and 2 outdated adoptions.
- Factual correctness: not independently scored for the new outputs. The two failed endpoints emitted facts supported for an earlier interval but wrong for the requested date.
- Component coverage: all eight supplied their single required identifier; this does not resolve date correctness or semantic completeness.
- Response relevance and conversational coherence: not independently scored.
- Linguistic Persona Fidelity: `NOT_APPLICABLE` for these C0 single-answer calibration outputs.
- Behavioral Persona Fidelity: `NOT_APPLICABLE` for the same reason. Neither metric is scored as zero.
- Researcher semantic adjudication of new outputs: pending.

The fallback tests only outdated-answer adoption under dated historical context. They do not independently validate general dialogue reliability, coherence, persona fidelity, real-speaker external validity, neutral-control semantics, general model capability, or algorithmic originality. The O/Q diagnostic reused historical D0 controls, used a small development sample, included Q1 cardinality changes, and selected a format through developmental work. Automatic gates remain provisional engineering controls, and conditional sampling must remain visible.

The prior temporal audit found no confirmed implementation path that substituted `registered_evaluation_date` for question/component-specific dates. The scorer was therefore not rewritten, and historical automatic results were preserved.

## 10. Regression and reproducibility checks

The final post-Stage-B offline suite completed with 57 passed, 0 failed, 0 skipped, and one warning in 10.57 seconds. The warning is the pre-existing pytest configuration warning for unknown option `cache_dir`. This suite exercised versioned execution binding, unblinding/decision integrity, closeout reconstruction, native stopping, date binding, annotation preservation, tamper rejection, synthetic mapping, frozen priority, full-denominator gates, exclusive budgets, and factor-corruption rejection. It did not start a model service or perform inference.

Five legacy tests whose assertions explicitly describe the pre-Stage-B 72/88/no-run state were not rerun as if they remained current. Their exact names and reasons are recorded in the test evidence. The new post-run validator reconstructs the actual 80/80 state instead.

Closeout corrections are preserved rather than hidden. A lowercase Python boolean typo in the new finalizer was found during import inspection and corrected before its actions ran. The first reproducibility-manifest attempt then failed before writing a manifest because a repository-relative evidence path was passed to `Path.relative_to`; path normalization was corrected and the audit succeeded. An initial combined documentation patch was rejected on exact-context verification and wrote nothing; the report and log were then patched separately. None of these offline corrections started a model service, altered scientific data, or consumed inference budget. Reproducibility manifest v1 preserves the immediately preceding valid snapshot; v2 is the authoritative successor with the correction record and additional direct reviewer-file hashes.

Primary evidence:

- Unblinding record: `docs/validation/p1/stage_b_v1/researcher_unblinding_record_v1.json`.
- Deterministic decision record: `docs/validation/p1/stage_b_v1/stage_b_decision_record_v1.json`.
- Execution evidence: `docs/validation/p1/stage_b_v1/stage_b_execution_evidence_v1.json`, SHA-256 `a2c41dfd4b91d232de72f0cbb44fa08429f7ac1d3334030e59f0e5ef76bcb3a5`.
- Regression evidence: `docs/validation/p1/stage_b_v1/regression_test_evidence_v1.json`, SHA-256 `df65704215183c217b2b4cbacb3d14a43c855b89ddecd05b5faa535ec53471c4`.
- Execution-binding reconciliation: `docs/validation/p1/blinded_audit_stage_a_v1/execution_binding_reconciliation_v2.json`, SHA-256 `8665d8670e3bc7360e887349f5ba37bdc07e776a641bf8e608ef6070f2d55d7c`.
- Raw run directory: `results/p1_conditional_sfh/v1/runs/20261016T211841-ca844dad54ba434e87904cffed817a43`.
- Authoritative reproducibility checkpoint: `docs/validation/p1/stage_b_v1/reproducibility_manifest_v2.json`.

The original blinded review, researcher annotation, restricted key, earlier AI proposals, historical raw outputs, original scores, frozen prompts and manifests, model/backend files, protocol, and paper title were left unchanged.

## 11. Research programme status

- P0: FROZEN.
- P1: ACTIVE; Stage B stopped at the failed Branch B fallback-calibration gate. New-output researcher adjudication is pending and the conditional pilot is unexecuted.
- P2: PAUSED.
- P3: PAUSED.
- P4: PAUSED.
- P5: DIAGNOSTIC COMPLETED and archived.
- P6: PAUSED; prior negative ESCP findings preserved.

## 12. Safe Git checkpoint guidance

No Git commit or push was performed. The researcher should inspect `git status --short` and `git diff --check`, then stage only explicitly reviewed source, tests, reports, annotation records, frozen manifests, and reproducibility metadata by named path. Do not use `git add -A` in this large mixed work tree.

The restricted unblinding key, model weights, binaries, caches, and local raw-result directories must not be accidentally staged. The ignored raw Stage B run should remain preserved locally and is cryptographically indexed by the reproducibility checkpoint; forcing it into Git requires a separate human decision. A suitable commit message after human review is: `Complete P1 Stage B unblinding and record failed fallback gate`.
