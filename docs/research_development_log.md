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
| 操作者 | Commit 与 Push 由研究者本人完成；Automated development tools 本次只读检查 Git 和准备文档变更 |

**修改文件：**`README.md`、`docs/P0_real_inference_report.md`、`docs/P0_acceptance_checklist.md`、`docs/P0_status.md`、本文件 `docs/research_development_log.md`。在当前说明中增加首次同步事实，并将旧说明明确标为历史快照；本日志仅追加本条。旧测试证据、阻塞运行清单和历史日志未修改。应用源码、测试代码、实验配置及数据未修改。

**AGENTS.md 检查：PASS，无需修改。**现有条款包括 `Execute git commit.` 和 `Execute git push.`（均在 `Automated development tools must NOT` 下）、`The human researcher exclusively manages Git commits and pushes.`、`Every engineering and experimental change must be documented.`，并指定维护本日志，记录日期时间、阶段、文件、命令、测试、配置、错误及科学局限。这四项要求已正确表达；所有此次文档改动继续由研究者审阅并提交。

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

## 2026-10-12 — P0 Final Validation：真实 C0 审计及控制条件验证

**阶段 / 目标：**仅 P0；核验已完成真实 CPU 运行、固定模型身份、tokenizer、实验控制、原始日志、Parser 和可复现性。题目与 Protocol v1.1 不变，不进入 P1，不训练 LoRA，不访问 MimooPet。研究者补充来源信息后继续当前验证，没有重新生成原 C0。

**时间和基线：**本轮环境检查时间为 `2026-10-12T18:46:48.3682095+02:00`；本条阶段记录依据截至 `2026-10-12T19:19:03.5439925+02:00` 的实际证据整理。详细命令记录统一采用 UTC，并保存真实起止时间，不将报告写入时间冒充实验时间。初始工作区干净，HEAD 为 `f1a1b019981d7f2eb002871c9e600887d9e79874`，首次人工提交 `4a538570c77666009a609c1218a435ac52a6187a` 的历史保留。未联网刷新 GitHub；没有执行暂存、commit、push 或修改 Git 身份。

**首先读取：**AGENTS.md、research_protocol_v1.1、annotation_guidelines、P0_acceptance_checklist、P0_real_inference_report 和本日志。AGENTS 已明确禁止 Automated development tools commit/push、由研究者提交，以及所有工程/实验记录可复现日志；无需改写规则。

**输入冻结：**本地配置 `configs/p0_runtime.local.json`；Qwen3.5-2B-Base Q4_K_M；llama.cpp b11573 / 0f701c882；CPU 4/4 threads、n_ctx 4096、seed 42、max_new_tokens 96、temperature 0、top_p 1、stop=[]；实际 /tokenize 使用 add_special=true、parse_special=false，直接提交 IDs；token_tolerance=0、max_match_candidates=256。只使用 `data/synthetic/p0_cases.jsonl`，SHA-256 `31b5242c2cc01411f524c2b922086de0ef216105920e723f1270560e0bc1f282`。

`selection_freeze.json` 实际创建于 `2026-10-12T16:51:07.859013+00:00`，先冻结按 ID 排序的前三例，再扩展其余 17 例。扩展依据工程完整性和可用资源，不依据事实回答质量。所有原始新增证据位于被 Git 忽略的 `results/p0_validation/20261012T164648/`；公开派生文件只用相对路径。

### 已执行的主要命令与结果

所有以下 Python 命令均使用 `.\.venv\Scripts\python.exe`。`tools/p0_capture.py --output <new-json> -- <command>` 包装实际 argv、stdout、stderr、退出码及耗时；此表为摘要，原始命令字符串见同名 JSON。

| 实际 UTC 时间 / 证据文件 | 命令或操作 | 实际结果 / 退出码 |
|---|---|---|
| 初始阶段；`initial_actions.json` | PowerShell、rg、只读 Git、配置/源码/日志读取、本地两文件 SHA-256 | 环境可执行；原 C0 定位到 `20261012T163840-d0e467a28a4e4df89eb35ce788dfa917`；模型和 exe 摘要匹配预期 |
| 16:51:07；`original_c0_inventory.json` | 对原 C0 全部文件保存摘要快照 | 原始记录仅读；用于最终无修改核对 |
| 16:55:53–16:55:54；`baseline_audit_command.json` | `-m personaslm audit-run --run-dir <original-C0>` | 271 个事件完整性 PASS、20 次 Parser 重放；退出 0。此前也直接执行同一只读审计，未生成模型输出 |
| 16:57:08；`c0_replay_command.json` | 新增 `replay-run` 第一次验证 | 退出 2，20 例均被审计实现误标 Parser 不一致；原始实验本身未失败 |
| 16:57:42；`c0_replay_corrected_command.json` | 修正 Python tuple 与 JSON list 的比较后，用新输出文件重放 | 20 例全部一致；退出 0；先前失败文件保留 |
| 16:59:05–17:00:02；`prepare_command.json` | `tools/p0_validate.py prepare` | v1：style 20 对 BLOCKED，每例 256 次、best delta −3；history 20 对 PASS，delta 0；退出 2，零 completion |
| 17:01:36–17:02:56；`prepare_v2_command.json` | 交错候选句数，`--freeze-name prompts_frozen_v2.json --reuse-history-from prompts_frozen.json` | style 20 对仍 BLOCKED，256 次、best delta −1；history 成功结果复用；退出 2，零 completion |
| 17:05:06–17:06:06；`prepare_v3_command.json` | 按 multiset 枚举减少相同句子排列占用预算；冻结新文件 | style 20 对在第 169 个候选精确匹配；两组最终 40 对 delta=0；退出 0，仍零 completion |
| 17:06:22–17:08:27；`initial_generation_command.json` | `tools/p0_validate.py initial --freeze-name prompts_frozen_v3.json` | 3 案例 × 4 条件，共 12 次真实生成；四个独立 run，adapter/audit PASS；退出 0 |
| 17:07:22–17:07:23；`semantic_review_command.json` | `tools/p0_review_controls.py` | 40 条盲审文件、0 条人工判断；语义 PARTIAL；退出 0 |
| 17:07:57；`publisher_fetch_command.json` | `tools/p0_fetch_provenance.py` | 沙箱网络 WinError 10013；退出 2 |
| 17:08:22–17:08:23；`publisher_fetch_escalated_command.json` | 经批准一次公开 HF 固定 revision 元数据查询 | tree API HTTP 200，LFS SHA/大小与本地匹配；README HTTP 404；命令整体退出 2，两项结果分别保留 |
| 17:08:49 起；`expansion_generation_command.json` | `tools/p0_validate.py expansion --freeze-name prompts_frozen_v3.json` | 仅扩展 004–020；最终完成情况在本条后续补记和最终报告中记录，不预填未完成结果 |
| 17:08:59–17:09:07；`c0_replay_final_a_command.json`、`c0_replay_final_b_command.json` | 两次 `replay-run`，分别写新文件 | 均退出 0；完整输出结构相同；未启动 C0 模型推理 |
| 17:11:32–17:17:47；`export_controls_command.json` | `tools/p0_export_evidence.py controls` | 三个 tokenizer journal 分别 10801、10391、6903 个事件，链验证通过；退出 0；保留全部候选失败证据 |

