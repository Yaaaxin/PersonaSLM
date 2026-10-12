# P0 Reproducibility Report

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
