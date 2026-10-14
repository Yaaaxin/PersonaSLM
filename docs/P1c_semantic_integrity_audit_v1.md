# P1c semantic integrity audit v1

Maintainer: Yaxin ZHENG. Status: AI-assisted review; researcher confirmation pending.

## Finding and provenance correction

The 72 proposals and eight alternative boundaries are intact. The old transcription code assigned groups of endpoints together. In particular, ordinal pairs were set together and explanations were generated conditional on those scores. Therefore the earlier claim of separately assessed dimensions must be qualified: conceptual separation was intended, but **independent rating passes were not demonstrated**. There was no literal factual-label-to-task-label assignment; shared group logic still prevents a procedural-independence claim. The source report and code remain unchanged as historical evidence.

All 72 masked question/evidence/reference/reply records were re-read. The new proposal stores separate factual, requested-component, relevance and fixed-context coherence arguments, alternatives and uncertainty. This remains the same AI analytical process, not independent human annotation or a second blinded reviewer. Source quotations are AI-selected evidence references, not researcher-written notes. All researcher fields remain blank. Full Stage B prompts were inspected after the primary reinspection snapshot; the provenance manifest discloses prior analytical knowledge and the failed schema-inspection command that loaded mapping keys without displaying records. No semantic condition effects were calculated.

## Recomputed proposal distributions

| Endpoint | Original frozen-boundary proposal | Reviewed recommendation |
| --- | --- | --- |
| Factual | 43 Correct / 20 Incorrect / 9 Unverifiable | Unchanged |
| Temporal | 43 Correct / 15 Incorrect / 14 Unverifiable | Unchanged |
| Task success | 43 success / 20 failure / 9 unknown | Unchanged |
| Required components | 44 complete / 20 zero / 8 unscorable | Unchanged |
| Semantic completeness | 64 YES / 8 UNCERTAIN | Unchanged |
| Relevance | 59 score 5 / 5 score 4 / 8 unscorable | 60 score 5 / 4 score 4 / 8 unscorable |
| Coherence | 59 score 5 / 5 score 4 / 8 unscorable | 64 score 5 / 8 unscorable |

The full denominator is 72 on all seven semantic axes; fidelity is predeclared N/A. Identifiable primary units: 64. C-versus-I factual coverage: 63; temporal coverage: 58; known task success: 63. All 72 AI assessments exist, but official human-confirmed ratings remain zero. Neither unresolved boundaries nor administrative missing confirmation is a false model claim.

## Integrity and policy

Actual model/backend bytes, 45 pinned sources, all 72 input-token records, original request order and raw HTTP bytes were verified. Execution reconstruction agrees twice; 700 run event files and 5,798 historical experiment artifacts were checked. Frozen status remains CROSS_TURN 64, AMBIGUOUS 8, COMPLETE 0, TRUNCATED 0; native budget stops 70 and EOS stops 2. No generation was performed.

The actual approved addendum is `p1c_addendum_proposed_v2`; approval is registered in [researcher_consolidated_approval_v1.json](validation/p1c/authorization_v2/researcher_consolidated_approval_v1.json). Its SHA-256 is `51d1987e2e91e2f4e72735304380e3f4442f418b731e972828677d24b7b96f55`. The historical proposal's pending flags are not a revocation of that approval. Protocols v1.1 and the v1.2 proposal remain unchanged.

The additive measurement-state flags do not change the rubric, applicability, 16 contrast weights or primary boundary. Rating recommendations require the existing annotation confirmation, not a new protocol approval. See the [confirmation packet](P1c_final_annotation_confirmation_packet_v1.md), [boundary audit](P1c_boundary_uncertainty_analysis_v1.md), [metric independence audit](P1c_factual_task_success_comparison_v1.md) and [ordinal audit](P1c_relevance_coherence_ceiling_audit_v1.md).

## Validation and retained failures

Full test result: **947 passed in 47.38s**. The active CSV/JSON pairs agree field by field. The first secondary CSV export stopped after nine rows because eight rows introduced additional columns. The complete JSON and partial CSV are preserved as inactive v1, together with the failure log; repaired uniform-column secondary v2 is the only active import source. This was an export failure, not missing inference or changed observations. Two guessed read paths failed and were resolved to the actual analysis_preparation directory and evaluation_policy_proposed_v1 file; no source was edited. All failures remain documented.

## Algorithmic Opportunity Assessment

The immediate opportunity is better measurement provenance and boundary validation, not a demonstrated new algorithm. See the [five-part candidate assessment](P1c_algorithmic_opportunity_update_v1.md). Correcting measurement coupling is necessary for an empirical paper, but tests alone do not establish scientific validity or publication readiness.