**实际测试历史（均未删除）：**

| 命令证据 | pytest 原始结论 | 进程墙钟 | 退出码 / warnings |
|---|---|---|---|
| `tests_before_generation.json`，16:59:28 UTC 起 | 113 passed in 3.96s | 4.56s | 0 / 0 |
| `tests_audit_and_matching.json`，17:01:47 UTC 起 | 119 passed in 7.26s | 7.86s | 0 / 0 |
| `tests_pre_controls.json`，17:06:00 UTC 起 | 122 passed in 9.07s | 9.53s | 0 / 0 |
| `final_tests.json`，17:16:04–17:16:24 UTC | **123 passed in 18.97s**，0 failed | 20.55s | 0 / 0 |

测试和部分只读审计与控制生成并行，不能将这些耗时当作隔离环境下的性能基准。新增测试覆盖有效日志链中的语义不一致/重复案例、输入 IDs 改变、评分变化、数据快照独立性、篡改检测、重放写入边界和真实匹配失败暴露出的候选覆盖问题；没有弱化已有测试。

### 工程改动、错误与修复

- `src/personaslm/reproducibility.py`、`runner.py`：新运行保存只读 Git SHA/dirty/porcelain、精确 dataset/source/tool 快照；生成前保存 prompt/evidence SHA；接受冻结 prompt 后再次实际 tokenize，IDs 变化则阻断生成。
- `server.py`、`observations.py`：将后端日志详细度明确为 4，记录实际加载 metadata、0/25 GPU offload、CPU buffers、4/4 threads；Windows API 保存进程 working set / peak working set 和系统可用内存。没有改变 seed、温度、上下文或停止策略。
- `matching.py`：保存每个候选和 delta；保留 v1/v2 两轮真实失败。诊断为有限预算被短句前缀与排列消耗，v3 用多重组合扩大长度覆盖；句子库、最大句数、容差 0 和 256 上限保持。history 搜索逻辑不变。
- `run_audit.py`、`cli.py`：新增离线 `replay-run`，比对 tokenizer/提交输入、原始 wire/native payload、Parser、评分和独立案例；不得向原 run 内写结果。首轮错误是 Python tuple/JSON list 表示差异，序列化规范化后修复；没有改动 Parser 或实验回答。
- `tools/p0_*.py`：命令留档、两阶段受控运行、来源元数据读取、语义盲审准备、原始日志核验和公开派生摘要。全部为 P0 工程工具。
- 初次读取错用了不存在的 `personaslm/runner.py`、`personaslm/cli.py`（命令退出 1），经 `rg --files` 定位到 `src/personaslm/` 后修正。一次 `rg ... tokenizer_runs/*/server.log` 在 Windows 下返回路径语法错误 123，改用目录参数和 `-g server.log`；这两项的精确命令时刻未单独采集，不虚构时间。
- 沙箱内 CIM 最初拒绝，HRESULT 0x80041003；经批准只读查询成功。第二份完整硬件观测实际时间 `2026-10-12T19:04:23.7088598+02:00`：Ryzen 7 PRO 5850U，8 核/16 线程，物理内存条 17,179,869,184 bytes，OS 可见 12,698,714,112 bytes，Windows 10 Professionnel 19045。后时点观测不代替历史 C0 运行时测量。
- 19:18:56+02:00 的 `git diff --check` 指出 `tests/test_matching.py` 尾部多余空行，已移除；该命令与后续成功的 `git check-ignore` 同组，组退出 0 不能掩盖单项警告。最终会独立再次检查。

### 实际观察与科学限制

原 C0：20 个可独立识别结果，raw 非空 20、空 0，Parser preserved 20，长度停止 20；城市规则 correct 20、incorrect 0、unknown 0。它们经常继续生成多轮对话和无依据额外个人事实，不能报告一般事实准确率。每例 tokenizer IDs 与提交 IDs 及 evaluated count 匹配，truncated=false；后端没有返回 evaluated input IDs，不构造缺失数组。

控制条件运行中发现 legacy 城市规则将 “lived in … in 2025” 的过去城市再次出现判成当前冲突。原判定完整保留，疑似误判另存 `P0_evaluator_review.json`；没有在实验中途改变评分器，没有把规则错误数冒充人工确认的真实错误数，更不能归因于 Persona/history。

中性文本技术检查未发现已知城市泄漏、证据/当前问题变化、额外日期变化。style 文本含重复句子，共享 style heading 也可能产生残余提示；history 保留原日期/角色格式。40 条盲审的人工判定均为空，不虚构独立语义有效性或 annotator agreement。

模型来源单独见 `P0_model_provenance_report.md`：固定 GGUF revision `765d2baaa04dbb8d6df3e78af571e6beaa4373d7`，来自第三方 aashish1904；本地和公开制品一致，不证明转换/量化完全忠实于 Qwen 原始模型。源模型固定 revision、量化配方及独立比对尚缺。

**文档与公开证据：**更新 README、P0_real_inference_report、P0_acceptance_checklist、P0_status 和本日志；新增 P0_final_validation_report、P0_reproducibility_report、P0_model_provenance_report 及 `docs/validation/P0_*` 派生审计/盲审文件。旧清单、旧阻塞运行、旧测试/同步日志保留为历史快照。整体 P0 保持 PARTIAL；所有变更未提交，提交/推送由研究者决定。

### P0 Final Validation 完成补记

**实际完成：**扩展命令 UTC `2026-10-12T17:08:48.810373+00:00`–`17:20:03.776637+00:00`，墙钟 674.97 秒，退出 0。四个条件各新增 17 例，首批 12 加扩展 68 共 **80 次新增生成**。每条件恰好覆盖 20 个不同 IDs，没有重复首批；C0 原 20 次未重跑。

`tools/p0_export_evidence.py final` 实际于 UTC `17:20:50.547549`–`17:20:59.216394` 执行，退出 0。9 个生成 run 的日志链通过，每个运行连续两次离线重建结果一致；原 C0 的 **273 个文件**与最初摘要清单完全相同。3 个 tokenizer journal 另已验证通过。汇总：raw 非空 100、空 0，Parser preserved 100、失败 0，stop_type=limit 100；每次返回 96 个输出 IDs，输入评估数量匹配且无截断。独立 evaluated input IDs 仍缺失 100/100，未伪造。

原城市规则的实际结果为 C0/C1/N_style/N_history 各 correct 20、incorrect 0；C3 correct 6、incorrect 14；unknown 均为 0。14 条 C3 判错全部列为待复核：9 条自动筛查 dated-past 表达式，5 条技术补充涉及上下文省略或其他过去时。人工语义真实错误数未确定；没有把这些计数作为 Persona 效应或一般事实正确率。

最终中性匹配为两组各 20 对 delta=0；history 原轮是 **14 例第 7 次、6 例第 15 次**命中。语义审阅仍 PARTIAL，人工判断 0/40。后端详细日志还保留了 “no API key / CORS allows all origins” 的原始警告；服务仅绑定配置中的本地回环地址，该警告不被隐藏为无警告运行。pytest 的 0 warnings 仅指测试进程输出。

