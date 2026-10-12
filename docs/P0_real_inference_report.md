# P0 真实推理准备与环境恢复报告

日期：2026-10-12。正式仓库：<https://github.com/Yaaaxin/PersonaSLM>。

论文题目保持为 **Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**。

**总体：PARTIAL。离线工程验证：PASS。真实模型推理验收：BLOCKED。**

本次没有真实 GGUF 推理结果。没有提供独立 Qwen GGUF、预期 SHA-256 或 `llama-server.exe`，因此没有启动真实服务、没有模型输出、没有速度/内存/准确率实验数据。自动化测试中的模型、Tokenizer 和 HTTP 响应替身仅用于软件测试。没有进入 P1，没有训练 LoRA，也没有读取或调用 MimooPet。

## 1. 环境验证

| 检查 | 状态 | 实际证据 |
|---|---|---|
| 当前目录 | PASS | `E:\DEVOIRS\Research\PersonaSLM-Lab\PersonaSLM-Lab-P0-v1.1\PersonaSLM-Lab` |
| PowerShell 执行 | PASS | `Get-Location`、Git、文件读写均成功；此前的 `helper_unknown_error: setup refresh had errors` 本次未复现 |
| 工作区文件写入 | PASS | 唯一临时文件写入、读取一致，随后只删除该探针文件 |
| Python 项目完整性 | PASS | `pyproject.toml`、`src/personaslm`、测试、协议、配置和 20 条合成案例存在；虚拟环境 Python 3.14.3；`pip check` 无依赖问题 |
| 系统 Python 别名 | PARTIAL | WindowsApps 下 `python.exe` / `py.exe` 无法执行；项目 `.venv/Scripts/python.exe` 正常。未修改系统安装或全局 PATH |
| 基线测试 | PASS | `34 passed, 1 warning in 0.41s`；警告为旧 pytest 缓存不可写 |
| 最终测试 | PASS | 当前进程 PATH 优先使用 `.venv/Scripts` 后执行 `python -m pytest -q`：`113 passed in 3.21s`，无警告 |
| 完整目录隔离审计 | PARTIAL | 未发现链接或 junction，但旧 `.pytest_cache` 目录拒绝读取：`[WinError 5] Accès refusé`；不能声称完整遍历通过 |

pytest 新缓存已配置到被 Git 忽略的 `results/.pytest_cache`，未删除旧目录或修改其 ACL。目录审计现在保留读取失败信息，而不会静默跳过后报告 PASS。

初始命令错误及每次测试摘要保存在 [环境记录](validation/P0_environment_transcript.txt)。最终实际命令输出及退出码保存在 [命令结果 JSON](validation/P0_command_results.json)。前两次 CLI 检查被 PowerShell 包装为退出码 1；后来显式 `exit $LASTEXITCODE` 确认应用的失败/不完整退出码为 2，两份证据均保留。

## 2. 已实现的 P0 工程

