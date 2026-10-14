# P1d independent measurement preparation: P1c boundary audit

Maintainer: Yaxin ZHENG. This package contains 72 existing P1c development continuations. It is a measurement audit, not new P1d empirical replication. No independent reviewer has been recruited and no ratings have been entered.

Reviewer file: [boundary_review_blinded_v1.csv](validation/p1d/development_readiness_v1/independent_measurement/boundary_review_blinded_v1.csv). Only this file and this guide should be supplied for initial boundary review. The separate mapping is withheld; separation into files is not an operating-system access-control guarantee.

Read the question, fixed context and complete unchanged continuation before selecting a span. Do not consult prior parser outputs, AI scores, treatment assignments, model identity or previous P1c results. Text may still reveal stylistic or treatment cues; perfect blinding is not claimed. The 72 records were independently reordered with software seed 716501; this randomization does not create an independent annotator.

Record `accepted_spans_json` as a JSON list of half-open character intervals, for example `[[0, 25]]`, measured in Unicode code points of the exact `unchanged_raw_continuation` cell after CSV decoding. Preserve whitespace; do not count the CSV file's quoting or doubled quotation escapes. A new role utterance may end the first assistant response; a heading inside a response does not automatically do so. A section title, quoted role marker and literal code block require contextual assessment.

Use `boundary_disposition` = `UNIQUE_DEFENSIBLE_SPAN`, `MULTIPLE_DEFENSIBLE_SPANS`, `NO_RECOVERABLE_REPLY`, or `UNRESOLVED`. Multiple spans are permitted. Leave spans blank when unresolved; `[]` is reserved for a judged absence of a recoverable reply. Record supporting cues, alternative interpretations and uncertainty. A complete but wrong answer may have an unambiguous boundary. A promise is identifiable text but may not deliver an answer. Do not change a boundary to make an answer correct.

Record `answer_delivered` = `YES`, `PARTIAL`, `NO`, or `UNCERTAIN`, with a separate justification. This does not substitute for full factual, temporal or task-success ratings. Leave reviewer identity, independence declaration and actual submission time to the real reviewer. Do not invent times or a second annotator.

After the independent boundary file is returned, preserve it unchanged and verify its raw text hashes and offsets. Prepare semantic scoring views from accepted spans separately from the original frozen primary view. A human adjudication may establish several defensible spans rather than a uniquely correct answer boundary. Compare original and adjudicated views as measurement sensitivity; never overwrite P1c structural labels. Agreement requires genuinely separate human judgments; no statistic is computed from this empty form.

`tools/p1d_independent_boundary_import.py` validates all original IDs/text fields, reviewer declarations, mandatory decisions and character offsets. It rejects blank forms, out-of-range spans and altered source text. A valid schema is not proof of actual reviewer independence, researcher adoption or annotation reliability; no historical labels are updated automatically.

The adopted P1d annotation plan retains nominal/ordinal agreement, component-level comparison, uncertainty, speaker clustering and a separate measurement pilot. New P1d confirmatory readiness requires independent material/rubric validity and useful unresolved-outcome rates, not merely completion of this P1c audit.
