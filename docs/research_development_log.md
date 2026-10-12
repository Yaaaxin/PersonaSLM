# PersonaSLM Research Development Log

论文：**Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**。

研究协议：**v1.1**。当前阶段：**P0 — Pipeline / Parser Validation**。

提交与推送由人类研究者独占管理。工程改动保持未提交，等待人工审阅。完整仓库规则见 [AGENTS.md](../AGENTS.md)。

本日志区分工程检查与模型实验，保留失败和未完成事项。新增记录应包含带时区的实际日期时间、阶段、修改文件、命令、测试结果、配置、错误及修复、科学局限。历史补录应注明来源和缺失信息，不能将补录时间写成实验发生时间。

## 2026-10-12 — P0 环境恢复与工程开发（历史补录）

**日期与时间：**开发日期为 2026-10-12；原命令记录没有保存每条命令的绝对开始/结束时间，无法补齐。一个可核验的时间锚点是阻塞运行清单中的 `created_utc=2026-10-12T15:20:36.533383+00:00`，即 Europe/Paris 的 17:20:36.533383。它只是该次运行清单的创建时间，不是整个开发阶段的起止时间。本条在 2026-10-12 17:41:45 +02:00 开始的文档维护中补录。

**研究阶段：**P0。总体验收 PARTIAL，真实推理 BLOCKED。工作基于已有 Python 工程和 20 条合成案例；没有重建其他项目的代码或历史。

**证据来源：**本次会话已执行的修改和命令，以及保留的 [环境记录](validation/P0_environment_transcript.txt)、[命令结果 JSON](validation/P0_command_results.json)、[P0 报告](P0_real_inference_report.md)、[验收清单](P0_acceptance_checklist.md)。下列命令按用途归类补录，不冒充带完整时间戳的逐条执行轨迹；工具输出中的 `wall_time_seconds` 是工具等待/执行记录，不是模型推理性能测量。

**修改文件：**

| 文件 | 变更 |
|---|---|
| `.gitignore`；新增 `.gitattributes` | 排除环境、模型、私人数据、运行结果和凭据；声明文本行尾 |
| `pyproject.toml` | pytest 缓存改到 `results/.pytest_cache`，保留原目录 |
| `configs/experiment_registry.yaml`；新增 `configs/p0_runtime.example.json` | 保留设计声明，增加显式 P0 运行配置与缺少真实模型的状态 |
| `src/personaslm/cli.py` | 配置覆盖、预检、摘要计算、受控运行与离线审计命令 |
| `src/personaslm/inference.py` | 原生 HTTP 适配、Token IDs、原始响应字节与终止信息保留 |
| `src/personaslm/conditioning.py` | 中性条件允许受控替换附加文本 |
| `src/personaslm/diagnostics.py` | Parser 操作链、原始/解析文本、摘要和空输出分类 |
| `src/personaslm/provenance.py` | 路径/链接校验，显式记录不可读取目录 |
| 新增 `src/personaslm/configuration.py` | 显式路径、参数、GGUF 头部和预期 SHA-256 校验 |
| 新增 `src/personaslm/server.py` | 拥有独立 CPU 服务子进程、参数/版本记录、健康等待与清理 |
| 新增 `src/personaslm/matching.py` | 完整提示词的有界中性文本 Tokenizer 匹配 |
| 新增 `src/personaslm/journal.py` | 清单、原子事件文件、摘要链和读取校验 |
| 新增 `src/personaslm/runner.py` | 预生成检查、原始生成日志、Parser 审计、有限评分和故障保留 |
| `tests/conftest.py`、`tests/test_diagnostics.py`、`tests/test_provenance.py` | 扩展临时目录、解析与目录审计测试 |
| 新增 `tests/test_configuration.py`、`tests/test_http_adapter.py`、`tests/test_matching.py`、`tests/test_journal.py`、`tests/test_runner.py`、`tests/test_server.py`、`tests/test_cli.py` | 配置、HTTP、匹配、日志、执行链、子进程和 CLI 测试 |
| `README.md`、`docs/P0_status.md` | 同步实际使用方法和验收边界 |
| 新增 `docs/P0_real_inference_report.md`、`docs/P0_acceptance_checklist.md` | 按 PASS / PARTIAL / BLOCKED 交付 |
| 新增 `docs/validation/P0_environment_transcript.txt`、`docs/validation/P0_command_results.json` | 保存错误、测试摘要和实际命令输出 |
| `.git/config` | 上一轮根据当时明确授权添加 origin；没有修改作者/提交者配置 |
| 忽略的本地文件 | 写入探针已单独清理；新增 `.local/p0_final_audit.py`、`.local/p0-evidence-validated.json`、测试缓存，以及 `results/p0/20261012T152036-8e02b7e54df249fd8676da16b77bd7ca/` 阻塞运行清单和两个事件 |

