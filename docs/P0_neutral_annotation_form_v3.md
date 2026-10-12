# P0 Researcher Annotation Form, Version 3

**Current readiness check (2026-10-12):** all 40 CSV rows were reconstructed from the original frozen prompts and matched the immutable JSON template, including evidence, question, identifiers and zero token differences. Human review remains **OPEN, 0/40 completed**. See [readiness evidence](validation/P0_neutral_review_readiness_v1.json). No new human submission was supplied. Existing import code also rejects incomplete ratings, invalid labels, duplicate or missing rows, changed form versions/material, blank reviewer IDs and invalid review times; its tests use explicitly identified software test doubles.

Status: **PARTIAL; 0/40 human reviews completed.** All judgments are blank. This is an English annotation instrument, not an automatic evaluation result.

Use the [CSV form](validation/P0_neutral_annotation_form_v3.csv) with its immutable [JSON template](validation/P0_neutral_annotation_form_v3.json). Each of the 40 historical matched controls includes `case_id`, `condition_id`, exact `neutral_text` including its heading, `reference_condition`, `token_count`, `reference_token_count`, `token_difference`, evidence, question and hashes. Token counts refer to the **entire final prompt**, not the neutral text alone. All historical differences remain zero.

This version exposes case/condition IDs as requested; it is **not condition-blinded**. It withholds model outputs and scores. The previous blinded material is preserved. Independent means the researcher supplies their own judgments, without substituting software or agent judgments.

## Rating instructions

For every dimension, `PASS` means the neutrality requirement is satisfied, `FAIL` means a substantive problem is present, and `UNCERTAIN` means available evidence is insufficient. Empty means not reviewed and is never converted to PASS. Quote the problematic text and explain uncertainties in `reviewer_notes`.

| Column | PASS criterion | FAIL examples |
|---|---|---|
| `answer_leakage` | The added neutral text does not reveal an answer | Explicit or implied expected city in the addition |
| `additional_factual_information` | No new personal or answer-relevant factual information is introduced | Added residence, age, preference or relationship claim |
| `contradictory_information` | No contradiction with the trusted record/question | A conflicting personal fact or instruction to ignore evidence |
| `temporal_interference` | No unintended date, outdated claim or misleading temporal cue | A wrapper/date that changes interpretation of the current question |
| `unintended_linguistic_style` | No extra persona style or strong stylistic instruction | Distinctive voice, mandatory catchphrase, or potentially influential repetition |
| `semantic_neutrality` | The full addition is acceptable as a neutral control | Any substantive semantic interference, including issues outside the other columns |

Answer leakage is assessed in `neutral_text`; the expected city is intentionally visible in trusted evidence. Inspect repeated sentences, role names and historical/style headings. Equal token counts and a preserved date are insufficient evidence of neutrality. Use UNCERTAIN when residual style or temporal effects cannot be resolved by inspection.

Fill all six ratings, a reviewer pseudonym in `reviewer_id`, actual review time in UTC in `reviewed_utc`, and notes for each completed row. Example timestamp syntax: `YYYY-MM-DDTHH:MM:SS+00:00`; do not copy a fabricated example date as the actual review time. Unreviewed rows stay entirely blank in the editable fields. Keep every item and do not edit immutable text, identifiers, counts or hashes.

## Separate storage and versioned import

Copy the CSV to a new file for each reviewer/round, for example `results/human_review/researcher_round1.csv`. Preserve the blank master and all original submitted copies. That local directory is ignored by Git. Import completed rows with the command below **after a real reviewer has supplied ratings**; it was not run on a completed human form in this session:

```powershell
.\.venv\Scripts\python.exe -m personaslm.neutral_review import --template docs/validation/P0_neutral_annotation_form_v3.json --input results/human_review/researcher_round1.csv --output results/human_review/researcher_round1.imported.json --review-round researcher_round1
```

The importer validates the schema, unique IDs, unmodified material, packet hash, allowed ratings, reviewer ID and explicit UTC time. It supports partial review of the packet but requires all six ratings for each completed item. It saves submitted UTF-8 text, file hashes, packet/version, review-round ID, actual import time, completed/remaining counts and ratings. It refuses to overwrite an existing import. Corrections and adjudications require a new file and round identifier; retain original judgments and disagreement rather than replacing them.

Software cannot authenticate that a named reviewer is human or independent. Import validation does not create human evidence, consensus or inter-reviewer agreement. Importing the actual blank master was tested and rejected with `No completed review items; no human judgments imported`; no review result was created. Positive importer tests use explicitly labeled test doubles in disposable test directories, never the research annotation ledger.

Do not select or revise controls based on model accuracy. If review identifies a failing control, preserve its original text and rating; construct and freeze a new control version, repeat real-tokenizer matching at tolerance zero, and independently review the revision before using it scientifically. No such replacements or additional control generations were performed here.