**最终产物：**[最终报告](P0_final_validation_report.md)、[来源报告](P0_model_provenance_report.md)、[可复现性报告](P0_reproducibility_report.md)、[验收表](P0_acceptance_checklist.md)、[逐案例原文与审计](validation/P0_case_audit.json)、[全部匹配和候选失败](validation/P0_control_matching.json)、[运行/环境摘要](validation/P0_final_evidence.json)、[评分复核](validation/P0_evaluator_review.json)、[复核补充](validation/P0_evaluator_review_addendum.md)、[盲审材料](validation/P0_neutral_blinded_review.jsonl)、[22 条已捕获命令的公开副本](validation/P0_final_commands.json)。原始完整数据保留本地忽略目录；公开副本将机器绝对路径脱敏并保留原文件摘要。

**末期错误与修复：**UTC 17:25:50 的命令索引导出因相对路径调用 `relative_to(absolute_root)` 抛 ValueError，退出 1，记录于 `export_commands_command.json`。工具先 resolve session 后修复；17:26:19 的新命令 `export_commands_corrected_command.json` 退出 0，旧失败保留。一次文档隐私扫描正则过宽，将 `EVIDENCE:` 后的 JSON 转义换行误识别为盘符；检查实际片段确认不是路径，修正盘符边界后通过，详情保存 `documentation_checks.json`，不删改真实 prompt。

**最后文档核验：**`2026-10-12T17:26:58.822293+00:00` 的 Python 只读核验确认已提交开发日志是当前日志的完整前缀，检查了 53 个本地 Markdown 链接及四个大型 JSON 的机器路径脱敏；AGENTS、Protocol、annotation guidelines、合成数据与 HEAD 无差异。`git diff --check` 独立返回 0。此前单项尾部空行问题已修复。最终只读 `git status --short --branch --untracked-files=all` 的完整列表另留本地；工作区变更均未暂存、未提交。

**验收决定：PARTIAL。** Adapter execution PASS；中性语义人工复核、上游量化过程独立验证、评分器时态/对话误判审阅、evaluated IDs 和历史 C0 provenance 缺口未解决，不签署完整 P0 research PASS。新工程日志已补齐适用记录，历史无法观测的量不能追补。P1 BLOCKED，不训练 LoRA，不访问 MimooPet，不生成科学效应结论。

## 2026-10-12 — P0 Methodology Acceptance and English Language Scope

Record created at **2026-10-12T18:06:22.204470+00:00** (UTC). This is a report-writing timestamp; actual command times are below. Phase: P0 only. Objective: diagnose generation budgets, prepare independent neutral review, audit C3 scoring, preserve reproducibility and record the prospective English language scope. Research Protocol v1.1 and the paper title remain unchanged.

The initial environment observation was `2026-10-12T19:38:18+02:00`; PowerShell and project venv were usable. Git was clean on `main...origin/main`, HEAD `8ffe1fdeb64ccc85182d2ff983b514940ecb6f70`, human commit dated `2026-10-12T19:33:32+02:00`. AGENTS and all mandatory research documents were read. No Git author configuration, staging, commit, push, history rewrite or remote network operation was performed. The initial tool-read outputs are retained in `initial_read_outputs.json`.

### Actual configuration and experimental actions

The immutable budget plan was created at `2026-10-12T17:39:54.613027+00:00`: first three lexicographically sorted synthetic IDs, C0/C3, budgets 96/192/256, exactly 18 generations, no adaptive extension or output-quality selection. A fresh 96-token reference was explicitly justified for within-session pairing. Original runs were neither overwritten nor replaced. English fixtures originated from the synthetic generator; original language `en`, translation false. No Chinese dialogue or real chat records were introduced.

Model and backend remain the pinned Qwen3.5-2B-Base Q4_K_M GGUF / llama.cpp b11573 (`0f701c882`), with the previously verified SHA-256 identities. CPU-only, 4/4 threads, 4096 context, seed42, temperature0, top_p1, stop[], cache_prompt=false, ignore_eos=false. Only generation budget changed. Model SHA `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; executable SHA `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. Dataset SHA `31b5242c2cc01411f524c2b922086de0ef216105920e723f1270560e0bc1f282`; template `transcript_base_v1`. Fixed publisher revision and its lineage limitations remain in the model report.

All six new manifests captured Git SHA and dirty=true, exact source/tool/data snapshots, hashes, runtime parameters, language metadata and the unchanged legacy evaluation version. Source/tool hashes remained the same across all six generation runs. Native requests/settings matched across each budget triplet apart from budget fields; both 96-token and 192-token prefixes match the longer outputs as an observation, not a determinism guarantee.

### Captured command history

Each record below stores exact argv, stdout/stderr, UTC start/end, exit code and duration under `results/p0_methodology/20261012T173818/`. Python commands use `.\.venv\Scripts\python.exe`. Wrapping command: `tools/p0_capture.py --output <new-record.json> -- <actual-command>`. Public redacted copies are in [P0_methodology_commands.json](validation/P0_methodology_commands.json); late documentation/Git verification commands and export completion are also retained locally even if created after this table.

| Command record | Actual UTC interval | Exit | Wall seconds |
|---|---|---:|---:|
| `integrity_before_command.json` | 2026-10-12T17:44:53.277597+00:00 to 2026-10-12T17:45:54.887099+00:00 | 0 | 61.610 |
| `tests_initial_v2.json` | 2026-10-12T17:45:03.787026+00:00 to 2026-10-12T17:45:16.447374+00:00 | 0 | 12.660 |
| `tests_pre_generation.json` | 2026-10-12T17:49:31.552155+00:00 to 2026-10-12T17:49:45.973518+00:00 | 1 | 14.421 |
| `tests_pre_generation_corrected.json` | 2026-10-12T17:49:57.221632+00:00 to 2026-10-12T17:50:11.559512+00:00 | 0 | 14.338 |
| `neutral_review_command.json` | 2026-10-12T17:50:14.601805+00:00 to 2026-10-12T17:50:14.925454+00:00 | 0 | 0.324 |
| `evaluation_audit_command.json` | 2026-10-12T17:50:14.792643+00:00 to 2026-10-12T17:50:15.135545+00:00 | 0 | 0.343 |
| `budget_generation_command.json` | 2026-10-12T17:50:19.490471+00:00 to 2026-10-12T17:55:59.646820+00:00 | 0 | 340.156 |
| `integrity_after_command.json` | 2026-10-12T17:56:25.179336+00:00 to 2026-10-12T18:01:46.660205+00:00 | 0 | 321.481 |
| `tests_final.json` | 2026-10-12T17:56:25.384714+00:00 to 2026-10-12T17:56:44.321589+00:00 | 0 | 18.937 |
| `replay_cli_command.json` | 2026-10-12T18:00:20.024228+00:00 to 2026-10-12T18:00:20.379524+00:00 | 0 | 0.355 |
| `export_methodology_evidence_command.json` | 2026-10-12T18:02:36.405738+00:00 to 2026-10-12T18:02:36.714786+00:00 | 0 | 0.309 |

The executed stages were `tools/p0_methodology.py integrity` before and after generation, `review`, `evaluate`, `budgets`, four `python -m pytest -q` invocations, `python -m personaslm replay-run` for the new 256/C3 run, and `tools/p0_methodology_report.py evidence`. All stage commands specify the exact session above. The full argv records are authoritative; no unexecuted experiment is presented as a command result.

### Actual results and preserved failures