研究协议、论文题目及既有合成案例没有修改。原 `test.txt` 保留并加入忽略规则。

**执行命令和操作：**

- 环境/文件检查：`Get-Location`；`Get-Command python,py,git`；`Get-ChildItem`；`Get-Content`；`rg --files` 与定向 `rg -n`；唯一文件的写入/读取/删除探针。读取均限研究目录、仓库指令查找和既有环境信息。
- Python 定位：`python --version`、`py -3 --version`、`python -m pytest -q` 在系统别名下失败；随后使用 `.\.venv\Scripts\python.exe`。只在相关 PowerShell 进程内将 `.venv/Scripts` 加入 PATH 前部，没有修改全局 PATH。
- 基线及回归：`.\.venv\Scripts\python.exe -m pytest -q`；中间使用 `-p no:cacheprovider`；缓存配置修复后运行字面命令 `python -m pytest -q`。
- 工程命令：`python -m pip check`；`python -m personaslm validate`；`python -m personaslm smoke`；`python -m personaslm preflight`；`python -m personaslm run-local --condition C0`；`python -m personaslm audit-run --run-dir results/p0/20261012T152036-8e02b7e54df249fd8676da16b77bd7ca`。此处 `python` 表示项目虚拟环境解释器。
- Git 检查：`git status --short --branch`、`git remote -v`、`git ls-files`、`git diff --check`、`git diff --no-index --check -- NUL src/personaslm/runner.py`；使用 `git check-ignore --no-index -v` 检查 16 个代表路径。
- 上一轮远端配置：`git remote add origin https://github.com/Yaaaxin/PersonaSLM.git`，沙箱权限失败后经批准执行成功。其后设置当前进程 `GIT_TERMINAL_PROMPT=0`，执行 `git -c credential.interactive=never -c http.connectTimeout=10 -c http.lowSpeedLimit=1 -c http.lowSpeedTime=15 ls-remote https://github.com/Yaaaxin/PersonaSLM.git`：沙箱内连接失败，仅一次经批准的沙箱外检查成功且无 refs。没有 commit、push 或身份配置更改。
- 文件编辑：使用 `apply_patch` 和指定路径的 PowerShell 文本写入；曾有一次同路径 delete/add patch 被工具拒绝，修正后成功，拒绝时没有文件修改。
- 最终文件检查：`.\.venv\Scripts\python.exe .local/p0_final_audit.py`；`.\.venv\Scripts\python.exe -m json.tool docs/validation/P0_command_results.json --no-ensure-ascii --compact`，后者输出到忽略的 `.local/p0-evidence-validated.json`。
- 外部接口核对：读取 [llama.cpp 官方 server 文档](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)，仅用于实现依据，不构成真实二进制兼容性验证。

**测试与检查结果（历史实际输出，未在本次文档维护重跑）：**

| 检查 | 实际结果 |
|---|---|
| 初始基线 | `34 passed, 1 warning in 0.41s` |
| 中间回归 | `34 passed in 0.37s`；`104 passed in 2.35s`；`107 passed in 2.77s` |
| 最后一次完整测试 | `113 passed in 3.21s`，退出 0，无警告 |
| 依赖检查 | `No broken requirements found.`，退出 0 |
| 合成案例检查 | 20 个案例、5 个 P0 条件；完整目录审计 PARTIAL，应用退出 2 |
| Parser smoke | 5 个人工构造输入，退出 0；不是模型生成 |
| 真实模型预检 | BLOCKED，应用退出 2；缺少模型、预期摘要、独立服务二进制 |
| 实际 `run-local` 尝试 | BLOCKED，退出 2；`completed_cases=0`，`real_inference_performed=false` |
| 阻塞运行审计 | 日志完整性 PASS；2 个事件；运行 BLOCKED；没有生成/Parser 回放记录；退出 2 |
| 忽略规则 | 16 个代表路径均匹配 |
| 最终候选文件检查 | 当时 43 个 Git 可见文件，未发现常见凭据签名、运行/私人目录或行尾空白；不等于通用秘密检测 |

