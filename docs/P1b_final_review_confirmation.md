# P1b Final Review Confirmation — AI Proposal v1

Maintainer: Yaxin ZHENG. First submission target: PLOS ONE. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Protocol v1.1 remains the formal experimental baseline. Proposed v1.2 r1 is unchanged and not adopted.

## Current decision

**TECHNICAL READINESS = PASS. SCIENTIFIC REVIEW = PENDING. INFERENCE AUTHORIZATION = PENDING.** The 192-request calibration is not GO yet. There are zero new model responses and zero human approvals in this package.

The [24-case AI proposal CSV](validation/p1b/final_review_v1/stimulus_review_AI_proposed_v1.csv) proposes **312 PASS judgments, zero FAIL, zero UNCERTAIN**, and **24 case-level ACCEPT recommendations solely for bounded development calibration**. These are source-based AI proposals, not researcher decisions, empirical task-difficulty results or automatic acceptance based on engineering tests. Each of the 13 criteria has a case-specific explanation and supporting verbatim quotations. Researcher confirmation remains blank.

All 41 original fields per row are preserved: **984/984 unchanged**, including the 13 blank human judgment columns. The source master, supplied preliminary AI assessments, earlier decision packet, dataset, manifests and historical results are unchanged. The new proposal has additional `ai_*` fields and a blank `researcher_confirmation` field. The [proposal inventory](validation/p1b/authorization_v1/proposal_inventory_v1.json) records hashes and provenance.

Dataset SHA-256: `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6`.

Frozen manifest SHA-256: `d73ceb403148b01f7b2c83a51a20165fdd625658e50c04a7ce0caa118ab22869`.

AI proposal CSV SHA-256: `652a21aa67a4ac04f357f95653cc7c449a2982719d2c375253fd1769158bd718`.

## Positive-criterion interpretation

The [existing review guide](P1b_researcher_review_guide.md) governs all 13 judgments: sufficiency, uniqueness, reference correctness, temporal interpretation, entity clarity, question clarity, context validity, speaker consistency, reference stability, no accidental leakage, no unplanned contradictions, applicability and appropriate demand description.

An appropriate demand description can explicitly identify a simple baseline or a reasoning shortcut. PASS does not mean the task has demonstrated discrimination, that every link is necessary for a model, that style is disentangled from identity, or that the model will obey the prompt. Context validity means the referent and question are interpretable, not that preceding context is indispensable. The AI review separately checked the actual English questions and evidence chains; the source derivations and quotations in the CSV explain why the references follow without relying on a validation-status flag.

The 13 previously undated questions have the fictional reference date in all eight actual prompts. H_L3 has explicit role boundaries. These mechanical issues were resolved in the [previous scientific review](P1b_final_scientific_review.md); they are not new questions for the researcher to re-prove.

## Family-by-family recommendations

All rows below are **AI-proposed ACCEPT**, with all 13 positive criteria proposed PASS. No case is confirmatory evidence. The CSV contains the full quotations and per-criterion rationale; this table emphasizes the supported answer and limited experimental role.

