# P1b Final Stimulus Validation — Development Revision 2

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Formal baseline: Research Protocol v1.1. The proposed v1.2 r1 is neither modified nor adopted. Target: PLOS ONE.

## Decision and scope

**Offline construction/reference validation: PASS, 24/24 cases and 192/192 factorial prompts. Researcher semantic approval: OPEN, 0/24. Empirical discrimination: UNTESTED. Inference readiness: PARTIAL.** No new tokenization or generation request was made. This audit does not show that the Wave 1 ceiling has been eliminated.

The new [development v2 dataset](../data/synthetic/p1b_development_proposed_v2.json) retains all 24 prototypes, eight families, three designed levels per family and twelve fictional English-speaking personas with two cases each. Its SHA-256 is `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6`. The [v1 dataset](../data/synthetic/p1b_development_proposed_v1.json) remains byte-identical, SHA-256 `feea8880314bea78e8b74aebbdbeb3439237551df56d7bd8b34a019ebeabd49a`.

## Independent analytic inspection and corrections

Every English question, fact ledger, dated history, recent context, intervention and answer was inspected. A separate reference table and family-specific derivation parse the rendered evidence rather than consuming the generator's query or answer key. Its answers and dated supporting quotations agree with the stored references in all 24 cases. This is **independent code-path checking assisted by automated tooling**, not an independent human annotation study. The original symbolic validator is a secondary check; its deletion and substitution diagnostics cannot prove what reasoning a model will actually use.

The [correction register](validation/p1b/final_v1/correction_register_v1.json) preserves complete before/after values and hashes. Only three cases change:

| Case | Original issue | Revision | What remains fixed |
|---|---|---|---|
| B_L2 | “its meeting place” follows “workshop and role”, leaving an avoidable attachment ambiguity | “Name Emery Lake's workshop and role in it. Also name the workshop's meeting place.” | Evidence, three answer components, speaker, context and S/F/H |
| B_L3 | The same attachment ambiguity in the four-component question | “Name Finley Ash's workshop and role in it. Also name the workshop's meeting place and the entrance to that place.” | Evidence, four answer components, speaker, context and S/F/H |
| E_L3 | Thursday, the original opening-day answer, is also the weekday of the reference date 2027-04-15 | Heron Hub 4 opening day and the corresponding reference change to Tuesday | Question, reference date, all other facts, history, context, speaker and S/F/H |

E_L3 removes a plausible calendar shortcut; no model was tested for using it. These corrections are based on source interpretation before inference, not an observed persona effect. They require researcher confirmation. Historical case IDs remain recognizable but must always be qualified by dataset version/hash.

## Case-by-case reference inventory

All dates below are **fictional proposition dates**, not execution timestamps. Fact IDs use the prefix `p1b_<case>_f`. Exact source quotations and dates at every lookup appear in [case validation](validation/p1b/final_v1/case_validation_v1.json) and the [blank review packet](validation/p1b/final_v1/stimulus_review_v2.csv). All 24 have uniquely supported reference components under the declared single-valued ledger relations; paraphrases are allowed in later human scoring.

| Case | Reference components | Supporting fact suffixes | Time interpretation / principal check |
|---|---|---|---|
| A_L1 | Juniper Room 1 | 01 | Archive box, not an unspecified possession; direct retrieval |
| A_L2 | Juniper Room 2 | 01 | Ignore the supply box; no additional reasoning hop |
| A_L3 | Juniper Room 3 | 01 | Two supply-box distractors; still one-hop retrieval |
| B_L1 | Bookbinding Group 4; materials coordinator | 01,02 | Two requested attributes of Dara |
| B_L2 | Bookbinding Group 5; materials coordinator; Cedar Hall 5 | 01,02,03 | Workshop-to-place link; revised explicit referent |
| B_L3 | Bookbinding Group 6; materials coordinator; Cedar Hall 6; east entrance | 01,02,03,04 | Place-to-entrance link; increased answer burden |
| C_L1 | Birch Counter | 02 | Applies on 2027-04-05, not the overall reference date |
| C_L2 | Cedar Counter | 03 | New interval starts inclusively on 2027-04-10 |
| C_L3 | Cedar Counter; previously Birch Counter | 03,02 | Compare April 10 with April 9 |
| D_L1 | Locker 60 | 01,02 | Assigned crate to locker |
| D_L2 | Fern Room 11 | 01,02,03 | Crate to locker to room |
| D_L3 | West Annex 12 | 01,02,03,04 | Room to building; unique terminal-value shortcut possible |
| E_L1 | Mereford 2 | 02 | Current residence; Alderwick was true in the dated past |
| E_L2 | Heron Hub 3 | 02,03 | Current residence to its hub; old city's hub is a distractor |
| E_L3 | Tuesday | 02,03,05 | Current residence to hub to opening day; amended source/key |
| F_L1 | Amber Shelf | 03 | Explicit Morgan North identifier; no need to infer archivist |
| F_L2 | Folder 76 | 01,03 | Unique archivist is Morgan North; Morgan South is treasurer |
| F_L3 | Amber Shelf | 01,03,05 | Archivist to folder to shelf; repeated template is a shortcut risk |
| G_L1 | Harbor Lodge | 03 | Current state on April 15 |
| G_L2 | Meadow Lodge | 02 | Historical state on March 20 remains a correct past-tense answer |
| G_L3 | Meadow Lodge; currently Harbor Lodge | 02,03 | Two explicitly different proposition dates |
| H_L1 | Elm Desk | 01 | Context selects Parcel 121, but it is the only parcel |
| H_L2 | Ash Desk | 01,03 | Parcel 122's recipient, valid desk on April 15; one parcel only |
| H_L3 | Ash Desk | 01,03 | Context selects Parcel 111 rather than Parcel 151; April 10 boundary |

