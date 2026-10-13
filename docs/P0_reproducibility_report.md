# Final P0 Closure - Current Acceptance

**P0 = PASS. Engineering and Methodological Infrastructure Validation Completed. P1 = NOT STARTED.**

The exact final Tessa sentence has explicit researcher ACCEPT_NARROW approval, registered separately without modifying its historical pending/failed records. Selected N_style: 6/6 narrowly accepted and exactly matched. History A: 6/6 narrowly accepted, 18 confirmed evidence links, all exact matches. Its topic/temporal FAIL and original coherence UNCERTAIN are retained; B remains rejected as neutral and C diagnostic-only. These are scoped comparisons, not complete semantic neutrality or equivalence to C0.

All 15 mandatory P0 infrastructure/measurement checks pass within their declared scope. Remaining mandatory P0 blockers: **none**. Full suite: **365 passed, 0 failed, 0 warnings reported, exit 0**. Protocol v1.1, original annotations, policies and experiments are unchanged. No generation was run for this acceptance. See the [final acceptance report](P0_final_scientific_acceptance_report.md), [hash-bound researcher approval](validation/P0_tessa_researcher_approval_v1.json), [verification](validation/P0_acceptance_verification_v1.json) and [delivery evidence](validation/P0_acceptance_delivery_v1.json).

Earlier statuses below are retained historical checkpoints, superseded only as current acceptance statements. Their measurements, missing fields, limitations and original decisions remain valid historical records.

---

> **Current final assessment:** P0 PARTIAL only pending the exact new Tessa wording's researcher approval. Style matching6/6 (Tessa99/99); other five style texts unchanged and ACCEPT_NARROW. History A6 narrow decisions,18 associations and6 scope-limited suitability PASS labels registered. Tests365 passed. Visible preliminary-analysis provenance remains disclosed; no blind-review claim. See the [final scientific acceptance report](P0_final_scientific_acceptance_report.md). Earlier records below are preserved history.

---

> **Current narrow closure:** P0 PARTIAL; P1 NOT STARTED. Revised style exact matches5/6; one FAILED (+1 token), no pool expansion and no answer generation. New style review0/6; History A needs18 source-association confirmations and6 explicit suitability labels. Original40 reviews,24 decisions and336 checks are preserved. Tests348 passed. See the [current closure report](P0_final_control_closure_report.md) and [minimum remaining gate](P0_remaining_blockers.md). Prior statements below remain historical evidence.


---

> **Current assessment — 2026-10-12T20:13:26.793933+00:00:** Human annotation **PASS, 40/40 completed**; final review is AI-assisted and not blind. Semantic-control validity remains **PARTIAL / resolution OPEN**; researcher overall ratings are PASS 0 / PARTIAL 40 / FAILED 0. Overall **P0 PARTIAL; P1 NOT STARTED**. See the [current control acceptance report](P0_control_acceptance_report.md) and [researcher annotation report](P0_researcher_annotation_report.md). Tests: **263 passed**. All earlier status/readiness statements below are preserved dated history, including earlier 0/40 review counts.

# P0 Reproducibility Report

**Latest policy assessment:** [P0_policy_acceptance_report.md](P0_policy_acceptance_report.md). Bounded instrumentation and evaluation-policy checks PASS; human neutral review OPEN (0/40). Overall PARTIAL. Earlier assessments are preserved as history.

**Current final-methodology update:** 19 historical inventories unchanged plus one new boundary journal; 16 generation runs / 134 responses reconstructed twice. See the final-methodology addendum below and [current acceptance boundaries](P0_remaining_blockers.md). Earlier snapshots are retained.

**Latest update:** the English completion addendum at the end records 19 verified journals and 15 generation runs / 118 responses reconstructed twice. Overall historical provenance remains PARTIAL. Earlier observations below are preserved.

2026-10-12；Research Protocol v1.1。研究题目：**Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**。

**可复现性验收：PARTIAL。** 已实现并实际执行离线输入重建、Parser 与当前城市评分重放；这不是重新调用模型的推理重放，也不声称相同 seed 必然得到相同输出。首次 C0 的历史 Git 状态和运行时内存无法追补为当时观测。

## 证据位置与历史保护

首次真实 C0：`results/p0/20261012T163840-d0e467a28a4e4df89eb35ce788dfa917/`，保留原始 `manifest.json`、271 个事件和 `server.log`。

本轮旁路验证根目录：`results/p0_validation/20261012T164648/`。`original_c0_inventory.json` 于 `2026-10-12T16:51:07.700502+00:00` 保存原始文件清单和摘要；最终导出会逐文件比较，任何差异都中止导出。原始 C0 不重跑、不补字段、不重写事件。

公开派生证据：

- [逐案例审计](validation/P0_case_audit.json)：实际提示词、证据、提示词 SHA-256、输入 IDs、tokenizer 请求/响应、生成请求、原始与解析文本、输出 IDs、终止原因、延迟、窄域评分、事件序号。
- [运行清单及环境摘要](validation/P0_final_evidence.json)：run ID、原始文件摘要、Git 状态、数据/源码/模型/后端摘要、配置、内存观测、实际汇总。
- [匹配与失败证据](validation/P0_control_matching.json)：三轮 token 检查、失败候选搜索、最小差值、特殊 token 探针。旧失败不是被后来的成功替换。
- [来源报告](P0_model_provenance_report.md)、[最终验证报告](P0_final_validation_report.md)、[开发日志](research_development_log.md)。

