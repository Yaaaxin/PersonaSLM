# P1b Control Review Preparation — v1

Maintainer: Yaxin ZHENG. Protocol v1.1 unchanged. **Existing P1 semantic review: OPEN,0/24 completed. New P1b controls: not yet constructed, tokenized or approved.** Engineering/token matching and human semantic approval are separate states.

## Concise review package

Use the new [24-item reading index](validation/p1b/control_review_index_v1.csv) to inspect candidate ID/family, exact active and control text, evidence, question, fixed context, dates, answer, full-prompt counts, hashes and narrow permitted scope. This is a read-only condensation, not a replacement annotation schema. Complete a **copy** of the unchanged [41-column review master](validation/p1/control_review_v1.csv); retain all original columns, IDs, text, hashes and packet version. The [original guide](P1_annotation_guide.md) and [master JSON](validation/p1/control_review_master_v1.json) remain authoritative. No preliminary analytical comment is inserted into human fields.

All eight questions are positive criteria: PASS means the requirement is met, including absence of leakage. Use PASS/FAIL/UNCERTAIN; NOT_APPLICABLE is allowed only for the history unintended-style item with justification. Inspect leakage, extra facts, contradictions, unintended style, evidence/question/context preservation, speaker identity, wrapper/length, and suitability **within the explicitly declared scope**. Quote source passages for FAIL/UNCERTAIN. Record the actual reviewer and assistance; leave an unknown review time blank. No blind-review claim follows merely from filling a CSV.

Final decisions: ACCEPT_NARROW, REVISION_REQUIRED, REJECT_AS_NEUTRAL, DIAGNOSTIC_ONLY or UNCERTAIN. A narrow decision is not complete semantic neutrality. Use the existing validated import command after the researcher supplies a completed copy:

```powershell
.\.venv\Scripts\python.exe tools/p1_review.py import --csv docs/validation/p1/control_review_completed_v1.csv --output docs/validation/p1/control_review_registration_v1
```

This command is provided for future use and **was not executed with fabricated labels**. It checks schema, source identity, duplicate/missing IDs, review version, all required judgments, reviewer provenance and acceptance consistency. It preserves the submitted CSV and refuses to overwrite an existing registration. If that destination already exists at import time, use a fresh version.

## Actual tokenizer evidence, without new inference

The [offline source audit](validation/p1b/historical_inspection_v1.json) reverified **24/24 full-prompt exact matches**, twelve N_style and twelve N_history, all difference0. It reconciled the original **720 native /tokenize records**:96 factorial reference prompts plus624 saved candidate attempts. Selected token arrays have the recorded lengths, reference and candidate prompt hashes reconstruct, and CSV prompt text equals the matching artifact. The original tokenizer chain and completion chain validate;3,192 run files remain identical to the starting inventory.

This uses **actual recorded GGUF tokenizer results**, not character counts or a simulated tokenizer. No server, new tokenizer request or completion was launched. The pinned Qwen3.5-2B-Base Q4_K_M file and llama.cpp b11573 executable hashes were rechecked against the original design. Backend evaluated input arrays remain unavailable where originally absent; no new array evidence is invented.

The old24 matches apply only to their old complete prompts. They **do not** establish matching for the new P1b bank, a changed question/evidence block or a future Instruct template. P1b full-prompt token counts remain null/NOT_EXECUTED. Before any intended new matched comparison, use the real pinned tokenizer for that arm, require difference0, retain unsuccessful candidates, and obtain a new semantic review. No approximate matching claim is made.

## Interpretation and residual confounds

| Family | Permissible narrow interpretation | Still uncontrolled |
|---|---|---|
| N_style | Specific style information versus an explicit absence-of-style statement, at matched wrapper/length | Absence wording changes metalinguistic context and may affect behavior; not equivalent to C0 |
| N_history | Residence history versus unrelated coherent dated conversation, at matched length and dialogue format | Topic relevance, personal factual content, temporal factual information and pragmatic function |

Matching token length cannot equate semantics, model attention, information content or lexical cues. C3−N_history is not a pure historical-format or temporal-conflict effect. Existing candidate wording is preserved independently of the observed outputs. Neither the old40 P0 reviews nor later P0 narrow approvals are imported as P1 approval. Pending controls block control-adjusted comparisons, but do not prevent a separately approved eight-cell factorial calibration with honest total-package interpretations.

## New stimulus review is a different task

The [24-case P1b stimulus review form](validation/p1b/stimulus_review_v1.csv) is separate from these24 old controls. It asks whether each new English question matches its symbolic oracle, has unique sufficient support, expresses the proposed complexity, avoids leakage/contradiction, and has clear speaker/context references. Human fields are blank. New stimulus approval does not approve neutral controls, and control approval does not prove empirical task discrimination.
