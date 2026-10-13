# PersonaSLM P1b — Condition-Masked AI Semantic Review Proposal (UNCONFIRMED)

## Status and provenance

This report is an **AI-assisted provisional scientific review**, derived from the researcher-supplied `semantic_scoring_view_v2.csv`. It is **not** human blind annotation, a second human rater, an adjudicated ground truth, confirmatory evidence, or a valid basis for final factorial conclusions. The candidate `human_*` columns of the original 35-column schema remain entirely blank. The researcher must review/correct/confirm all scores before they are used for scientific results. Treatment identity was not present in the reviewer-facing CSV; anonymization cannot eliminate response-text clues.

## Input integrity

- Records: **192**; anonymous cases: **24**, exactly eight per case; response IDs: **192 distinct**.
- First-reply SHA-256: **192/192 verified** using exact UTF-8 bytes as loaded from CSV.
- Predefined applicability: factual **192/192**, temporal **88/192**, relevance **192/192**, coherence **192/192**.
- Human judgement fields: all blank in source. **All 35 original columns are copied without changing values** into the new CSV, and appended `ai_*` fields are suggestions only.
- No original model generations, prompt conditions, response-status classifications or raw experiment artifacts were modified or reconstructed.

## Candidate labeling policy (proposal; confirm against project guidelines before adoption)

- `Correct` describes explicitly verifiable claims consistent with trusted evidence. It does **not necessarily mean the user received all requested answer components**. `PARTIAL_ANSWER` is maintained independently to prevent inflation of full task success.
- `Incorrect` means a contradictory specific claim/answer, including using an expired fact as current. An incorrect but directly responsive answer may still have Response Relevance **5**.
- `Unverifiable` is used for a non-answer, promise to check or unfinished reasoning-only output; **not** for demonstrably false assertions. The official annotation guide also discusses `unknown/abstains`; a decision about mapping nonanswers to this label should be made before final import.
- `Not Applicable` is used for the **104** cases in which Temporal Consistency was frozen as inapplicable. It does not represent a model failure.
- `ai_candidate_delivery` distinguishes full answer, explicit wrong answer, partial answer, and no final answer. A wrong requested value can count as a **delivered** (but wrong) answer.
- Relevance: **5** for direct responsive answer (even when false); **3** for a partial but relevant response; **1–3** for an uncommitted promise or internal reasoning. Coherence: **5** for coherent continuation, generally **4** for a coherent promise, **2** for internal reasoning, and special diagnostic exceptions recorded explicitly. These are suggested ratings, not objective scales.

## AI-proposed provisional distributions — NOT experimental findings

| Proposed Factual Consistency | Count |
|---|---:|
| Correct | 137 |
| Incorrect | 34 |
| Unverifiable | 21 |

| Proposed Temporal Consistency | Count |
|---|---:|
| Correct | 40 |
| Incorrect | 34 |
| Unverifiable | 14 |
| Not Applicable | 104 |

| First-reply task delivery | Count |
|---|---:|
| FULL_ANSWER | 110 |
| WRONG_ANSWER_DELIVERED | 33 |
| PARTIAL_ANSWER | 27 |
| PARTIAL_WITH_FALSE_CLAIM | 1 |
| NO_FINAL_ANSWER | 21 |

**83** records are highlighted for explicit review, including missing components, temporal contradictions, uncommitted nonanswers, and truncated reasoning. The remaining records still require human confirmation if they are to become final human judgments.

## Individual case patterns (AI-proposed)

