# P1d identification and controls — proposed v1

Maintainer: Yaxin ZHENG. All new designs are prospective. P1c condition IDs, prompts and interpretations remain unchanged.

## Primary source-selection manipulation

| Cell | Entity in repeated history | Interval of historical fact | Scientific role |
| --- | --- | --- | --- |
| E0V0 | Other entity | Expired relative to requested date | Other-entity, expired candidate |
| E0V1 | Other entity | Contains requested date | Entity mismatch at relevant time |
| E1V0 | Target entity | Expired relative to requested date | Historically true competing value |
| E1V1 | Target entity | Contains requested date | Explicit answer-supporting positive control |
| D_procedural | Same historical speaker | Procedural statement | DIAGNOSTIC_ONLY; semantic neutrality unproved |
| H_none | No added quotation | None | Shorter-context baseline |

Every cell receives the same full trusted ledger, current question, query date, evaluation date, fixed context, persona profile and answer requirements. History repeats one ledger proposition as a quotation by the same speaker, in the same location and format. Four active records are historically true. The requested date, not the latest date in the ledger, determines correctness. E1V1 intentionally adds redundant answer support; it is not covert leakage and must not be interpreted as pure topical relevance. On relational tasks it supplies a required intermediate source rather than the final hub/exit answer.

E changes entity and selected attribute value; V changes interval and selected value. The common estimand is the effect of selecting these classes of true auxiliary claims under a complete ledger. No latent cognitive mechanism is isolated. Independent entity/value permutations, lexical realizations, target positions and dates must be counterbalanced across cases before generation. Within-case lexical and date differences remain part of the package; randomization balances them on average only under the allocation assumptions.

## Separate non-answer relevance design

`separate_manipulation_designs_v1.json` contains an explicit auxiliary example. It repeats a blue-cover fact about either the collection archive or gardening archive; the question asks for a volunteer's locker. Both propositions are valid throughout the year. A second factor changes the dated attestation from July–September to October–December while preserving predicate/value. For a November query, this tests **attestation coverage and date cues**, not whether a now-false proposition is stale. It demonstrates why exact semantic orthogonality cannot be claimed simply by keeping a value constant.

This auxiliary R×A design could have 12 new speakers, 24 cases and six conditions (144 requests), but is not recommended in the first core allocation. If the scientific target is expired-value competition, use the explicit E/V design instead. If pure topical relevance is essential, use a fixed-date R simple comparison and accept residual lexical/topic differences. Do not silently mix these three questions.

## Token, format and control checks

The actual pinned GGUF tokenizer processed all 96 development v3 prompts: 1,633–1,807 input tokens, all fitting 4,096 with 96 output tokens. Four active cells match exactly in 14/16 cases. `p1d_dev_05_0` and `_05_1` differ by one token between entity levels. All 16 procedural controls are 21–25 tokens shorter than E1V1; none is length matched. These are measured failures, not successful controls. Evidence appears before history so its starting position stays fixed within a case; the question position shifts with unmatched history length.

Before independent stimulus freeze, obtain exact active-cell token matching using independently reviewed synonymous names/wording, and construct a fixed finite bank of length-matched procedural candidates. Preserve all rejected candidates/counts. Semantic neutrality requires separate review of topic, personal information, authority, chronology, style and answer interference. If strict neutrality cannot be defended, retain DIAGNOSTIC_ONLY and restrict the contrast; do not claim a controlled semantic history effect. H_none intentionally remains shorter.

A no-answer-clue domain control, a benign matching-history positive control, quoted-role/heading adversaries for boundary evaluation, and ledger-order permutations are separate control roles. Adversarial boundary fixtures are measurement-development strings, not additional main experiment conditions. All six active-example ground truths reconstruct from source IDs, but that mechanical check does not approve task naturalness or prove reasoning demand.

## Falsification

An entity/interval selection hypothesis is weakened if effects vanish under independent annotations, disappear with value/name counterbalancing, reverse solely under accepted boundary alternatives, or are explained by answer repetition/length. Report such outcomes. A zero mean with mixed case contributions is not proof of no heterogeneity. A topical-history claim cannot be supported merely by a nonzero E×V interaction.