| 项目 | 工程状态 | 实现与边界 |
|---|---|---|
| 真实路径配置 | PASS | JSON 配置及 CLI 覆盖；相对路径基于研究根目录；禁止越界和 symlink/junction；不扫描或自动发现模型 |
| GGUF SHA-256 | PASS | 必须给出预期 64 位十六进制摘要，流式计算并逐字比较；文件缺失、摘要错误、非法头部阻止启动；当前只支持单文件 GGUF |
| CPU llama.cpp 适配器 | PASS | 显式启动配置中的独立可执行文件；固定线程、上下文和单 slot；禁用 GPU 层、设备卸载、KV/操作卸载及 context shift；离线启动；移除 `LLAMA_ARG_*` 环境覆盖 |
| 服务生命周期 | PASS | 拒绝已占用端口；有界健康等待；隐藏 Windows 子进程窗口；退出时只清理本次拥有的服务进程；记录参数、PID、版本输出、可执行文件摘要和服务日志 |
| 模型/Tokenizer 绑定 | PASS | `/props` 校验模型路径和上下文；记录 build 信息并支持校验声明的 revision；运行结束再次校验文件及服务身份 |
| 实际 Tokenizer 接口 | PASS | 使用同一服务的 `/tokenize`；显式 `add_special=true`、`parse_special=false`；拒绝伪造类型或非法 token IDs；完整 IDs 直接提交给 `/completion` |
| Token 数核对 | PASS | 生成前检查上下文预算；生成后必须返回匹配的 `tokens_evaluated` 及 `truncated=false`；返回 prompt IDs 时再核对 IDs |
| 中性文本匹配 | PASS | 在完整 Base 提示词上计数；N_style 对 C1、N_history 对 C3；保留证据、标题、行数和角色标签；默认容差 0、有界候选搜索，失败停止生成 |
| Raw Generation Logging | PASS | HTTP 原始字节先于 JSON 解码写入事件；保留请求、完整原生响应、特殊 token 支持状态、终止字段、时间；HTTP 错误及已收到的截断响应字节也保留 |
| Parser Audit | PASS | raw/parsed 分离；逐步记录操作前后文本、长度、摘要、空文本分类；区分 EOS、停止词、换行截断、去空白、去角色前缀、下游过滤；支持离线回放 |
| 运行清单与故障保留 | PASS | 每次独立 run ID、固定清单、源码/案例摘要、预生成 applicability、逐事件原子替换与 fsync、关联清单的摘要链；已有记录不会被下一次运行覆盖 |
| 自动化测试 | PASS | 113 项通过，包括本地 HTTP 传输、错误分支、清理、路径/摘要、匹配、日志完整性和解析回放；没有真实模型测试 |

适配接口依据 [llama.cpp 官方 server 文档](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) 核对。所用独立二进制的实际版本仍未提供，参数及返回字段兼容性必须通过将来的真实 P0 运行确认；不兼容时会保留错误并停止，不会绕过校验。

主要代码见 `configuration.py`、`server.py`、`inference.py`、`matching.py`、`journal.py`、`runner.py`、`diagnostics.py`。`configs/experiment_registry.yaml` 保留研究声明，实际运行配置为 `configs/p0_runtime.example.json` 的本地副本；尚未实现整个研究 YAML 的运行时冻结。

## 3. 真实执行结果与阻塞

| 命令 | 结果 | 解释 |
|---|---|---|
| `python -m pip check` | PASS，退出 0 | `No broken requirements found.` |
| `python -m pytest -q` | PASS，退出 0 | `113 passed in 3.21s` |
| `python -m personaslm validate` | PARTIAL，退出 2 | 20 个合成案例及 5 个 P0 条件验证完成；完整路径审计被旧缓存 ACL 阻塞 |
| `python -m personaslm smoke` | PASS，退出 0 | 5 个手写合成输入的 Parser 演示；不是模型回答 |
| `python -m personaslm preflight` | BLOCKED，退出 2 | `model_file and model_sha256 are required`；`server_file is required; no executable is auto-discovered` |
| `python -m personaslm run-local --condition C0` | BLOCKED，退出 2 | `completed_cases: 0`，`real_inference_performed: false`；未启动服务 |
| `python -m personaslm audit-run --run-dir …` | 日志完整性 PASS，运行 BLOCKED，退出 2 | 2 个事件：preflight 和 run_finished；没有 raw_generation 或 Parser 回放样本 |

实际阻塞运行保存在 `results/p0/20261012T152036-8e02b7e54df249fd8676da16b77bd7ca/`，含 `manifest.json` 及两个事件文件；该目录不上传 Git。其真实检查输出已保存到上述命令结果 JSON，因此不会把本地暂存日志误当作公开实验数据。

## 4. 尚未完成的真实验收

以下均为 **BLOCKED**：独立 Qwen GGUF 的实际摘要/架构/量化和 Base 身份；真实 llama.cpp build 的启动与加载；真实 Tokenizer 的特殊 token 行为；实际中性文本能否在给定预算内匹配；真实返回 token IDs/终止信息；CPU 运行日志和硬件观测；延迟及内存测量。