- Budget command: UTC 17:50:19.490471–17:55:59.646820, exit0, 340.156s. All18 generated exactly the assigned96/192/256 tokens and stopped at limit. Raw nonempty18, parser-preserved18, errors0, reported EOS/EOG0, returned EOG IDs0. All initial replies have punctuation and are followed by generated dialogue turns; no full output has terminal punctuation. Structural flags are not independent semantic-completeness judgments. Latencies and all raw/parsed text are in the diagnostic report/JSON.
- Neutral preparation: 40 exact-matched historical pairs retained, zero token difference. English CSV/JSON with six dimensions, actual text/evidence/questions, partial blinding and an independent-review guide. Human reviews0/40; all ratings remain empty. Mapping retained separately for the researcher. Semantic acceptance PARTIAL.
- C3 audit: all14 original incorrect responses retained. Supplemental whole-output city statuses:2 contradicted,11 unverifiable,1 supported. Nonexclusive diagnostics:2 verifiable historical city contradictions,14 length-limit stops,2 temporal confusions,14 unsupported legacy current-conflict reasons,11 undetermined claims. Agent structural inspection identifies11 visibly cut tails; the other3 end in a city proposition without punctuation. No new verdict silently replaces an old score; no independent human ground truth is claimed.
- Integrity before:13 journals and9 generation runs pass. After:19 journals and15 generation runs/118 responses pass; two offline reconstructions per generation run are identical. All13 historical file inventories unchanged, including all earlier failures. The zero-generation BLOCKED run and PARTIAL token searches retain their terminal states. CLI replay of the new256/C3 run returns PASS,3 cases, exit0, without model inference.
- Tests: initial142 passed in12.06s (wall12.660s); guard expansion then1 failed/146 passed in13.74s (wall14.421s); fix147 passed in13.68s (wall14.338s); final147 passed in18.07s (wall18.937s), exit0,0 warnings. The failure was `Not Paris, Lyon.` becoming unverifiable after a conservative residence guard; the implementation now recognizes this explicit contrast. Test expectations were not weakened. All original test captures remain. Tests overlapped with offline integrity work, not budget generation.
- One apply_patch attempt used an incorrectly composed absolute test path (Windows error3); no files changed, confirmed by rg, then reapplied using relative paths. A later multi-file documentation patch assumed an English heading in the historically Chinese real-inference report and failed matching; no changes applied, then the valid file headers were used. Individual patch execution timestamps were not captured and are not invented.
- One read-only progress inspection used nonexistent `latency_seconds`, raising `KeyError`; it was corrected to `response_latency_seconds`. Saved experiments and the running generator were unaffected. Separate engineering notes retain this error and the inspection summaries. A pre-execution source review also corrected the report helper's field name to `classification`; no failed experiment resulted.

### Files and scope

Source: `src/personaslm/runner.py` (new-run metadata and explicit legacy evaluation label), new `src/personaslm/evaluation_v2.py` (bounded separate audit); tests in `tests/test_evaluation_v2.py` and `tests/test_runner.py`; orchestration/export tools `tools/p0_methodology.py` and `tools/p0_methodology_report.py`. The legacy evaluator, inference decoder, parser, fixture dataset and original journals were not changed.

Documentation: appended final-validation, reproducibility, real-inference and acceptance reports and this log; new English methodology-acceptance, budget-diagnostic, evaluation-audit and neutral-review documents; new language-scope addendum with parent-protocol changelog link and annotation-guide addendum. New `docs/validation/P0_*` sidecars hold the frozen plan,18 full diagnostic responses,14 supplemental evaluations,40 blank review items,19-run integrity,control summary and command history. Raw local configurations, models, credentials and results remain ignored; no private chat data was used.

Public reports use relative paths. Original raw HTTP/server/journal/source-snapshot archives remain local and must be supplied by the researcher for full independent archive verification. Missing historical C0 Git/memory metadata and independently evaluated input IDs were not fabricated. Upstream quantization fidelity and human semantic/evaluation review remain unverified.

**Decision: P0 PARTIAL, P1 BLOCKED.** Budget execution, logging, exact controls, offline reconstruction and automated tests pass their stated engineering checks; natural termination, independent neutral semantics and independent evaluation adjudication remain unresolved. No Persona causal effect, general accuracy, coherence or real-speaker fidelity conclusion is made. No P1, LoRA, MimooPet access, commit or push occurred. The English scope is prospective; no historical experiment or raw response was translated or altered.

### Final documentation and delivery verification

Recorded: 2026-10-12T18:09:44.609195+00:00. The public command index exported 14 complete captured command records at 2026-10-12T18:07:30.344579+00:00 (exit 0), retaining the failing intermediate test. Its own later completion record and subsequent delivery checks are separately retained locally.

The delivery checker completed at 2026-10-12T18:08:45.316417+00:00 (exit 0): 87 local Markdown links resolve; the old development log is a full prefix; prior protocol/annotation text is retained; AGENTS, the dataset, legacy evaluator/parser/inference and all 9 pre-existing public evidence files match HEAD. It verified 40 blank independent-review items and matching CSV/JSON text, evaluation source hashes, diagnostic-export identity, 7 ignored path classes, no staged changes, and no machine/home paths in the 13 new public documents present at scan time. Full checks and the complete **27-file uncommitted inventory** are in [P0_methodology_delivery_checks.json](validation/P0_methodology_delivery_checks.json). The subsequent delivery-check file contains only relative paths and this factual summary.

`git diff --check` at 18:07:11 UTC returned 0 with no output; `git status --short --branch --untracked-files=all` returned 0 at 18:07:12 UTC. Final read-only Git checks follow this note and are saved to new local command records. All changes remain uncommitted and unstaged; the researcher alone performs commits and pushes.

## 2026-10-12 — P0 Final Methodological Validation

Recorded **2026-10-12T18:43:52.286335+00:00**, UTC, after the actual actions summarized below. Project/paper, Protocolv1.1, Real-Speaker target and English primary language unchanged. Phase: P0 only. Initial environment observation20:17:18.5002461+02:00; clean main tracking origin/main, human-created HEAD `2b0fc5ee04f05af0fbb878fd71356a6afeaa6865`. No network, staging, commit, push, authorship change, P1, LoRA or MimooPet operation was performed.

Read AGENTS, protocol, methodology/final reports and research log first, then source/configuration and original raw records. Initial read-only commands and exact observed baseline are retained in `engineering/initial_actions.json`; individual uncaptured patch/read timestamps are not fabricated.

### Objectives, configurations and actual results


**Overall P0: PARTIAL. P1: BLOCKED.** The latest assessment is [Remaining Blockers](P0_remaining_blockers.md), which explicitly separates mandatory methodological blockers from acceptable documented limitations and later research. Natural EOS, a fully reproduced upstream quantization pipeline, and an unsupported backend evaluated-ID interface are not blanket P0 prerequisites.

The response unit remains unresolved across the intended development scope. Four newly authored English cases, disjoint from the historical case IDs/speakers, were frozen before 16 requests at a fixed 96-token budget. T0/T1 use the existing transcript without/with role stops; T2/T3 request a literal end marker without/with its stop. All 16 requests completed. T0/T2/T3 reached 96; T1 stopped at 9/23/9/11 tokens. EOS/EOG 0. Supplementary structure checks pass 2/4 in each of T0/T1 and 0/4 in T2/T3. The original v1 check missed uppercase USER in one ordinary task; its old classifications and raw payloads remain unchanged alongside the supplementary correction. A literal-role challenge also remains invalid; no extra experiments were run to manufacture a pass. See [termination diagnostics](P0_response_termination_diagnostics.md).

