# P1c Researcher Confirmation Registration (Scoped)

## Status

**Researcher-reviewed AI-assisted scientific proposals: registered.** The researcher explicitly stated that the supplied review material was fully read and confirmed. Approval applies to the concrete scope proposed in the 77-row review, not to additional claims, missing external policy documents, or execution of inference.

| Item | Count | Registered disposition |
|---|---:|---|
| P1c development cases | 12 | RESEARCHER_CONFIRMED — ACCEPT_WITH_RESTRICTED_ESTIMAND |
| Active R/T history texts | 48 | RESEARCHER_CONFIRMED — ACCEPT_WITH_LIMITATIONS |
| Matched procedural controls | 12 | RESEARCHER_CONFIRMED — DIAGNOSTIC_ONLY |
| Global restricted scientific scope | 1 | RESEARCHER_CONFIRMED — ACCEPT_WITH_RESTRICTED_ESTIMAND |
| Global neutral control scope | 1 | RESEARCHER_CONFIRMED — DIAGNOSTIC_ONLY |
| Evaluation/statistical policy | 1 | PENDING_DOCUMENT_REVIEW |
| Prospective protocol addendum | 1 | PENDING_DOCUMENT_REVIEW |
| Execution authorization | 1 | NO_GO_PENDING_EXPLICIT_AUTHORIZATION |
| **Total** | **77** | **74 confirmed scoped decisions; 3 acknowledged pending gates** |

## True annotation provenance

- **Original item-specific conclusions:** AI-assisted scientific review, based on the uploaded source records.
- **Final approval of the 74 scoped scientific dispositions:** Yaxin ZHENG, after personally reviewing the proposals.
- **Human-review characterization:** researcher review and adoption of AI-assisted proposals, **not** a second independently blinded annotation or inter-annotator agreement study.
- **Review time:** not recorded; no timestamp was invented.
- **Source material:** unchanged; all versioned output files are new.
- **Row-level subcriteria:** remain blank where distinct manual ratings were not supplied.

## Preserved limits on inference

1. The 12 cases may be used for bounded development calibration. R and T compare **history text bundles**: changing R also changes topic, predicate, and lexical cues; changing T also changes historical validity dates and some attribute values. They do **not** isolate a pure temporal mechanism or stale-answer competition.
2. The implicit relation between parcel topics and desk/day queries is not equally strong across task families. Report family-level sensitivity and do not infer a homogeneous semantic relevance mechanism.
3. The 12 matched control texts are **procedural diagnostic comparators**, not verified semantically neutral, information-equivalent history. They may prime answer organization or archival form.
4. No-history prompts are shorter and are not length-controlled comparisons.
5. The existing 12 development cases and six speaker clusters do not support stable population-level interaction estimates. The proposed 72 generations are a development calibration, not confirmatory or publication-complete evidence.
6. Original experimental responses, historical experiments, model manifests, and frozen prompt hashes were not changed by this registration.

## Mandatory remaining checks before real generation

- Read and explicitly approve the **actual complete P1c evaluation rubric, metric applicability/missingness rules, 16 contrast definitions, and cluster-aware statistical plan**. These documents were not part of the three original reviewer CSVs; thus the global review item remains PENDING_DOCUMENT_REVIEW.
- Read and explicitly approve the **prospective P1c protocol addendum**. Do not silently modify historical Protocol v1.1 or adopt a proposed v1.2 by default.
- Validate the original 72-request manifest and its digest against the current dataset, prompt/tokenizer, model/backend and policy versions. The previously reported local technical checks are not a substitute for final preflight.
- **Explicitly and separately authorize exactly 72 real CPU generations** after the preceding approvals. This file and the researcher's confirmation of review proposals do **not** confer execution authorization.

## Placement and usage

The ZIP bundle contains versioned files with project-root-relative paths. Extract into the repository root without overwriting the original review CSVs. The canonical import candidate is:

`docs/validation/p1c/final_review_v1/researcher_confirmation_form_RESEARCHER_CONFIRMED_v1.csv`

The enriched proposal-to-confirmation trace is:

`docs/validation/p1c/final_review_v1/PersonaSLM_P1c_77_item_RESEARCHER_CONFIRMED_v1.csv`

Importers must reject unknown decision labels or report schema differences rather than silently converting pending approvals to PASS. Preserve the AI suggestion versions and Git provenance. No inference, commit, or push is performed here.

## Cryptographic audit

Input source SHA-256:

```json
{
  "proposal": "4b3aeecc1ffcdf92960c54c12c129b621c939927e604309f7710a594887e2c77",
  "confirmation": "84acbea45f26f6ac13585fa27c8aaf33093a2485e8872d015d2c1b8ebdb2bf7f",
  "cases": "c7e868d82c0a9bb7ac01b4b756c128329035f2190d9f5cb6b847db682aaa780c",
  "history": "82f77dec440b1ca9966de7933dc13f9128bc201efa428cdf8e5a9982680c1150",
  "report": "9cb0528d54f0cd641df338f1719c6d289d84747c62728f3b434e1930c9af9b68"
}
```

The machine-readable manifest includes hashes of generated CSVs; validate after copying or importing. No claim is made of independent reproduction of the original 72-tokenizer/preflight tests from these reviewer files alone.
