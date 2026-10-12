# P0 验收清单

**Latest decision:** P0 PARTIAL. The [English methodology acceptance table](P0_methodology_acceptance_report.md) and the completion addendum at the end incorporate the budget diagnostic, versioned evaluation audit and pending human review. Earlier tables below are historical snapshots.

## P0 Final Validation：当前验收

**总体：PARTIAL。Adapter execution PASS 与 Research acceptance PASS 分开；尚不签署完整 P0 通过，P1 保持 BLOCKED。** 以下逐项覆盖 Protocol v1.1 中与 P0 有关的义务；未来阶段仅核对边界，不虚构实验完成。

| Requirement | Status | Evidence | Remaining limitation |
|---|---|---|---|
| 研究题目、独立 Real-Speaker 目标、0.8B–3B 范围 | PASS | 协议不变；仅 20 条虚构案例；实际 GGUF 后端报告 1.88B | 合成案例不证明真实说话者拟真 |
| 环境、虚拟环境、工程可执行 | PASS | 实际命令日志；123 tests passed | 全局 Python 别名问题保留，不影响项目 venv |
| 首次 C0 独立案例和日志链 | PASS | 原 run `20261012T163840-d0e467a28a4e4df89eb35ce788dfa917`；20 个独立案例；[逐例审计](validation/P0_case_audit.json) | 完成请求不等于事实正确 |
| 文件完整性与公开固定制品 | PASS | [来源报告](P0_model_provenance_report.md)：本地 GGUF/exe SHA；固定 HF revision API 的 LFS 摘要及大小 | exe 未独立构建或验证发布签名 |
| GGUF 元数据和实际加载 | PASS | `qwen35` / Base / Q4_K Medium；详细 server.log、/props | 元数据是文件自述，不能单独证明权重来源 |
| 上游官方模型关系及量化保真度 | PARTIAL | Qwen 官方 Base 仓库、第三方固定文件身份可追溯 | 缺上游固定权重 revision、转换/量化配方和独立对照 |
| CPU-only、4/4 threads、4096 context | PASS | 新运行日志实际报告 0/25 GPU layers，CPU model/KV/compute buffers，n_threads=n_threads_batch=4，n_ctx=4096；CIM 硬件信息 | 旧 C0 日志仅有部分观察；新观察不冒充旧运行时测量 |
| CPU/OS/RAM、延迟与内存记录 | PARTIAL | 硬件 8 核/16 线程、安装 16 GiB；逐响应时间和新进程内存采样 | C0 无历史内存；没有连续内存采样或受控性能 benchmark |
| 同一 GGUF tokenizer 和特殊 token | PASS | 同一受控进程 /tokenize；实际 probes；发送 IDs 与保存 IDs 一致 | 不使用字符数冒充 token 数 |
| 实际 evaluated IDs 与输入 IDs 独立逐项核对 | PARTIAL | 实际 evaluated count 相同、decoded prompt 可追溯、truncated=false | 后端未返回 evaluated input ID 数组；不伪造 |
| Track A 相同证据/问题、固定上下文 | PASS | 每案例证据摘要、最终 prompt；实际两组匹配 | 不适用于 Track B 信息可用性效应 |
| 中性控制完整 prompt 零容差匹配 | PASS | [三轮匹配记录](validation/P0_control_matching.json)；最终 40 对 delta=0；256 候选上限未变 | 原 v1/v2 style 失败分别 −3/−1，均保留；候选顺序经 P0 工程修正 |
| 中性语义与残余操纵检查 | PARTIAL | 检查实际文本，无已知城市泄漏、证据/问题/日期未变；[盲审文件](validation/P0_neutral_blinded_review.jsonl) | 无独立人工判定；重复句子、style heading、历史日期包装可能有残余影响 |
| 预生成 applicability、按规则冻结样本 | PASS | `selection_freeze.json`；001–003 首批、004–020 扩展；不按输出好坏选样 | 只用于 P0；不等于 confirmatory freeze |
| Raw / parsed / stop / IDs / filtering 日志 | PASS | 原始 HTTP 字节、native JSON、逐例输出、Parser 操作链 | 原始忽略目录由研究者保管；中断未完成写入不保证持久化 |
| Parser 五类区分 | PASS | 单元测试和实际解析回放；没有将空响应直接归为模型故障 | 真实观察没有覆盖所有五种故障；合成测试不是自然发生频率 |
| 窄域事实评分与错误解释 | PARTIAL | 原评分结果完整保留；[疑似误判案例](validation/P0_evaluator_review.json) | dated “lived in … in YEAR” 可能被误判为当前冲突；需要版本化修正和独立复核，不中途改评分器 |
| 四个可靠性维度与 Persona Fidelity 分离 | PASS | Protocol / annotation guidelines / applicability | 本次未完成开放式盲评、真实说话者 fidelity 或标注一致性；不声称已完成 |
| Git/source/data/model/backend/template/seed provenance | PARTIAL | 新 manifest 有 Git 状态与精确输入/源码快照；[可复现性报告](P0_reproducibility_report.md) | C0 未记录 Git dirty state / commit；历史 prompt SHA 仅事后重建 |
| 日志完整性、离线重建重复核对 | PASS | `audit-run`、`replay-run`；全部生成运行的二次重建结果见结构化证据 | 离线 replay 不重新生成模型输出；日志未数字签名 |
| 原始实验记录不覆盖、失败可追溯 | PASS | 原 C0 文件摘要清单；匹配失败、CIM/网络拒绝、README 404、重放开发错误分别保留 | 公开派生报告不替代完整原始归档包 |
| 软件自动化测试 | PASS | 123 passed，0 failed，0 warnings；pytest 18.97s，进程墙钟 20.55s，退出 0 | 与推理并行时测得，不是性能基准 |
| Git 人工提交与首次同步历史 | PASS | AGENTS.md 四项规则仍正确；首次 SHA `4a538570c77666009a609c1218a435ac52a6187a` 历史保留 | 当前源代码/文档均未提交；Codex 不 commit/push |
| 数据隔离、路径与隐私 | PARTIAL | 仅项目内合成数据、独立模型；无 MimooPet 访问；忽略模型/私有数据/结果/凭据 | 旧 `.pytest_cache` ACL 阻塞完整目录审计，历史失败不删除 |
| 效应分析、统计推断、确认性冻结 | BLOCKED | 本次仅工程观察；不报告 Persona 改善/损害、历史因果效应或一般事实能力 | P1 及后续阶段待 P0 接受后另行授权；本项非本次应执行实验 |
| Track B、自然数据、oracle、跨模型、LoRA | BLOCKED | 遵守协议阶段边界，没有实施 | 属于未来 P2–P6；不得把未开展阶段记作完成 |

