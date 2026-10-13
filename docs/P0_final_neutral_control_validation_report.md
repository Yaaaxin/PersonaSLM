> **Current researcher-decision update:**24/24 new candidate decisions are registered as AI-assisted human review. N_style:6 REVISION_REQUIRED; History A:6 ACCEPT_NARROW; History B:6 REJECT_AS_NEUTRAL; History C:6 DIAGNOSTIC_ONLY. The official65-column conversion preserves336 supplied checks but has18 missing suitability labels,6 disallowed N/A labels and81 missing required field-quote associations. **P0 PARTIAL; P1 NOT STARTED;334 tests passed.** See [the current decision and acceptance report](P0_control_decision_registration_report.md). Earlier review-status statements below remain historical records.

# P0 Final Neutral-Control Validation — Review Preparation v3

Recorded **2026-10-12T21:09:15.271521+00:00**. Researcher: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Protocol v1.1; English. **Engineering PASS; exact matching PASS; semantic-control validity OPEN; overall P0 PARTIAL; P1 NOT STARTED.** This is an offline inspection and annotation-package update, not a new model experiment or a protocol amendment.

## Evidence actually inspected

All24 selected records in the v2 CSV/JSON master were read and compared with original active interventions, frozen candidate pools, constructed prompts and the native tokenizer journal. All420 candidate prompts plus24 reference requests match the saved original HTTP request text and decoded response token IDs: **444/444 reconciled**. All24 selected differences remain exactly0. The first-exact-match selection rule replays unchanged. Final wrapper/evidence/question equality was checked, and current construction reproduces the frozen pool.

This validation used saved **real** GGUF observations; it did not approximate counts, start a backend or request new tokenization/generation. Model hash `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; backend hash `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; build `b11573-0f701c882`. Prompt version `transcript_base_v1`; candidate version `neutral_control_candidate_v2_dev`. Original tokenizer options are add_special=true, parse_special=false, with_pieces=false. The source run retains configuration CPU4/4, context4096, seed42/cap96 (unused for tokenization), original source/config hashes and Git dirty state.

Run `results/p0_control_development_v2/20261012T202741/experiments/20261012T203926-471064d78d6e4164a9f623c8d3ca9c09` has1384 verified chained events. Its20 HTTP503 responses occurred on `/health` during the earlier model startup, before successful tokenizations; they remain preserved. No tokenizer errors or missing IDs were found among the444 responses. These are historical startup observations, not new failures. The original140 generated responses in17 generation runs were neither rerun nor rescored. All23 historical journal inventories remain byte-identical to this task's initial snapshot. [Full offline evidence](validation/P0_final_control_evidence_v3.json).

## Exact candidate inventory and analytical concerns

Counts below are **reference/candidate complete-prompt tokens**. Every row is a development-analysis observation, not a human semantic judgment. The [structured per-item analysis](validation/P0_final_control_analysis_v3.json) gives each candidate's stable ID, full texts, intended contrast, constant/manipulated variables, residual confounds, semantic risks, information removed/retained/changed, appropriate interpretation and exact native request/response sequence numbers and hashes.