| Case | Question | Supported required answer | Fully delivered correct | Delivered incorrect / false partial | Partial supported but incomplete | No final answer |
|---|---|---|---:|---:|---:|---:|
| BC001 | Which room stores the archive box assigned to Arden Vale? | room=Juniper Room 1 | 8 | 0 | 0 | 0 |
| BC002 | Name Dara Wells's workshop and role. | role=materials coordinator, workshop=Bookbinding Group 4 | 6 | 0 | 2 | 0 |
| BC003 | Name Finley Ash's workshop and role in it. Also name the workshop's meeting place and the entrance to that place. | entrance=east entrance, place=Cedar Hall 6, role=materials coordinator, workshop=Bookbinding Group 6 | 8 | 0 | 0 | 0 |
| BC004 | Which building contains the crate assigned to Linden West? | building=West Annex 12 | 0 | 0 | 8 | 0 |
| BC005 | Which room stores the archive box assigned to Cleo Reed? | room=Juniper Room 3 | 8 | 0 | 0 | 0 |
| BC006 | Gale Rowan needs the shelf holding the folder assigned to the archivist. Which is it? | shelf=Amber Shelf | 8 | 0 | 0 | 0 |
| BC007 | Which counter applies to Indigo Shaw on 2027-04-10, and which applied on the preceding day? | counter=Cedar Counter, previous_counter=Birch Counter | 1 | 7 | 0 | 0 |
| BC008 | On which day does the hub serving Dara Wells's residence on 2027-04-15 open? | day=Tuesday | 0 | 8 | 0 | 0 |
| BC009 | Which collection hub serves Cleo Reed's residence on 2027-04-15? | hub=Heron Hub 3 | 2 | 6 | 0 | 0 |
| BC010 | Which desk should it go to on 2027-04-10? | desk=Ash Desk | 6 | 2 | 0 | 0 |
| BC011 | Which desk should it go to? | desk=Elm Desk | 6 | 0 | 0 | 2 |
| BC012 | Which locker contains the crate assigned to Jules Finch? | locker=Locker 60 | 4 | 0 | 4 | 0 |
| BC013 | Where does Briar Moss live on 2027-04-15? | city=Mereford 2 | 8 | 0 | 0 | 0 |
| BC014 | Name Jules Finch's pickup site on 2027-03-20 and the different site valid on 2027-04-15. | current_site=Harbor Lodge, site=Meadow Lodge | 4 | 0 | 0 | 4 |
| BC015 | Which room stores the archive box assigned to Briar Moss? | room=Juniper Room 2 | 8 | 0 | 0 | 0 |
| BC016 | Name Emery Lake's workshop and role in it. Also name the workshop's meeting place. | place=Cedar Hall 5, role=materials coordinator, workshop=Bookbinding Group 5 | 6 | 0 | 0 | 2 |
| BC017 | Which pickup site was valid for Indigo Shaw on 2027-03-20? | site=Meadow Lodge | 3 | 2 | 1 | 2 |
| BC018 | Finley Ash needs the folder assigned to the archivist. Which is it? | folder=Folder 76 | 8 | 0 | 0 | 0 |
| BC019 | Which collection counter applies to Gale Rowan on 2027-04-05? | counter=Birch Counter | 1 | 7 | 0 | 0 |
| BC020 | Which collection counter applies to Hollis Fern on 2027-04-10? | counter=Cedar Counter | 8 | 0 | 0 | 0 |
| BC021 | Which pickup site was valid for Hollis Fern on 2027-04-15? | site=Harbor Lodge | 2 | 2 | 4 | 0 |
| BC022 | Which desk should it go to on 2027-04-15? | desk=Ash Desk | 0 | 0 | 0 | 8 |
| BC023 | Which room contains the crate assigned to Kit Sorrel? | room=Fern Room 11 | 0 | 0 | 8 | 0 |
| BC024 | Emery Lake is checking the project: which shelf is assigned to Morgan North (p1b_F_L1-N)? | shelf=Amber Shelf | 5 | 0 | 0 | 3 |

## High-priority examples

- `BC008` (8 responses): `Monday` is the historical hub's opening day while the current residence's hub opens `Tuesday`. **Wrong current-date evidence chain**; not merely parsing.
- `BC007` (7 responses): correct `Cedar Counter` on April 10 is combined with wrong previous-day `Maple Counter`; the preceding day was `Birch Counter`.
- `BC019` (7 responses): refers to `Maple Counter` at April 5, whereas `Birch Counter` was valid on the stated date.
- `BC004` and `BC023`: output an intermediate entity/location but do not provide the requested final building or room. **Partial task completion is not automatically false factual content.**
- `BC022` (8 responses): a promise to check the parcel/desk rather than a delivery-desk answer; `Unverifiable` for factual/temporal assessment, **not Incorrect**.
- `BC014` (4 responses): incomplete `<think>` blocks, no user-facing final answer.
- `BC021` `BR188/BR113/BR090`: correctly reject expired Orchard Lodge without identifying Harbor Lodge; truthful partial evidence **does not meet full task success**. `BR096` explicitly identifies Harbor Lodge but its final date phrase is truncated; user must adjudicate completeness.
- `BC017` `BR001`: lists three correct dated site ranges without selecting the specific requested March site; the evidence may permit inference, but reviewer should decide if this satisfies task delivery.
- `BC024` `BR004/BR183/BR002`: mentions the correct Amber Shelf only inside “I will check”; this is **not** automatically a committed answer.
- `BC003` `BR168`: supplies all required facts but also starts a newly generated question; coherence and response-boundary interpretation merit review.

## What cannot yet be concluded

- This CSV is not a verified human-annotated dataset. Counts are **provisional AI suggestions**, not factual accuracy estimates or statistical results.
- Candidate success rates must not be compared as causal effects of P1 vs Wave 1, because tasks, prompts and selection differ.
- The structurally classified 186 CROSS_TURN cases and 5 TRUNCATED cases cannot be relabeled from this CSV alone; Stage B structural audit remains separate.
- Any apparent S/F/H differences require **researcher-confirmed annotation**, subsequent protected-condition unblinding, case-paired estimands and speaker-level uncertainty. The file itself contains no treatment labels and should stay that way.

## Recommended action for researcher and implementation agent

1. Preserve source `semantic_scoring_view_v2.csv` unchanged in `docs/validation/p1b/measurement_audit_v1/`.
2. Copy proposed CSV and this note to a versioned `docs/validation/p1b/review_support/` folder (or use another existing review-support convention).
3. Independently inspect the **83** priority records first; then examine the remaining records to confirm the suggested scores. Corrections must be recorded with reason.
4. After explicit researcher confirmation, create `semantic_review_researcher_confirmed_v1.csv` with original 35 columns, versioned review provenance, no fabricated independent review or agreement claims.
5. Only after a verified import should factorial effects and Algorithmic Opportunity Assessment be updated from semantic outcomes.