公开 JSON 为派生审计文件，不冒充原始日志链。机器路径留在被 Git 忽略的本地原始日志内；公开报告采用相对路径。原始运行和源码快照尚未作为独立归档包公开，独立研究者若需复核原始 HTTP 字节/完整日志链，需要研究者提供这些本地证据。因此“Git 仓库已经包含全部原始归档”的说法不成立。

## 保存字段与缺口

| 字段 | 首次 C0 | 新控制条件运行 |
|---|---|---|
| Git commit / dirty state | 未记录；不事后断言当时为 clean | manifest 在运行开始只读采集；HEAD 与 dirty 状态真实记录 |
| 源码 | 文件 SHA-256；缺少当时源码内嵌快照 | UTF-8 源码快照、SHA-256；验证工具也保存快照/摘要 |
| 数据 | 数据 SHA-256、案例 IDs，可与版本库合成数据核对 | 所选 JSONL 的精确 UTF-8 内容、SHA-256、IDs、预声明 applicability |
| 模型 / 后端 | 前后 preflight 的文件 SHA、版本输出、`/props` | 同左；详细加载日志补充架构、量化及 CPU buffers |
| 模板、实际 prompt、IDs | 配置中模板名、实际文本和 IDs；prompt 摘要是本轮事后计算 | 模板名、实际文本、IDs、prompt/evidence 摘要在生成前保存 |
| 解码参数 / seed | HTTP 请求及 native generation_settings，seed 42 | 同左；temperature 0，top_p 1，max_new_tokens 96，stop=[] |
| 时间、OS、CPU | 运行/事件时间、通用平台字段、服务日志 | 同左；详细服务 CPU 信息、逐次内存观测，硬件侧证据另存带时间的 CIM 记录 |
| 内存 | 无历史内存测量 | Windows API 记录可用物理内存、working set、peak working set 等；非持续采样曲线 |
| 原始/解析输出、评分、错误 | 原始 HTTP 字节、native JSON、Parser 操作链、评分原因 | 同左；保持错误先留档、无自动重试 |
| 实际评估输入 IDs | 后端仅回显解码文本；未返回输入 IDs | 同样缺失，不构造替代 ID 数组 |

本轮开始时本地 HEAD 为 `f1a1b019981d7f2eb002871c9e600887d9e79874`，新运行包含尚未提交的工程变更；不得把 commit SHA 单独视为精确代码版本。每次 manifest 的源码快照与摘要才覆盖这些未提交变更。Git 只执行只读命令，提交/推送始终由研究者本人执行。

## 实际重建检查

原有 `audit-run` 已实际运行，确认首次 C0 日志完整性并重放 20 个 Parser 结果。新增 `replay-run` 从 saved prompt、tokenizer wire response、completion request 和 raw response 关联案例，复算摘要、Parser 和城市评分；检测重复案例、事件顺序、计数/IDs 不一致、源码版本差异及评分不一致。

```powershell
.\.venv\Scripts\python.exe -m personaslm audit-run --run-dir results/p0/20261012T163840-d0e467a28a4e4df89eb35ce788dfa917
.\.venv\Scripts\python.exe -m personaslm replay-run --run-dir results/p0/20261012T163840-d0e467a28a4e4df89eb35ce788dfa917 --output results/p0_validation/new_c0_replay.json
```

第二条输出路径必须尚不存在，且必须在原运行目录以外。历史运行若数据移动，可用 `--cases` 提供摘要完全相同的 JSONL。新运行优先用内嵌数据快照，不依赖外部数据文件未改动。此命令不会执行快照中的 Python，也不会启动模型。当前 Parser/evaluator 源码摘要若不同，会明确标为 PARTIAL。

首次 C0 的最终两次 CLI 重放分别保存 `c0_reconstruction_final_a.json`、`c0_reconstruction_final_b.json`。全量导出还对每个生成运行连续调用两次审计并比较完整结构，结果见 `offline_replay_identical`。任何断链、篡改或不一致都不被当成成功。

## 冻结、搜索修正与运行配方

`selection_freeze.json` 在新增控制条件生成之前保存：全部 20 条合成案例、按 ID 排序前 3 条先验证，成功后仅扩展余下 17 条。扩展门槛是输入/执行/日志完整性，不是回答是否正确。没有按 C0 输出质量筛选案例。

