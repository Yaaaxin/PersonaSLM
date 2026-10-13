# P1b Factual and Temporal Error Analysis

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Target: PLOS ONE. Protocol v1.1 remains formal; v1.2 Revised Proposed r1 is unadopted. Exploratory development evidence only. No new inference.

## Separate denominators and adopted factual judgments

Factual labels:137 Correct/192 (71.35%),34 Incorrect/192 (17.71%),21 Unverifiable/192 (10.94%). No missing annotation or factual N/A. The assessable subset is 171 responses;137/171=80.12% is conditional on assessability and must not replace the eligible-denominator distribution. These are output-level claim-consistency labels, not independently atomized claim precision. Of 137 Correct responses,110 are full correct answers and 27 are partial supported responses.

Temporal labels:40 Correct/88 (45.45%),34 Incorrect/88 (38.64%),14 Unverifiable/88 (15.91%);104 additional records are frozen N/A. The assessable temporal subset is 74;40/74=54.05% is a selected-subset description. No N/A is assigned a truth value.

## Exact factual-temporal overlap

| Factual / temporal labels | Responses |
| --- | --- |
| Correct / Correct | 40 |
| Correct / Not Applicable | 97 |
| Incorrect / Incorrect | 34 |
| Unverifiable / Not Applicable | 7 |
| Unverifiable / Unverifiable | 14 |


All 34 factual Incorrect labels coincide with temporal Incorrect labels; this wave does not provide 34 additional independent temporal failures. These ratings overlap by definition and content, not evidence for independent mechanisms. Some Unverifiable outputs are promises or unfinished reasoning; none is automatically converted to Incorrect.

## Temporal contradiction inventory

Every error has a preserved full model claim, exact trusted-evidence quotations, expected components and the adopted AI-assisted explanation in [the 34-row evidence table](validation/p1b/confirmed_analysis_v1/analysis_v1/temporal_error_evidence_v1.csv). The following task grouping is post-review analyst description, not a new human code or causal attribution.

| Case | Errors across eight conditions |
| --- | --- |
| p1b_C_L1 | 7 |
| p1b_C_L3 | 7 |
| p1b_E_L2 | 6 |
| p1b_E_L3 | 8 |
| p1b_G_L1 | 2 |
| p1b_G_L2 | 2 |
| p1b_H_L3 | 2 |


C-family errors select an interval-incompatible counter, including the wrong preceding-day counter at a boundary. E-family errors use an old residence or the hub/day linked to it when the question names a later date. G-family errors choose an expired pickup site for the requested historical/current date. H errors select the old delivery desk. Correct historical facts can be false answers at the requested date. All relevant old and current source entries remain in the evidence table so reviewers can check this distinction.

Crucially, C0 has four errors without any S/F/H package. A stale value may originate in the trusted dated ledger itself, not necessarily added H. Current H effects cannot isolate relevance, temporal status, first-entry bias or persona salience. Those are falsifiable prospective explanations, not established causes.

## Missing final answers and annotation limits

Twenty-one Unverifiable responses comprise 17 prospective-check responses plus four unfinished thinking continuations. The distinction is answer delivery, not an assumption that every literal token in a reasoning segment is false. Three promises contain the expected shelf name and have source component coverage 1/1, but remain NO_FINAL_ANSWER and Unverifiable; substring occurrence is not a committed answer.

Source coding is preserved, including implicit date interpretations, partial date-window listings and supported intermediate facts. Independent reannotation should inspect these cases, the ambiguous BR168 span and possible extra unsupported pronoun/identity claims. Do not silently revise the current version. The present researcher confirmation is not evidence of independent inter-rater reliability.

## Comparison with Wave 1

Wave 1 had 72/72 eligible factual Correct and 48/48 temporal Correct. P1b now has observed label variation and more component/interval demands, but datasets, applicability, prompt construction and annotation workflow differ. This is descriptive evidence of measurement range, not an isolated causal effect of task difficulty or proof of superior construct validity. Neither wave is pooled with the other; no historical rating is rewritten.
