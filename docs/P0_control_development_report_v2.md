# P0 Control Development v2 — Engineering and Identification Report

Recorded **2026-10-12T20:45:56.264380+00:00**. **P0 PARTIAL; neutral-control validity OPEN; P1 NOT STARTED.** Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Protocol v1.1 and the English scope are unchanged. Researcher/maintainer: Yaxin ZHENG.

## Scope and frozen development selection

This is tokenizer-only engineering, not a reliability experiment. Candidate version `neutral_control_candidate_v2_dev`; prompt version `transcript_base_v1`. Six invented development cases were specified before tokenization: Riley, Samara and Devon reuse the three v1 development scenarios, while Tessa, Blair and Robin are newly authored. All six were included by construction; none was selected using answer quality. They are not a holdout or a confirmatory set. The three reused cases support declared engineering repair, not out-of-sample generalization. The original four response-boundary examples were not reused for tuning.

Each case uses the original `build_prompt` factory, the unchanged style-profile heading, fixed named speaker in current question/evidence, and the same evidence/question across all variants. The historical twenty-case dataset, its forty controls and all researcher annotations are unchanged. New synthetic cases and exact source bytes are contained in [the freeze](validation/P0_control_candidate_freeze_v2.json); no private dialogue was used.

The entire pool was frozen at `2026-10-12T20:39:19.571775+00:00` before requests. It contains 32 single-sentence style candidates, 16 neutral-format question/answer pairs, 12 topic-clarification replies and 10 generalized-residence replies per case: **420 candidate prompts plus 24 reference tokenizations = 444 requests**. Selection is the first exact match in fixed order; fallback is smallest absolute difference, then earliest index. Tolerance remains **0**. All failed alternatives remain in the artifact, even though every pair has at least one match. No adaptive pool expansion or generation followed the observed counts.

## Why v1 style matching failed

The old pool concatenated one or two complete sentences, leaving gaps in achievable lengths. Actual saved counts were 94/95/102/103/104 against target 100 for Riley, 96/97/104/105/106 against 100 for Samara, and 94/95/102/103/104 against 98 for Devon. Best differences remained +2/-3/-3. These are observed candidate-coverage failures, not evidence of a faulty tokenizer. Old failures remain intact.

V1 also used `Speaker context:` instead of the original wrapper's `Speaker style profile:`. V2 restores the original factory for both arms, so the first three reference lengths become 101/101/99. This explicit version change means the v1/v2 numbers are not silently presented as the same prompts. The new pool supplies a broader range of natural single-sentence lengths without repetitive sentence padding or copied answer facts. No assertion that generic prose is stylistically inert follows from its wording.

## Actual complete-prompt token matching

Numbers are **reference/candidate** counts, including backend special-token behavior, for the selected candidate. Every difference is zero. A/B/C refer to the distinct history families below, not additional official factorial conditions.

| Case | Style | History A: format | History B: topic | History C: generalization |
|---|---:|---:|---:|---:|
| control_v2_dev_001 | 101/101 | 118/118 | 118/118 | 118/118 |
| control_v2_dev_002 | 101/101 | 120/120 | 120/120 | 120/120 |
| control_v2_dev_003 | 99/99 | 119/119 | 119/119 | 119/119 |
| control_v2_dev_004 | 99/99 | 120/120 | 120/120 | 120/120 |
| control_v2_dev_005 | 99/99 | 119/119 | 119/119 | 119/119 |
| control_v2_dev_006 | 100/100 | 118/118 | 118/118 | 118/118 |

Thus **style 6/6, A 6/6, B 6/6, C 6/6**, or **24/24 engineering matches**. All 420 candidate constructions preserve wrapper, trusted evidence and current question. Selected complete-prompt token arrays share 31–35 suffix tokens with their references; exact IDs and prompt hashes are saved. Byte offsets inside variable-length additions are not asserted to be identical. Overall input token length, intervention position and unchanged outer text are controlled. This is bounded verification on six cases, not universal matching performance.

