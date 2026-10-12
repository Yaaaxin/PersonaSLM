# P0 验收清单

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
