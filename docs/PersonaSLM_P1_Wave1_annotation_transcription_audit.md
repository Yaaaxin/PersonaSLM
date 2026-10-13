# PersonaSLM P1 Wave 1 — Annotation Transcription and Provenance Audit

## Scope and provenance

- Source: submitted 98-page mobile-review PDF and the original 96-row, 41-column masked `output_human_review_v1.csv`.
- 96/96 PDF records had nonempty, researcher-submitted free-text notes and were marked complete. **Every A–F radio button in the submitted PDF was unselected**.
- Source narrative annotations are the researcher's masked-to-condition-label review **as represented in the submitted form**. The new categorical/numerical selections are AI-assisted **interpretations of those notes**, not choices made in the source PDF, not a second independent human reviewer, and not yet researcher-confirmed numeric labels.
- Whether the reviewer had prior access to treatment assignment or model scores was not documented in these artifacts. Therefore no stronger claim of complete independent blinding is supported. The form's `review_assistance` value of `人工盲审` is preserved verbatim in the source PDF; the derivative CSV discloses assisted transcription.
- The PDF provides review date `13/10/2026`, **not a verifiable UTC timestamp**; `reviewed_utc` remains blank.
- Version 1.1 historical scores, raw model responses, treatment assignment, predeclared applicability, token counts, stop reasons and SHA-256 hashes were not changed. No new generation was run.

## Proposed codings (NOT confirmed researcher scale choices)

| Case outcome description from PDF notes | Count | Boundary | Completeness | Factual consistency | Temporal consistency | Relevance | Coherence |
|---|---:|---|---|---|---|---:|---:|
| Direct evidence-supported answer | 72 | true | complete | correct (72) | correct (48); N/A (24) | 5 | 5 |
| Complete greeting introducing prohibited personal facts | 7 | true | complete | N/A | N/A | 3 | 5 |
| Unfinished `<think>` with no delivered answer | 17 | true | incomplete | N/A | N/A | 2 or 3 (as noted) | 2 |

All 96 first-reply boundary confirmations follow explicit narrative references in the source PDF, not the automated structural status alone. In particular the original `AMBIGUOUS` status of MR069 remains unchanged in the source record.

Fact/temporal correctness in the 72 applicable rows is explicitly supported by individual narrative statements comparing the answer to the valid source ledger. **No label is inferred for a predeclared inapplicable metric.** A response can be `CROSS_TURN` yet have a semantically complete first reply. Conversely, unfinished internal reasoning is not counted as an incorrect factual claim.

## Researcher confirmation gate

- **Do not import the derived CSV as finalized human annotations yet.** Obtain explicit researcher confirmation or correction of the inferred choices. This is especially important for all 24 nontrivial greeting/unfinished-reasoning records and for 1–5 scale distinctions, because the source notes do not uniquely determine numeric values.
- Preserve the original PDF, the original masked CSV, the derived PDF, the proposed 41-column CSV and the row-level provenance audit as separate versioned artifacts.
- If the researcher confirms a row, update the provenance ledger and produce a separately versioned researcher-approved file, retaining the first inferred scores for comparison.
- The original masked labels must stay hidden until the full review/confirmation procedure is frozen and all required labels are confirmed.
- A second genuinely independent annotator is advisable for a prespecified subset or all pivotal contrasts before confirmatory analysis; do not report inter-annotator agreement for a single reviewer and AI transcription.

## Scientific caution / publication relevance

- This pilot has only 12 speaker-level cases × 8 conditions. Do not extrapolate 72/72 proposed factual `correct` labels to a general model accuracy result; they are proposed codings of easy, evidence-supplied development cases and require sign-off.
- Explicit instruction constraint violations on greeting tasks are recorded in the PDF notes, but factual consistency and temporal consistency remain N/A there according to frozen applicability. Do not add those violations to the factual-error numerator retrospectively; they may be explored in a separately preregistered criterion.
- 78 `CROSS_TURN`, 17 `TRUNCATED`, 1 `AMBIGUOUS`, 0 `COMPLETE` remain untouched; reply-boundary correctness and semantic completeness are separate questions.
- The current pilot alone cannot validate or refute S×H effects. After researcher sign-off and independent review, unblind by ID under reproducible code, report case-paired differences and uncertainty, and decide whether to test an independently versioned post-trained arm.