## Validation coverage and limits

| Requirement | Actual evidence | Status / limit |
|---|---|---|
| Evidence sufficiency, reference answer, unique query resolution | Independent answer table and rendered-ledger derivation agree on all 24 | PASS for declared ledger semantics; human English interpretation OPEN |
| Temporal correctness | Inclusive boundaries, past questions and genuine past residence inspected; no overlapping single-valued intervals | PASS analytic; temporal human review OPEN |
| Entities and speaker identity | Named context, factual subject, supplemental fact and history speaker agree; unique archivist and explicit parcel focus | PASS construction; H_L1/L2 are weak context-disambiguation probes |
| Evidence, question, context and answer invariance | All eight cells have the same evidence prefix, recent context, final question and evaluation references per case | PASS, 192 prompt hashes |
| Factor routing | Only assigned S/F/H additions appear in C0–C7 | PASS; effects remain package effects |
| Accidental leakage / contradiction | No expected answer string in S/F/H; history dates agree with source validity; E past residence agrees with trusted ledger | PASS scoped checks; literal checks cannot exclude every semantic cue |
| Applicability | 24 factual, 11 temporal, 24 relevance/coherence; no fidelity scoring | PASS prospective routing; semantic rubric awaits approval |
| Necessity/sensitivity tests | 46 supporting-fact removals rejected by symbolic oracle; 24 terminal-value substitutions change its key | PASS offline; not proof of model reasoning or new Track A interventions |
| Actual P1b tokens/context | Counts and IDs are null, not estimated | PENDING real-tokenizer preflight |
| Human decisions / measured difficulty | All review fields blank; no responses generated | OPEN / UNTESTED |

## Cognitive demands and confounding

“Level” means **designed complexity**, not established difficulty. A adds distractors without deeper reasoning. B increases requested answer components as well as links. C/G test date selection and changes; C/G L1 are largely retrieval with a date constraint. D supplies a chain but the unique terminal room/building can be recognized without proving every intermediate join. E combines relevance, old facts and additional joins. F mixes explicit IDs with role resolution; the repeated North/archivist association is not counterbalanced. H_L1/L2 do not force competition between referents; only H_L3 does. Its recent context ends in a User turn immediately before the final User question, a format limitation retained for review.

The same woven-bookmark fact occurs across speakers, limiting F generality. Style is nested in persona rather than independently replicated per category; the profile wrapper does not by itself establish speaker fidelity or instruct a first-person identity. Named historical speakers are consistent, but how the model operationalizes the profile remains an unvalidated manipulation assumption. Residence history is topically relevant only in E, so H relevance is confounded with task family. Numbered fictional locations and recurring answer templates allow shortcuts. A revised calendar clue does not eliminate all such risks.

Do not broaden this cycle into outcome-driven stimulus search. Retain all 24, annotate these risks, and ask whether the bank is suitable for bounded development calibration. A researcher may require a further explicit version if a semantic issue is substantive. No failed or difficult case may be deleted after viewing calibration results.

## Identification preserved

| Contrast | What is controlled | Defensible interpretation | Not identified |
|---|---|---|---|
| C1−C0 | Evidence, question, recent context, answer, model and decoding within arm | Total added style-profile package | Pure style independent of length, wording or salience |
| C3−C0 | Same common inputs | Total dated-residence-dialogue package | Temporal conflict alone, relevance alone, or presentation alone |
| Average S/F/H and interactions | Eight paired cells per case; fixed case inputs | Operational factorial contrasts over these specific stimuli | General persona mechanisms or isolated latent style effects |
| C1−N_style / C3−N_history | No new P1b controls exist | Not in this calibration; no adjusted result permitted | Prior P0 acceptance and Wave 1 token equality cannot transfer |

Evidence deletion and substitution are validation probes only. Track A always contains sufficient identical evidence. No Track B, protocol amendment, model switch or new treatment arm is introduced.

## Evidence and next gate

The [readiness report](P1b_inference_readiness_report.md) contains the frozen manifest, precision assessment and operational gates. The [review guide](P1b_researcher_review_guide.md) explains the blank forms. The [decision form](P1b_final_researcher_decision_form.md) separates accepting materials from authorizing execution. Scientific opportunity is assessed in the [algorithmic assessment](P1b_algorithmic_opportunity_assessment.md); no algorithm is launched.
