# P1d task and metric design — proposed v1

Maintainer: Yaxin ZHENG. These are new prospective scoring instructions; historical rubrics and labels are not changed.

## Tasks and ground truth

| Family | Required response | Distinguishing failure | Control against shortcuts |
| --- | --- | --- | --- |
| Single factual retrieval | One dated entity attribute | Wrong entity versus wrong interval | Multiple entities/intervals with independent values |
| Multi-component | Two explicitly requested attributes | Correct fact with incomplete task | Component list fixed before outputs; no success from one correct item |
| Relational integration | Hub and exit reached through an entity's assigned locker | Correct intermediate fact without delivered requested result | Independently permuted links; several plausible terminal nodes |
| Context follow-up | Resolve the preceding referent and provide two attributes | Coherent but wrong referent, missing context binding | No target name in current question; independently alternate the referent between persona and another entity in the final bank |

Current and historical queries are balanced within speaker and family. Use explicit ISO dates and inclusive intervals. Avoid service-day/calendar-weekday ambiguity in the independent bank unless it is an explicitly separate diagnostic. Ground truth is a trace of ledger IDs and required components, not a guessed reference string. An answer's correctness does not establish that multi-step reasoning occurred. The development examples do not yet supply four independent domains; that remains a bank-freeze requirement.

The current demonstration follow-ups still permit a persona-name shortcut: their referent is always the persona itself. They are valid follow-ups, but do not prove context necessity. The final bank must counterbalance referents independently of persona identity and include a context-removal diagnostic at material review, without changing the sufficient ledger or including that diagnostic as a primary inference arm. This is an unresolved stimulus-validity requirement, not a passed manipulation check.

## Separate endpoint definitions

| Endpoint | Proposed rule | Applicability / unresolved handling |
| --- | --- | --- |
| Relevance, 1–5 | Addresses requested subject and action: 5 directly responsive; 4 small detour; 3 materially partial/off-focus; 2 tangential; 1 unrelated | All cases; boundary-unscorable stays blank with reason |
| Factual consistency | Correct if material claims supported; Incorrect if contradicted; Unverifiable if support insufficient | All cases; no claim or uncertain span is not automatically false |
| Temporal consistency | Judge explicit dates, interval attribution and requested-date selection separately from entity-only errors | All cases; an entity error alone need not imply a temporal error |
| Coherence, 1–5 | 5 coherent turn linked to fixed context; 4 minor transition/reference defect; 3 substantial but interpretable; 2 fragmented; 1 unintelligible | All cases; do not copy relevance or factual score |
| Task success | All requested components correctly delivered as an answer, without material false claim | Success / Failure / Uncertain / Missing; correct partial claims are not success |
| Required components | For each component: present, supported, contradicted, unsupported, absent or unscorable | Separate presence and supported coverage fractions; no single proxy for factuality |
| Semantic completeness | YES / PARTIAL / NO / UNCERTAIN | A complete wrong answer can be YES; a promise is not an answer |
| Structural status | Frozen response_status_v1 plus independent boundary diagnostics | Raw continuation and first reply retained separately |
| Persona Fidelity | Narrow adherence to assigned calm/full versus brief/direct style, separately justified 1–5 | All person-conditioned cases; no claim of real-person or global identity fidelity |

The applicability matrix v2 adds the explicitly required semantic-completeness field to the initial P1d tooling matrix. It does not alter P1c applicability. Ordinal scores need separate textual evidence, plausible alternatives and uncertainty. Do not infer scale independence from distinct names. Report ceiling/floor frequencies, cross-tabs, concordance and zero variance. Scores must never be changed to manufacture variation.

For mixed supported and unsupported claims, record claim-level statuses; the output is Incorrect if any material claim is demonstrably false, otherwise Unverifiable if a material claim cannot be verified, otherwise Correct. Requested-answer coverage remains a different record. If the interpretation of a claim is unresolved, retain alternatives rather than coercing a label. N/A, missing administrative annotation, unavailable boundary, unsupported evidence and semantic uncertainty have separate reason fields.

## Measurement challenge checks

Eight authored structured fixtures exercise full correct answers, correct partial answers, wrong entity values, expired values, a promise containing correct mentions, no answer, negation and unsupported predicates. They are software/rubric-development fixtures, not model responses or human annotations. The verifier distinguishes factual Correct from task Failure on both partial and promise fixtures. This proves an implementation can represent the distinction, not that a future model will exhibit it or that free-text extraction is validated.

Stage A scores relevance/coherence in separate passes without condition, structure or automated predictions. Claim verification uses the ledger and query date; component/delivery scoring uses a distinct evidence record. Stage B reviews raw boundary behavior. Independent humans must be able to disagree with both the parser and the reference proposal. See the [annotation plan](P1d_independent_annotation_plan.md).