| 阶段 | 命令入口 | 输入与输出 |
|---|---|---|
| 原搜索审计 | `tools/p0_validate.py prepare --session <session>` | 容差 0，上限 256；style 全部失败，history 全部通过 |
| 候选长度交错 | 同上，`--freeze-name prompts_frozen_v2.json --reuse-history-from prompts_frozen.json` | style 最小差值 −1，仍失败；复用已通过 history |
| 去除排列浪费 | 同上，`--freeze-name prompts_frozen_v3.json --reuse-history-from prompts_frozen.json` | style 第 169 个候选精确匹配；不改容差、预算、证据或问题 |
| 首批 | `tools/p0_validate.py initial --session <session> --freeze-name prompts_frozen_v3.json` | 001–003；四个条件；生成前重新 tokenization，IDs 不同即阻断 |
| 扩展 | 同上，stage 为 `expansion` | 004–020；每案例每条件只生成一次 |

`<session>` 是 `results/p0_validation/20261012T164648`；模型配置为本地 `configs/p0_runtime.local.json`。实际命令用 `tools/p0_capture.py --output <new-json> -- <argv>` 包装，记录真实起止 UTC、退出码、stdout/stderr、墙钟时间。上述表用于解释已经记录的步骤，不要求覆盖原文件来重跑。复现实验必须使用新的 session、重新冻结选择并保留新 run ID。

两次 style 失败仅因候选集合的预算覆盖不足而修正构造顺序；没有改变匹配接受规则，没有参考模型生成质量调整文本。这是 P0 工程修正，不是新的 Persona 算法或 P1 条件优化。

## 科学和操作限制

同一 seed 不保证跨机器、操作系统、后端版本或 CPU 数值内核的输出字节一致。当前离线 replay 验证输入和解析/评分可重建，**未进行模型输出确定性重跑**，因为已有成功生成不需要为本任务重复。

摘要链可检出不一致修改，但无签名或外部时间戳锚定，不是不可篡改存储。没有自动续跑或多写者恢复；未完成写入的响应不能保证在断电后恢复。后端 DLL 与编译依赖没有逐项独立构建复现。上游量化过程、独立语义盲审仍未完成。所有结果只用于 P0 工程验收，不支持 Persona 效应、开放域事实能力或真实说话者拟真结论。

## 2026-10-12 Methodology Completion Addendum

Recorded: 2026-10-12T18:06:22.204470+00:00. Earlier history is retained.

**Current overall reproducibility status: PARTIAL**, owing to the retained historical/provenance and archive-access limitations, while the current engineering checks pass.

| Check | Status | Actual evidence | Limitation |
|---|---|---|---|
| Every existing and new journal | PASS | [19 journal inventories](validation/P0_methodology_integrity.json), including the historical BLOCKED run and PARTIAL matching attempts | Integrity does not convert a failed experiment into a successful one |
| Offline reconstruction | PASS | 15 generation runs, 118 responses; consecutive audit outputs identical | Reconstructs saved inputs/parser/legacy scoring, not new model inference |
| CLI replay | PASS | `replay-run` on `20261012T175449-2d3695902beb4fbaa7bb1f53bc062a22`, exit 0, 3 cases | Original results remain unchanged |
| Historical file preservation | PASS | All 13 pre-existing run inventories equal before/after fingerprints; original 9 generation inventories also equal the prior published hashes | No signatures or external timestamp anchoring |
| New Git and implementation provenance | PASS | All 6 new manifests: HEAD `8ffe1fdeb64ccc85182d2ff983b514940ecb6f70`, dirty=true, exact UTF-8 source/tool snapshots and SHA-256 | Commit SHA alone is insufficient; preserve snapshots with the archive |
| Frozen inputs and configuration | PASS | [Plan](validation/P0_budget_plan.json), [18 complete cases](validation/P0_budget_diagnostic.json), [native-setting checks](validation/P0_methodology_summary.json) | The plan freezes selection/configuration; generation-time snapshots identify the final tested implementation |
| Model/backend/hardware | PASS | Same pinned GGUF/build/executable; new server logs observe CPU 4/4 threads, context 4096 and 0/25 offload | Prior lineage and memory qualifications are retained |
| Evaluation version | PASS | New manifests explicitly label `current_city_legacy_v1`; supplemental module uses `english_city_temporal_audit_v2` and its source hash | Legacy label is a retrospective name for unchanged old code; it was not retroactively inserted into old manifests |
| English language provenance | PASS | Script-authored English fixtures; no translation; prospective metadata in plan/manifests | Raw output deviations must be retained; declared language is not a language-detector result |
| Evaluated input IDs and original C0 provenance | PARTIAL | Absence remains visible | Cannot reconstruct observations that were never saved |
| Public raw archive availability | PARTIAL | Public derived artifacts contain exact experimental inputs/outputs and traceable hashes; raw journals remain local | Independent full wire/journal verification requires the researcher to supply the ignored archive |

The new local evidence root is `results/p0_methodology/20261012T173818/`. Keep `budget_plan.json`, `budget_cases.jsonl`, `budget_prompt_freeze.json`, all six `budget_runs` directories with manifests/events/server logs, both integrity snapshots, all audit/replay files, review mapping, evaluation sidecars and command captures. The public plan is a derived copy with the original immutable plan hash; it does not pretend that the public JSON has the same bytes.

