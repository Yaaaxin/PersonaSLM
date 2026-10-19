# Stage-A Human-Review Workflow v4 Addendum

Status: append-only operational addendum. It does not modify the frozen v3
protocol, controller, review materials, 168-record requirement, or evidence.

## Purpose

The frozen v3 provenance validator records all required fields, but its
classification omits `prior_rubric_or_item_involvement` and does not distinguish
a blinded project reviewer from a project-independent reviewer. The v4 offline
helper corrects those claim boundaries without reading the protected condition
mapping or creating labels.

The helper accepts partially completed working copies so the reviewer can save
locally and obtain row-specific feedback. Final readiness still requires all 168
rows to be valid `COMPLETED` or documented `UNAVAILABLE` records.

## Workflow

Never edit the official template. Create an exclusive working copy:

```powershell
.venv\Scripts\python.exe -B tools\p1_persona_dialogue_disjoint_surface_validation_review_v4.py init-copy --submission <PRIVATE_WORKING_COPY.csv>
```

Validate after any local save. Blank and unfinished rows are counted but are
allowed in draft mode; immutable changes, invalid enums, and invalid evidence
spans are errors.

```powershell
.venv\Scripts\python.exe -B tools\p1_persona_dialogue_disjoint_surface_validation_review_v4.py validate-draft --submission <PRIVATE_WORKING_COPY.csv>
```

After all 168 rows are finalized, create an exclusive provenance skeleton. Hash
bindings are filled automatically, but every human attestation is deliberately
left blank and must be completed truthfully by the human reviewer.

```powershell
.venv\Scripts\python.exe -B tools\p1_persona_dialogue_disjoint_surface_validation_review_v4.py create-provenance --submission <PRIVATE_WORKING_COPY.csv> --provenance <PRIVATE_PROVENANCE.json>
```

Run final offline validation and preserve its append-only receipt:

```powershell
.venv\Scripts\python.exe -B tools\p1_persona_dialogue_disjoint_surface_validation_review_v4.py validate-final --submission <PRIVATE_WORKING_COPY.csv> --provenance <PRIVATE_PROVENANCE.json> --report <NEW_PRIVATE_V4_VALIDATION_RECEIPT.json>
```

`READY_FOR_OFFICIAL_SEAL_ATTEMPT_NOT_SEALED` means only that the public package,
168 rows, provenance attestations, and hashes passed the offline checks. The
helper does not read the protected mapping, create the official v3 seal, or
authorize unblinding. The frozen controller remains the run-bound sealing step.

## Corrected provenance classes

- `CLEAN_INDEPENDENT_BLINDED_HUMAN`: genuine human, no relevant exposure, and
  attested project independence with `INDEPENDENT_EXTERNAL` relationship.
- `BLINDED_NONINDEPENDENT_HUMAN`: genuine condition-blinded human, no recorded
  exposure, but not project-independent. A principal-researcher review belongs
  here and is not independent validation or inter-rater reliability.
- `HUMAN_EXPOSURE_LIMITED`: genuine human with `YES` or `UNCERTAIN` for prior
  rubric/item involvement, prior output/item exposure, condition mapping,
  automatic labels, or premature Stage-B material. Project independence remains
  a separate attestation and does not turn this into clean blinded evidence or
  independent experimental validation.
- `INELIGIBLE_AS_GENUINE_HUMAN`: non-human review, or AI assistance for judgments
  reported as `YES` or `UNCERTAIN`.

The v4 receipt reports the predicted legacy v3 class alongside the corrected
class. Scientific claims must use the corrected class. No AI-generated judgment
may be entered into the review CSV.
