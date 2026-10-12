# P0 Reproducibility Report

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