Recorded entry points use the project virtual environment: `tools/p0_methodology.py budgets|review|evaluate|integrity --session <session>` and `tools/p0_methodology_report.py evidence|commands --session <session>`. The budget stage refuses a previously started session; exports use immutable output files. Do not invoke these exact commands into the completed session to replace records. Independent inference replication should first recover the saved exact cases/prompts, pinned binaries and source snapshots into a separate environment, create new local configuration files for the three budgets, and retain new run IDs/output destinations. The standard `run-local` command is available for fresh generations; existing `replay-run` remains a safe offline reconstruction operation with a new output destination.

The observed 96-token prefixes match both longer outputs for all six pairs; the 192-token prefixes also match 256-token outputs. This is a measurement in this session, not a cross-platform determinism promise. No heavy test suite or full-journal audit ran concurrently with generation; subsequent tests and full integrity checking overlapped, so those command durations are not an isolated performance measurement. Sequential budget order and uncontrolled system state limit latency interpretation.

All exact captured commands, times, stdout/stderr, exit codes and intermediate failures are linked in [P0_methodology_commands.json](validation/P0_methodology_commands.json). Read-only inspections and patch errors without exact individual timing are explicitly distinguished in that file's engineering notes and the development log. No timestamp was invented for an uncaptured action.

## 2026-10-12 Final Methodological Validation Addendum

Recorded 2026-10-12T18:43:52.286335+00:00. Historical sections retained.

New local evidence root: `results/p0_methodological_final/20261012T181718/`. **Engineering** commands/tests/errors are under `engineering/`; immutable model **experiment** journals and replays are under `experiments/`; freezes, evaluation and source sidecars are under `materials/`. The old result directories were read only.

New real run: `20261012T182432-ea39ea100d8c449ab05b04cf80e6b78c`. Its manifest records Git HEAD `2b0fc5ee04f05af0fbb878fd71356a6afeaa6865`, actual dirty state, exact generation-time source/tool/data snapshots, frozen plan/configuration, prompt versions and hashes. Each cell retains real tokenizer IDs, request IDs, raw HTTP/native output, native settings, generated IDs/count, stop reason/stopping word, latency, legacy parse, versioned boundary parse and excluded tail. Evaluation is explicitly Not Applicable for this termination diagnostic. Model/backend identities are the unchanged pinned GGUF SHA and build 11573 executable SHA; preflight/postflight and detailed CPU logs are retained.

All 19 historical byte-level file inventories match the previously chain-verified inventory, including the original blocked run and failed matching attempts. This proof reuses the prior chain verification on byte-identical journals; it does not pretend every old tokenizer event was reparsed this time. The 15 old generation runs were additionally reconstructed twice with identical outputs; the new boundary journal was directly chain-checked and reconstructed twice. Total: 20 journals accounted for, 16 generation runs, 134 responses. See [integrity evidence](validation/P0_final_methodological_integrity.json).

The generation command returned exit 1 after all 16 requests because its subsequent offline audit incorrectly treated 14 startup health 503 responses as failed inference. The journal's execution terminal state is PASS. Corrected offline replay retains the 503 observations, requires successful tokenizer/completion responses, and passes without generation. A separate audit-tool hash identifies the corrected implementation; the generation-time snapshot preserves the original auditor bug. Dedicated regression tests cover startup 503 and rejection of failed completion 503.

The importer initially compared CSV column order with sorted JSON key order. Tests caught 2 failures/191 passes; field-name/uniqueness validation now accepts the valid unchanged schema and rejects material edits. This was an engineering fix, not a fabricated reviewer result. Corrected tests 195 passed in 12.11s. Final tests 195 passed in 9.29s, 0 failed, 0 warnings, exit 0; process wall9.707s. Initial pre-generation tests 157 passed in 8.84s. All failure captures remain.

Raw stopped output means the complete payload actually returned by the backend. A native stop can withhold its delimiter; no invisible continuation is invented. No-stop shadow responses are separately logged actual generations with the same prompt/IDs/settings apart from stop. Full public derived [boundary evidence](validation/P0_response_termination_evidence.json) redacts machine paths, while local originals retain raw bytes and source snapshots. [Evaluation evidence](validation/P0_evaluation_validity_v3.json) records independent fixture/source hashes and all 14 old raw responses with separate versions.

The final analysis-code/source snapshot is retained in `materials/final_source_snapshot.json`. It is explicitly later than the inference snapshot and is not backfilled into that run. Current generated and evaluated-ID limitations are stated accurately: returned output IDs and submitted prompt IDs exist, but independently evaluated input IDs do not. No unsupported interface is required as an acceptance gate.

All actual captured commands and failures are indexed in [P0_final_methodological_commands.json](validation/P0_final_methodological_commands.json). Export completion and later delivery checks remain separate local records. Reproduction must use fresh run/output paths; never repeat an already-started session or overwrite original files. Human imports require a genuine reviewer-provided form, new review-round identifier and new output file. The raw archive remains local for researcher-controlled independent dissemination.


## 2026-10-12 Frozen Response and Evaluation Policy Acceptance