详细结果、确切 run IDs、逐例输出及 remaining blockers 见 [P0_final_validation_report.md](P0_final_validation_report.md)。本表保留所有尚未人工或独立验证的内容为 PARTIAL/BLOCKED。

## 历史快照：模型尚未提供时的清单（保留）

日期：2026-10-12。

论文：**Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**。

**当前 P0 总体为 PARTIAL；真实推理验收为 BLOCKED，不能签署完整 P0 通过。**

PASS 表示已在注明范围内实际验证；PARTIAL 表示存在明确缺口；BLOCKED 表示缺少必要输入或运行条件。软件测试 PASS 不替代真实模型验收。

| 验收项 | 状态 | 证据 / 剩余条件 |
|---|---|---|
| 工作目录正确、PowerShell 可执行、工作区可写 | PASS | 环境探针通过；原 unified exec 错误未复现 |
| 现有 Python 工程及依赖完整 | PASS | `.venv` Python 3.14.3，`pip check` 通过 |
| `python -m pytest -q` | PASS | 项目虚拟环境 PATH 下 113 passed，3.21s，无警告 |
| 全局 `python`/`py` 别名 | PARTIAL | WindowsApps 别名不可执行；使用 `.venv` 可继续开发 |
| 合成案例与研究主题保持 | PASS | 20 条合成案例；可信证据、固定上下文、预生成 applicability 保留；论文题目未变 |
| 完整目录审计 | PARTIAL | 未发现链接；旧 `.pytest_cache` 读取失败，错误已保留；新缓存正常 |
| Git 初始化检查 | PASS | `.git` 已存在、`main`；保留原文件；无历史提交 |
| Git 远端配置 | PASS | origin 指向 `Yaaaxin/PersonaSLM`；一次沙箱外只读检查成功，无 refs |
| 首次 GitHub 同步（2026-10-12 更新） | PASS | 上述两项中的“无历史提交 / 无 refs”为同步前快照，保留原记录。研究者 Yaxin ZHENG 已完成首次 Commit 和 Push；SHA `4a538570c77666009a609c1218a435ac52a6187a`，本地 `main` 与 `origin/main` 一致 |
| Git 与可复现日志规则检查 | PASS | AGENTS.md 已禁止 Codex commit/push，提交由研究者本人完成，所有工程及实验变更须记录可复现日志 |
| Git 忽略规则 | PASS | 16 个代表路径检查通过；模型、私人数据、结果、凭据、`.venv` 被忽略 |
| 文件路径配置与边界校验 | PASS | 显式 JSON/CLI，拒绝越界/链接；不自动寻找模型 |
| GGUF 摘要验证代码 | PASS | 正确摘要、错误摘要、篡改、坏头部、缺失配置等测试通过 |
| 真实 GGUF 与预期摘要 | BLOCKED | 用户尚未提供；不得使用其他项目模型 |
| CPU 服务适配与生命周期代码 | PASS | CPU 参数、健康等待、端口冲突、异常清理测试通过 |
| 真实 llama-server 启动与版本兼容 | BLOCKED | 独立二进制未提供，未启动真实进程 |
| 真实 Tokenizer 接口和计数代码 | PASS | 完整提示词调用 `/tokenize`，IDs 直接作为输入，核对实际计数/截断 |
| 真实模型 Tokenizer 验证 | BLOCKED | 未发生任何真实 tokenization |
| 中性文本长度/格式匹配代码 | PASS | 有界候选搜索，容差固定，保留格式/证据；失败拒绝生成 |
| 实际中性文本长度及语义匹配 | PARTIAL | 真实长度匹配被模型缺失阻塞；操纵和语义中性仍需人工审阅 |
| Raw Generation Logging 代码 | PASS | 原始 HTTP 字节先持久化；完整响应及错误保留；日志摘要链和不可覆盖清单 |
| 真实 raw generation 日志 | BLOCKED | 当前真实生成数为 0；只有缺少配置的阻塞运行日志 |
| Parser Audit 和离线回放 | PASS | 五类诊断、前后文本、操作链、摘要、回放及错误保留有测试 |
| 真实 CPU-only、延迟、内存与终止行为 | BLOCKED | 必须获得真实服务日志和独立观测，不以启动参数代替测量 |
| 崩溃后的事件保留与重复运行区分 | PASS | 独立 run ID；已完成事件可验证；未完成运行不伪报通过 |
| 自动续跑与并发恢复 | PARTIAL | 尚未实现；每次运行独立，不自动重试生成 |
| P0 报告与失败证据 | PASS | 两份要求的 Markdown 报告及环境/命令证据文件已生成 |
| 进入 P1 / LoRA / 实验效应结论 | BLOCKED | 本次不开展；完整 P0 尚未验收 |