Sources: [all attempts and token IDs](validation/P0_control_tokenizer_validation_v2.json), [selected texts and hashes](validation/P0_control_development_selection_v2.json). Run `results/p0_control_development_v2/20261012T202741/experiments/20261012T203926-471064d78d6e4164a9f623c8d3ca9c09` contains **1384 chained events**. Tokenizer `/tokenize`: `add_special=true`, `parse_special=false`, `with_pieces=false`. Owned llama.cpp `/props` reports **b11573-0f701c882**, matching model path and context 4096; model/server preflight and postflight hashes agree. Configured CPU threads/batch 4/4 and zero GPU layers are retained in the server journal. This run does not independently repeat prior hardware measurements or generate new performance data.

GGUF SHA-256: `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`. Server SHA-256: `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. File identity does not establish independently reproduced upstream quantization fidelity. **Completion requests: 0.** No new raw or parsed model responses, output tokens, EOS or factual scores exist for these candidates; those fields are not applicable, not fabricated zeros from a generation experiment.

## Control families and estimands

| Comparison | What is held fixed | Defensible proposed interpretation | Residual confounds / limits |
|---|---|---|---|
| C1–C0 | Trusted evidence, current question, recent context | Total insertion effect of this style profile | Added length, heading, semantics and style all change |
| C1–new N_style | Above plus heading, position and total tokens | Replacing generic discourse description with a style profile | Generic prose has its own register; heading can cue style; semantic salience and instruction force differ. Human validation required |
| C3–C0 | Trusted current evidence/question | Total effect of adding the specified dated old-residence dialogue | Length, old information, topic, temporal cues and dialogue format are bundled |
| C3–A `history_format` | Named speaker, date/header syntax, User-to-speaker turn order, two turns, position and total tokens | Residence history versus an equally presented unrelated exchange | Topic relevance, personal information, assertion type and internal past reference differ; cannot isolate historical format |
| C3–B `history_topic` | Same historical question, residence topic, speaker, date, structure, position and total tokens | Old-residence answer versus a residence clarification | Answer/clarification speech acts differ; potential questioning, uncertainty and abstention priming; not a semantic placebo |
| C3–C `history_stale_generalized` | Residence topic, dated prior-city residence, speaker, question, structure and total tokens | Named old city versus an unspecified old city: information-specificity ablation | Informativeness, lexical choices and evasiveness change; no pure stale-fact mechanism or neutral-control claim |

Example selected style: `A conversation includes an exchange of questions and replies between participants.` It contains no named city or new personal fact, but its generic expository register may still affect behavior. A selected A exchange asks `What does a conversation involve?` and replies `An exchange of questions and replies.` It repairs the earlier unrelated document-statement adjacency, while remaining off the residence topic. B uses `The city or the address?` or `Are you asking about the city?`, retaining the historical question but adding clarification behavior. C uses `In a city back then.` or `In a city at the time.`; it preserves a vague past-residence assertion deliberately.

The explicit name in every development question/evidence fixes the earlier `the person`/Alice referent ambiguity only for these new inputs. Date values and timestamp syntax are mechanically equal across each history pair. A lacks the reference's internal past-tense residence relation. B retains the old-time question but provides no historical fact. C retains past-city residence without its name. Natural coherence, temporal interference and unintended style remain **unreviewed human questions**, despite mechanical checks.

Exact token equality controls total context length, not token content, attention allocation, within-block information position or semantic difficulty. A cannot isolate topic relevance; B cannot isolate factual content independently of response pragmatics; C cannot isolate temporal conflict from named-answer competition. A named old city valid in the past is not itself a false statement. Identifying temporal-conflict effects would require a separately approved time-validity manipulation with content balanced. Identifying history presentation would require the **same facts** in prose and dialogue, with length/position checks. Neither diagnostic was executed here. Track A trusted evidence remains fixed, and Persona Fidelity remains separate from Dialogue Reliability.

## New human review and acceptance

The [new CSV](validation/P0_control_development_review_v2.csv), [JSON master](validation/P0_control_development_review_v2.json) and [English guide](P0_control_development_review_v2_guide.md) cover **24 items: 18 proposed neutral/control alternatives and 6 non-neutral diagnostics**. All human labels, identities, times and notes are blank: **0/24 reviewed**. Fourteen judgment axes, exact evidence-quote fields, version/hash checks and an immutable importer support tracking. Optional review time remains blank when unavailable. The software importer was tested with clearly marked artificial fixtures only; no actual human import occurred.

The original **40/40** researcher reviews remain complete, with original overall **PASS 0 / PARTIAL 40 / FAILED 0**. They do not transfer to new wording. This package offers alternatives: adopting every family or reviewing unused diagnostics is not a new blanket P0 gate. Before adoption, review the selected intended control inventory and resolve FAIL/UNCERTAIN findings with defensible claim boundaries. No new annotations or acceptance decision have been supplied.

| Requirement | Status | Evidence / remaining limitation |
|---|---|---|
| Exact final-prompt accounting and wrapper preservation | PASS | 24/24 selected pairs, tolerance 0; all attempts retained |
| Candidate source/version freeze and no answer-based selection | PASS | Freeze precedes 444 tokenizer calls; no completion calls |
| Old records and frozen protocol/policies preserved | PASS | 110 protected files and 22 historical journal inventories unchanged |
| Journal integrity and selected-result reconstruction | PASS | All 23 current chains checked; 24 new pair results reconstructed |
| Old human review completeness | PASS | 40/40 unchanged; validity remains PARTIAL |
| New candidate semantic review | PARTIAL / OPEN | 0/24; actual human review needed for controls to be adopted |
| Historical control validity | PARTIAL | Existing style/topic/identity findings unresolved for old materials |
| Identification of isolated style/history/time mechanisms | PARTIAL | Narrow replacement contrasts specified; residual confounds explicit |
| New development software | PASS | 285 passed in 15.44s; existing runner/evaluators unchanged |
| Overall P0 acceptance | PARTIAL | Engineering matches do not close semantic validity; P1 requires closure and researcher approval |

Acceptable limitations include bounded model termination behavior under the frozen policies, unsupported backend evaluated-input arrays and unverified upstream quantization equivalence, within the already stated scope. Future robustness, fidelity studies and mechanism experiments are research extensions; perfect model performance or all external interfaces are not prerequisites. Neither P1 nor training was started.

## Tests, errors and reproducibility

**285 passed, 0 failed, 0 warnings reported**, pytest **15.44s**, process **16.106s**, exit **0**. Actual interval: `2026-10-12T20:40:50.776176+00:00` to `2026-10-12T20:41:06.881737+00:00`.

Initial new-module tests: **16 passed, 6 failed**, exit 1, 0.36s. A `dataclasses.asdict` result retained a tuple of facts while the existing schema correctly requires a list. The new development serializer was corrected to emit lists; the old schema and tests were not weakened. Targeted rerun: **22 passed**, 0.13s, exit 0. A read-only inspection initially used nonexistent `schema.py`; the correct `schemas.py` was then read. That PowerShell command continued with exit 0 despite the read error. Both limitations are recorded rather than suppressed.

Starting HEAD: `4d00ee1adbe538d24175d5c3e83c318bff8365a3`, dirty **true**, with 40 preexisting uncommitted files. New run manifests retain the exact commit, dirty status, dataset/source/tool bytes and hashes, config, candidate freeze, prompt IDs and requests. No commit, push, history edit or author configuration occurred. All 22 prior journals remain byte-identical; the new journal adds tokenizer evidence only. Existing 140 generations across 17 generation runs remain unchanged.

Engineering command/error captures are under `results/p0_control_development_v2/20261012T202741/engineering/`; experimental evidence is under `experiments/`; pre-change inventory and development data under `materials/`. [Integrity evidence](validation/P0_control_development_integrity_v2.json) and [command index](validation/P0_control_development_commands_v2.json) provide traceability. Early read-only tool calls retain transcript provenance; their individual times are not reconstructed. Fresh reproduction requires a new session and artifact version; immutable outputs refuse overwrite. Late reporting-source changes are retained in a separate delivery snapshot, not backfilled into the experimental freeze.

The [novelty matrix addendum](related_work_novelty_matrix.md) checks three additional primary papers. Length/structure controls and persona/context contrasts have prior art. These improvements establish engineering feasibility, not a verified original methodological contribution or a persona-reliability result.


## 2026-10-12T20:50:38.420802+00:00 — Delivery checks and concurrent workspace provenance

The final source scan and Git diff whitespace check passed after a documented checker correction. The first delivery command exited1: its path scan matched its own diagnostic string and machine paths in an unchanged historical report body. The checker now uses a generic pattern for newly added content and separately verifies that the historical body remains byte-identical. No historical path/measurement was erased to obtain PASS. The failed capture remains at `results/p0_control_development_v2/20261012T202741/engineering/delivery_command.json`; corrected delivery exited0 in0.874s, with171 source/document text files scanned, zero prohibited product-name matches and zero broken local links at that checkpoint. Six Git CRLF-to-LF notices were reported, separate from the test suite's zero reported warnings. Final inventory/check results are in [the closure evidence](validation/P0_control_development_final_checks_v2.json).

Concurrent workspace activity was observed: files became staged and `docs/PersonaSLM_related_work_novelty_audit_2026-10-12.md` appeared after the starting inventory. Its SHA-256 is `8083dd74f44a60dc4b067e503737077d2fd1aaf6ed52f01c8ccbff8c653ffaeb`. The automated work did not add/stage, commit, push or alter Git identity/history, and did not edit this additional document. Its authoring/review claims are not attributed to this run. The earlier delivery artifact's field named `files_changed_this_task` is an **observed change-since-baseline inventory**, not an authorship claim; it includes this concurrently supplied file. The field name is corrected in the utility for future execution, and the final sidecar separates automated edits from concurrent additions without rewriting the earlier artifact.

The supplied literature audit was read. Three of its especially relevant primary records/abstracts (Principled Personas; One Persona, Many Cues; When Personalization Misleads) were independently checked, in addition to the three papers in the earlier v2 addendum. Full numerical/model details of all nine supplied studies were not reverified. The novelty matrix distinguishes these evidence levels. These checks strengthen the caution against generic novelty claims; they do not add experimental results or change Protocol v1.1.

No runtime source or tests changed after the complete suite:285 passed in15.44s, process16.106s, exit0. Subsequent changes are reporting/checker code and English documentation. Experimental frozen sources remain unchanged. P0 remains PARTIAL; existing40 human reviews remain complete, new review0/24 remains OPEN; only adopted controls require closure, not every unused diagnostic. No P1 or training was executed. The new run has444 tokenizations,1384 journal events and0 completions.


## 2026-10-12T20:51:18.989888+00:00 ? Concurrent Git HEAD observation

The final read-only check observed HEAD `e1da38723b310ff6a12b04e1164ac20bb12feb1f`, whereas the tokenizer run and starting snapshot recorded `4d00ee1adbe538d24175d5c3e83c318bff8365a3` with dirty state true. A concurrent external Git update occurred during this task. The automated workflow performed no staging, commits, pushes, identity changes or history rewrites. Original experimental commit/source snapshots are retained, not backfilled with the new HEAD. Current runtime-source hashes still match the experimental freeze; test validity is unchanged. The final structured checks record both the remaining working-copy changes and the concurrent document separately. All still-pending edits remain for maintainer review.