Recorded 2026-10-12T19:19:43.094673+00:00. The [current English acceptance report](P0_policy_acceptance_report.md) provides the full checklist and evidence. **P0 PARTIAL; P1 BLOCKED; neutral-control human review OPEN (0/40).** Earlier statuses below/above remain dated historical records.

Frozen `response_status_v1` and `separate_axes_policy_v1` passed their scoped instrumentation checks. Software holdout: 24/24 classifications and spans, six AMBIGUOUS, 75% decided coverage; author-specified software expectations, not human semantic accuracy. Six new real responses: 5 CROSS_TURN and 1 AMBIGUOUS; all hit the 96-token cap, EOS/EOG zero. Actual real-output classification accuracy is unavailable without independent labels. Policy sources did not change after holdout access; the original four development examples were not reused for prompt optimization.

The new scoring unit is the identifiable first reply/prefix, with exact raw/excluded text retained. Separate factual categories, completeness, relevance, temporal consistency and coherence are stored. New bounded factual accounting: 1 Correct, 0 Incorrect, 5 Unverifiable, 0 Not Applicable; no scalar accuracy/effect claim. Legacy scores remain untouched. Unsupported claims and incomplete outputs are not automatically wrong.

The mandatory outstanding action is independent neutral-control review and resolution of findings. Natural termination, general semantic accuracy, upstream quantization fidelity and unavailable backend input-ID arrays are scope-qualified limitations. The policy-definition and bounded instrumentation work is now complete; future use must retain logged versions and independent annotation routing. Tests: **223 passed, 0 failed, 0 warnings reported, 13.28s, exit 0**. All 20 old journals are byte-identical, the new journal replays twice identically, and 140 raw responses are retained across 17 generation runs.


## 2026-10-12T20:13:26.793933+00:00 — Control validity and researcher annotation provenance

Session: `results/p0_neutral_validity/20261012T195226/`. Starting HEAD: `4d00ee1adbe538d24175d5c3e83c318bff8365a3`; initial working copy contained the researcher's untracked earlier CSV. New runs record actual dirty state and exact source snapshots. Preparation inventories were saved before experimental or historical-file changes.

Tokenizer-only run: `20261012T195708-1dc4429d05c94341bf5a92c6da48c020`, **756 chained events**, **238 tokenizations**, **0 completions**. Native request/response bodies, server log, `/props` binding, CPU launch arguments, configuration, pre/postflight hashes and exact prompt/ID arrays are retained. GGUF SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; server SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; b11573 / `0f701c882`; CPU 4/4, context 4096. Tokenizer options: add_special=true, parse_special=false, with_pieces=false. Generation parameters/raw/parsed responses are not applicable to this new run because no generation was requested; the inherited runtime seed/cap are logged but unused.

The historical `transcript_base_v1` prompts and IDs match 100/100. `neutral_control_candidate_v1_dev` / `control_candidate_prompt_v1_dev` was frozen before tokenization, with all 132 attempts retained; three history matches and three style failures. The dataset identifier in the new reconstruction is an analysis-local label; exact file SHA identifies the unchanged historical dataset. No token approximation or tolerance change was used.

All **21 historical journal inventories remain byte-identical**; all **22 current journals passed fresh chain validation**. Existing **140 raw generations across 17 generation runs** remain historical, with no new outputs. Annotation import replay reproduces the final registration excluding the new actual import time. Legacy scores and frozen response/evaluation policies remain unchanged. See [delivery evidence](validation/P0_neutral_validity_delivery_v1.json).

The prior source CSV, final researcher CSV and both registration records are separate. The final registration records reviewer identity from explicit researcher confirmation and final source metadata, no invented review time. Zero judgment edits between available snapshots does not establish zero edits from the unavailable initial AI/independent-pass versions. The declared intermediate source hash is preserved as an unverified link. Missing earlier versions limit edit-history reconstruction but do not erase the observed completed final review.

**263 passed, 0 failed, 0 warnings reported**, pytest **10.11s**, process **10.638s**, exit **0**. Actual test interval: `2026-10-12T20:08:42.850912+00:00` to `2026-10-12T20:08:53.488847+00:00`.

Engineering command/error captures are under `engineering/`; source/config/input freezes and original incoming files under `materials/`; backend HTTP journals under `experiments/`. The public [command index](validation/P0_neutral_validity_commands_v1.json) links summarized actions to full local logs. Initial uncaptured read-only commands retain tool-transcript provenance; their individual timestamps are not backfilled. All public additions use English and repository-relative paths.

The literature review used primary web sources. Access/query metadata are in [the access index](validation/P0_literature_access_v1.json); selected tool responses are preserved locally under `literature/`. Two unavailable guessed HTML URLs returned 404 and were replaced with available versioned PDF sources. A revised real-person simulation paper's new title/author list was detected and recorded without combining version-specific findings. Literature results were not independently reproduced and novelty remains unproven.


## 2026-10-12T20:45:56.264380+00:00 — Development control v2 validation

**P0 PARTIAL; P1 NOT STARTED.** [Full report](P0_control_development_report_v2.md), [selected controls](validation/P0_control_development_selection_v2.json), [all tokenizer observations](validation/P0_control_tokenizer_validation_v2.json), [new review guide](P0_control_development_review_v2_guide.md), [integrity audit](validation/P0_control_development_integrity_v2.json), [command index](validation/P0_control_development_commands_v2.json).

