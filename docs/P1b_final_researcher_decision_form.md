# P1b Final Researcher Decision Form

Maintainer: Yaxin ZHENG. **Unfilled form; no approval is inferred.** Preparation version `p1b_calibration_manifest_v1`; dataset `p1b_development_proposed_v2`, SHA-256 `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6`.

This form concerns bounded development calibration, not confirmation, protocol adoption or publication sign-off. Formal v1.1 and proposed v1.2 r1 remain unchanged. Original P0 and Wave1 approvals/results remain intact.

## Materials to review

- [Final stimulus validation](P1b_final_stimulus_validation.md), including all24 cases and three corrections.
- [Blank24-case review CSV](validation/p1b/final_v1/stimulus_review_v2.csv) and [annotation guide](P1b_researcher_review_guide.md).
- [Readiness, evaluation and precision report](P1b_inference_readiness_report.md), with the [192-request manifest](validation/p1b/final_v1/calibration_manifest_v1.json).
- [Algorithmic assessment](P1b_algorithmic_opportunity_assessment.md): no new algorithm proposed for implementation.

## Decisions — researcher to fill

| Decision | Permitted response | Researcher response | Notes / source |
|---|---|---|---|
| Accept the24 development stimuli after completing their per-case review | ACCEPT / REVISION_REQUIRED / UNCERTAIN | | |
| Approve B_L2/B_L3 wording corrections and E_L3 Tuesday reference revision | ACCEPT / REVISION_REQUIRED / UNCERTAIN | | |
| Accept designed-demand labels with documented shortcuts, not proven empirical difficulty | ACCEPT / REVISION_REQUIRED / UNCERTAIN | | |
| Approve prospective manual semantic routing and separate completeness/support axes | ACCEPT / REVISION_REQUIRED / UNCERTAIN | | |
| Retain pinned Base-only arm,96-token budget,4 CPU threads,4096 context and recorded randomization | ACCEPT / REVISION_REQUIRED / UNCERTAIN | | |
| Approve a narrow execution adapter and tokenizer-only preflight once material issues are resolved | APPROVE / DEFER | | |
| Authorize exactly192 factorial generations **only after** successful preflight and review of the execution record/configuration | AUTHORIZE / DEFER | | |
| Acknowledge development-only status and retention of null, ceiling, failed and unscorable outputs | ACKNOWLEDGE / UNCERTAIN | | |

Reviewer identifier: ____________________

Review method / assistance actually used: ____________________

Review date, only if actually recorded: ____________________

Decision-source record or completed-review filename: ____________________

The current task authorizes preparation, **not generation**. A completed stimulus import does not authorize a run. Keep source and completed forms separately; any substantive stimulus change needs a new version and revised hashes. The final execution gate is the current-tokenizer/context evidence plus explicit authorization, not elapsed time or absence of objection.

## Separate neutral-control decision

The [24-item neutral form](validation/p1b/final_v1/neutral_control_review_v1.csv) is an unchanged copy for the original Wave1 candidates. Its status is OPEN. Complete it separately if those exact matched comparisons are to be used. It does not approve new P1b controls, and its incompleteness does not block the proposed factorial-only192 requests. No neutral-control-adjusted effect is included in this calibration.

## Minimal next action

Complete the24 stimulus records and the material/routing decisions above. Resolve only concrete failed checks. Then review a narrowly implemented execution adapter and real-tokenizer preflight before deciding whether to authorize the frozen192-request run. Do not select cases using model answer quality, raise token tolerance, launch a model arm, or enlarge the pilot to seek a preferred effect.