**实验配置：**以下为预检时的声明配置，不是已执行的模型实验。`model_file=null`、`model_sha256=null`、`server_file=null`、`engine_revision=unprovided`、标签 `unconfigured-qwen-base`；条件 C0；20 条合成案例；seed 42；4 CPU threads；n_ctx 4096；max_new_tokens 96；endpoint `http://127.0.0.1:8080`；请求超时 180 秒；启动超时 120 秒；token_tolerance 0；max_match_candidates 256；模板 `transcript_base_v1`；parser `p0_parser_v2`；matcher `neutral_sentences_v1`。预期解码 temperature 0、top_p 1、无额外停止词，Tokenizer 预期 add_special=true / parse_special=false。由于预检已停止，以上推理请求参数没有交给真实模型执行。

**错误与修复：**此前用户报告的 `helper_unknown_error: setup refresh had errors` 本次没有复现。WindowsApps Python 别名不可执行，改用已存在的虚拟环境。旧 `.pytest_cache` 存在权限错误，迁移新缓存位置而不删除旧文件或修改 ACL；目录审计仍为 PARTIAL。Git 配置与网络受沙箱限制的失败按授权各作一次必要升级处理。初始 stdin 忽略规则探针缺少首尾两条输出，改用直接参数确认全部 16 条。未跟踪文件 diff 的行尾警告通过 `.gitattributes` 处理；其退出 1 表示存在差异，不能伪记为应用测试失败。PowerShell 早期包装 CLI 退出状态为 1，后用 `exit $LASTEXITCODE` 保留应用退出 2；两种原始记录均保留。

**科学局限：**没有真实模型、真实 Tokenizer 计数、CPU 硬件观测、延迟/内存或模型准确率结果。测试中的固定回复、字节头部和 Tokenizer 替身不能当作实验数据。中性文本仍需真实分词器和人工语义审阅；文件头/摘要不证明完整 tensor 与模型身份；CPU 启动参数不等于硬件层证明；城市评分器只适用于窄合成任务。无自动续跑或并发写恢复，日志摘要链不等于签名或不可篡改存储。没有开始 P1、训练 LoRA 或访问 MimooPet。

## 2026-10-12T17:41:45+02:00 — 仓库规则落地与开发日志建立

**日期与时间：**首个环境检查实际输出 `2026-10-12T17:41:45.0194393+02:00`（Europe/Paris）；后续配置/清单读取的时间检查为 `2026-10-12T17:42:11.4136968+02:00`。这些时间对应文档维护，不对应旧工程或实验的执行时间。

**研究阶段：**P0 文档与工程来源记录；不开展新的模型实验。

**修改文件：**新增根目录 `AGENTS.md`，保存用户提供的仓库规则；新增本文件 `docs/research_development_log.md`，补录可核验的 P0 开发经历并建立后续记录要求。应用源码、配置、合成数据和历史证据文件均未修改。

**执行命令/操作：**`Get-Date -Format o`、`Get-Location`；`Get-Item -LiteralPath AGENTS.md,docs/research_development_log.md -ErrorAction SilentlyContinue`；`git status --short --branch`；`rg --files --hidden -g AGENTS.md`（排除 `.git`、`.venv`、`results`、`.local`）；`Get-Content -LiteralPath` 读取上述环境记录、P0 状态、命令证据、配置示例和指定阻塞运行的 `manifest.json`；使用 `apply_patch` 创建这两份文档。创建前两个目标文件均不存在。

**测试结果：**本次只有文档变更，不重跑 Python 测试，也不将历史 113 项测试标为本次新结果。文档落地检查已通过，结果如下。

**实验配置：**没有新的实验配置或模型请求。原示例中的模型、摘要和服务路径仍为空；读取的阻塞清单属于上一轮。

**错误与修复：**尚无本次新增的执行错误。历史缺失的命令时间戳明确标为未知，未编造；已有失败记录未覆盖或删除。