A complete reply is operationally a nonempty, bounded assistant turn with no extra role turns or delimiter/content ambiguity, followed by a separate check of whether it completes the requested components. Token limits, punctuation and factual correctness do not alone establish this. Backend string stops are allowable recorded interventions when validated. Current examples support only a restricted observed scope; no online revised case-insensitive/escaping rule has been adopted.

The new [English annotation form v3](P0_neutral_annotation_form_v3.md) exposes case/condition/reference IDs, actual neutral text, full-prompt token counts/differences, evidence and six PASS/FAIL/UNCERTAIN fields plus reviewer notes. All 40 remain blank. The form is unblinded as requested; software imports are versioned, hashed, immutable and traceable. A real empty-form CLI import was rejected without creating a review. Positive import tests are explicitly simulated test doubles, not human judgments.

The new [evaluation v3 audit](P0_evaluation_validity_v3.md) distinguishes Correct, Incorrect, Unverifiable and Not Applicable. Independent synthetic checks cover the six requested categories, inapplicability and conflicting source facts. All 24 declared contract checks pass; a separate regression additionally preserves the v2 foreign-subject failure. Six of 22 development texts expose v2 scope problems. The historical 14 C3 results remain unchanged, with separately saved v3 counts 2 Incorrect/11 Unverifiable/1 Correct. No unsupported claim was silently converted to Incorrect. V3 remains a narrow English residence-claim audit, not general semantic truth or an automatically selected production evaluator.

Mandatory closure: validate the intended reply boundary, complete independent review of all 40 controls and resolve issues, and freeze a scoring unit/policy consistent with that boundary. P1 does not require retrospective human relabeling of every old diagnostic or a perfect general-purpose automatic judge. P0's bounded software checks are useful but do not authorize a scientific comparison yet.


### Reproducibility and error recovery


New local evidence root: `results/p0_methodological_final/20261012T181718/`. **Engineering** commands/tests/errors are under `engineering/`; immutable model **experiment** journals and replays are under `experiments/`; freezes, evaluation and source sidecars are under `materials/`. The old result directories were read only.

New real run: `20261012T182432-ea39ea100d8c449ab05b04cf80e6b78c`. Its manifest records Git HEAD `2b0fc5ee04f05af0fbb878fd71356a6afeaa6865`, actual dirty state, exact generation-time source/tool/data snapshots, frozen plan/configuration, prompt versions and hashes. Each cell retains real tokenizer IDs, request IDs, raw HTTP/native output, native settings, generated IDs/count, stop reason/stopping word, latency, legacy parse, versioned boundary parse and excluded tail. Evaluation is explicitly Not Applicable for this termination diagnostic. Model/backend identities are the unchanged pinned GGUF SHA and build 11573 executable SHA; preflight/postflight and detailed CPU logs are retained.

All 19 historical byte-level file inventories match the previously chain-verified inventory, including the original blocked run and failed matching attempts. This proof reuses the prior chain verification on byte-identical journals; it does not pretend every old tokenizer event was reparsed this time. The 15 old generation runs were additionally reconstructed twice with identical outputs; the new boundary journal was directly chain-checked and reconstructed twice. Total: 20 journals accounted for, 16 generation runs, 134 responses. See [integrity evidence](validation/P0_final_methodological_integrity.json).

The generation command returned exit 1 after all 16 requests because its subsequent offline audit incorrectly treated 14 startup health 503 responses as failed inference. The journal's execution terminal state is PASS. Corrected offline replay retains the 503 observations, requires successful tokenizer/completion responses, and passes without generation. A separate audit-tool hash identifies the corrected implementation; the generation-time snapshot preserves the original auditor bug. Dedicated regression tests cover startup 503 and rejection of failed completion 503.

The importer initially compared CSV column order with sorted JSON key order. Tests caught 2 failures/191 passes; field-name/uniqueness validation now accepts the valid unchanged schema and rejects material edits. This was an engineering fix, not a fabricated reviewer result. Corrected tests 195 passed in 12.11s. Final tests 195 passed in 9.29s, 0 failed, 0 warnings, exit 0; process wall9.707s. Initial pre-generation tests 157 passed in 8.84s. All failure captures remain.

Raw stopped output means the complete payload actually returned by the backend. A native stop can withhold its delimiter; no invisible continuation is invented. No-stop shadow responses are separately logged actual generations with the same prompt/IDs/settings apart from stop. Full public derived [boundary evidence](validation/P0_response_termination_evidence.json) redacts machine paths, while local originals retain raw bytes and source snapshots. [Evaluation evidence](validation/P0_evaluation_validity_v3.json) records independent fixture/source hashes and all 14 old raw responses with separate versions.

The final analysis-code/source snapshot is retained in `materials/final_source_snapshot.json`. It is explicitly later than the inference snapshot and is not backfilled into that run. Current generated and evaluated-ID limitations are stated accurately: returned output IDs and submitted prompt IDs exist, but independently evaluated input IDs do not. No unsupported interface is required as an acceptance gate.

All actual captured commands and failures are indexed in [P0_final_methodological_commands.json](validation/P0_final_methodological_commands.json). Export completion and later delivery checks remain separate local records. Reproduction must use fresh run/output paths; never repeat an already-started session or overwrite original files. Human imports require a genuine reviewer-provided form, new review-round identifier and new output file. The raw archive remains local for researcher-controlled independent dissemination.


### Actual captured commands

Every Python command uses `.\.venv\Scripts\python.exe` through `tools/p0_capture.py --output <new-json> -- <argv>`. Exact argv/stdout/stderr/exit/time are in the listed files under this session's `engineering/` directory. Nonzero exits are retained: the real generation command's post-generation audit failure, two importer unit-test failures, and the deliberate expected empty-form rejection. An expected rejection is not a failed human annotation or failed model generation.

| Record | Actual UTC interval | Exit | Wall seconds |
|---|---|---:|---:|
| `tests_before_inference.json` | 2026-10-12T18:24:03.249425+00:00 to 2026-10-12T18:24:12.532180+00:00 | 0 | 9.283 |
| `freeze_boundary_command.json` | 2026-10-12T18:24:13.116236+00:00 to 2026-10-12T18:24:13.389679+00:00 | 0 | 0.273 |
| `run_boundary_command.json` | 2026-10-12T18:24:32.068339+00:00 to 2026-10-12T18:26:28.312076+00:00 | 1 | 116.244 |
| `export_annotation_form_command.json` | 2026-10-12T18:26:42.945785+00:00 to 2026-10-12T18:26:43.074271+00:00 | 0 | 0.128 |
| `boundary_replay_a_command.json` | 2026-10-12T18:27:54.865937+00:00 to 2026-10-12T18:27:55.307531+00:00 | 0 | 0.442 |
| `boundary_replay_b_command.json` | 2026-10-12T18:27:54.989195+00:00 to 2026-10-12T18:27:55.421285+00:00 | 0 | 0.432 |
| `tests_methodological_modules.json` | 2026-10-12T18:30:24.042413+00:00 to 2026-10-12T18:30:36.720773+00:00 | 1 | 12.678 |
| `tests_corrected_modules.json` | 2026-10-12T18:32:35.575638+00:00 to 2026-10-12T18:32:48.123146+00:00 | 0 | 12.548 |
| `evaluate_v3_command.json` | 2026-10-12T18:35:41.092780+00:00 to 2026-10-12T18:35:41.298528+00:00 | 0 | 0.206 |
| `integrity_and_boundary_export_command.json` | 2026-10-12T18:35:41.847096+00:00 to 2026-10-12T18:38:43.980437+00:00 | 0 | 182.133 |
| `blank_review_rejection_command.json` | 2026-10-12T18:37:23.847772+00:00 to 2026-10-12T18:37:24.000073+00:00 | 1 | 0.152 |
| `tests_final.json` | 2026-10-12T18:41:53.299343+00:00 to 2026-10-12T18:42:03.006398+00:00 | 0 | 9.707 |