Objective: repair style matching while preserving the original wrapper, and separate history format, topic and old-fact-specificity controls. Candidate version `neutral_control_candidate_v2_dev`, prompt `transcript_base_v1`; six predetermined development cases, 420 candidate prompts, 444 native tokenizer requests, 24/24 matches, tolerance zero, no generations. The earlier 0/3 style failures are preserved, with observed length gaps diagnosed as pool coverage. No model answer was used for selection. New human review is 0/24 (18 alternatives plus 6 non-neutral diagnostics); old human review remains 40/40, with 40 PARTIAL overall suitability judgments. Review only transfers to its exact materials.

Session `results/p0_control_development_v2/20261012T202741`; run `20261012T203926-471064d78d6e4164a9f623c8d3ca9c09`; 1384 chained events. Git `4d00ee1adbe538d24175d5c3e83c318bff8365a3`, dirty true; 40 changes predated this task. Qwen3.5-2B-Base Q4_K_M SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; server SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; b11573 / `0f701c882`; configured CPU4/4, context4096, zero GPU layers. Pre/postflight identity and /props binding pass. New independent hardware measurements were not made. Seed42 and cap96 are inherited configuration only; generation parameters/output/parser/evaluation scores are not applicable to the tokenizer run. Frozen response/evaluation policies remain untouched.

New sources: `control_candidates_v2.py`, `control_review_v2.py`, `test_control_candidates_v2.py`, `p0_control_development_v2.py` and the v2 report utility. English reports, access/command indexes, candidate freeze/selection/tokenizer/integrity artifacts and blank review CSV/JSON are separate additions. Existing acceptance documents receive a current notice without removing historical text; development and reproducibility logs are appended. The related-work matrix gains a primary-source addendum; protocol, old prompts, raw generations, evaluations and old annotations remain unchanged.

**285 passed, 0 failed, 0 warnings reported**, pytest **15.44s**, process **16.106s**, exit **0**. Actual interval: `2026-10-12T20:40:50.776176+00:00` to `2026-10-12T20:41:06.881737+00:00`.

Actual earlier failure: targeted tests returned 16 passed/6 failed in0.36s, exit1, because newly serialized facts were tuples; fixed the new serializer to produce schema-compatible lists. Rerun22 passed in0.13s, exit0. Original schema/tests unchanged. A read-only request for nonexistent `schema.py` was corrected to `schemas.py`; PowerShell reported the error but returned0 after later reads. Full errors and exact actual command start/end times are retained in local engineering captures. Initial uncaptured read-only operations retain interface-transcript provenance; no missing timestamps are fabricated.

All 110 protected source/data/annotation files are unchanged; all 22 old journals retain the same members and bytes. All 23 chains pass; 24 new observations and deterministic matching decisions replay from saved IDs without re-inference. Existing140 generations/17generation runs remain intact. Freeze/source/config/input hashes and complete native HTTP response bodies support reconstruction; new scientific claims, perfect determinism and independent human semantic validation are not inferred. No Git mutation, P1, training or unrelated application access occurred.

Literature: three primary papers were inspected, with exact versions and access limitations in the [novelty addendum](related_work_novelty_matrix.md). Persona length/structure controls already exist. Character-versus-token wording in one paper was distinguished from independently verified exact matching. New controls are engineering improvements with unproven novelty. P0 remains open for semantic findings and defensible adoption of chosen replacement contrasts, not for perfect model behavior or review of every optional future diagnostic.


## 2026-10-12T20:50:38.420802+00:00 — Delivery checks and concurrent workspace provenance

The final source scan and Git diff whitespace check passed after a documented checker correction. The first delivery command exited1: its path scan matched its own diagnostic string and machine paths in an unchanged historical report body. The checker now uses a generic pattern for newly added content and separately verifies that the historical body remains byte-identical. No historical path/measurement was erased to obtain PASS. The failed capture remains at `results/p0_control_development_v2/20261012T202741/engineering/delivery_command.json`; corrected delivery exited0 in0.874s, with171 source/document text files scanned, zero prohibited product-name matches and zero broken local links at that checkpoint. Six Git CRLF-to-LF notices were reported, separate from the test suite's zero reported warnings. Final inventory/check results are in [the closure evidence](validation/P0_control_development_final_checks_v2.json).

Concurrent workspace activity was observed: files became staged and `docs/PersonaSLM_related_work_novelty_audit_2026-10-12.md` appeared after the starting inventory. Its SHA-256 is `8083dd74f44a60dc4b067e503737077d2fd1aaf6ed52f01c8ccbff8c653ffaeb`. The automated work did not add/stage, commit, push or alter Git identity/history, and did not edit this additional document. Its authoring/review claims are not attributed to this run. The earlier delivery artifact's field named `files_changed_this_task` is an **observed change-since-baseline inventory**, not an authorship claim; it includes this concurrently supplied file. The field name is corrected in the utility for future execution, and the final sidecar separates automated edits from concurrent additions without rewriting the earlier artifact.

