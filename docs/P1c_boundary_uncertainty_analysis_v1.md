# P1c boundary uncertainty analysis v1

Maintainer: Yaxin ZHENG. Status: AI-assisted review; researcher confirmation pending.

## Primary versus sensitivity units

All eight changed factual judgments correspond exactly to the eight frozen AMBIGUOUS outputs: PC010, PC023, PC033, PC039, PC042, PC044, PC054 and PC063. Their primary F/T judgments remain Unverifiable, task success unknown and semantic completeness UNCERTAIN. This is an unavailable evaluation unit, not evidence that eight answers contain unknowable facts. The source `response_status_v1` and original candidate text remain unchanged.

Each alternative is a literal initial prefix ending before a generated section heading, never a later answer selected for correctness. Offsets, raw/prefix hashes, native stop, full continuation, excluded continuation, question, ledger and source quotations appear in [boundary_sensitivity_table_v1.csv](validation/p1c/calibration_v1/semantic_integrity_v1/boundary_sensitivity_table_v1.csv). All eight prefixes are plausible, self-contained answers; none is certified as the uniquely attributable first reply. A generated document heading can be answer content or a transition. Human adjudication is still necessary. PC010 and PC023 end at EOS (85 and 93 generated tokens); the other six reach 96 tokens. Termination applies to the whole continuation, not just the proposed prefix.

| ID | Exact proposed prefix | Factual / temporal / task sensitivity | Case-specific interpretation |
| --- | --- | --- | --- |
| PC010 |  The schedule for 2042-12-15 shows Elian Moss assigned to the Orchid collection desk and service day Thursday. | Correct / Correct / 1 | Correct Orchid/Thursday prefix; a generated new music question follows. EOS does not settle attribution. |
| PC023 |  The schedule for 2042-12-15 shows Elian Moss assigned to the Orchid collection desk on a Thursday. | Correct / Correct / 1 | Correct Orchid/Thursday service assignment under the service-day reading; repeated question/answer follows. Calendar-language alternative retained. |
| PC033 |  The schedule for 2042-06-15 shows that Elian Moss is assigned to the collection desk "Silver" and the service day "Tuesday." | Incorrect / Unverifiable / 0 | Silver/Tuesday instead of Maple/Tuesday: one supported component, wrong desk. Later turn truncates; primary unit remains unresolved. |
| PC039 |  The schedule for 2042-06-15 shows that Elian Moss is assigned to the collection desk "Silver" and the service day is "Friday." | Incorrect / Unverifiable / 0 | Silver/Friday instead of Maple/Tuesday: contradicted desk and unsupported weekday. Later turn truncates. |
| PC042 |  The schedule for 2042-06-15 shows Elian Moss assigned to the collection desk "Silver" and the service day "Friday." | Incorrect / Unverifiable / 0 | Same target error as PC039, independently preserved raw text. Friday is not in the ledger; later continuation is incomplete. |
| PC044 |  The schedule for 2042-06-15 shows that Elian Moss is assigned to the collection desk named Maple and the service day named Tuesday. | Correct / Correct / 1 | Correct Maple/Tuesday before a generated recent-conversation replay ending at Assistant. Formatting attribution is unresolved. |
| PC054 |  Nora Finch's destination room for parcel collection on 2042-06-15 is Silver. | Incorrect / Incorrect / 0 | Silver follows an earlier route; June requires Cobalt through the updated route. Generated context replay follows. |
| PC063 |  Nora Finch's assigned destination room for parcel collection on 2042-12-15 is Laurel. | Correct / Correct / 1 | Correct December Laurel prefix, then repeated dialogue and a trailing incomplete Assistant turn. |


All original prompts, parser traces and eight native responses were inspected. Prompt/input-token reconstruction is in the **analyst-only** protected_boundary_prompt_audit_v1.json; it is deliberately excluded from Stage A because intervention language can reveal assignments. The repeated question/context headings make a boundary interpretation plausible but not certain. A procedural text's discussion of question/reply ordering may prime format; that is a hypothesis, not a controlled finding.

## Uncertainty types

BOUNDARY_UNRESOLVED identifies the unknown unit; STRUCTURALLY_UNSCORABLE describes its scoring consequence. ANNOTATION_UNCERTAIN covers calendar/attribute/entity-versus-time readings. EVIDENCE_UNVERIFIABLE identifies a specific unsupported proposition. NOT_APPLICABLE is predeclared metric exclusion. MISSING is absent required annotation/confirmation. These are additive, potentially overlapping flags, not replacement categorical scores.

Primary factual Unverifiable = eight unresolved boundaries + PC006 calendar reading. Primary temporal Unverifiable = those eight + PC006 + PC011/027/030/035/040 entity-versus-time interpretations. PC004's accepted alias reading is also explicitly uncertain without changing its Correct proposal. In secondary PC039/042, the unsupported Friday component coexists with a demonstrably wrong desk, so an evidence-gap flag does not erase the whole-answer Incorrect rating. All human confirmation states remain MISSING; no primary semantic axis is N/A; fidelity is N/A for all 72.

## Distribution and identification sensitivity

Primary F = 43/20/9 (C/I/U); alternative F = 47/24/1. Primary T = 43/15/14; alternative T = 47/16/9. Task = 43/20/9 versus 47/24/1 (success/failure/unknown). Component coverage = 44 full, 20 zero, 8 unscorable versus 48 full, 1 half, 23 zero. Completeness = 64 YES/8 UNCERTAIN versus 72 YES under the assumed prefixes. These are proposal-conditional descriptive counts, not official effects or general accuracy.

Allowing unknown units/judgments to range over success/failure gives primary F [43,52]/72, T [43,57]/72 and task [43,52]/72; secondary F [47,48]/72, T [47,56]/72 and task [47,48]/72. These are identification bounds conditional on accepted scored labels, **not sampling confidence intervals**, and do not recode Unverifiable as Incorrect. Evaluated-only F is 43/63 versus 47/71; T is 43/58 versus 47/63. Selection may depend on condition and response form. All 72 requests remain in incidence denominators; official paired signed-weight bounds await confirmation.