Main executed commands: `tools/p0_turn_boundary.py freeze`, `run`, and two `audit` calls; `-m personaslm.neutral_review export`, and a deliberately rejected blank `import`; `tools/p0_final_methodology.py evaluate` and `inspect`; four `-m pytest -q` runs. The frozen model order, config, prompt texts/hashes and case versions were saved before generation at 18:24:13.295251 UTC. The request budget remained 96 throughout; no stop rule was selected using factual answer quality. Later documentation, export and delivery checks are separately captured as they occur.

Engineering patches added `response_boundary.py`, `boundary_review.py`, `neutral_review.py`, `evaluation_v3.py`, two P0 diagnostic/export tools, independent English fixtures and regression tests. The role-case miss is exposed by supplemental v2 review while the frozen v1 parser remains intact. Exporter code retains raw payloads but redacts machine paths in public copies; read-only inspections of native payloads motivated that redaction before publication. The legacy scorer, v2 scorer, historical parser/inference code and original dataset were not modified. No actual human ratings were entered by the agent.

Documentation updates: methodology/final/reproducibility reports, acceptance cross-reference and this append-only log. New English reports: response termination, evaluation validityv3, annotation formv3 and `P0_remaining_blockers.md`; new public evidence retains full actual outputs, original/new judgments, review materials, inventory proofs and command results. All private configurations, model binaries and raw results remain ignored. Existing reports are dated historical snapshots, not erased contradictions.

Scientific boundaries: new experiments are engineering diagnostics, not Persona-effect estimates. Narrow rule-contract tests do not estimate model accuracy or human annotation validity. Model upstream fidelity, backend missing evaluated IDs, absent old C0 metadata, public raw-archive availability and generalization remain explicit limitations. **P0 PARTIAL; P1 BLOCKED by the specific A-category methodological issues, not by requirements for unsupported external APIs.** Git review/commit/push remain exclusively the researcher's responsibility.


### Final delivery checks and preserved delivery-script errors

Recorded 2026-10-12T18:49:55.876776+00:00. Command export at 18:47:09 UTC saved 13 captured commands in the immutable public index. Subsequent delivery checks and their exact command/time/stdout/stderr records remain under this session's `engineering/` directory.

The first delivery script at 18:48:18 UTC exited 1: its prose-spacing step did not recognize the development log's distinct new-entry heading and also touched old prose. The prefix assertion detected this immediately. The exact historical HEAD prefix was restored while retaining the entire new dated entry. The failed script is retained as `verify_delivery_failed_v1.py`. No experimental artifact was changed. The second check at 18:48:50 UTC exited 1 because tool snapshot keys already contained `tools/`, and the checker prepended it again. Correcting this path interpretation required no source or experiment change. Both original failed command captures remain; these are delivery-tool errors, not test/model failures.

The corrected checker completed at 2026-10-12T18:49:04.631126+00:00, exit 0. It verified the unchanged historical development-log prefix, 66 protected tracked files, additions-only tracked report changes, all 40 blank form rows, zero token differences, frozen parser and evaluator/source hashes, 98 local Markdown links, private/model/results ignore rules, no staged changes, and no machine/home paths in newly published materials. Details and the complete **29-file uncommitted inventory** are in [delivery verification](validation/P0_final_methodological_delivery.json). The delivery record points to the successful capture and also lists both failed captures. The ignored engineering checker itself is outside the experimental source snapshot.

`git diff --check` completed at 2026-10-12T18:49:22.614952+00:00, exit 0, with no whitespace errors; Git emitted four CRLF-to-LF working-copy notices, retained in stderr. `git status --short --branch --untracked-files=all` completed at 2026-10-12T18:49:23.249766+00:00, exit 0: five modified tracked documents and 24 untracked deliverables, no staged files. The HEAD remains `2b0fc5ee04f05af0fbb878fd71356a6afeaa6865`.

Final automated test result remains **195 passed, 0 failed, 0 warnings reported, 9.29 seconds, exit 0**; subsequent changes were documentation and an ignored delivery checker only. All prior test and audit failures remain recorded. Overall research acceptance remains PARTIAL; no human review or missing evidence has been converted to PASS. No Git commit or push was executed.


## 2026-10-12 — Frozen Measurement Policies and Vendor-Neutral Attribution

Recorded 2026-10-12T19:19:43.094673+00:00, UTC. Phase P0 only. Initial environment observation: 2026-10-12T21:00:50.9501402+02:00. Clean main/origin-main at researcher-created HEAD `1c9bfc3791f7f5cb4b4bda78cd02e2580f0429da`. AGENTS and current acceptance reports were read before changes. No protocol, research-objective, Git authorship or history change; no commit/push. Exact initial actions and early errors are in `results/p0_acceptance_policy/20261012T190050/engineering/initial_actions.json`.

Objective: classify and measure response status without demanding every Base response stop naturally; freeze consistent separate-axis scoring; verify human-review readiness. Added 16 development software cases, then froze policy at 2026-10-12T19:09:12.410208+00:00. Created separate 24-item software holdout and six fictional English inference cases afterward, sealed at 2026-10-12T19:10:31.766880+00:00. All holdout items selected before outputs; no adaptation after inspection. Software result 24/24, with 6 AMBIGUOUS and 75% decided coverage. Same author knows the rules; these are not human semantic-accuracy labels.

New run `20261012T191040-7205faad677e426c8838576739d49717` completed 6/6 requests. Same model/backend hashes and parameters as in the [full report](P0_policy_acceptance_report.md), C0 only, unchanged transcript, stop=[], max_new_tokens=96. Saved exact prompts/IDs/raw/native/parsed results, applicability, seed, latency, source/configuration hashes and Git dirty state. All six hit the cap; response-status sidecar yields 5 CROSS_TURN, 1 AMBIGUOUS. Factual sidecar yields 1 Correct/0 Incorrect/5 Unverifiable/0 Not Applicable; relevance, temporal consistency and coherence are separately pending. Unsupported city grammar was not extended after viewing holdout results.

Reproducibility: all 20 prior journal inventories unchanged; new journal replayed twice identically. Historical 134 responses plus 6 new = 140. New policies are additive sidecars; old evaluation versions and scores remain. Engineering logs are under `engineering/`, immutable experiment records under `experiments/`, and freezes/snapshots under `materials/`. No raw journal was rebranded or altered. No model generation was rerun for a better result.