The supplied literature audit was read. Three of its especially relevant primary records/abstracts (Principled Personas; One Persona, Many Cues; When Personalization Misleads) were independently checked, in addition to the three papers in the earlier v2 addendum. Full numerical/model details of all nine supplied studies were not reverified. The novelty matrix distinguishes these evidence levels. These checks strengthen the caution against generic novelty claims; they do not add experimental results or change Protocol v1.1.

No runtime source or tests changed after the complete suite:285 passed in15.44s, process16.106s, exit0. Subsequent changes are reporting/checker code and English documentation. Experimental frozen sources remain unchanged. P0 remains PARTIAL; existing40 human reviews remain complete, new review0/24 remains OPEN; only adopted controls require closure, not every unused diagnostic. No P1 or training was executed. The new run has444 tokenizations,1384 journal events and0 completions.


## 2026-10-12T20:51:18.989888+00:00 ? Concurrent Git HEAD observation

The final read-only check observed HEAD `e1da38723b310ff6a12b04e1164ac20bb12feb1f`, whereas the tokenizer run and starting snapshot recorded `4d00ee1adbe538d24175d5c3e83c318bff8365a3` with dirty state true. A concurrent external Git update occurred during this task. The automated workflow performed no staging, commits, pushes, identity changes or history rewrites. Original experimental commit/source snapshots are retained, not backfilled with the new HEAD. Current runtime-source hashes still match the experimental freeze; test validity is unchanged. The final structured checks record both the remaining working-copy changes and the concurrent document separately. All still-pending edits remain for maintainer review.


## 2026-10-12T21:09:15.271521+00:00 — Final control review preparation v3

**P0 PARTIAL; P1 NOT STARTED.** [Current validation report](P0_final_neutral_control_validation_report.md), [identification matrix](P0_control_identification_matrix_v3.md), [24-item English review](validation/P0_final_control_review_v3.csv), [import guide](P0_final_control_review_v3_guide.md), [per-item analysis](validation/P0_final_control_analysis_v3.json).

Offline audit reconciled all444 saved native tokenizer requests/responses with420 candidates and24 references. All24 selected pairs retain difference0 and their original wrapper/evidence/question. All23 historical journal inventories are unchanged. Twenty historical /health503 startup records were retained; no new model server, tokenization or completion was run. Original40 human reviews remain complete; new review0/24 remains OPEN. New v3 is a form version, not a prompt revision; all old masters, original prompts, source fixtures and evaluation policies are retained.

N_style still risks generic register/profile-heading effects. A changes topic and historical information. B changes question-answer to clarification, with address granularity added in3/6 replies. C removes six named old cities but retains vague prior-city residence, with temporal phrase changes in3/6; it is a diagnostic, not a neutral placebo. Precise variables and limited replacement estimands are now documented for every candidate. Protocolv1.1, title and primary contrasts are unchanged; no effect or originality claim is made. Four relevant primary sources were rechecked, including direct2B/3B precedent; five falsifiable proposals remain unexecuted future work.

**307 passed, 0 failed, 0 warnings reported**, pytest **17.08s**, process **17.773s**, exit **0**. Actual interval: `2026-10-12T21:03:02.125992+00:00` to `2026-10-12T21:03:19.899104+00:00`.

Targeted22 passed in0.89s. Actual blank-import command deliberately returned1 with `Incomplete human review: 0/24`; no review output was created. This is a successful negative validation, not a human annotation or silently discarded error. No corrective implementation changes were needed after this round's tests. New module `control_final_review.py`, its22 tests, offline audit/report tools, CSV/JSON master, evidence/analysis artifacts and English reports were added. Acceptance reports receive dated notices; old report bytes and all old validation artifacts remain preserved.

Session `results/p0_final_control_review/20261012T205559`. Initial Git `e1da38723b310ff6a12b04e1164ac20bb12feb1f`, dirty=true,19 preexisting paths; model `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`, backend `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` / `b11573-0f701c882` are references to the saved tokenizer run, not fresh binary/hardware measurements. Source-run Git/config/tokenizer options/prompt hashes/raw HTTP IDs are in [offline evidence](validation/P0_final_control_evidence_v3.json). Exact commands, times, outputs, exit codes, files and final integrity checks are in [delivery evidence](validation/P0_final_control_delivery_v3.json) and linked local captures. No commits, pushes, identity changes, P1, training or private-data access occurred.


## Researcher decision registration and lossless schema conversion

The source34-column CSV and an independently hashed byte copy are retained. All24 candidate IDs and overlapping materials match the official v3 CSV/JSON; prompt and material hashes are rechecked offline. The original40 annotations and new blank masters remain unchanged. [Registration report](P0_control_decision_registration_report.md); [immutable registration](validation/P0_final_control_researcher_registration_v1/registration.json); [conversion](validation/P0_final_control_researcher_registration_v1/annotation_65_columns.csv); [field confirmation inventory](validation/P0_final_control_researcher_registration_v1/confirmation_needed.csv).

