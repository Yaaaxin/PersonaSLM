# P1d published-method and offline baseline comparison — v1

Maintainer: Yaxin ZHENG. No new model inference, external inference API, training or private-data collection. Published results are not reproduced by implementing similarly named prompt fragments.

## Primary-source comparison

The [versioned literature matrix](related_work_novelty_matrix_monitor_v4.md) and its JSON/CSV give exact sources, versions, authors, models, datasets, methods, metrics, limitations and overlap. Main methods/experiments were read for the nine requested works and newly discovered LongMemEval-V2. This is a targeted search, not an exhaustive systematic review; appendices and source-code/statistical replication remain incompletely verified. Conference status is taken from official proceedings; October manuscripts and LongMemEval-V2 remain preprints where no venue was verified.

| Required baseline family | Feasible local implementation / adaptation | What is not claimed |
| --- | --- | --- |
| Trusted evidence only | Prompt builder removes persona and history | Not an adequate fidelity-preserving solution |
| History removal | Prompt builder retains persona but removes auxiliary claims | No generated-answer benefit measured |
| Lexical selection | Deterministic word overlap, top one, explicit tie ordering | Not semantic retrieval or a strong learned-ranker replica |
| Temporal selection | Query-date interval membership | Ordinary established filtering, not originality |
| Entity/time joint selection | Exact structured entity and interval join | Assumes correct metadata; free-text extraction not validated |
| Evidence-priority prompt | Explicit source/entity/date priority | Prompt construction only; no quality evaluation |
| Component verification | Structured claims, support, coverage and delivery checks | Not CoVe or RARR reproduction; not a free-text semantic scorer |
| Response boundaries | Reuse frozen, EOS, literal-role, heading and fence-aware development tools | No independent accuracy without adjudicated spans |
| FPPS | Specify activation-probe/steering baseline and required adapter/backend work | Not feasible through current plain GGUF request interface; not implemented |
| FC/PS admission, LongMemEval retrieval | Map metadata gates and time filtering; document missing adjudicator/indexing components | Partial adaptation, not the published full system |
| CoVe / RARR | Prospective same-model verification/revision with a supplied ledger | Extra calls need authorization; no silent hosted-model substitution |

## Completed offline results

`tools/p1d_offline_baselines.py` evaluates 16 development v3 cases. Each pool contains four auxiliary claims; the full trusted ledger is never removed. All methods receive the same query/entity/date metadata and no reference-answer field.

| Selection | Target/query-valid facts retained | Other or expired facts retained | Total retained |
| --- | ---: | ---: | ---: |
| All history | 16 | 48 | 64 |
| Remove history | 0 | 0 | 0 |
| Lexical top one | 0 | 16 | 16 |
| Time filter | 16 | 16 | 32 |
| Entity/time filter | 16 | 0 | 16 |

These are **selection diagnostics**, not factual accuracy or improved persona fidelity. Every lexical comparison ties all four candidates: its deterministic ID tie-break selects an unsuitable candidate. Reversing ID order also selects an unsuitable candidate. A uniform tie selection has expected target-valid probability 1/4 by construction, not an observed model score. This fixture design cannot establish that sophisticated retrieval is inadequate. Retention budgets also differ; a fair future generation comparison needs equal top-k/token budgets and separately reported metadata advantages. No claim that the joint filter outperforms published algorithms is supported.

The structured verifier meets all eight authored fixture specifications. Removing entity, time or delivery checks separately meets seven of eight. It separates correct partial/promise content from successful delivery. These are specification checks and bounded ablations, not eight independent scientific observations. Median process CPU time was approximately 19.5 microseconds per verification in five batches; traced Python allocation peak was 872 bytes, not process peak RAM. Timer quantization and the tiny structured problem preclude broader efficiency claims. Costs of metadata extraction, model generation, I/O and annotation are excluded and unmeasured.

The previous P1c boundary investigation remains unchanged: heading and fence-aware methods recover the same 64 primary/8 alternative candidates, with **zero incremental real-output recovery** for fence awareness. Authored quoted-heading fixtures reveal remaining false splits. This negative result argues for independent boundary validation rather than naming a new parser.

## Fair future method experiment

Use separate algorithm-development cases, not the future empirical validation bank. Compare no-history, evidence-priority, lexical and exact metadata/time baselines before adding an adapted published verifier. Hold total generation tokens/candidate count fixed where possible; also show a cost curve when verification needs extra calls. For CoVe, specify draft/plan/independent-check/revise calls; for ledger-adapted RARR, use identical supplied evidence and label omission of web search. Measure correct-answer damage, full task delivery, all reliability outcomes, narrow style fidelity, abstention and CPU/RAM. Stronger full published systems can be reported as infeasible with reasons, not defeated by an intentionally weak local substitute.

## Algorithmic Opportunity Assessment

**Observed Failure Modes:** structured entity/time and missing-component distinctions are real measurement requirements; P1c boundary ambiguity is observed. **Existing Methods and Published Prior Art:** the table and primary-source matrix show substantial overlap. **Potential Algorithmic Improvements:** only selective abstention/verification beyond these strong simple baselines remains a hypothesis. **Validation Feasibility:** independent language-to-claim and boundary ground truth are missing; generation improvements untested. **Publication Value:** current work is an engineering adaptation and a preserved negative boundary result, not an independently supported algorithmic contribution.