**科学局限与 Git 状态：**没有新增实验测量或研究结论，P0 的真实推理 BLOCKED 状态不变。检查时为 `main`、`No commits yet`；没有执行 commit、push、历史重写或作者/提交者配置变更，所有改动保持未提交，供人类研究者审阅。

**落地验证：**检查完成后的 `Get-Date -Format o` 为 `2026-10-12T17:45:07.2419432+02:00`。通过 PowerShell 单引号 here-string 将只读 Python 检查传给 `.\.venv\Scripts\python.exe -`：检查 11 个关键规则字符串、日志中的 5 个本地 Markdown 链接、两份新文档的行尾和末尾换行，并逐一比较 `src/personaslm` 的 15 个文件与先前阻塞运行清单中的 SHA-256。没有写入新实验数据。随后执行 `Get-Date -Format o`、`git status --short --branch`、`git diff --check`；命令组退出 0。实际检查输出：

```json
{"documentation_check": "PASS", "rule_checks": 11, "local_links_checked": 5, "source_files_matching_prior_manifest": 15, "pytest_rerun": false}
```

源码摘要全部一致。Git 仍为 `No commits yet on main`，新增 `AGENTS.md` 未跟踪，`docs/` 等现有改动继续保留本地。`git diff --check` 没有输出；由于文件尚未跟踪，文档空白检查依靠上述直接读取验证，不将空 diff 当作完整覆盖。

## 2026-10-12T17:57:42+02:00 — 研究者首次 GitHub 同步确认与 P0 文档修正

**日期与时间：**本次检查开始于 `2026-10-12T17:57:42.4654197+02:00`（Europe/Paris）。首次提交的 AuthorDate 和 CommitDate 均为 `2026-10-12T17:52:42+02:00`。研究者确认首次 Push 已完成，精确 Push 时间未记录，不能以提交时间代替。此前的未提交/未推送记录描述当时的真实状态，全部保留，不用当前状态改写历史。

**研究阶段：**P0 文档修正与真实模型验证准备。GitHub 同步 PASS；完整 P0 验收仍为 PARTIAL，真实模型推理仍为 BLOCKED。

**同步事实与来源：**

| 项目 | 事实 / 证据 |
|---|---|
| 远端仓库 | `https://github.com/Yaaaxin/PersonaSLM` |
| 首次 Commit SHA | `4a538570c77666009a609c1218a435ac52a6187a` |
| Author / Committer | Yaxin ZHENG / Yaxin ZHENG |
| 提交说明 | `Initialize PersonaSLM research infrastructure` |
| 首次提交属性 | `git log` 的 parent 字段为空，是根提交 |
| 本地引用 | `main`、`origin/main` 都指向首次提交；初始 `git status --short --branch` 仅输出 `## main...origin/main`，工作区干净 |
| Push 完成依据 | 研究者明确报告已完成 Push，并有本地远端跟踪引用佐证；本次没有联网刷新或读取实时 GitHub 状态 |
| 操作者 | Commit 与 Push 由研究者本人完成；Codex 本次只读检查 Git 和准备文档变更 |

**修改文件：**`README.md`、`docs/P0_real_inference_report.md`、`docs/P0_acceptance_checklist.md`、`docs/P0_status.md`、本文件 `docs/research_development_log.md`。在当前说明中增加首次同步事实，并将旧说明明确标为历史快照；本日志仅追加本条。旧测试证据、阻塞运行清单和历史日志未修改。应用源码、测试代码、实验配置及数据未修改。

**AGENTS.md 检查：PASS，无需修改。**现有条款包括 `Execute git commit.` 和 `Execute git push.`（均在 `Codex must NOT` 下）、`The human researcher exclusively manages Git commits and pushes.`、`Every engineering and experimental change must be documented.`，并指定维护本日志，记录日期时间、阶段、文件、命令、测试、配置、错误及科学局限。这四项要求已正确表达；所有此次文档改动继续由研究者审阅并提交。

**已执行的检查命令/操作：**