| Case | Family | Tokens | Difference | Specific analytical concern |
|---|---|---:|---:|---|
| control_v2_dev_001 | style_generic | 101/101 | 0 | The generic control is itself a concise single sentence, potentially cueing the brevity under investigation. |
| control_v2_dev_001 | history_format | 118/118 | 0 | The question and reply concern conversation, not residence; generic propositions replace dated personal information. |
| control_v2_dev_001 | history_topic | 118/118 | 0 | Adds an address-versus-city distinction not present in the active answer. |
| control_v2_dev_001 | history_stale_generalized | 118/118 | 0 | Changes at the time to back then as well as replacing the city name. |
| control_v2_dev_002 | style_generic | 101/101 | 0 | The generic control is formal, grammatical expository prose, potentially overlapping the formality intervention. |
| control_v2_dev_002 | history_format | 120/120 | 0 | The question and reply concern conversation, not residence; generic propositions replace dated personal information. |
| control_v2_dev_002 | history_topic | 120/120 | 0 | Adds an address-versus-city distinction not present in the active answer. |
| control_v2_dev_002 | history_stale_generalized | 120/120 | 0 | Changes at the time to back then as well as replacing the city name. |
| control_v2_dev_003 | style_generic | 99/99 | 0 | The control does not use certainly, but changes instruction force and semantic content as well as the lexical preference. |
| control_v2_dev_003 | history_format | 119/119 | 0 | The question and reply concern conversation, not residence; generic propositions replace dated personal information. |
| control_v2_dev_003 | history_topic | 119/119 | 0 | Uses a second-person clarification about city granularity, not a residence assertion. |
| control_v2_dev_003 | history_stale_generalized | 119/119 | 0 | Retains at the time verbatim; the city name becomes a city. |
| control_v2_dev_004 | style_generic | 99/99 | 0 | The control uses no contraction; absence of a prescribed contraction habit does not establish style neutrality. |
| control_v2_dev_004 | history_format | 120/120 | 0 | The question and reply concern conversation, not residence; generic propositions replace dated personal information. |
| control_v2_dev_004 | history_topic | 120/120 | 0 | Adds an address-versus-city distinction not present in the active answer. |
| control_v2_dev_004 | history_stale_generalized | 120/120 | 0 | Changes at the time to back then as well as replacing the city name. |
| control_v2_dev_005 | style_generic | 99/99 | 0 | The control describes questions and replies; it can frame conversational response structure without explicitly prescribing an acknowledgment. |
| control_v2_dev_005 | history_format | 119/119 | 0 | The question and reply concern conversation, not residence; generic propositions replace dated personal information. |
| control_v2_dev_005 | history_topic | 119/119 | 0 | Uses a second-person clarification about city granularity, not a residence assertion. |
| control_v2_dev_005 | history_stale_generalized | 119/119 | 0 | Retains at the time verbatim; the city name becomes a city. |
| control_v2_dev_006 | style_generic | 100/100 | 0 | The control itself demonstrates a single sentence, potentially overlapping the active single-sentence response tendency. |
| control_v2_dev_006 | history_format | 118/118 | 0 | The question and reply concern conversation, not residence; generic propositions replace dated personal information. |
| control_v2_dev_006 | history_topic | 118/118 | 0 | Uses a second-person clarification about city granularity, not a residence assertion. |
| control_v2_dev_006 | history_stale_generalized | 118/118 | 0 | Retains at the time verbatim; the city name becomes a city. |

Each family therefore retains6/6 matching. The six cases are not a holdout or a representative speaker population. Three scenarios were reused from v1 development and three were new in v2; this round adds **no cases, new wording or new selection**. Multiple styles occur across cases, but each style is tied to one synthetic person/scenario. Neither independent style-axis effects nor S/F/H interactions are estimated by this inventory.

N_style removes explicit repeated padding but still demonstrates a register beneath a style-profile heading. A controls presentation length/structure while leaving topic and personal/temporal content unequal. B preserves the residence question but turns its answer into a clarification; three replies add an address-versus-city distinction. C deliberately removes a named old city while retaining vague past-city residence; three cases also change temporal phrasing. **C is a diagnostic, not a neutral placebo.** Named questions eliminate the old implicit person/Alice referent link in these inputs, but do not independently establish speaking-as versus speaking-about fidelity.

The [control identification matrix](P0_control_identification_matrix_v3.md) separates seven dimensions and explicitly states which effects each contrast cannot identify. The official C1–C0/C3–C0 and matched-control contrasts are unchanged. A/B/C have distinct roles; none isolates all historical effects. Prose/dialogue fact-equating and crossed relevance/time/presentation tests remain future proposals requiring approval, not P0 completion requirements.

## Final human-review package

Use **[P0_final_control_review_v3.csv](validation/P0_final_control_review_v3.csv)**, with [English instructions](P0_final_control_review_v3_guide.md) and an [immutable JSON master](validation/P0_final_control_review_v3.json). The CSV has24 rows/65 columns, including candidate/case/family IDs, active/candidate texts, evidence/question, reference/evaluation dates, expected answer, exact counts,15 review questions, blank judgments/quotations/notes/reviewer fields, complete prompts and provenance hashes.

Expected answers are review-only metadata from frozen fixtures. They were not added to experimental prompts. Style blocks have no historical reference date, so that field is explicitly NOT_APPLICABLE. Conditions and answers are visible; this is not blind review. Original v2 masters are unchanged and still available. The new form contains **0/24 human reviews**, and the original40 completed annotations have not been transferred. Old control-suitability counts remain PASS0/PARTIAL40/FAILED0, applying only to the old materials.

