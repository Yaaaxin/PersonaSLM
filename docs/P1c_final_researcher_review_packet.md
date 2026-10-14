# P1c Final Researcher Review Packet — v1

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE.

## Decision presented for approval

**Recommend accepting the existing 12 cases for bounded development under restricted, package-level estimands. Execution remains NO-GO until researcher decisions and explicit authorization are registered.** No reference-answer defect requiring stimulus replacement was found. No stimulus, previous review, generation, protocol or original request order was changed.

The packet is AI-assisted scientific analysis, not completed human annotation. There are **12 case proposals and 60 text proposals**. The **12 neutral assessments are a subset of those 60**, not 12 additional independent items. Human decisions, identities and timestamps are blank. Technical success does not settle semantic suitability.

## Files to review

1. [12 case decisions](validation/p1c/final_review_v1/final_case_review_proposed_v1.csv): full trusted ledger, question, dates, context, reference answer, source quotations, 13 criterion-specific assessments, restrictions and correction recommendation.
2. [60 historical/control text decisions](validation/p1c/final_review_v1/final_history_review_proposed_v1.csv): original complete texts, source associations, case-specific judgments, token evidence and limitations. Join the `case_id` to the first file for its full ledger; no unrelated raw log is needed.
3. [12 neutral-control assessments](validation/p1c/final_review_v1/final_neutral_review_proposed_v1.csv): an identical convenience subset of the text file, emphasizing failed strict-neutrality criteria.
4. [Researcher confirmation form](validation/p1c/final_review_v1/researcher_confirmation_form_v1.csv): 72 unique item decisions plus five global decisions. Return a completed copy; preserve the master. Do not enter a review time unless actually known.

`AI_checks` contains each criterion's label and its explanation. PASS means that named criterion is supported; FAIL means it is not; UNCERTAIN means semantic interpretation or behavioral evidence is unresolved. Overall operational PASS does **not** override a failed pure-identification criterion. JSON companions preserve the same information for validation. No AI proposal is automatically imported as human approval.

For case decisions use `ACCEPT_AS_DEVELOPMENT`, `ACCEPT_WITH_RESTRICTED_ESTIMAND`, `REVISION_REQUIRED` or `REJECT`. For text disposition use `ACCEPT_WITH_LIMITATIONS`, `REVISION_REQUIRED` or `REJECT`, with an explanation for corrections. Global decisions may be APPROVE, DECLINE or DEFER. A single explicit researcher statement adopting all specified case/text IDs and the exact manifest hash can also confirm the set; it must explicitly acknowledge the restrictions and distinguish approval from permission to execute.

## Case-level proposal summary

Every row below proposes **ACCEPT_WITH_RESTRICTED_ESTIMAND**. Historical queries request 2042-06-15; current queries request 2042-12-15. The evaluation reference is 2042-12-15 throughout.

| Case | Speaker | Required delivered answer | Designed demand and specific limitation |
|---|---|---|---|
| p1c_01_historical | Auden Vale | Laurel | Single interval lookup; implicit parcel/desk relation; retrospective archive |
| p1c_01_current | Auden Vale | Harbor | Single interval lookup; implicit parcel/desk relation |
| p1c_02_historical | Celia North | Harbor | Single interval lookup; explicit identity; retrospective archive |
| p1c_02_current | Celia North | Maple | Single interval lookup; parcel association is assumed |
| p1c_03_historical | Elian Moss | Maple and Tuesday | Two requested components; direct retrieval remains possible; retrospective archive |
| p1c_03_current | Elian Moss | Orchid and Thursday | Two requested components; correctness of one is not full success |
| p1c_04_historical | Greta Sable | Orchid and Thursday | Two components; task-family/speaker nesting; retrospective archive |
| p1c_04_current | Greta Sable | Silver and Saturday | Two components; parcel/desk/day association not explicit |
| p1c_05_historical | Idris Fern | Silver | Dated route-to-room join; correct terminal does not prove reasoning; retrospective archive |
| p1c_05_current | Idris Fern | Cobalt | Route join; parcel topic explicit; cyclic-value shortcut remains possible |
| p1c_06_historical | Nora Finch | Cobalt | Route join; multiple rooms available; retrospective archive |
| p1c_06_current | Nora Finch | Laurel | Route join; explicit entity cues; no empirical difficulty claim |

All references are entailed by the common ledger. Auxiliary-history deletion/substitution in the reference solver leaves answers unchanged. This establishes formal evidence independence, not the absence of learned lexical shortcuts. The case file deliberately marks absence of shortcuts UNCERTAIN and isolated factor semantics FAIL.

## Text and control recommendations

Of 60 text-level operational judgments, **32 PASS and 28 UNCERTAIN**: 24 music-topic records and eight parcel records for explicit parcel-route questions pass their operational assignment checks; 16 parcel records for desk/day questions need confirmation of the assumed topical association; all 12 procedural controls remain uncertain in suitability. Each text is proposed only as **ACCEPT_WITH_LIMITATIONS**, subject to researcher adoption. These counts are not human acceptance counts.

All active texts are historically true in their stated intervals. T=0 means expired **at the requested date**, not false. T=1 means valid at that date, not necessarily the latest record. All use the same target speaker, Archivist role, archive date and two-turn layout. R changes the auxiliary attribute and color; T changes color and interval. No active text directly gives the required desk/day/room or an alternative value of that target predicate.

All neutral texts preserve the earlier repair, including “its two distinct parts.” They match complete prompt length but discuss question/reply organization. Information equivalence, absence of style/topic priming and chronological equivalence fail their strict criteria. The defensible proposed role is **matched procedural-content comparator**, not inert placebo or full semantic neutrality. Approving this limited comparison is a substantive researcher decision, not a relabeling of FAIL as PASS.

## Five concrete decisions

1. Accept package-level R/T meanings, the implicit parcel association for eight desk/day cases, and retrospective rather than as-of-knowledge historical questions.
2. Accept or reject all 12 controls for the limited procedural-content comparison; do not certify complete neutrality.
3. Approve the [estimand registry](P1c_final_estimand_registry.md) and prospective evaluation/statistical policy, including unknown outcomes and six-speaker uncertainty.
4. Approve the [P1c-specific addendum](P1c_protocol_addendum_proposal.md), leaving v1.1 and proposed v1.2 untouched.
5. Separately authorize exactly 72 requests under the [candidate manifest](validation/p1c/final_review_v1/calibration_manifest_candidate_v1.json) after execution preflight. Approval of scientific materials alone is not an inference instruction.

There is no request for another broad candidate search. If a specific item is rejected, address that identified defect with a preserved new version; do not silently alter this candidate.

## Scope of the eventual evidence

The development calibration can examine measurement feasibility and outcome differences between these text packages under sufficient identical evidence. It cannot identify pure topical attention, temporal cognition, direct stale-answer competition, a general persona law or publication readiness. Six speakers, repetitive lexical assignments, topic/family coupling, retrospective records, procedural priming and a fixed 96-token budget remain visible limitations. Neutral comparisons require their own approval. Independent validation and optional model/algorithm work are later research decisions, not additional conditions invented to prolong this review.