- `Get-Date -Format o`；`Get-Content -LiteralPath` 读取 `AGENTS.md`、README、三份 P0 文档、本日志和 `configs/p0_runtime.example.json`。
- `git status --short --branch`；`git log -1 --format=fuller`；`git log -1 --format=fuller 4a538570c77666009a609c1218a435ac52a6187a`；`git log -1 --format=oneline --decorate refs/remotes/origin/main`。
- `git log -1 --format="%H%n%an%n%aI%n%cn%n%cI%n%P%n%s" HEAD`，核对 SHA、作者、提交者、时间、父提交及说明。
- 定向 `rg -n` 检查上述文档中的 Git 状态和可复现性条款；`Test-Path -LiteralPath configs/p0_runtime.local.json` 返回 `False`。
- 使用 `apply_patch` 修正文档；没有执行 `git commit`、`git push`、暂存、历史重写或任何身份配置写入。

**测试结果：**文档修改后重新执行 `.\.venv\Scripts\python.exe -m pytest -q`，实际输出为 `113 passed in 4.49s`，退出 0，无警告。命令前后 `Get-Date -Format o` 分别为 `2026-10-12T18:00:08.2309244+02:00` 和 `2026-10-12T18:00:13.7268251+02:00`；4.49 秒是 pytest 报告的测试耗时，不是模型推理测量。历史的 `113 passed in 3.21s` 保留为上一轮结果。

**实验配置与准备：**没有新增实验配置，示例中 `model_file`、`model_sha256`、`server_file` 仍为 null，实际 `configs/p0_runtime.local.json` 尚不存在。后续取得研究目录内独立单文件 Qwen Base GGUF、可信 SHA-256、独立 llama-server.exe 和引擎 revision 后，填写被忽略的本地配置，先运行离线 `preflight`，再执行单条件 C0 的真实 P0 验证并 `audit-run`。保留原始响应、Token IDs、终止信息、Parser 操作、CPU 参数/日志及失败事件，不依据测试替身推断真实模型行为。

**错误与修复：**将首次同步前的 Git 描述标记为历史并添加当前事实，修复当前状态说明过时的问题。检查命令截至本条创建时没有新增错误；没有虚构精确 Push 时间，也没有覆盖原始工程历史。

**科学局限：**GitHub 同步仅确认工程版本的保存与协作基线，不是模型实验或 P0 真实推理通过证明。本次未启动真实模型、未访问 MimooPet、未训练 LoRA；保持 Research Protocol v1.1，P0 验收前不开始 P1。

**本次测试原始输出：**

```text
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 4.49s
```

**P0 准备预检：**另执行 `.\.venv\Scripts\python.exe -m personaslm preflight`，以 `exit $LASTEXITCODE` 保留退出码 2，结果 BLOCKED。返回的两项原始原因分别为 `model_file and model_sha256 are required` 和 `server_file is required; no executable is auto-discovered`；`model` 与 `server` 均为 null。该命令仅做离线文件配置预检，没有模型下载、Tokenizer 调用或推理。此结果是必要输入缺失的真实记录，不是已完成真实模型验证。

**差异检查：**执行 `git diff --check`、`git diff --stat` 以及对 README 和三份 P0 文档的 `git diff -- <paths>`，命令组退出 0，没有空白错误；只有上述 5 份 Markdown 文件变更。

**历史保留及最终状态验证：**通过 PowerShell 单引号 here-string 将只读检查传给 `.\.venv\Scripts\python.exe -`；内部用 `git show HEAD:docs/research_development_log.md` 读取已提交日志并确认它是当前日志的完整前缀，检查 AGENTS.md 的 11 个关键规则字段及 25 个本地文档链接，并用 `git diff --name-only` 确认只有预期的 5 份文档变更。AGENTS.md、源码、测试、配置、合成数据与旧证据文件均无差异。随后执行 `Get-Date -Format o`、`git status --short --branch`、`git diff --check`；退出 0，检查时间为 `2026-10-12T18:01:02.8622811+02:00`。实际结果：

```json
{"documentation_check": "PASS", "historical_log_preserved": true, "AGENTS_policy_checks": 11, "AGENTS_modified": false, "local_links_checked": 25, "changed_files": ["README.md", "docs/P0_acceptance_checklist.md", "docs/P0_real_inference_report.md", "docs/P0_status.md", "docs/research_development_log.md"]}
```

```text
## main...origin/main
 M README.md
 M docs/P0_acceptance_checklist.md
 M docs/P0_real_inference_report.md
 M docs/P0_status.md
 M docs/research_development_log.md
```

以上改动未暂存、未提交、未推送，由研究者本人后续审阅处理。本条仅追加同步与验证事实，保留首次 Push 之前的所有历史记录。
