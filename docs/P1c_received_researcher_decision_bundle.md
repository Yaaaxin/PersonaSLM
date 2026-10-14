# P1c Supplied Researcher Decisions — Intake and Remaining Gate

Maintainer: Yaxin ZHENG. This update supersedes the initial **absence-of-supplied-decisions** status in the [workflow preparation record](P1c_decision_registration_and_execution_gate.md); it does not overwrite that record or authorize inference.

## Newly located source

During the final working-tree check, a new directory appeared: `PersonaSLM_P1c_Researcher_Confirmed_Registration_v1/`. It contains four CSVs, a supplied confirmation manifest and a report. These six supplied files were read and left unchanged; they were not moved into, or substituted for, historical master files.

The [machine intake check](validation/p1c/decision_gate_v1/received_bundle_check_v1.json) verifies the three original repository-source hashes, all four supplied CSV hashes, exact IDs and cross-file decisions. **1,772 non-annotation fields match; zero differences.** The extra external proposal/report identified by two declared source hashes were not separately supplied and are marked unverified declarations. That does not negate the verified direct comparison with the original three repository masters.

## What the supplied records actually state

| Supplied disposition | Count | Registration interpretation |
|---|---:|---|
| Cases: ACCEPT_WITH_RESTRICTED_ESTIMAND | 12 | Explicitly scoped researcher-confirmed dispositions |
| Active histories: ACCEPT_WITH_LIMITATIONS | 48 | Legacy label preserved; new-schema mapping needs confirmation |
| Matched controls: DIAGNOSTIC_ONLY | 12 | Subset of the 60 text records; no neutrality approval |
| Global restricted interpretation | 1 | Scoped confirmation |
| Global diagnostic-control role | 1 | Scoped confirmation |
| Evaluation/statistics | 1 | PENDING_DOCUMENT_REVIEW |
| Protocol addendum | 1 | PENDING_DOCUMENT_REVIEW |
| Execution authorization | 1 | NO_GO_PENDING_EXPLICIT_AUTHORIZATION |

The supplied bundle therefore contains **74 scoped confirmations and three acknowledged pending gates**, including 72 unique case/text items. It does not contain 84 independent items or 77 approvals. Its provenance states researcher review and adoption of AI-assisted proposals, not independent two-human annotation. No review timestamp or separate manual subcriterion values are supplied; their blanks remain blank.

## Canonical registration status

**Source integrity: PASS. New-schema canonical registrations: 0. Execution: NO_GO.** The new importer deliberately rejects unknown labels; 48 legacy `ACCEPT_WITH_LIMITATIONS` values are not silently rewritten into the newly requested vocabulary. A narrowly scoped question has been presented: confirm mapping those 48 values to `ACCEPT_WITH_RESTRICTED_ESTIMAND`, retaining both the original values and reasons. No mapping approval is inferred from waiting or file presence.

The source's unfilled fine-grained subcriteria must not be filled as if separately rated. Its actual overall adoption can be preserved in a legacy-scoped record; it must not be represented as a completed v2 positive-criterion form. The current strict v2 importer has not imported this legacy bundle. Any later compatibility conversion must be separately recorded, preserve the original source, and use only explicitly confirmed information. No request to redo the 72 scientific reviews is made here.

## Minimum remaining decisions

1. Resolve the single legacy-label mapping question for the 48 active histories; preserve the original record and missing subratings.
2. Review and approve the actual complete evaluation/applicability/16-contrast/statistical documents. Their approval is explicitly pending in the supplied bundle.
3. Approve the actual P1c prospective addendum.
4. Separately authorize exactly 72 requests tied to the original manifest and accepted registration, after mandatory technical checks.

The neutral-control interpretation is already explicitly diagnostic-only in the supplied source. All twelve retain original `N_history` IDs and the analysis classification `LENGTH_MATCHED_DIAGNOSTIC_CONTROL`. No pure semantic history mechanism is claimed. The frozen manifest, configuration and 96-token budget remain unchanged. No generation occurred, and no new experimental or algorithmic work is proposed by this intake.

## Validation scope

The workflow's focused automated suite remains **105 passed**. The additional supplied-file intake is an actual successful read-only integrity check, not a new model experiment or fabricated annotation test. Its exact command, source hashes and resulting counts are retained separately. Earlier NO_GO output correctly described the state before this directory appeared; it is preserved as historical status, with this intake supplement recording the changed file availability.