The new versioned importer has a default v3 master and a simple input/output command in the guide. It validates exact inventory, labels, frozen content, versions/hashes, reviewer identity/assistance, optional UTC times and actual quotations. Default import requires all24 completed rows; explicit partial import remains available without changing the inventory. Completion does not automatically imply validity. Software fixture reviews used in tests are clearly marked and never written to research annotation fields.

An actual command against the blank form was intentionally tested and rejected with exit1: `Incomplete human review: 0/24`. No output review file was created. This expected negative check demonstrates that blank materials cannot become completed human evaluation. No genuine completed submission was supplied or imported, no reviewer identity/time was invented, and no agreement statistic was computed.

## Acceptance checklist and remaining blockers

| Requirement | Status | Evidence / limitation |
|---|---|---|
| Protocol, title, English scope and research boundaries | PASS | No frozen protocol or factor/endpoint/policy changes |
| Existing engine and logging engineering | PASS within existing scope | Previous real inference retained; this round only reconciles saved evidence |
| Actual full-prompt matching | PASS |24/24 selected pairs, all444 native request/response observations consistent |
| New review package/import tooling | PASS |24 blank complete materials;22 new targeted tests; actual empty-import rejection |
| Original human annotation completion | PASS |40/40 unchanged, old semantic findings still PARTIAL |
| New human annotation completion | PARTIAL / OPEN |0/24; a new presentation does not create a human review |
| Semantic validity of proposed adopted controls | PARTIAL / OPEN |Style, topic, speech-act and specificity findings require human judgment/resolution |
| Historical reproducibility | PASS within scope |23 unchanged journal inventories, source run chain and token replay verified; raw archive remains local |
| Scientific identification | PARTIAL |Narrow replacement estimands documented; pure format/topic/time mechanisms not identified |
| Automated tests | PASS |307 passed, no failures |
| Overall P0 | PARTIAL |Valid adopted controls and justified interpretation remain required; P1 requires separate authorization |

Mandatory closure is real semantic review of the exact controls intended for use and resolution of substantive findings, with a defensible interpretation accepted by the researcher. A completed form alone, token equality, or model fluency is insufficient. Unused alternatives and optional diagnostics do not all become new acceptance gates. A pure-format or pure-temporal-effect claim cannot be licensed by the present controls. Any change to protocol/primary estimands requires explicit approval.

Bounded response instrumentation, missing unsupported backend input-ID arrays and independently unverified upstream quantization fidelity remain documented limitations under their existing claim scope. Perfect Base-model termination or completion of future model-size/external validation experiments is not required for P0 instrumentation. Persona Fidelity remains independent of reliability. No P1, training, unrelated application access or Git mutation was performed.

## Novelty and reproducibility

The [five falsifiable proposals](P0_control_hypotheses_v3.md) retain priorities A–E and specify supporting/falsifying observations and confounds. The [novelty matrix](related_work_novelty_matrix.md) and four rechecked primary sources show direct overlap with persona cues, context interference, factual reliability and authentic-person simulation. The inclusion of2B/3B models in Principled Personas was checked in its PDF. This is scoped source verification, not a systematic review or proof of originality. No persona-effect finding follows from this preparation.

**307 passed, 0 failed, 0 warnings reported**, pytest **17.08s**, process **17.773s**, exit **0**. Actual interval: `2026-10-12T21:03:02.125992+00:00` to `2026-10-12T21:03:19.899104+00:00`.

Targeted new tests:22 passed in0.89s, exit0. All positive checks passed on their first run this round; the intentional blank-import exit1 is retained separately. The full suite was not weakened. Existing modules, evaluation policies, candidate-generation code, fixtures and old review masters remain unchanged; only a new review module/test and audit/report tools were added.

Session `results/p0_final_control_review/20261012T205559` stores exact command start/end times, outputs, exits and errors under `engineering/`; baseline hashes and original document bytes under `materials/` and `original_documents/`. Starting HEAD `e1da38723b310ff6a12b04e1164ac20bb12feb1f` was dirty (19 preexisting changed/untracked paths). The source tokenizer run retains its original HEAD `4d00ee1adbe538d24175d5c3e83c318bff8365a3` and dirty=true; current metadata is not backfilled into it. No new model-run manifest is invented for this offline work. [Command/delivery evidence](validation/P0_final_control_delivery_v3.json) records final checks and file changes. Initial read-only interface calls retain transcript provenance; individual missing timestamps are not fabricated.