## 完成真实 P0 所需输入

1. 研究目录内独立的单文件 Qwen Base GGUF，以及可信的预期 SHA-256、模型来源/架构/量化信息。
2. 研究目录内独立的 `llama-server.exe`，及其依赖和对应 llama.cpp revision。
3. 填好的 `configs/p0_runtime.local.json`，保留本地，不上传实际机器路径。

运行示例见 [README](../README.md)。`preflight` 只检查本地文件；`run-local` 在检查通过后管理自己的 CPU 服务。服务已占用端口时停止，不接管已有进程。

## 可复核证据

- [完整报告](P0_real_inference_report.md)
- [环境错误与测试阶段记录](validation/P0_environment_transcript.txt)
- [实际命令输出、退出码及阻塞运行](validation/P0_command_results.json)
- 本地 `results/p0/20261012T152036-8e02b7e54df249fd8676da16b77bd7ca/`：零生成，日志完整性 PASS，运行状态 BLOCKED。

Research Design Freeze：YES。Confirmatory Experiment Freeze：NO。真实 P0 sign-off：BLOCKED。

## 2026-10-12 Methodology Completion Addendum

Recorded: 2026-10-12T18:06:22.204470+00:00. Earlier history is retained.

**Overall P0 research acceptance: PARTIAL.** The [complete English requirement table](P0_methodology_acceptance_report.md) supersedes the earlier snapshots for current status. Adapter execution PASS is distinct from research acceptance.

| This session's requirement | Status | Evidence | Remaining limitation |
|---|---|---|---|
| Frozen 96/192/256 budget diagnostic | PASS | 18 actual CPU responses, same 3 cases under C0/C3; only budget changes | All 18 stop at limit, no EOS/EOG; natural response termination unresolved |
| Prompt/config/token/raw/parsed/latency logging | PASS | Per-case hashes and full [diagnostic artifacts](validation/P0_budget_diagnostic.json) | Structural completeness flags do not replace human semantics |
| Existing 40 zero-difference controls | PASS | Original prompt freeze and matching records retained | Length matching alone does not certify neutrality |
| Independent neutral semantic review | PARTIAL | English 40-item CSV/JSON with all six checks | 0/40 independent human reviews completed |
| C3 original 14 incorrect outputs audited | PASS | Separate [versioned claim audit](validation/P0_evaluation_audit_v2.json) and regression tests | No silent replacement of original scores |
| Independent factual/temporal ground truth | PARTIAL | 2 city/time contradictions, 11 unverifiable, 1 supported by supplemental rules | Agent/rule audit is not independent human adjudication |
| All-run integrity and repeat offline reconstruction | PASS | 19 journals; 15 generation runs / 118 responses; two identical reconstructions | Offline replay, not new inference; hashes are unsigned |
| New-run Git commit and dirty state | PASS | All six manifests retain SHA, dirty=true and exact implementation snapshots | Original C0 missing fields remain missing |
| Automated tests | PASS | 147 passed, 0 failed, 0 warnings; exit 0; 18.07s pytest | Earlier 1-failed/146-passed record retained and fixed |
| English scope without historical alteration | PASS | Dated protocol addendum; original English synthetic inputs unchanged | No retrospective translation or new naturalistic data |
| Human-only commits/pushes | PASS | AGENTS unchanged; all session changes uncommitted | Researcher review and submission still required |
| Overall P0 sign-off | PARTIAL | All remaining limits listed in current acceptance report | Independent review and unresolved methodology limits remain |
| P1 entry | BLOCKED | Current task remains P0 only | Do not start P1 or infer Persona effects |

Prior model-lineage, independent evaluated-input-ID, historical provenance and archive-access limitations remain in force. No LoRA training or MimooPet access occurred.