| Family / case | Supported reference | Intended retained role and limitation |
|---|---|---|
| A_L1 | Juniper Room 1 | Simple retrieval baseline; the only archive record supplies the answer |
| A_L2 | Juniper Room 2 | Retrieval with one supply-box distractor; the archive record stays first |
| A_L3 | Juniper Room 3 | Retrieval with two supply-box distractors; no added reasoning hop is established |
| B_L1 | Bookbinding Group 4; materials coordinator | Two-component calibration; missing a component is separate from a contradictory claim |
| B_L2 | Bookbinding Group 5; materials coordinator; Cedar Hall 5 | Three-component calibration; the existing v2 question explicitly identifies the workshop's place |
| B_L3 | Bookbinding Group 6; materials coordinator; Cedar Hall 6; east entrance | Four-component calibration; output demand and possible 96-token censoring covary with level |
| C_L1 | Birch Counter | Simple dated lookup on April 5; the global reference does not override the question date |
| C_L2 | Cedar Counter | Inclusive April 10 start-boundary probe; Birch ends April 9 |
| C_L3 | Cedar Counter; previously Birch Counter | April 10 versus preceding April 9, with two answer slots |
| D_L1 | Locker 60 | Valid crate-to-locker chain; the only locker permits a shortcut |
| D_L2 | Fern Room 11 | Valid crate/locker/room chain; a unique terminal room does not prove traversal |
| D_L3 | West Annex 12 | Valid four-link chain; the only building can cue the answer directly |
| E_L1 | Mereford 2 | Current-residence baseline with genuinely true 2026 history; not isolated temporal interference |
| E_L2 | Heron Hub 3 | Current city-to-hub selection with an old-city branch; relevance and family remain entangled |
| E_L3 | Tuesday | Current city-to-hub-to-opening-day selection; confirm the existing v2 Tuesday correction, not the calendar weekday |
| F_L1 | Amber Shelf | Simple explicit-ID baseline for Morgan North; not a difficult disambiguation task |
| F_L2 | Folder 76 | Unique archivist-to-folder lookup; recurring North/archivist mapping limits generality |
| F_L3 | Amber Shelf | Role/folder/shelf chain; recurring mapping and answer template may permit shortcuts |
| G_L1 | Harbor Lodge | Current-date retrieval baseline on April 15 |
| G_L2 | Meadow Lodge | Correct March 20 historical value; not an outdated-current error |
| G_L3 | Meadow Lodge; currently Harbor Lodge | Two valid values at different dates; no simultaneous factual contradiction |
| H_L1 | Elm Desk | Simple follow-up baseline with only one parcel; context necessity is not established |
| H_L2 | Ash Desk | Dated follow-up through Recipient 142; only one parcel remains available |
| H_L3 | Ash Desk | Focus on Parcel 111 excludes Parcel 151/Oak Desk; two consecutive labelled User turns may influence Base continuation |

These fictional proposition dates are part of the experimental content, not execution dates. A/B/D/F and H_L1 retain temporal endpoint N/A; C/E/G and H_L2/H_L3 are temporal-eligible. All cases are factual/relevance/coherence-eligible. No Persona Fidelity ground truth is created.

## Limitations that must remain visible

- Designed levels are metadata, not an empirically established ranking. Longer evidence, more output slots or more source links do not automatically mean greater difficulty.
- H_L1/H_L2 retain a useful baseline role without establishing context necessity. H_L3 distinguishes referents in the supplied source, but actual context use is untested. Its two successive User turns remain unchanged; format may affect continuation.
- D's unique terminal entities and F's explicit identifiers or repeated role mapping allow shortcuts. Correct outputs cannot establish the internal reasoning route.
- Style is partially nested within persona identity. Between-speaker differences do not isolate style. The uniform woven-bookmark fact limits the generality of F.
- Historical residence is especially relevant in E. Task family, history relevance and temporal content are not fully separated. S/F/H contrasts estimate these intervention packages; they do not isolate historical relevance, temporal conflict or presentation alone.
- The fixed 96-token output budget may constrain B's larger answers or Base reasoning continuations. Factual support, response completeness and structural status must remain separate.
- No independent confirmatory dataset has been evaluated. This bank remains development material even if calibration is successful. No neutral-adjusted comparison is authorized; the 24 prior Wave 1 neutral candidates remain OPEN and are not P1b controls.

## Exact researcher decisions needed

**Q1 — case validity:** inspect the proposed judgments and quotations for all 24 cases, including the existing B_L2/B_L3 wording corrections and E_L3 Tuesday correction. Confirm or disagree with the 13 positive criteria per case. A case-level confirmation explicitly covers those proposed judgments; agreement must not be inferred from the AI decision.

**Q2 — qualified interpretation and measurement:** confirm retaining the unchanged bank with the limitations above and the existing manual, task-specific evaluation routing. Approving a simple baseline does not authorize a context-necessity or multi-step-reasoning claim. Approving factual support does not remove completeness or relevance assessment.

