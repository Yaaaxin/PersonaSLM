# P1c offline boundary baselines and algorithm opportunity assessment v1

Maintainer: Yaxin ZHENG. Development-only analysis of saved outputs; no model generation, training or alteration of the frozen parser. Researcher adoption of the semantic views does not certify a unique boundary or independent boundary ground truth.

## Completed bounded investigation

The [baseline records](validation/p1c/calibration_v1/boundary_baselines_v1/summary_v1.json) compare five deterministic procedures on the same 72 saved continuations. Source spans, abstentions, timings and failures are retained. Content matching permits surrounding-whitespace normalization explicitly; it does not create a new human rating. The frozen implementation is reconstructed exactly. The literal-stop procedure is an offline shadow, not evidence of what a model would generate with different stop settings.

| Procedure | Returned candidates / 72 | Matches to primary spans | Matches to eight sensitivity prefixes | Independent boundary accuracy |
| --- | ---: | ---: | ---: | --- |
| Frozen response_status_v1 extraction | 64 | 64 | 0 | Not available |
| Native EOS/EOG only, whole continuation | 2 | 0 | 0 | Not available |
| Literal role-stop shadow | 71 | 63 | 0 | Not available |
| Anchored role or section heading | 72 | 64 | 8 | Not available |
| Same rule with code-fence awareness | 72 | 64 | 8 | Not available |

The literal rule also differs on identifiable PC015. Native termination is not proof of a single speaker reply. The fence-aware variant provides **no additional recovery on the real development outputs** relative to the simple heading rule. Matching existing AI-inspected prefixes is circular reference agreement, not independent accuracy or improved model answering. Full raw records and original AMBIGUOUS/CROSS_TURN labels remain unchanged.

Twelve authored software fixtures expose failure cases, including quoted roles, code fences and document headings. They are synthetic test strings, not model generations or independently labeled scientific evaluation data. The simple heading rule matches 6/12 intended fixture spans and falsely splits six; fence awareness matches 10/12 but still falsely splits a multiline quotation and an ordinary document heading. These failures argue against automatic promotion to the primary policy. All unsuccessful cases remain available.

Five batches of 50 repeated passes over the preloaded records measured median process CPU time per extraction of approximately 65.1 microseconds (frozen), 4.3 (EOS), 4.3 (literal), 17.4 (heading), and 13.0 (fence-aware). Timer granularity is visible in the batch logs; tiny differences are not robust speed claims. One-pass traced Python allocations were 1.5–5.3 KB, **not process peak RAM**. These exclude model generation, disk reads and human adjudication. Official templates, grammar-constrained decoding and native stop changes require a separately authorized generation experiment; none was simulated as real inference.

## Algorithmic Opportunity Assessment

### 1. Observed Failure Modes

Boundary management has direct evidence: 64 cross-turn and eight ambiguous outputs, with 70 budget terminations. Eight readable prefix candidates remain non-unique. Temporal and entity errors must be separated: five Laurel/Silver cases support wrong-entity attribution but do not independently establish expired-evidence selection. Factual consistency and task success coincide here; P1b separately contains 27 correct partial replies. This makes component completion a real broader measurement issue but not a distinct P1c failure rate. Persona interference and interaction-aware adaptation require the registered contrasts and independent replication; neither is assumed from an individual wrong answer.

### 2. Existing Methods and Published Prior Art

Boundary baselines include deterministic role parsing, native stops and model-specific templates. [Willard and Louf's guided generation](https://arxiv.org/html/2307.09702v4) constrains token sequences through finite-state/grammar machinery; structural validity does not imply factual truth. This is a versioned preprint reference, not a claim of a verified publication venue.

[LongMemEval](https://arxiv.org/html/2410.10813v2) evaluates time-aware retrieval, indexing and reading. [What to Admit and How to Present](https://arxiv.org/html/2610.11188v1), a preprint, separates memory admission from presentation. [Decoupling Logic from Persona](https://arxiv.org/html/2610.09772v2), also a preprint, proposes separated processing and compares structural and semantic outcomes. [Chain-of-Verification](https://aclanthology.org/2024.findings-acl.212/) already studies generation followed by planned verification. These are substantive prior art, not names to attach to a new filter. The wider persona, RARR and steering comparisons remain in the versioned novelty matrix; this investigation does not reproduce those systems.

### 3. Potential Algorithmic Improvements

| Direction | Remaining gap / falsifiable candidate | Classification and decision |
| --- | --- | --- |
| Response boundary | Confidence-aware abstention that avoids splitting quoted/section text while recovering genuine turns | Known parsing engineering; fence-aware prototype completed, zero incremental gain on real outputs. Preserve failures; do not call it original. |
| Temporal evidence | Bind entity, predicate and query-time interval before selecting a value; preserve historical-query correctness | Ordinary relational/time filtering is established. A novel gap is not yet isolated. No new method implemented. |
| History relevance | Preserve useful history while excluding distracting content at an equal selection budget | Admission/retrieval already addresses this; package contrasts do not validate a new gating mechanism. |
| Persona/evidence separation | Reduce evidence errors without deleting all persona information | Compare separation, instruction priority and published steering; fidelity is not measured here, so a trade-off claim is unsupported. |
| Answer components | Check final requested components rather than reward correct intermediate claims | Checklists and verification are known. P1b motivates prospective evaluation; P1c alone provides little construct separation. |
| Interaction-aware conditioning | Adapt only if independent paired contrasts reproduce a useful interaction | Insufficient evidence for implementation or originality; no adaptation tuned to six clusters. |

### 4. Validation Feasibility

First obtain genuinely independent boundary/semantic judgments without exposing current candidates. Compare frozen extraction, literal roles, headings, fence awareness and abstention on newly authored held-out outputs with quoted-role and heading strata. Freeze thresholds on separate development material. A generation comparison must separately control official template, native stops, output budget and candidate count; do not interpret offline clipping as such a comparison. Evaluate user-facing delivery and semantic damage, not only parser recovery.

For temporal methods, compare a simple entity/date join, lexical and semantic retrieval, time filtering, admission and applicable published baselines. Use current and historical queries, independently assigned values and evidence-validity intervals. Ablate entity binding, time filtering and evidence priority individually; hold model calls and candidate budget fixed and account for extra verification calls. Measure retention of useful history and persona fidelity if the method claims to preserve them. No future independent materials have been used for tuning.

### 5. Publication Value

The completed experiment supports an engineering observation and a falsifiable measurement-robustness question. It does not establish an unresolved limitation of the strongest published methods or an original algorithm. Independent measurement validation and controlled empirical replication have higher immediate information value than naming this parser variant as a contribution. A reproducible negative baseline result belongs in the scientific record. PLOS ONE readiness still requires stronger measurement and independent evidence; the empirical project remains viable without a new algorithm.
