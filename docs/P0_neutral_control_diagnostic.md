# P0 Neutral-Control Diagnostic

Version `neutral_control_diagnostic_v1`, 2026-10-12. Researcher: Yaxin ZHENG. **P0 PARTIAL; P1 NOT STARTED.** Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Protocol v1.1, English, Real-Speaker Persona Modeling. No protocol amendment or causal result is claimed.

## Evidence and reconstruction

All 20 original cases were reconstructed under C0, C1, N_style, C3 and N_history: **100/100 prompts** equal the previously recorded inputs. The [reconstruction](validation/P0_control_reconstruction_v1.json) retains every prompt, question, evidence block, style/history intervention, speaker identity, dated facts, input IDs, counts and hashes. Dataset SHA-256: `31b5242c2cc01411f524c2b922086de0ef216105920e723f1270560e0bc1f282`. Template: `transcript_base_v1`.

Actual frozen overrides from `results/p0_validation/20261012T164648/prompts_frozen_v3.json` were used. The default neutral strings in `fixtures.py` are **not** the controls used in those runs. Fresh checks through the loaded GGUF's `/tokenize` reproduced all **100/100 historical ID arrays**; the original **40/40 pairs** retain zero token difference. No generation was repeated. [Tokenizer evidence](validation/P0_control_tokenizer_validation_v1.json) identifies the separate tokenizer-only journal, all candidate attempts and raw HTTP evidence.

The trusted evidence precedes the additional context; recent context and the current question follow it. Matched pairs retain the exact evidence, question, complete prompt token count, section order and evidence-prefix location. Equal total counts alone do not certify every interior token position. Compared with C0, adding context increases the evidence-to-question distance and moves the question. Equal total tokens do not establish equal attention, meaning, information content or syntactic complexity.

## What is actually in the controls

All 20 cases have persona ID `alice`, the same style profile, the same unrelated supplemental fact, and the same recent-context instruction. The profile requests short casual replies and sometimes “haha”, followed by a factual-content disclaimer. There are ten old/current city pairs repeated twice, two question templates and ten questions/evidence blocks using “Alice” versus ten using “the person”. Twenty cases therefore do not represent twenty independent speakers or a diverse style population.

All **20 N_style** additions are exactly:

> Speaker style profile: The page is plain. This is a text record. The heading is printed above the text. The heading is printed above the text.

The “style profile” heading asks the model to interpret the material as speaker style. Repetition and short declarative sentences can themselves prime a response pattern. The control is free of named residence answers but cannot be certified as stylistically inert.

All **20 N_history** additions retain the 2025-05-12 date, User/Alice role labels and three-line structure. Fourteen use `User: The page is plain.` and six use `User: This is a text record.`; all end with `Alice: The heading is printed above the text.` C3 instead asks about past residence and provides the old city. The actual neutral controls already use Alice, unlike a default fixture string using generic speakers.

| Concern | Observed evidence | Consequence |
|---|---|---|
| Answer leakage | Researcher marks no leakage in 40/40; known residence names are absent from neutral additions | Supports this narrow check; absence of explicit names is not a universal semantic proof |
| Additional personal facts | Researcher marks no additional facts in 40/40 | Document statements still add propositional content even when not biographical |
| Temporal interference | Researcher marks no temporal interference in 40/40; C3 and N_history share the date | C3 contains a time-qualified residence assertion; N_history does not. Matching dates cannot balance temporal reasoning load |
| Extra style | All 20 N_style marked yes; all 20 N_history uncertain | Repetition, metadiscourse, declarative rhythm and the heading can contaminate the intervention |
| Identity ambiguity | Ten N_history rows flag an implicit link between “the person” and Alice | This affects the history comparison; the fixtures' persona ID does not explicitly bind referents in the prompt |
| Topic relevance | Residence dialogue versus document descriptions in 20 history pairs | Topic and answer competition change along with the content of the history |
| Dialogue coherence | C3 has a residence question/answer pair; neutral turns are document declarations | Equal roles/lines do not balance adjacency structure or pragmatic coherence |
| Residual factors | One style, one persona, repeated city pairs, fixed placement, a factual disclaimer only in C1 | Limits construct coverage and external validity; no speaker-population effect is identified |

Old facts valid in 2025 and current facts valid in October 2026 are not inherently contradictory. Reporting an old residence as current would be a temporal misuse; supplying the historical assertion is not itself a factual error.

## Identification supported by the original comparisons

| Contrast | Defensible interpretation of the input intervention | What is not isolated |
|---|---|---|
| C1–C0 | Total addition of this particular style-profile bundle under shared current evidence | General persona effect, pure style effect independent of added length/header/disclaimer/position |
| C3–C0 | Total addition of this dated, attributed residence-dialogue bundle | History formatting alone; old personal information, relevance, identity cues, length and dialogue structure all change |
| C1–N_style | Replacement of document-format metadiscourse with this style instruction at equal final input length | A clean semantic placebo; neutral style cues and repetition remain |
| C3–N_history | Replacement of document dialogue with residence dialogue, retaining date/roles and final input length | A pure history-presentation effect or separately identified information-content effect; topic, content and question/answer coherence differ |

