# Development Control Review v2 — English Annotation Guide

This is a **new, unreviewed development package**, separate from the 40 completed researcher annotations. Review version: `control_development_review_v2`. Candidate version: `neutral_control_candidate_v2_dev`. Twenty-four items cover six synthetic cases and four comparison families. No model outputs, preliminary ratings or reviewer identities are supplied. Conditions are visible: this is not a blind review. The `neutral_text` column is a common schema name; the `history_stale_generalized` family is explicitly **not a neutral placebo**.

Use [the CSV form](validation/P0_control_development_review_v2.csv) and its [immutable JSON master](validation/P0_control_development_review_v2.json). Save a separate completed CSV; do not edit the distributed form. The [development report](P0_control_development_report_v2.md) defines the proposed comparisons and limitations. Reading that analysis should be disclosed in `review_assistance`; it does not invalidate a genuine human judgment but prevents a claim of independent blinding.

## Reading an item

Read the trusted evidence, current question, reference conditioning text and candidate text together. Token counts concern **entire final prompts**, not isolated conditioning text. Equal token length is a mechanical property, not evidence of semantic neutrality. A historical residence can be true at its historical date while differing from the current residence; distinguish dated truth from contradiction.

The families have different purposes:

- `style_generic`: generic discourse description beneath the unchanged style-profile heading. Check whether this still prescribes or implicitly demonstrates a distinctive style.
- `history_format`: a dated two-turn exchange about conversation. Speaker/date/turn structure are matched, residence topic is not. Do not approve a pure topic- or fact-controlled interpretation.
- `history_topic`: the original residence question followed by a clarification question. Check whether this primes questioning, uncertainty or answer avoidance.
- `history_stale_generalized`: an old residence described only as a city. This is an information-specificity diagnostic. Check retained temporal meaning, added facts and evasiveness; do not certify it as semantically neutral.

## Labels and evidence

For each applicable dimension use **PASS**, **FAIL**, or **UNCERTAIN**. PASS means the criterion below is satisfied; it does not mean the model answered correctly. UNCERTAIN is a completed judgment and must remain distinct from missing data and PASS.

| Field | Criterion for PASS |
|---|---|
| `answer_leakage` | Candidate supplies no required current answer beyond the unchanged trusted evidence |
| `additional_factual_information` | Candidate introduces no additional personal assertion; generic facts about conversation are not personal facts |
| `contradictory_information` | No conflict with the supplied evidence or internally conflicting assertions |
| `temporal_interference` | No misleading or unintended time cue affecting the current question |
| `unintended_linguistic_style` | No unintended register, rhythm, brevity, question-asking or other style intervention |
| `semantic_neutrality` | No discernible semantic intervention beyond the intended neutral comparison |
| `unnecessary_repetition` | No redundant repetition used as padding within the candidate |
| `speaker_identity` | Historical reply clearly belongs to the same named target as evidence/question |
| `dialogue_structure` | Same ordered roles and two-turn structure as the reference; note differences in speech act |
| `timestamp_format` | Same date value and date/header format as reference |
| `topic_alignment` | Candidate concerns the same residence topic as the reference |
| `temporal_relationships` | Reference and candidate preserve the relevant past-versus-current relation |
| `conversational_coherence` | The exchange is plausible natural English, including the relation between turns |
| `comparison_suitability` | Suitable for its stated narrow comparison with the residual differences acknowledged |

`NOT_APPLICABLE` is allowed only for the five history-specific fields (`speaker_identity`, `dialogue_structure`, `timestamp_format`, `topic_alignment`, `temporal_relationships`) in `style_generic`, and for `semantic_neutrality` in `history_stale_generalized`. Other dimensions still require a label. A format-only history can FAIL topic alignment without automatically invalidating its narrower intended comparison. Record a diagnostic's personal assertion accurately even when deliberate. Software does not convert these dimensions into acceptance or overrule the reviewer.

For each FAIL or UNCERTAIN, supply the corresponding `_evidence_quote` using an exact excerpt from the four supplied material fields. For an absence, quote the closest relevant reference/candidate text and explain the missing feature in `reviewer_notes`. Do not manufacture a quotation. Add reasoning, possible confounds and any recommendation in the notes.

Supply your actual `reviewer_id`. Set `review_assistance` to `unassisted`, `AI-assisted`, or `other-assisted`, and explain assistance in notes. `reviewed_utc` may be blank if unavailable; if known, use the actual UTC time with `+00:00` or `Z`. Import time is recorded separately. Never invent a past review time. Preserve all material fields, case-condition identifiers, versions, hashes and all 24 rows. Entirely blank review rows remain OPEN; partly completed rows are rejected until complete.

## Import and traceability

The following is a usage example, **not a command claiming an actual human submission was imported**:

```powershell
.\.venv\Scripts\python.exe -m personaslm.control_review_v2 --template docs/validation/P0_control_development_review_v2.json --input docs/validation/RESEARCHER_COMPLETED_COPY.csv --output docs/validation/RESEARCHER_REVIEW_NEW_VERSION.json
```

The importer validates version/digest, unchanged materials, exact inventory, duplicate records and headers, legal labels, reviewer identity, assistance disclosure, optional time and evidence quotations. It refuses an all-blank submission or an existing output. Partial imports explicitly retain completed/remaining counts. It cannot authenticate human identity from a string or establish semantic validity automatically. Keep the source CSV, imported JSON and subsequent adjudication separately. No second reviewer or agreement statistic is assumed.

Current completion: **0/24**. The earlier **40/40** reviews remain valid only for their historical materials. Human review of new controls and resolution of its findings remain required before adopting them for research comparisons. P0 remains PARTIAL; P1 is not started.