Source SHA-256 `fbfa50099e8d5c55083a531d23d7bb1db1a41b42739f9ad0fa3e58ccccd637d0`; converted CSV SHA-256 `550e9e140995ac10dc6578c65e0a17ec63fc3b3da1a5b7a7db20cf213f10c651`. All336 source checks use the researcher's explicitly confirmed positive-question mapping. Decisions/notes remain verbatim. Only A's exact narrow-comparison acceptance supplies a categorical suitability PASS; other disposition semantics remain separate, with unresolved fields explicit. Per-field quote attribution and missing timestamps are never invented.

Registration is researcher-confirmed, AI-assisted and non-blind. Decision completeness24/24 PASS differs from detailed-schema PARTIAL:18 missing suitability labels,6 disallowed coherence N/A values and81 missing required per-axis quotes. The unchanged strict importer returned1 and created no completed-review output; successful decision registration returned0. Original human review time remains unknown; registration metadata is actual software metadata. No preliminary source, second reviewer or agreement statistic was fabricated.

Git HEAD `e1da38723b310ff6a12b04e1164ac20bb12feb1f`, dirty=true. Pre-change inventory covers189 repository-visible files and preserves original document bytes; source code and protocol preservation checks are in [delivery evidence](validation/P0_control_decision_delivery_v1.json). The11-stage engineering report retains stage organization and no calendar/clock/duration values; its prior version and prior validation digest remain archived.

No model process, tokenizer request, generation, new candidate selection or historical rescoring occurred. Existing model SHA `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`, backend SHA `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` and b11573 /0f701c882 are references to historical evidence, not fresh measurements. Effective prompt version, tokens and original native request evidence remain tied to v2 candidates and the v3 master. Tests:334 passed,0 failed,0 warnings reported, exit0. Full command captures are separate under `results/p0_researcher_decisions/registration_v1/engineering/`. P0 PARTIAL; no P1 or Git mutation.


## Narrow closure tokenizer and annotation reconciliation

Recorded 2026-10-12T22:11:11.449571+00:00; human review timestamps remain unknown/blank. HEAD `e1da38723b310ff6a12b04e1164ac20bb12feb1f`, dirty true. Candidate version `neutral_style_closure_v1_dev`, prompt `transcript_base_v1`, unchanged six-case dataset SHA-256 `2469c88daeddd5f91882ccdd670a18ed0a7c7b2e55926feba9f4b7bd8dfe1453`. Model `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` and backend `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` match both preflight and postflight. The [freeze](validation/P0_style_closure_freeze_v1.json) captures complete source/tool/config hashes and actual Git status.

One run `results/p0_control_closure/closure_v1/experiments/20261012T220311-55715491d1114a30ba52afa66d662bed`:78 native tokenizations,294 chained events,0 completions,5 exact matches and one FAILED at+1. Every native raw body is reconciled against saved IDs; no answer experiment is rerun. The [delivery audit](validation/P0_control_closure_delivery_v1.json) verifies23 earlier journal inventories and historical source/artifact hashes, plus the new chain and offline reconstruction. Original65-column conversion and original reviews remain unchanged; six derived A labels are explicitly not direct human ratings.

Full tests348 passed,0 failed,0 warnings reported,exit0; pytest reported21.17s, captured process duration21.867511899996316s. Both actual blank imports exit1 as intended and create no completed review. [Command captures](validation/P0_control_closure_commands_v1.json) retain exact execution metadata and sanitized public stderr; unredacted originals remain locally. The engineering narrative remains organized by stages without calendar/clock metadata. Raw timestamps are preserved, not fabricated or retroactively removed.

New control review remains0/6, A source confirmations0/18, categorical clarifications0/6. Byte-identical archival verification is not a claim of deterministic outputs, public availability of every raw journal, human agreement or complete semantic neutrality. P0 PARTIAL; no P1 execution or protocol amendment.


## Final scientific closure evidence

Recorded 2026-10-12T23:09:45.189401+00:00. New freeze `02c50725838edc9c0280c3297b52ff37b9b911264273c1fd5fec09ce520f4bed`, dataset `2469c88daeddd5f91882ccdd670a18ed0a7c7b2e55926feba9f4b7bd8dfe1453`, Git `e1da38723b310ff6a12b04e1164ac20bb12feb1f` dirty. The new Tessa run logs83 events,2 native tokenizations and0 completions; final counts99/99. All five accepted style prompts are copied unchanged from their reviewed master; six History A rows retain original prompts and native IDs. [Selected controls](validation/P0_final_selected_controls_v1.json), [registration](validation/P0_scientific_review_registration_v1/registration.json), [native result](validation/P0_tessa_minimal_tokenizer_v1.json) and [delivery inventory](validation/P0_final_scientific_delivery_v1.json) bind sources and configurations.

Full tests365 passed,0 failed,0 warnings reported,exit0. New researcher attestations remain distinct from original blank CSV fields and visible preliminary judgments; no blind-review or human timestamp is manufactured. Old model answers and policies remain immutable. New Tessa approval remains pending and P0 PARTIAL; no P1 execution or scientific effect estimate is produced.
