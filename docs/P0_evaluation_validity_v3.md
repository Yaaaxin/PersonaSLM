# P0 Evaluation Validity, Version 3

Scope: English synthetic residence claims, not general factuality, persona fidelity, response relevance or coherence. Historical v1 and v2 implementations/results remain unchanged. New module: `evaluation_v3.py`, version `english_residence_claim_audit_v3`. Evidence: [versioned checks and C3 audit](validation/P0_evaluation_validity_v3.json).

## Four explicit outcomes

| Outcome | Bounded interpretation |
|---|---|
| Correct | Recognized residence assertions are supported by the applicable synthetic facts; this does not certify that the question is fully answered |
| Incorrect | At least one recognized assertion contradicts a unique applicable city fact |
| Unverifiable | Missing/conflicting evidence, unsupported grammar, unidentified subject, incomplete or non-city claim, or insufficient temporal coverage |
| Not Applicable | The factual endpoint was marked inapplicable before generation |

Unverifiable is never silently converted to Incorrect. Not Applicable is outside the endpoint denominator. A supported city assertion plus an unverified age claim remains Unverifiable at whole-output scope. A verified contradiction remains Incorrect even if another assertion is uncertain; retain both claim-level reasons. No general accuracy score is computed from these diagnostics.

## Independent development checks

The new Morgan/Bristol/Chester fixture is independent of the historical Alice city cases and of the termination-development speakers. Its expected values are engineered software-test expectations, **not human annotation or model outcomes**. The fixture records its English origin, facts, validity intervals, question and applicability in `tests/fixtures/p0_evaluation_dev_v3.json`.

Twenty-two declared text examples cover affirmation, negation, contradiction, outdated facts, multiple conflicting assertions and unverifiable statements. Two additional checks cover Not Applicable and conflicting trusted source records. All 24 contract checks pass under v3. Regression tests also preserve and contrast v2 behavior.

Six of the 22 items expose v2 limitations relative to this explicitly declared contract:

| Text | v2 | v3 |
|---|---|---|
| `Morgan does not live in Bristol.` | Unverifiable | Incorrect |
| `Morgan does not live in Chester.` | Unverifiable | Correct |
| `Morgan lives in Tokyo now.` | Unverifiable | Incorrect under the canonical, exclusive current-city schema |
| `Taylor currently lives in Bristol.` | Correct | Unverifiable: wrong subject |
| `Morgan lives near Bristol.` | Correct | Unverifiable: proximity is not residence in the city |
| `Morgan lived in Chester in` | Correct | Unverifiable: unfinished clause |

These examples are regression findings, not a comparative evaluator-accuracy benchmark. The v3 grammar restricts subject, residence predicate, negation and temporal suffixes; it does not certify arbitrary text merely because it contains a known city. Bare answers are restricted to known cities. A year-level assertion requires covering evidence, and overlapping contradictory source facts prevent certification. Unknown named-city alternatives count as contradictions only for explicit residence predicates under the synthetic unique-city assumption, not an open-domain geographical ontology.

## The original 14 C3 incorrect records

The supplemental v3 whole-output counts remain **2 Incorrect, 11 Unverifiable, 1 Correct**. The first replies have supported current-city claims; the complete outputs may contain additional historical or unsupported claims.

- 008 and 018 assert Nancy for “back then,” inconsistent with Metz at the unique dated history anchor. This remains a bounded contextual interpretation requiring review if the referent is ambiguous.
- 002, 003, 005, 006, 009, 011, 012, 014, 015, 017 and 020 contain unsupported earlier-year claims or incomplete material. Absence of evidence for 2023 is not evidence those claims are false.
- 019's recognized current/past city claims are supported. This does not certify general language quality or semantic completeness.

All case IDs, raw/parsed text, v1 reasons, v2 statuses, v3 claims, fact references and source hashes remain traceable in the JSON. The historical model runs were not rescored in place. `run-local` retains its explicitly logged legacy evaluator; the v3 audit is separately invoked offline, so no default evaluator was silently switched during an experiment.

## Validity boundary and P1 implications

V3 is reliable only for the tested canonical residence-claim contract. Complex reference resolution, quoted speech, aliases, mixed temporal cues, unsupported syntax, non-city facts and general conversational judgments are not independently validated. It is not a universal semantic judge. Rule development cases do not substitute for independent human validation on future open-ended scientific outputs.

A P1 pilot does not require a perfect open-domain automatic evaluator or retrospective human relabeling of every historical diagnostic. It does require an explicit response unit and endpoint policy: preserve all categories, route unsupported claims to Unverifiable/manual review, and distinguish initial reply from model-authored continuation. That scoring unit cannot yet be finalized while the response boundary remains unresolved. Legacy substring scoring must not be presented as the sole validated scientific evaluator.

No human judgment or inter-annotator agreement has been claimed. Existing annotation procedures and the four separate reliability endpoints remain unchanged; this is a software audit and conservative scope definition, not a new research endpoint.