**Separate execution decision:** after Q1/Q2, explicitly authorize this exact 192-request plan if desired. Scientific review confirmation alone does not authorize model generation. The original [two-question packet](validation/p1b/final_review_v1/decisions_pending_v1.csv) remains untouched; [the current decision sheet](validation/p1b/authorization_v1/researcher_decisions_v1.csv) provides references to the new proposal and separates the execution decision.

Researcher decision, identity, method and optional actual review date remain blank. There is no fabricated blind review, independent second reviewer or agreement statistic.

## How to confirm without rewriting the master

Save a completed copy of the AI proposal CSV under a new filename. For a case whose proposed judgments and limited interpretation you explicitly confirm, enter `CONFIRM_ALL_PROPOSED_JUDGMENTS` in `researcher_confirmation`, your actual `reviewer_id` and `review_method`; an actual `reviewed_utc` is optional. Keep all original stimulus fields and AI suggestions unchanged. Add notes if needed. Confirming the complete, hash-identified packet in an explicit researcher message can also be registered later with that actual decision source; no such message has yet been supplied for this proposal.

If you disagree, do not change AI labels to impersonate the original proposal or choose acceptance to satisfy the importer. Save a completed copy of the original 41-column master with your own judgments and notes. The existing manual importer preserves it. A substantive negative/uncertain decision pauses acceptance; any resulting correction or registration adaptation must preserve the submission and remain separately versioned.

For an explicitly confirmed proposal copy, the following command is available **for future use; not executed here**:

```powershell
.\.venv\Scripts\python.exe tools/p1b_review_proposal.py register-confirmed --csv docs/validation/p1b/P1b_AI_proposal_researcher_confirmed.csv --output docs/validation/p1b/researcher_confirmation_v1 --confirm-limited-interpretation --confirm-evaluation-routing
```

Use the confirmation flags only after the researcher has made those decisions. The importer checks all 24 IDs, immutable original/AI fields, per-case confirmation, actual reviewer/method and valid supplied dates. It preserves the submitted file, creates a new official 41-column annotation copy and a versioned provenance register, and records AI-assisted confirmation explicitly. It never invents a review date or authorizes inference. Rejected submissions stay untouched.

## Measurement success and publication value

The calibration asks whether factual/temporal outcomes become meaningfully variable and assessable, whether structural failures censor coverage, whether paired operational S/F/H contrasts are interpretable, and which families need independent validation. Continued ceilings, null effects, task-invariant errors and low semantic coverage are valid findings. Producing errors alone is not success. All 24 cases remain selected; no C0-correct filtering or exclusion of unfavorable outputs is permitted.

The existing [novelty matrix](related_work_novelty_matrix.md) and [algorithmic assessment](P1b_algorithmic_opportunity_assessment.md) delimit direct overlap: *Principled Personas* and *One Persona, Many Cues* cover unintended persona effects/cue sensitivity; *When Personalization Misleads* directly overlaps personalized factual reliability; *Decoupling Logic from Persona* and *What to Admit and How to Present* overlap separation and memory intervention designs. These are the repository's previously documented comparisons, not a new literature verification in this task. Factorial design, CPU execution, a new adapter and high continuation rates are not novelty claims. A defensible PLOS ONE contribution requires informative, reproducible empirical evidence and appropriately bounded claims; this preparation alone does not provide it.

## Algorithmic opportunity assessment

| Required aspect | Current assessment |
|---|---|
| Observed failure modes | Historical Wave 1 shows structural/semantic disagreement and automatic-scorer coverage limitations; P1b has no outputs |
| Existing methods | The linked assessment covers memory selection, time-aware access, persona/evidence separation, boundary controls and claim/evidence verification |
| Potential improvements | Conditional diagnostic candidates only; no P1b failure currently justifies implementing a new algorithm |
| Validation feasibility | Any later method needs a reproducible observed failure, comparison baselines, separate development material and independent evaluation |
| Publication value | Better measurement and carefully qualified empirical comparisons are the immediate value; no algorithmic originality is claimed |

No algorithm implementation, new model arm, expansion, Wave 2, P2–P6 or inference is performed. See [execution readiness](P1b_calibration_execution_readiness_v1.md) for the adapter, authorization gate, tests and reproducibility evidence.
