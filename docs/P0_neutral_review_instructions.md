> **Current assessment — 2026-10-12T20:13:26.793933+00:00:** Human annotation **PASS, 40/40 completed**; final review is AI-assisted and not blind. Semantic-control validity remains **PARTIAL / resolution OPEN**; researcher overall ratings are PASS 0 / PARTIAL 40 / FAILED 0. Overall **P0 PARTIAL; P1 NOT STARTED**. See the [current control acceptance report](P0_control_acceptance_report.md) and [researcher annotation report](P0_researcher_annotation_report.md). Tests: **263 passed**. All earlier status/readiness statements below are preserved dated history, including earlier 0/40 review counts.

# P0 Independent Neutral-Control Review

Status: **PARTIAL — no independent human reviews have been completed.**

Use the English [CSV form](validation/P0_neutral_review_form_v2.csv) or the equivalent [JSON form](validation/P0_neutral_review_form_v2.json). There are 40 items drawn from the already frozen, exactly token-matched controls. This review does not authorize new generation or changes to historical prompts.

## Procedure

The researcher should distribute a separate copy to each independent reviewer. Reviewers work without consulting each other's ratings. Record reviewer ID, actual review time in UTC, and conflicts of interest. Do not put personal contact details in public files. Preserve the blank master, each original completed copy, and any later adjudication separately.

Read the exact `neutral_text`, both trusted-evidence blocks, both questions, and the reference date wrapper. Inspect the entire neutral text, including headings, role names, repeated sentences and dates. The correct city appears in the trusted evidence by design: decide whether the *conditioning text itself* additionally reveals it. Do not treat equal token counts as proof of neutrality.

Explicit condition IDs, model outputs and scores are withheld. Text formatting may reveal the type of control, so blinding is partial; do not claim complete condition blindness. The researcher retains the mapping in `results/p0_methodology/20261012T173818/neutral_review_v2_mapping.json`. Reviewers should not consult that mapping or the scoring reports while rating.

## Fields to complete

Use `yes`, `no`, or `uncertain` for each dimension. Empty cells mean **not reviewed**, not a negative judgment.

| Field | Question | Desirable answer |
|---|---|---|
| `answer_leakage` | Does the neutral text reveal or imply the expected city or another factual answer? | no |
| `new_personal_facts` | Does it introduce personal facts, preferences, relationships, identity attributes or biographical claims? | no |
| `contradictory_or_stale_information` | Does it conflict with the evidence or add outdated/ambiguous temporal information? | no |
| `additional_persona_style` | Does it prescribe or demonstrate a distinctive extra persona style, including through repetition or headings? | no |
| `question_and_evidence_unchanged` | Are the current question and trusted evidence exactly preserved and free from reinterpretation caused by the addition? | yes |
| `other_semantic_interference` | Is there another clear semantic distraction, instruction, role or temporal cue that could affect interpretation? | no |

Put exact affected text in `evidence_quotes`, and explain each `yes`/`uncertain` or preservation failure in `notes`. Each review ID maps to one historical case and control; never replace the actual conditioning text with a paraphrase. No external factual research is needed: use the supplied synthetic evidence and identify anything it does not establish.

Set `overall_PASS_PARTIAL_FAILED` to `PASS` only when all checks support validity, `FAILED` for a substantive violation, or `PARTIAL` for unresolved ambiguity. Matching a reference date does not by itself rule out temporal interference. An empty review remains pending, regardless of automated checks.

The researcher should report the number reviewed, per-dimension counts, reviewer disagreement and any agreement statistic actually computed. Resolve disagreements in a separately dated adjudication record with reasons, retaining the original ratings. Do not fabricate a second reviewer, consensus or agreement. P0 semantic acceptance remains PARTIAL until the required independent review and handling of identified issues are complete.

English is the primary language under the [Protocol v1.1 language addendum](research_protocol_v1.1_language_scope_addendum.md). These are script-authored English synthetic materials, not translated native-speaker conversations or real-speaker data. No primary dataset, prompt, question, evidence or output has been retroactively translated or edited.
