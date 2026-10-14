# P1d consolidated researcher decision packet ? v1

Maintainer: Yaxin ZHENG. Status: PENDING. No P1c confirmation is reopened.

## One current decision

**Recommended: approve `p1d_addendum_proposed_v1` and the bound policy as a prospective plan with documented limitations; authorize zero inference requests at this stage.** The required formal-protocol gate comes from the researcher?s P1d instructions, sections 18, 20 and 24. It is not an engineering milestone gate.

The recommended scope is 144 independent synthetic speakers, 288 paired cases, six E/V source-selection conditions, 1,728 Base calls and a 24-speaker paired Instruct subset of 288 calls: 2,016 proposed calls. The two primary outcomes are temporal Incorrect-label incidence and complete task success, each with E, V and E?V. All 16 prospective comparisons and all separate reliability/fidelity outcomes remain reportable. E/V is explicitly different from pure topical R/T.

## Exact approval objects

| File / version | SHA-256 |
| --- | --- |
| [docs/P1d_protocol_addendum_proposed.md](P1d_protocol_addendum_proposed.md) | `1ea81f56548d6685fc0eb67bdc291283f0867e73008f8fd7e26eea432bc30319` |
| [docs/validation/p1d/proposed_v1/analysis_policy_proposal_v1.json](validation/p1d/proposed_v1/analysis_policy_proposal_v1.json) | `08503570fdc4a8e6597f54efb217a1b432d1ce05d6e1fb2f833eed7e2687fc92` |
| [docs/validation/p1d/proposed_v1/contrast_specification_v1.json](validation/p1d/proposed_v1/contrast_specification_v1.json) | `f2395c19e7c88b80ca0498335739a730e85cebba4afcdf15484995048e10e4ef` |
| [docs/validation/p1d/proposed_v1/model_configuration_proposal_v1.json](validation/p1d/proposed_v1/model_configuration_proposal_v1.json) | `d33cd657654520715b95d0f39da20381a79146dcc0e9841ad529f4468b475806` |
| [docs/validation/p1d/proposed_v1/allocation_selection_v1.json](validation/p1d/proposed_v1/allocation_selection_v1.json) | `b5bf5e259707bb4e466a06b1523dc940e02c4005f21efa94c9963e1e46355a5a` |
| [docs/P1d_independent_annotation_plan.md](P1d_independent_annotation_plan.md) | `0b3afcadbacf89e5b0995b251b05b24739e3b5192394cb0ac28f6fbfa17c9eb7` |
| [docs/P1d_identification_and_controls.md](P1d_identification_and_controls.md) | `a2410966194ae9a3406c4c3aedd9e43cd81a8792d2d031e3794e85ec0a0de265` |
| [docs/P1d_task_and_metric_design.md](P1d_task_and_metric_design.md) | `7ca4ffe806e04030dd919e560da08e5439b4e19e69ee90548025ddba01bd4020` |
| [docs/P1d_sample_size_precision_plan.md](P1d_sample_size_precision_plan.md) | `7f5f322d30fa96f65ea08f719d5658d1c03025eea37efc575b3c56e6895e47e0` |

Machine-readable packet: [researcher_decision_packet_v1.json](validation/p1d/proposed_v1/researcher_decision_packet_v1.json), SHA-256 `5c93da0ffaee13738573f18049d3e6d86c41b49348b0e98637c488031d712253`. The [decision row](validation/p1d/proposed_v1/researcher_decision_v1.csv) is blank; no approval or human timestamp is invented.

## Scientific rationale and unresolved limits

Prioritize independent measurement because P1c correct-label contrasts were small, uncertain and boundary-sensitive. The proposed sample follows 216 planning scenarios plus a stronger-dependence stress check. At 144 speakers, the selected stress scenario has simultaneous median half-widths about 9.22 pp main and 18.38 pp interaction; these are assumptions-based planning estimates. Persistent unscorability can leave much larger identification bounds. Six original speakers do not support population inference.

The new 16 examples are development-only and excluded from validation. All 96 prompts fit the Base context, but two cases have a one-token active mismatch and all procedural controls are shorter. Their semantic neutrality is unproved. Follow-up context necessity, independent domains/templates and independent annotation remain unvalidated. Local Instruct quantization and exact tokenizer/template hashes are unavailable. No independent validation bank or executable frozen manifest exists. The narrowed design still identifies selected text packages, not pure internal cognition.

## Consequences and final freeze

Approval adopts only the specified prospective scientific plan and resource envelope. Continue independent stimulus preparation and measurement validation; preserve diagnostic-control limitations. Before actual execution, the independent bank, controls, rubric and model artifacts must pass their specified checks, a complete immutable request manifest must exist, and the researcher must authorize that exact bounded execution. This is the already-required execution gate, not a request to approve the same protocol twice. A rejection or correction changes only the affected prospective item.

Choose one: **APPROVE WITH DOCUMENTED LIMITATIONS (PLAN ONLY)**; **REVISION REQUIRED** with the specific issue; or **REJECT**. No silence or completed form is treated as authorization. No large-model/API spending, further waves, training, publication, commit or push is included.

## Completed non-gated work

P1c closeout/source checks; independent allocation rules; 216-scenario simulations and deterministic stress reconstruction; 16 development cases/96 prompts and native GGUF token records; known-method selection and structured-verifier baselines/ablations; paired analysis and boundary-evaluation primitives; primary-source comparison including ten papers; annotation and publication plans. The [reproducibility manifest](validation/p1d/proposed_v1/reproducibility_manifest_v1.json) records final validations. No empirical P1d response or independent human annotation has been produced.