These are simple paired contrasts, not average S/F/H factorial main effects. P0 logging and generation success establish no scientific effect of any sign. Trusted current evidence remains shared, so this is not a missing-evidence Track B manipulation.

## Human annotation update

The researcher's latest file is [PersonaSLM_P0_Researcher_Reviewed_v3.csv](validation/PersonaSLM_P0_Researcher_Reviewed_v3.csv). Registration: [researcher_verified_annotation_v1, revision 2](validation/P0_researcher_verified_annotation_v1_revision2.json). **40/40 records, 240/240 core judgments complete**. Reviewer `Yaxin_ZHENG`; review type `researcher_human_review`; final review is AI-assisted and not blind. The file reports an independent initial pass followed by consultation/revision; that process claim is retained, but no separately saved initial pass was supplied. Original review timestamps and inter-annotator agreement are unavailable.

| Accounting basis | PASS | PARTIAL | FAILED |
|---|---:|---:|---:|
| Researcher-supplied `control_suitability` | 0 | 40 | 0 |
| Separate conservative dimension disposition v1 | 0 | 20 | 20 |

The second row is software routing: any explicit adverse dimension -> FAILED; otherwise any uncertainty -> PARTIAL. It does not overwrite or impersonate the first row. The 20 style controls fail the extra-style dimension; the 20 history controls remain uncertain. All 40 overall semantic-neutrality labels are uncertain.

The [version comparison](validation/P0_researcher_annotation_version_comparison_v1.json) finds **0 changes in the eight judgment fields between the two available versions**, with provenance/metadata changes in **40 records**. The earlier received source was already described by the researcher as corrected; it is [archived separately](validation/P0_received_review_source_v1.csv). The untouched original AI CSV and independent human first-pass CSV are absent, so the total number of changes from either of those stages is **unknown**, not zero. A declared intermediate source hash is retained without claiming possession of its bytes. Earlier automated semantic audits and the initial registration remain separate historical artifacts.

## Candidate design v1 — DEVELOPMENT ONLY

The [candidate freeze](validation/P0_control_candidate_freeze_v1.json) precedes tokenizer access. Three new fictional development cases use explicit, consistent speaker names. All 36 style candidates and eight history candidates per case were enumerated in a fixed order; no model responses were requested or inspected. The candidate pool is independent of the current/old city values. No original fixture or prompt changed.

Style candidates remove document-format repetition, use coherent conversation descriptions, and share a neutral `Speaker context` heading with their reference. This changes the development template, not the frozen P0 template. History candidates retain the residence question, dated wrapper and speaker name, but withhold the city. They improve topic/role alignment while potentially cueing abstention and changing information availability within the additional context. Neither design is automatically a valid placebo.

| Development case | Pair | Reference tokens | Best candidate tokens | Difference (neutral-reference) | Attempts | Matching |
|---|---|---:|---:|---:|---:|---|
| control_dev_001 | C1–N_style | 100 | 102 | +2 | 36 | FAILED |
| control_dev_002 | C1–N_style | 100 | 97 | -3 | 36 | FAILED |
| control_dev_003 | C1–N_style | 98 | 95 | -3 | 36 | FAILED |
| control_dev_001 | C3–N_history | 118 | 118 | 0 | 8 | PASS |
| control_dev_002 | C3–N_history | 120 | 120 | 0 | 8 | PASS |
| control_dev_003 | C3–N_history | 119 | 119 | 0 | 8 | PASS |

There are **132 candidate attempts + six reference counts + 100 historical checks = 238 tokenizations**, tolerance **0**, **zero completion requests**. Style failures reflect gaps in the fixed phrase-length inventory under this tokenizer; historical ID agreement provides no evidence of a tokenizer inconsistency. No pool extension was made after observing these failures. New candidate semantic review is unperformed. All six candidates remain developmental regardless of token matching.

Further proposed controls should separately balance topic, attribution, date, proposition count, adjacency structure and token positions. A fact-equated prose/transcript comparison can test presentation more directly, while an answer-independent topic-matched contrast can assess information relevance. These are proposed supplementary diagnostic estimands requiring researcher approval, not replacements for the frozen comparisons. There may be no semantically inert natural-language placebo for every instruction; an explicitly characterized replacement contrast may be the defensible endpoint, subject to approval.

## Acceptance implication

Human annotation completion now **PASS**. Semantic control validity remains **PARTIAL**, with repair/adjudication **OPEN**. The outstanding mandatory action is to resolve the identified style/topic/identity/coherence confounds and approve a defensible control interpretation or a newly matched/reviewed version. A second reviewer, natural EOS on every response, or an unsupported backend token endpoint is not imposed as a new blanket P0 requirement. Proposal work can continue; P1 execution remains unauthorized.
