# P1c Identifiability Assessment — Proposed v1

Maintainer: Yaxin ZHENG. Formal baseline: Protocol v1.1. All P1c estimands below await approval. No historical estimand or annotation is redefined.

## Identification matrix

Let Y_i(r,t) denote an endpoint for case i under one reviewed history realization. R1 is topically related auxiliary content; T1 is valid at the **requested** date. R0 is unrelated auxiliary content; T0 is expired at that date. These operational definitions are deliberately narrower than direct answer relevance.

| Contrast | Held constant | Intentionally varied | Justified scope | Remaining differences and prohibited claim |
|---|---|---|---|---|
| R, averaged over T | Evidence, answer, requested date, recent context, model, wrapper, turns; intended exact full-prompt length | Auxiliary topic: parcel versus music label | Average replacement effect of these topic-linked ancillary records | Predicate semantics, lexical associations and salience change. Not pure attention, answer relevance or general history relevance |
| T, averaged over R | Same target case and property family, wrapper, history position and intended token length | Which historically true interval/value is repeated | Valid-versus-expired auxiliary-record replacement | Interval position, elapsed time, value and overlap with the requested date co-vary. Not falsity or an isolated recency mechanism |
| R×T | Above controls | Difference between two T contrasts | Interaction of these operational packages | Does not establish mediation, S×H or a universal stale-history effect |
| R1T0−R0T0 | Expired status and target evidence | Topic of the expired auxiliary fact | Topic contrast at fixed expired status | Does not expose an old answer; direct answer competition remains untested |
| R1T1−R0T1 | Requested-date validity | Topic of the valid auxiliary fact | Topic contrast at valid status | Same limited topical interpretation |
| Active−N_history | Wrapper, two turns, named speaker and intended exact final length | Personal dated fact versus procedural archive exchange | Scoped history-content replacement after semantic approval | Topic, factual content, embedded dates and speech act differ. Neutral is not semantically equivalent |
| N_history−H_none | Evidence prefix, question, context, empty-slot wrapper | Added coherent dialogue plus its length and speech acts | Total added procedural-history package | Length, dialogue presence and semantic content co-vary; not a pure length effect |
| Active−H_none | Trusted inputs and model | Full added-history package | Exploratory total addition | Neither token-length control nor isolated R/T effect |

The four R/T cells remain answerable without using the additional history. All required answers are already present in the same trusted ledger. No target-answer component is inserted into the history bank. A temporal fact can be both historically true and irrelevant to the requested date. For a historical-state question, choosing the latest entry is wrong when its interval does not include the requested date.

## Why direct answer relevance is not fully crossed here

A valid target-property history normally discloses the answer. An irrelevant history does not. Equal token count cannot remove that informational asymmetry. Calling this a pure R×T design would contradict v1.1's prohibition on factorial interpretation when interventions disclose different answers. Including every relevant fact in trusted evidence establishes task sufficiency but does not remove differential answer repetition in conditioning.

The prepared auxiliary cross avoids answer disclosure and tests a weaker question. If the researcher's priority is old-answer intrusion itself, a narrower T0-only stale-target versus stale-unrelated comparison may be more informative. It requires distinct reviewed material and approval; it cannot be relabelled as the current four-cell R/T design. A target-fact valid/expired contrast could be studied as an explicit repetition/status package only after its limitations are approved, without claiming pure temporal validity.

## Construction checks versus semantic validity

The [validation records](validation/p1c/proposed_v1/manipulation_validation_v1.json) check reference derivation, inclusive intervals, entity identity, equality of evidence/question/context, fixed applicability and absence of answer-string leakage throughout the finite candidate bank. Historical questions have a different answer from both the oldest and newest interval. Route questions have several possible terminal rooms; two facts are needed by the reference solver.

These checks do not prove that a model cannot exploit lexical regularities, that the auxiliary facts are psychologically irrelevant, or that a neutral conversation is pragmatically inert. Label colors and assignment values follow a small construction scheme; semantic cues and latent correlations require researcher review and later independent lexical counterbalancing. Topic is not independently varied across natural domains. Task family is nested within speaker in this small bank, so between-family patterns cannot be assigned to family alone. The archive wrapper can itself cue record-reading behavior.

The no-history prompt is shorter. Exact lengths among the other five cells, if validated, hold the requested question's token position fixed only when the prefix and suffix boundaries are also verified. Token equality is an engineering condition, not an assertion of equivalence. The complete prompt strings and actual token IDs are retained separately.

## Inferences that remain unavailable

This bank cannot establish persona fidelity, real-speaker generalization, general natural-history neutrality, task difficulty, causal mediation, post-training effects, S/F interactions or a new algorithm. It cannot prove that the P1b H effect was caused by stale history. P1b contains errors without added history and lacks an orthogonal R/T manipulation. A near-zero P1c auxiliary interaction would not falsify direct stale-answer competition; it would constrain only the approved auxiliary-history hypothesis.

Presentation is held fixed. Reformatting the same admitted units is a separate arm; adding retrieval or deleting trusted evidence would change the intervention and must not enter this Track A study. A valid empirical paper must preserve these qualified interpretations rather than infer a mechanism from a significant coefficient.
