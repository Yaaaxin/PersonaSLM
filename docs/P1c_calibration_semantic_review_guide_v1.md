# P1c Calibration Semantic Review Guide v1

Maintainer: Yaxin ZHENG. This guide implements the approved P1c development evaluation policy. It is not a change to Protocol v1.1, an adoption of Protocol v1.2, or completed human annotation.

## Review materials and order

Use [Stage A: semantic scoring](validation/p1c/calibration_v1/measurement_v1/semantic_scoring_view_v1.csv) first. It contains the 72 frozen response identities PC001–PC072 in their original prospective presentation order (seed 715005), the question, common trusted ledger, requested date, evaluation date, fixed context, required answer components and the exact extracted first span. Original input references and response hashes must remain unchanged. Work on a separately named copy; retain the blank source.

Complete Stage A without opening the execution report, treatment mapping, condition comparisons or [Stage B: structural review](validation/p1c/calibration_v1/measurement_v1/structural_review_view_v1.csv). The mapping is stored separately for analysis; file separation is not encryption or a guarantee of blinding. Names, wording and response content may reveal intervention cues. Do not claim independence from all prior knowledge.

Stage B follows a preserved Stage A snapshot. It shows the full continuation, frozen extraction, excluded tail through the parser trace, native stopping and original structural status. Record extraction validity and uncertainty separately. Do not replace a first reply with a later, better answer or overwrite `response_status_v1`. If the automated extraction is indefensible, preserve the proposed span and original Stage A rating, flag the issue, and keep the affected primary semantic result unscorable until an explicit disposition is recorded. Any alternative boundary analysis needs its own version.

## Separate judgments

All 72 outputs are eligible for each of the eight declared reliability/delivery/structural axes; Persona Fidelity is Not Applicable because this experiment supplies no fidelity reference. Missing annotation is an administrative state, not Unverifiable or Not Applicable.

| Field | Decision rule |
|---|---|
| Response relevance, 1–5 | Existing rubric: 1 nonresponsive, 3 partial, 5 adequately responsive; intermediate values express intermediate performance. A wrong answer can still be relevant. |
| Factual consistency | Correct, Incorrect, Unverifiable, Not Applicable. Supported claims, demonstrably false claims and absent/unsupported/unassessable claims are distinct. Use the approved P1c application, not the city-specific checker. |
| Temporal consistency | The same four categories, evaluated against **requested_date** and the stated validity intervals. The newest fact and evaluation date are not automatically the required answer. |
| Conversational coherence, 1–5 | Assess integration with the fixed preceding context, reference resolution and topic continuity. Keep independent of factual truth. |
| Task success | 1 only if every requested component is delivered, supported and no incompatible answer is asserted. Known partial, wrong or no-final-answer delivery is 0 for this diagnostic; an unknown reply unit or missing review remains unknown. |
| Component coverage | Supported requested components divided by the fixed number of reference components. Document supported, omitted, unsupported and contradictory components separately in evidence/notes. An intermediate route does not supply a requested destination room. |
| Semantic completeness | YES, PARTIAL, NO or UNCERTAIN. A complete wrong answer can be YES; a promise to check is not a delivered answer. |
| Structural status | Frozen separately under response_status_v1. Stage A does not score or see this classification. |

Quote the exact model claim and trusted fact identifiers for each factual or temporal judgment. Explain missing final answers separately from false claims. Preserve uncertainty rather than filling an unsupported category. A factual label applies to the assessable assertions in the response; it is not an atomic-claim census and is not complete-answer accuracy. Full task success remains separate.

Do not infer successful reasoning from a correct intermediate fact, keyword overlap, punctuation, native EOS, cross-turn continuation or the presence of all reference words. CROSS_TURN can contain a correct first reply; TRUNCATED need not contain a false assertion. Neither status decides semantic completeness. Full continuation is secondary boundary evidence, not a source of replacement answers.

## Provenance and confirmation

All human fields in the distributed source are blank. If analytical assistance is used, keep proposed labels, supporting quotations and uncertainties in a separate AI-assisted version. The researcher may correct or explicitly adopt that version. Register only actual confirmation with source hashes, reviewer identity and exact scope; do not invent a review timestamp. Software registration time is distinct from human review time. No second human reviewer or agreement statistic exists unless independently collected.

An [optional 72-item analytical notes file](validation/p1c/calibration_v1/review_support_v1/AI_review_observations_UNCONFIRMED_v1.csv) is available after initial Stage A work has been preserved. It contains source quotations and specific review issues, not completed endpoint scores. It must not be imported as human annotation or treated as independent blinded review.

Before any official semantic treatment analysis, validate all non-annotation fields against the masked source, freeze the accepted annotation file and its hash, then join the protected mapping in a separate analysis dataset. Do not insert treatment labels into the reviewer file. An independently selected, condition-masked second-human subset would add reliability evidence; it is not retrospectively manufactured by researcher adoption of assisted coding.

## Analysis limits

Retain all 12 paired cases and all six conditions. There are six synthetic speaker clusters, not 72 independent participants. The approved 16 comparisons refer to historical text packages, not pure relevance, temporal validity, stale-answer competition or internal mechanisms. N_history remains a length-matched procedural diagnostic control; H_none is shorter. Unknowns retain their categories and signed sensitivity bounds without reweighting surviving cells. Report ordinal distributions, paired changes, whole-speaker uncertainty and leave-one-speaker-out diagnostics. No composite reliability score, significance selection or confirmatory claim is authorized.

Policy authority: [approved registration](validation/p1c/authorization_v2/researcher_consolidated_approval_v1.json), [frozen evaluation policy](validation/p1c/final_review_v1/evaluation_policy_proposed_v1.json), [frozen contrast registry](validation/p1c/final_review_v1/estimand_registry_proposed_v1.json). The latter source files retain their historical proposal status; the separate explicit approval is operative.