Neutral review: original 40-row CSV/JSON matches the historical freeze exactly, all token differences zero, no completed human ratings and no submitted human files. English guide updated with readiness evidence. Existing importer retained; four regression cases added for missing labels, changed versions, missing records and blank reviewer IDs. Positive test inputs remain labeled test doubles. Human-review requirement OPEN; P0 PARTIAL and P1 BLOCKED.

Mandatory documentation correction by the researcher: 17 product-name occurrences across 11 source/documentation/configuration files were changed to vendor-neutral attribution. AGENTS identifies maintainer Yaxin ZHENG and retains the prohibition on automated commits/pushes. One metadata label in `tools/p0_review_controls.py` and the corresponding published evidence copy changed; AST comparison and JSON value comparison verify no algorithm or measurement changes. Original bytes are archived under `engineering/attribution_originals/`; [before/after hashes](validation/P0_vendor_neutral_attribution_audit.json) preserve traceability. The private tool-directory ignore rule uses an equivalent glob, verified by `git check-ignore`; no new private files became eligible for publication. Historic commands, numeric results, timestamps, model metadata and Git history are preserved. The correction does not assert that all code was written manually.

Engineering errors: an absolute patch-path typo caused a partial patch failure; the remaining files were applied using correct relative paths. The first test-capture wrapper failed after child execution because its output directory did not exist; child output/exit status are unavailable, so no result is claimed. Directories were created, and the captured targeted run passed 37 tests in 0.64s. A read-only request for the analysis report while it was still being written returned file-not-found; the report was read after completion, with no inference rerun. Uncaptured read/patch timestamps are not fabricated.

Final test command: `.\.venv\Scripts\python.exe -m pytest -q`; **223 passed in 13.28s**, 0 failures, 0 reported warnings, exit 0, wall 13.894s. Tests ran after generation; offline audit overlap makes timing unsuitable for performance claims. Documentation/attribution changes are distinct from the separately authorized methodological implementation.

### Exact captured command index

All paths below are under the current session's `engineering/`; each JSON retains actual argv, start/end UTC, stdout/stderr and exit code. This table covers commands completed before this report-writing command; later exports and delivery checks are separately captured.

| Record | Started UTC | Finished UTC | Exit | Wall seconds |
|---|---|---|---:|---:|
| `development_tests_captured.json` | 2026-10-12T19:05:50.906214+00:00 | 2026-10-12T19:05:52.008055+00:00 | 0 | 1.102 |
| `freeze_policy_command.json` | 2026-10-12T19:08:56.000635+00:00 | 2026-10-12T19:09:12.586708+00:00 | 0 | 16.586 |
| `author_holdout_command.json` | 2026-10-12T19:10:30.913391+00:00 | 2026-10-12T19:10:31.012324+00:00 | 0 | 0.099 |
| `seal_holdout_command.json` | 2026-10-12T19:10:31.551203+00:00 | 2026-10-12T19:10:31.797517+00:00 | 0 | 0.246 |
| `software_holdout_command.json` | 2026-10-12T19:10:32.339820+00:00 | 2026-10-12T19:10:32.612582+00:00 | 0 | 0.273 |
| `real_holdout_command.json` | 2026-10-12T19:10:40.656415+00:00 | 2026-10-12T19:11:37.316093+00:00 | 0 | 56.660 |
| `form_readiness_command.json` | 2026-10-12T19:10:51.831417+00:00 | 2026-10-12T19:10:52.452417+00:00 | 0 | 0.621 |
| `analyze_real_holdout_command.json` | 2026-10-12T19:13:04.409782+00:00 | 2026-10-12T19:16:00.726099+00:00 | 0 | 176.316 |
| `vendor_neutralize_command.json` | 2026-10-12T19:13:15.399363+00:00 | 2026-10-12T19:13:15.960390+00:00 | 0 | 0.561 |
| `tests_final.json` | 2026-10-12T19:14:04.806138+00:00 | 2026-10-12T19:14:18.700372+00:00 | 0 | 13.894 |

Main artifacts: new `response_status.py` and `evaluation_policy.py`, policy documents, development/holdout fixtures, two new test modules, neutral-import regressions, `p0_policy_validation.py`, sealed policy/holdout manifests, full software/real validation JSON, readiness and attribution audits. Updated methodology/final/reproducibility/remaining-blocker reports and acceptance checklist. See [current acceptance report](P0_policy_acceptance_report.md) for the A/B/C decision. No new scientific-effect conclusion, P1, LoRA or unrelated project operation occurred.


### Final source search, preservation and Git delivery checks

Recorded 2026-10-12T19:22:12.484651+00:00. The final case-insensitive repository search at 19:20:19 UTC returned zero matches (search exit 1, empty stdout and stderr, meaning no matches). The independent delivery checker completed at 2026-10-12T19:21:19.563165+00:00, exit 0, scanning 124 current tracked/non-ignored source and documentation files before creation of its own report. Private datasets, model weights, environments, binaries and immutable original experiment archives were excluded. Product references in old immutable snapshots are not erased; they remain original reproducibility evidence outside current publishable source.

The checker verified unchanged frozen policies/holdout hashes, all archived pre-edit attribution hashes, unchanged numeric/experimental JSON content, no operational AST change from the attribution correction, unchanged protocol/source files outside authorized changes, and the historical log prefix except the explicitly authorized neutral wording substitutions. All original 40 blank form records remain byte-identical. It checked 153 local Markdown links, private ignore rules and absence of machine paths in newly published evidence. Full checks and the **35-file uncommitted inventory** are in [delivery evidence](validation/P0_policy_acceptance_delivery.json).

`git diff --check` finished at 2026-10-12T19:21:38.816773+00:00, exit 0; no whitespace errors. Six Git CRLF-to-LF working-copy notices are preserved in stderr and are separate from the zero pytest warnings. `git status --short --branch --untracked-files=all` finished at 2026-10-12T19:21:39.382442+00:00, exit 0: **16 modified tracked files and 19 new files**, none staged. HEAD remains `1c9bfc3791f7f5cb4b4bda78cd02e2580f0429da`. All commits and pushes remain under Yaxin ZHENG's control.

The public command index includes the 12 completed command captures available at export time. Export, delivery check, final Git checks and this closing write have their own immutable local captures. Final automated tests remain 223 passed / 0 failed / 0 warnings reported, 13.28 seconds, exit 0; subsequent edits were reports only. No actual human reviews were supplied, so P0 stays PARTIAL and neutral review stays OPEN. A final source search after this appendix is captured separately; no experimental re-generation is needed.


## 2026-10-12T20:13:26.793933+00:00 — P0 control diagnosis and researcher-verified annotation

Phase: **P0 only**. Objective: investigate semantic controls, reconstruct all original inputs, test versioned development candidates with the actual tokenizer, register supplied human judgments, and prepare proposals/literature review without executing P1. Maintainer: Yaxin ZHENG. Git HEAD `4d00ee1adbe538d24175d5c3e83c318bff8365a3`; dirty working state recorded in source/run snapshots. No commit, push, history rewrite or author-identity change.

