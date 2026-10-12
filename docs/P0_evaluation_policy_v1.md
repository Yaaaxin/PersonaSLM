# P0 Evaluation Policy v1

Version: `separate_axes_policy_v1`; boundary instrument: `response_status_v1`; bounded factual rule: `english_residence_claim_audit_v3`. This prospective implementation declaration retains Research Protocol v1.1, existing endpoints, applicability rules and human annotation procedures. It does not overwrite any historical score or switch the legacy runner's default evaluator.

## Independent measurements

| Axis | Stored output | Procedure |
|---|---|---|
| Response completeness | COMPLETE / TRUNCATED / CROSS_TURN / AMBIGUOUS; separate semantic-completeness label, raw backend stop and reasons | Frozen boundary instrument; completeness evidence must be supplied separately |
| Factual support | Correct / Incorrect / Unverifiable / Not Applicable, rule version and claim evidence | Apply the bounded English residence audit only to the identifiable first reply or observed prefix |
| Response relevance | Existing 1–5 scale; PENDING and null rating until annotated; Not Applicable when predeclared | Existing independent annotation procedure; never derived from city correctness or length |
| Temporal consistency | Correct / Incorrect / Unverifiable / Not Applicable; separate reason | Independent annotation pending; no automatic general temporal certification from the residence rule |
| Conversational coherence | Existing 1–5 scale; PENDING and null rating until annotated; Not Applicable when predeclared | Judge against the fixed original context, never model-generated follow-up questions |

Persona Fidelity remains separate. No composite reliability score is introduced. Applicability is fixed before generation and copied into each record. A blank annotation, pending rating or unsupported claim is not a positive or negative judgment.

## Scored unit and uncertainty handling

The scored unit is the exact observed first reply/prefix. Exclude model-generated later speaker turns using the frozen boundary policy and retain them verbatim with offsets. If the unit cannot be identified safely, factual support is Unverifiable until independent adjudication. If the cap interrupts a reply, recognized supported assertions may still be Correct; unresolved additional material makes the bounded whole-unit judgment Unverifiable. A verified contradiction remains Incorrect with all claim reasons retained. Response completeness never supplies the factual label.

Correct certifies only recognized assertions under the canonical synthetic unique-city schema. It does not certify the whole answer's adequacy or general factuality. Unsupported grammar, missing evidence and abstention stay Unverifiable with their underlying reason. Not Applicable is used only for predeclared endpoint inapplicability. Missing execution/measurement data must be retained as an error plus an unresolved eligible observation, never an automatically correct or incorrect reply.

The primary accounting population is **all pre-eligible frozen cases**. Report each categorical count and Unverifiable coverage; do not silently drop uncertain, truncated, ambiguous or cross-turn outputs. Not Applicable is reported separately and excluded only according to predeclared applicability. If a supported-response proportion is later reported, its denominator must remain all pre-eligible cases, with Incorrect and Unverifiable separately visible; it is not an accuracy estimate over only verifiable answers. No scalar model-accuracy or causal estimate is computed here. Pending relevance/coherence ratings have no fabricated mean; report coverage before any rated-subset descriptive statistic.

For future open-ended outputs, independent blinded annotation/adjudication remains required by the protocol. Preserve individual judgments, disagreements and original automated outputs. Freeze evaluator/policy versions and handling of unresolved annotations before any P1 execution; changes require dated versions and fresh validation. This P0 freeze defines measurement routing, not a claim that future human evaluation is already complete or that confirmatory thresholds have been chosen.

## Implementation and historical compatibility

`personaslm.evaluation_policy.evaluate_response` returns separate axes and the full boundary record. `category_accounting` retains uncertainty in the pre-eligible denominator. `tools/p0_policy_validation.py` produces additive, versioned records from actual journals and holds the generation plan fixed. Existing v1/v2/v3 factual scores, original parser output and journals are preserved. Software tests contrast supported and contradicted city assertions under identical maximum-token termination, verify cross-turn extraction, and check uncertainty and inapplicability accounting.
