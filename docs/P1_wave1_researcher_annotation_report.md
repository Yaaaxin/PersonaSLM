# P1 Wave 1 Researcher Annotation Registration

Maintainer and final decision authority: Yaxin ZHENG. Official paper title: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Executed protocol: v1.1. The revised v1.2 r1 remains an unchanged, unadopted proposal.

## Registration decision

**96/96 records are registered as RESEARCHER_CONFIRMED**, version `researcher_verified_annotation_v1`. There are 12 anonymous cases with eight unique responses per case. The final [41-column annotation CSV](validation/p1/output_human_review_researcher_verified_v1.csv) retains the original review schema and anonymous IDs. The [registration](validation/p1/researcher_annotation_registration_v1.json) freezes its SHA-256:

`ed718f8e93b347cc33733edcc123f2811d9d48ec72af2139d697dd99df6cb3dd`.

The researcher's explicit instruction confirmed all proposed categorical and numerical judgments. This is **condition-masked human narrative review followed by AI-assisted structured coding and explicit researcher confirmation**. It is not independent numerical entry into the original questionnaire, an independent second rating, or proof of independence from all prior experimental knowledge. No second reviewer, inter-annotator agreement, consensus statistic, confirmation time or UTC review time is fabricated.

## Source preservation and availability

The following remain separate and unchanged: the blank masked master; the supplied `PersonaSLM_P1_Wave1_96_AI_assisted_structured_review_PENDING_CONFIRMATION.csv`; the supplied `PersonaSLM_P1_Wave1_annotation_provenance_and_confirmation.csv`; the transcription audit; and `review_sources/PersonaSLM_P1_96_已回填_待研究者确认.pdf`. Their earlier pending-confirmation wording remains historical provenance, superseded by this new registration rather than edited away.

The actual supplied PDF has 98 pages and 991 form fields. All 96 narrative notes and 888 present annotation fields agree with the proposed CSV; all 96 completion boxes are marked. The separate original uncoded `PersonaSLM_P1_96条.pdf` was **not located** in the requested directory or scoped public repository search. Two embedded revisions of the available PDF both already contain coded selections; they do not independently establish the uncoded original. Registration relies on the preserved supplied artifacts and the researcher's explicit confirmation. Recovering the separate original would strengthen the archive; its absence is a provenance limitation, not a reason to invent a source or discard the now-confirmed ratings.

The source reports a calendar review date, retained in the provenance ledger. It does not supply a verifiable UTC review timestamp, so all 96 `reviewed_utc` fields remain blank. The actual registration time is recorded separately in machine-readable metadata. Previous access to treatments/scores is undocumented, represented as UNCERTAIN; the researcher specifically confirms condition-label masking of the narrative stage. The source's original assistance wording is preserved, alongside the more precise confirmed method above.

Some original narrative notes and form instructions are Chinese. They are preserved verbatim as annotation provenance, not silently translated into native English persona data. The experimental prompts/responses remain the original English materials, and all new scientific reports are English.

## Integrity and representation conversion

Every non-annotation field was compared against the original master: IDs and associations, question, trusted evidence, evaluation date, fixed context, historical ledger, raw continuation, first reply, excluded continuation, offsets, raw/first-span hashes, token/stop fields, frozen applicability and structural category. **Zero differences** were found. Original researcher notes also match the separate supplied provenance ledger exactly.

The supplied codings do not use the existing importer's categorical spellings. The [normalization audit](validation/p1/researcher_annotation_normalization_v1.json) records every conversion:

| Supplied representation | Registered representation | Meaning preserved |
|---|---|---|
| `true` | `YES` | Reply-unit confirmation |
| `complete`, `incomplete` | `COMPLETE`, `INCOMPLETE` | Separate semantic completeness |
| `correct` | `Correct` | Applicable factual/temporal judgment |
| Blank factual/temporal entry with frozen applicability=false | `Not Applicable` | No new substantive judgment; eligibility already frozen |
| Long pending assistance description | `AI-assisted` | Importer enum; full original and final method retained in provenance |
| Undocumented prior-access field | `UNCERTAIN` | Administrative disclosure of unavailable evidence, not a fabricated NO |

There are **576 representation/provenance-field changes and zero numerical score changes**. All notes, quotations, continuation notes and numeric ratings are unchanged. No applicable missing judgment was converted to Correct. The new [provenance register](validation/p1/researcher_annotation_provenance_v1.csv) preserves all original ledger values under `source_*` columns and adds final confirmation separately. In particular, the historical `source_researcher_numeric_score_confirmed=false` coexists with the new confirmed state and is not a contradiction about chronology.

The existing validated importer accepted all 96 registered records with no unavailable timestamp filled and no historical score overwritten. Its workflow status COMPLETE is separate from this registration's authority status RESEARCHER_CONFIRMED.

## Verified distributions

| Dimension | Confirmed distribution | Eligibility / coverage |
|---|---|---|
| First-reply unit | YES 96 | 96/96 |
| Semantic completeness | COMPLETE 79; INCOMPLETE 17 | 96/96; no uncertain labels |
| Frozen structural classification | COMPLETE 0; TRUNCATED 17; CROSS_TURN 78; AMBIGUOUS 1 | Original labels unchanged |
| Factual consistency | Correct 72; Incorrect 0; Unverifiable 0; Not Applicable 24 | 72/72 eligible assessed |
| Temporal consistency | Correct 48; Incorrect 0; Unverifiable 0; Not Applicable 48 | 48/48 eligible assessed |
| Response relevance | Score 5:72; score 3:11; score 2:13 | 96/96; scores 1/4:0 |
| Conversational coherence | Score 5:79; score 2:17 | 96/96; scores 1/3/4:0 |

The 72 supported factual answers, seven complete greetings with prohibited personal information, and 17 unfinished reasoning replies match the supplied narrative categories and confirmed counts. The complete greetings receive relevance 3 and coherence 5. Four incomplete replies receive relevance 3, thirteen relevance 2; all seventeen receive coherence 2. These are accepted pilot codings, not general model performance estimates or calibrated independent ratings.

MR069 remains structurally **AMBIGUOUS**, separately semantically **COMPLETE**. The annotation did not rerun `response_status_v1` with new completeness inputs or rewrite any frozen label.

## Freeze, unblinding and validation

The final masked CSV and registration were written before the analysis opened the existing protected treatment mapping. The [analysis specification](validation/p1/researcher_analysis_specification_v1.json) is post-generation exploratory planning, not preregistration. Analysts already had historical results; analyst blindness is not claimed. The private shuffle seed remains undistributed. The separate [analysis dataset](validation/p1/researcher_analysis_dataset_v1.json) joins treatments after the freeze and leaves all source CSVs treatment-masked.

Original output/prompt hashes, model/backend bytes, dataset and wave-manifest hashes, both P1 event chains and all 3,192 original run files were verified. The first analysis attempt stopped before writing results because it treated a saved prompt object as a string; the correction hashes its `text` field. The failed command and registration-time source snapshot remain available, with a new regression test. No output or rating was repaired or regenerated.

The complete final suite passed **479 tests in 23.12 seconds**, exit 0, with no warnings reported. The earlier 45-test targeted result, 478-test intermediate result and failed analysis remain in separate engineering captures. See [delivery verification](validation/p1/researcher_analysis_delivery_v1.json) for preservation, replay, command and file inventories. Original experimental logs and annotation files are not overwritten.

Registration and exploratory analysis are complete. This does not establish independent annotation reliability, remove the factual/temporal ceiling, approve the 24 new controls, adopt a proposed protocol, or make the pilot publication-ready.
