# P1c Counterfactual Pair Audit — v1

Maintainer: Yaxin ZHENG. Offline analysis; all original stimuli and model results remain unchanged. Human decisions remain OPEN.

## Scope and reconstruction

The [72-row matrix](validation/p1c/scientific_review_v1/counterfactual_comparison_matrix_v1.csv) includes all six unordered R/T pairs for each of 12 cases, not just selected favorable contrasts. The [cell audit](validation/p1c/scientific_review_v1/cell_audit_v1.json) also includes both baselines. Each pair retains source quotations, proposition/property/value/date identity, requested-date validity, turn/role/header identity, lexical negation, direct answer disclosure, full-token counts and evidence/question positions.

Original IDs are R0T0, R0T1, R1T0, R1T1, N_history and H_none. The configuration contains an explicit order of case/condition tuples, but no separate request_id. The review snapshot preserves these 72 original identities and order without inventing historical request IDs. Order seed remains 715001; decoding seed remains 42.

| Check | Actual audit result | Interpretation |
|---|---|---|
| Same evidence/question/reference/context/date within case | 72/72 reconstructed | No Track B evidence intervention |
| All four cells historically true in stated interval | 48/48 source facts reconciled | T0 is expired at requested date, not false |
| Temporal routing | 24 expired / 24 valid | Validity uses requested date, not archive/evaluation date |
| Same entity, two turns, archive date and framing | 72/72 R/T pairs | No new competing entity in the additional history |
| T-only pairs | 24/24 change color and interval; preserve predicate | Date/value package, not same-proposition date manipulation |
| R-only pairs | 24/24 change predicate and color; preserve interval | Topic/property/lexical package |
| Full entity/property/value proposition unchanged | 0/72 pairs | Mathematical factorial routing is not semantic orthogonality |
| Cross-topic identical color | 12 off-diagonal pairs | Construction regularity, not proof of answer competition |
| Direct required-answer fact/string in active history | 0/48 | Semantic indirect cues still require review |
| Final token equality across active cells plus neutral | 12/12 sets; zero difference | Engineering property only |
| Native retokenization | 72/72 token-ID lists identical | No generation or approximation |

## Case-level evidence

The following table lists the actual references. “Historical” requests 2042-06-15; “current” requests 2042-12-15. Every prompt exposes fictional evaluation date 2042-12-15 and the requested date in the question. Each speaker's two rows share a ledger and form one cluster.

| Case suffix | Speaker | Family | Historical answer | Current answer | Matched full tokens | H_none tokens |
|---|---|---|---|---|---:|---:|
| 01 | Auden Vale | Single retrieval | Laurel | Harbor | 770 | 705 |
| 02 | Celia North | Single retrieval | Harbor | Maple | 766 | 701 |
| 03 | Elian Moss | Multiple components | Maple; Tuesday | Orchid; Thursday | 915 | 850 |
| 04 | Greta Sable | Multiple components | Orchid; Thursday | Silver; Saturday | 926 | 860 |
| 05 | Idris Fern | Route integration | Silver | Cobalt | 938 | 873 |
| 06 | Nora Finch | Route integration | Cobalt | Laurel | 911 | 846 |

For example, p1c_01_historical uses music green in January–April versus music red in May–August, and parcel blue versus parcel green in the same respective intervals. Its answer remains Laurel. The valid parcel color equals the expired music color. That equality is a possible cue, not an injected desk answer. Exact fact IDs/quotations for every other case are in the matrix and [12-case review](validation/p1c/scientific_review_v1/case_review_v1.csv); no quotation was authored as a human judgment.

## Dependency diagnostics

[Reference dependency checks](validation/p1c/scientific_review_v1/reference_dependency_checks_v1.json) recompute all 12 answers after auxiliary-fact deletion and auxiliary-value substitution in unsaved internal copies. Answers remain unchanged. Deleting any required fact prevents a unique reference; changing the final required value changes the answer. These tests demonstrate formal derivation dependencies only. They neither estimate model responses nor prove that a model will use the required path. No mutated evidence enters a proposed condition.

Evidence occurs before the archived-dialogue block, and its token prefix is identical within every case. The five matched histories also share the final-context/question start token. H_none changes downstream position because it is shorter and has different separator tokenization; it is intentionally not a matched placebo.

## Limits and disposition

No syntactic, hash, reference or factor-routing failure was found. Semantic risks remain: topic assumptions, cyclic colors, interval/value coupling, requested-month overlap, retrospective archive framing and neutral metadiscourse. The [resolution](P1c_identifiability_resolution.md) therefore permits only a proposed operational interpretation pending human acceptance. No cells are dropped and no interaction is declared identified at a unique mechanism level.
