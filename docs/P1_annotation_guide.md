# P1 Development Annotation Guide

Maintainer: Yaxin ZHENG. Protocol v1.1 is unchanged. All materials are fictional English development data. These forms contain no completed human judgment. P0 approvals do not transfer to P1 candidates.

## Control review

Use [control_review_v1.csv](validation/p1/control_review_v1.csv); copy it to a new filename before editing. Do not edit the master. Inspect every candidate against the active intervention, trusted evidence, current question, context, dates and exact tokenizer evidence. All eight review questions use positive criteria: PASS means the requirement is satisfied, including absence of answer leakage. FAIL means it is not; UNCERTAIN means insufficient evidence. NOT_APPLICABLE is allowed only for the history family's unintended-style item when justified in notes.

N_style is an explicit absence-of-style comparator, not a guarantee of behavioral equivalence to C0. History A is a residence-history versus unrelated-dialogue comparison under matched format/length. Topic, factual content and temporal relationships intentionally differ. Do not call narrow acceptance full semantic neutrality or an isolated temporal-conflict manipulation.

Fill all check_* fields and researcher_decision: ACCEPT_NARROW, REVISION_REQUIRED, REJECT_AS_NEUTRAL, DIAGNOSTIC_ONLY or UNCERTAIN. Supply reviewer_id and review_assistance (unaided, AI-assisted, or other-disclosed-in-notes). Give verbatim evidence quotations for FAIL/UNCERTAIN and explanatory notes. Actual review time may be supplied in reviewed_utc; leave it blank if unknown. Do not copy an import timestamp as a review time. No reviewer identity is prefilled.

The importer checks unchanged source/version/packet, all IDs, duplicate/missing rows, required labels, reviewer provenance, exact matching and conflicts between acceptance and required checks. It preserves the received CSV separately and never launches inference:

```powershell
.\.venv\Scripts\python.exe tools/p1_review.py import --csv docs/validation/p1/control_review_completed_v1.csv --output docs/validation/p1/control_review_registration_v1
```

The completed-file path is a prospective destination, not a claim that annotations already exist. Any revised candidate needs a new version and review. Do not force unresolved labels to PASS.

## Response review

The output packet uses anonymous review IDs and shuffled rows. It hides condition/model identity and automated scores; the administrator mapping is separate. Do not consult the mapping before submitting independent judgments. Raw wording can reveal clues about treatments, so masking does not guarantee successful blinding. No blind human evaluation has been completed merely by creating this packet.

Review the fixed question/context and shared source fact ledger, then inspect the raw response and proposed first-reply span. Mark whether the proposed unit is identifiable; use completeness COMPLETE / INCOMPLETE / UNCERTAIN as a semantic judgment, separately from backend length termination. Quote the relevant response and evidence. A length cap does not make supported statements false. Additional generated turns are not new benchmark questions.

Factual labels: Correct, Incorrect, Unverifiable, Not Applicable. Recognize negation, incompatible alternatives, attribution and fact validity intervals. Unverifiable is not automatically right or wrong. Endpoint applicability is frozen: factual A/B/D, temporal A/D, relevance/coherence all; do not change eligibility because an answer is poor. Assess temporal consistency independently from factual support. Relevance and conversational coherence retain the existing 1-5 scales in [annotation guidelines](annotation_guidelines.md). Do not invent fidelity ratings without independent speaker reference behavior.

All raw outputs, including CROSS_TURN, AMBIGUOUS and unscorable outputs, remain in the planned denominators. Any later human registration or adjudication must be an additive, hash-bound version; do not overwrite automatic wave results. Independent reviewers and agreement may be reported only after actual annotations are supplied. Current forms do not establish consensus or scientific effects.