以下为 **PARTIAL**：中性文本的语义与操纵有效性仍需人工检查；EOS 分类依据返回的终止元数据及可见文本，不等于已证明单 token 直接 EOS；摘要链用于发现损坏或不一致，不是不可篡改存储或签名；断电/磁盘故障不能保证尚未完成写入的响应被保存。中断后的已有事件可读并可回放，但没有实现自动续跑或并发多写者恢复；不自动重试生成，避免重复回答被隐藏。

文件头及摘要校验不代替完整 GGUF tensor 校验。服务路径、文件摘要、受控子进程参数也不等于独立硬件层的 CPU-only 证明。当前事实评分器仅适用于合成城市更新案例，不能当作一般 factuality 指标。

## 5. Git 状态

### 当前状态：研究者已完成首次 GitHub 同步（PASS）

2026-10-12，研究者本人完成首次 Commit 和 Push，远端为 `https://github.com/Yaaaxin/PersonaSLM`。首次提交为 [`4a538570c77666009a609c1218a435ac52a6187a`](https://github.com/Yaaaxin/PersonaSLM/commit/4a538570c77666009a609c1218a435ac52a6187a)，Author 和 Committer 均为 **Yaxin ZHENG**；Git 记录的提交时间为 `2026-10-12T17:52:42+02:00`，提交说明为 `Initialize PersonaSLM research infrastructure`。

本次只读检查确认本地 `main` 和远端跟踪引用 `origin/main` 均指向该 SHA，修改前工作区干净。Push 完成事实由研究者确认；未取得精确 Push 时间，不能将提交时间当作 Push 时间。本次未联网刷新远端引用，也未执行 commit、push 或更改 Git 身份配置。AGENTS.md 已明确禁止 Codex 提交/推送，提交由研究者本人完成，并要求所有工程和实验变更记录可复现日志。详细记录追加在 [研究开发日志](research_development_log.md)。

### 历史快照：首次同步之前（保留原记录）

本地 `.git` 已存在，分支 `main`，没有历史提交；没有重新初始化、覆盖现有文件或导入其他项目历史。`origin` 已设为 `https://github.com/Yaaaxin/PersonaSLM.git`。

第一次写 `.git/config` 被沙箱拒绝，经授权后成功。沙箱内 GitHub 连接失败；随后仅进行一次经授权的沙箱外 `git ls-remote`，退出 0 且无 refs 输出，检查时远端没有分支/标签。未进行 push。

`.gitignore` 已覆盖虚拟环境、模型及分片、二进制、私人数据、聊天导出、临时实验、运行结果、本地配置及常见凭据文件。`data/` 只允许明确列出的合成案例进入版本控制；16 个代表路径的 `git check-ignore` 检查全部匹配。`test.txt` 原文件保留并忽略。全部交付文件保留在本地工作区，尚未 commit。

最终枚举了 43 个 Git 可见文件：未发现应被忽略的运行/私人目录、常见凭据签名或行尾空白。该检查仅覆盖 Git 可见文件和常见签名，不等于通用秘密检测。普通 `git diff --check` 对未跟踪文件不提供覆盖，因此另行检查了实际候选文件；新 `.gitattributes` 明确 LF 行尾。

## 6. 后续仅限完成 P0

将用户独立提供的模型和服务放在本研究目录内，在忽略的 `configs/p0_runtime.local.json` 填入 `model_file`、可信预期 `model_sha256`、`server_file`，并记录模型标签与引擎 revision。先完成离线预检，再进行单个 P0 条件的受控 smoke run；按清单补充真实证据。不得据当前测试推断 persona conditioning 对可靠性的研究效应。

首次 GitHub 同步完成后，下一步准备进行 **P0 真实模型验证**。本次检查时 `configs/p0_runtime.local.json` 尚不存在，示例中的三项必需输入仍为 null。取得独立 GGUF、可信预期摘要和独立服务二进制后，依次执行 README 中的 `preflight`、单条件 `run-local --condition C0` 与 `audit-run`，保留配置、完整日志、成功及失败信息；当前仍未开展真实模型实验，P0 总体 PARTIAL、真实推理 BLOCKED 不变，不进入 P1。