Read the project instructions, frozen protocol, annotation guide, current acceptance reports, conditioning/fixture implementation, original synthetic cases and 40-row annotation materials. The actual matched overrides were distinguished from unused fixture defaults. Reconstructed **100 prompts**, with identical evidence/questions and historical hashes/IDs. All 20 cases share one style and persona ID; ten have implicit “the person”/Alice binding. N_style repeats formatting language; N_history changes residence discourse to unrelated document dialogue. Findings and admissible contrast interpretations are in [the diagnostic](P0_neutral_control_diagnostic.md).

Researcher delivery occurred during this work. The first file was archived with SHA `f09a128f212a1405b9276ccc27ffd871c2365df5798d6e8feec6194dbca1733e` before its original working path disappeared. The researcher then supplied `PersonaSLM_P0_Researcher_Reviewed_v3.csv`, SHA `06629e8bc69684b3a276ec00a71558291c5762c64acc23dac619cc86d88bfb42`. Registered **40/40 human-reviewed records**, reviewer `Yaxin_ZHENG`, type `researcher_human_review`, version `researcher_verified_annotation_v1`, latest registration revision 2. Source process: claimed independent first pass, then AI-reference consultation/revision; final review is AI-assisted, not blind. Review timestamps/second reviewer/agreement remain unavailable. Initial registration and both source versions remain separate.

Available-version comparison: **0 changes across six core/two auxiliary judgment fields**, metadata/provenance changes in **40 records**. The source preceding final v3 had already been described as researcher-corrected, so it is not mislabeled as untouched AI assessment. Original AI CSV, independently saved first-pass CSV and one intermediate declared hash are unavailable: total earlier corrected judgments cannot be verified. No missing version or timestamp was fabricated.

Human overall control suitability: **PASS 0 / PARTIAL 40 / FAILED 0**. Separate deterministic dimension routing: **PASS 0 / PARTIAL 20 / FAILED 20**, reflecting 20 explicit unintended-style findings and 20 uncertain history controls. All 40 overall semantic-neutrality judgments are uncertain. Human annotation completion passes; unresolved control validity keeps P0 PARTIAL. A second reviewer is not introduced as a new blanket gate.

Development-only candidate version `neutral_control_candidate_v1_dev`, template `control_candidate_prompt_v1_dev`: all three new fictional cases, **36 style +8 history candidates each**, frozen before tokenizer access. **132 candidate attempts**, 6 reference counts, 100 historical rechecks; native GGUF tokenizer, exact tolerance 0. History **3/3** matches; style **0/3**, best signed differences **+2, -3, -3**. Failed lengths were preserved; candidate pools were not enlarged after observation and no generation answers were consulted. **Zero completions**. New history content may cue abstention, and style metadiscourse may still prime behavior; no semantic acceptance claimed.

Full tokenizer config/raw HTTP/tokens/input hashes, model/server pre/postflight and Git/source snapshot are in journal `20261012T195708-1dc4429d05c94341bf5a92c6da48c020`. Model and backend hashes match the prior pinned values; see the reproducibility addendum. All **21 original journal inventories** unchanged; all **22 current journal chains** freshly validated; annotation reconstruction also matches. Prior 140 generations, failures, parser/evaluation versions and dataset bytes preserved.

New modules: `researcher_review.py`, `control_candidates.py`, `control_resolution_review.py`; new regression files test their actual import/path/material/quote/matching failure modes. Original strict v3 importer and historical inference/evaluation code were not edited. A blank 40-item follow-up resolution form supplies original comparison materials and quotation fields; no follow-up judgments or human identities were invented. [Guide](P0_neutral_control_resolution_guide.md).

Prepared [P1 design proposal](P1_experimental_design_proposal.md), preserving S/F/H, eight factorial cells, two matched controls, separate tracks and fidelity/reliability. The illustrative 480-generation allocation is arithmetic only; no pilot or confirmatory set was generated. Reviewed nine primary-source studies in [the novelty matrix](related_work_novelty_matrix.md), including overlapping persona/factuality, memory, speaker simulation and context research. Five falsifiable proposals are not claims of established novelty. No private conversation datasets were downloaded.

Errors preserved: an early inline Python inspection failed with `SyntaxError: unterminated string literal` because Windows shell quoting removed quotes; subsequent inspections used stdin scripts/files. This was a read-only failure, not a model failure. First targeted tests: **29 passed /1 failed**, because an integration fixture used a temporary directory outside the modeled repository. Corrected the test repository root with a fixture; production path restrictions unchanged. Rerun **30 passed**. Two paper HTML routes returned 404; used available versioned PDF/abstract sources and recorded the failures.

Final full command `.\.venv\Scripts\python.exe -m pytest -q`: **263 passed, 0 failed, 0 warnings reported**, pytest **10.11s**, process **10.638s**, exit **0**. Actual test interval: `2026-10-12T20:08:42.850912+00:00` to `2026-10-12T20:08:53.488847+00:00`.

Changed files include the three additive modules/tests, control validation/report tools, new diagnostic/registration/resolution/proposal/literature reports and immutable JSON/CSV artifacts. Current-status notices were added to nine existing reports/guides with original bytes archived; README points to current evidence. Protocol and prior experiment/evaluation sources are unchanged. Exact file inventory, hashes and command captures are indexed in the delivery evidence and command index. Tool-assisted implementation is described neutrally; no claim of exclusively manual authorship is made.

The new [current acceptance checklist](P0_control_acceptance_report.md) distinguishes completed engineering, completed human review, unresolved methodological controls, acceptable artifact/backend limitations and future research. **Overall P0 PARTIAL. P1 NOT STARTED.** Historical 0/40 entries remain accurate records of earlier moments, not current status. All Git changes await researcher review and commit.

### Final documentation and repository checks

Final export ran from `2026-10-12T20:14:40.077629+00:00` to `2026-10-12T20:14:40.806626+00:00`, exit 0: 11 completed command captures indexed, nine original report bodies preserved verbatim inside the updated files, the committed development-log prefix preserved, 198 local Markdown links checked and 153 current text files scanned with zero prohibited development-product references. The [final check artifact](validation/P0_neutral_validity_final_checks_v1.json) retains file hashes and the full uncommitted inventory; later captures are local under the same engineering directory.

`git diff --check` at `2026-10-12T20:15:03.285408+00:00` exited 0 with no whitespace errors. Six Git CRLF-to-LF notices are retained in its stderr; they are unrelated to pytest warnings. `git status --short --branch --untracked-files=all` at `2026-10-12T20:15:03.312285+00:00` exited 0: **11 modified tracked files, 29 untracked files, 0 staged files**. The untracked set includes the researcher's delivered CSV. Branch remains `main`, HEAD remains `4d00ee1adbe538d24175d5c3e83c318bff8365a3`.

The final case-insensitive `rg` scan of README, repository instructions, docs, source, tests, tools, ignore rules and project metadata at `2026-10-12T20:15:03.285850+00:00` returned no matches (exit 1 with empty stdout/stderr, the normal no-match result). Private data, models, environments and original binary/experimental archives were not included in the branding audit. Captures: `final_export.json`, `git_diff_check.json`, `git_status.json`, `final_source_search.json`. A closing verification after this appendix is retained separately. No new model responses or historical rescoring occurred during final delivery. Latest full tests remain 263 passed, exit 0; subsequent changes were reports and the successfully executed evidence-export tools.
