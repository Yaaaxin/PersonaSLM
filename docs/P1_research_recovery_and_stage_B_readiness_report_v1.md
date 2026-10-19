# PersonaSLM P1 中断恢复、时间评分审计与 Stage B 就绪报告 v1

记录日期：2026-10-16（Europe/Paris）  
研究者：Yaxin ZHENG  
范围：P1 离线恢复与验证；未解盲、未执行 Stage B、未运行模型推理。  
基线：Research Protocol v1.1 及已批准的限定范围 addenda；v1.2 仍为 proposal。

## 1. 结论

**Stage B 离线材料状态：READY。** 研究者的 32 条盲审判断已完整定位并验证；冻结自动评分代码未发现以 `registered_evaluation_date` 替代问题日期的缺陷；Stage A 候选、历史 raw outputs、预算和 key 哈希均完整；最终相关回归为 126 passed、0 failed、1 skipped。Stage B 仍未获授权、未解盲、未选择条件、未执行任何 manifest。

READY 不豁免未来执行门槛：必须收到后续单独的明确激活消息，并在加载模型前重新通过不少于 3 GiB available physical RAM、模型/后端/tokenizer/hash 和 live-token preflight。本次审计时的瞬时可用内存为 3,029,762,048 bytes，低于 3,221,225,472-byte 门槛 191,463,424 bytes；若当时获授权，执行器应停止。这是实时执行条件，不是冻结材料损坏。

## 2. Repository status 与中断时间线

- 工作目录与 Git root：`E:/DEVOIRS/Research/PersonaSLM-Lab/PersonaSLM-Lab-P0-v1.1/PersonaSLM-Lab`。
- 分支：`main`。
- HEAD：`c40667ad266082481b1850453f67784b593f3723`，提交题为 `Complete P1d format diagnostics and prepare Instruct feasibility test`。
- staged changes：0。
- 仓库在恢复开始前已不是 clean：`docs/research_development_log.md` 有未暂存追加，另有大量 P1/P5/P6 未跟踪研究材料、工具和测试。它们不是本次恢复新建的完整集合，不得用 reset/clean 丢弃。
- 中断会话确实产生了实质文件变更，而不是“未开始”：研究者 v3 包约在 19:41 进入仓库；integration artifacts 约在 20:19 生成；失败回归证据约在 20:21 生成；工具与时间测试约在 20:22 再次修改，随后会话中断。

中断时留下的关键状态：

| 对象 | 恢复初始分类 | 证据 |
|---|---|---|
| 研究者完成版 v3 CSV | `COMPLETE_AND_VERIFIED` | 32/32、预期 SHA-256 精确匹配 |
| annotation import JSON、compatibility CSV、date audit JSON | `COMPLETE_AND_VERIFIED` | 与当前 validator 的内存重建一致 |
| scorer audit v1 | `INCONSISTENT` | 绑定了瞬态 `p1_recovery_design.py` hash `6017...`，当前冻结 hash 为 `b556...` |
| regression evidence v1 | `PARTIALLY_COMPLETED_FAILED` | 116 passed、2 failed、1 skipped |
| integration reproducibility manifest | `MISSING` | 中断前未生成 |
| `patches/scoring_date_v2/` 旧补丁包 | `INCONSISTENT_SUPERSEDED` | 把六项 AI proposals 描述为 human patch，且 merge 脚本会强制覆盖；后来的 v3 README 明令禁止使用 |

旧回归还暴露一项 provenance 问题：它运行的两个 legacy Stage A 测试在 Python 子进程中解析了真实 restricted key，却把 `restricted_unblinding_key_read` 记录为 false。测试输出没有显示映射，没有计算 condition-level audited results，也没有证据表明研究者看到了映射；且研究者提交已在该测试之前冻结。因此这是一项程序性盲法事件，不会改写研究者判断，但“中断会话从未读取 key”的旧声明不成立。本次恢复续做没有解析 key；相关测试已改为真实 key 仅做存在性/SHA-256 检查，语义和映射测试使用 synthetic key。

## 3. Recovery matrix 与研究进度

| 项目 | 当前分类 | 科学含义 |
|---|---|---|
| P0 validation | `COMPLETE_AND_VERIFIED / FROZEN` | acceptance evidence 为 PASS；不重开历史验收 |
| P1a initial factorial pilot | `COMPLETE_AND_VERIFIED_DEVELOPMENT` | 96 outputs 和 96 researcher-confirmed annotations 已登记；不是 confirmatory evidence |
| P1b complex-task pilot | `COMPLETE_AND_VERIFIED_DEVELOPMENT` | 192 条确认记录与 integrity evidence 完整；模板/任务覆盖限制保留 |
| P1c history/temporal diagnostic | `COMPLETE_AND_VERIFIED_EXPLORATORY` | 72 条确认记录；R/T/P 仍是 package effects，不证明纯机制 |
| P1d model/format diagnostics | `COMPLETE_AND_VERIFIED_DIAGNOSTIC` | 已完成限定 development diagnostics；main independent validation 仍 `NO-GO / UNEXECUTED` |
| P1 C0 calibration | `COMPLETE_AND_VERIFIED` | A_C0 32 attempts，历史 seal 完整 |
| P1 O/Q recovery | `COMPLETE_AND_VERIFIED` | D0 8 个 archived outputs 复用；D1-D3 共 24 个历史新生成；本次未重复 |
| P1 Stage A preparation | `COMPLETE_AND_VERIFIED` | 408 条互斥候选规格、0 generation；冻结来源和 manifest 验证通过 |
| Researcher annotation integration | `NEWLY_COMPLETED_AND_VERIFIED` | 32 条真实判断已导入为保留原值的版本化视图 |
| Temporal scoring audit | `NEWLY_COMPLETED_AND_VERIFIED` | 无 confirmed registered-date substitution defect；v2 audit 取代 stale v1 provenance |
| Stage B | `READY_BUT_NOT_AUTHORIZED / NOT_EXECUTED` | 只表示离线前置条件满足；仍需未来授权和 live preflight |

仍未做且本任务不授权：解盲、D0-D3 条件选择、condition-level audited 结果、Stage B generation、LoRA、P2/P3/P4/P6 恢复、模型切换、prompt 或配置修改。

## 4. 研究者注释完整性

权威输入：`docs/validation/p1/blinded_audit_stage_a_v1/blinded_researcher_audit_RESEARCHER_FILLED_DATE_RULE_v3.csv`。

- SHA-256：`b0e8cff9b80bdb6055d81333fc0a42a3117e1d5a3bc043f7dcce4cd9aa8ecb84`，与先前报告值完全一致。
- 32 records、32 unique `anonymous_review_id`；ID 集合及 shuffle 顺序与冻结 blank sheet 相同。
- 按 anonymous ID 核对，`original_question`、`registered_evaluation_date`、`trusted_evidence`、`frozen_reference_answer`、`complete_raw_model_response`、`required_answer_components` 均 0 mismatch。
- task/factual/temporal 判断、failure type、comment 和 researcher name 全部非空；研究者名 32/32 为 `Yaxin ZHENG`；未伪造 review timestamp 或第二 reviewer。
- 分布：task Success 16 / Failure 16；factual Correct 16 / Incorrect 16；temporal Correct 16 / Incorrect 16；failure type 为 None 16、Temporal selection error 15、Missing required component 1。
- 冻结 blank sheet SHA-256：`5bc9712ef9c5ad0e2a1769e55d99b72f7a4e99ab9e77a4657a605b642bfb1781`。
- derived Stage A compatibility CSV SHA-256：`b7b6c40900d42b03643808db4aa74d57f1f776e651b21dfb512f328586211cad`。它只做显式 label mapping，v3 仍是权威提交。
- README 记录原始手工 `csv.txt` 标签 hash 为 `cea5090418633b2ec153becbd27600ee1d6a71645134aad536ad77908ddba8d7`；该单独源文件当前不在项目内，故只能保留记录值，不能重新哈希。项目内未发现安全导入 ZIP。

`PersonaSLM_six_proposals_NOT_APPLIED_v3.csv` SHA-256 为 `49d423a8f3ec10ce52c64d9cd9561173773da012ef73d223c6b48cf4eb143275`。它包含 source rows 6、16、17、22、27、29 的 13 个字段级 AI proposals；所有 `researcher_original_value` 仍与 v3 一致，0 项被应用。第 17、27 行的实质性分歧继续作为独立 provenance 层保存，不以 aggregate result 或 AI proposal 覆盖研究者判断。

## 5. 时间评分实现审计

结论：**没有确认 `registered_evaluation_date` 替代问题明确日期的实现缺陷。** 因此没有创建新的 corrected scorer，没有覆盖历史评分，也没有生成伪造的 32-row original/corrected 差异表；该比较为 `NOT_APPLICABLE`，而不是声称“32 条差异均为零”。

实际调用链：

- `tools/p1_recovery_measurement_v2.py::automatic`：D0/D1 调用 `p1_measurement_scoring_v2.score`；D2/D3 调用冻结的 `p1_recovery_design.score_single`。
- `tools/p1_measurement_scoring_v2.py::temporal_check`：使用 `c['requested_date']` 与证据有效期，不读取 `evaluation_date` 或 `registered_evaluation_date`。
- `tools/p1_measurement_scoring.py::score`：dated comparison 逐项把 `march_bay` 绑定到 March、`september_bay` 绑定到 September；日期和值互换不会成为 Success。
- `tools/p1_recovery_design.py::reference_audit`：按 component-specific date 检查证据链、有效期和唯一 witness。
- `tools/p1_recovery_design.py::q1` / `score_single`：Q1 使用单个 requested date；只接受预先冻结的整答 aliases。
- `tools/p1_conditional_execution.py::automatic`：未来 Stage B 保留相同分派；尚未执行。

32 行日期核验：16 行问题包含 `2051-03-15`，原始 source rows 正是 3、4、6、8、9、10、11、12、14、16、20、22、23、26、27、32；其中 6、16、22、27 为双日期比较。另 16 行为 September-only。所有 component requested date 都存在于原问题中；`registered_evaluation_date=2051-09-15` 仅作为 metadata。

alias 规则没有根据观察到的输出扩张：Q0 只规范已声明的 Bay/Zone/Gate type syntax；Q1 只做 NFKC、空白折叠、casefold 和单个尾随句点处理，并接受冻结的完整 `Bay B...` / `B...` aliases。自由说明、否定、多个候选或未知语法不会被静默改成 Success。

已知但不构成本 32-row defect 的范围限制：dated-comparison 的自动 temporal secondary endpoint 保守返回 `Unverifiable`；Q1 没有独立自动 temporal/completeness endpoint；`stale_state()` 的裸值规则不是通用任意日期解析器。冻结 O/Q 输入没有显示这些限制导致 registered-date substitution。更早的 v1 FC/TC label coupling 已由既存 `p1_measurement_scoring_v2.py` 版本化修正，并非本次新发现。

## 6. 历史输出、候选和预算完整性

当前权威 O/Q raw audit 重建 24 attempted / 24 results / 0 blocked；run manifest SHA-256 为 `c235e309a3726952fc1edc2f96a9259d537293bd4e61ce0a24e9234abfdb5404`。8 个 D0 prompt/raw/request/token hashes 保持 byte-identical，`D0_regenerated=false`。旧 v1 auditor 对后续 v2 journal 报告 reordered/unplanned 是 superseded auditor 的版本不兼容，不是 raw corruption。

Stage A manifest index SHA-256：`799a95f0edc033b1af56ef937f56954ac43ffed14f21871df6beca4e74b2078a`。验证结果为 `PASS_CANDIDATES_NOT_EXECUTION_AUTHORIZATION`：

| 候选 | 规格数 | SHA-256 |
|---|---:|---|
| D0 | 80 | `157afc1ca2243c58527f41c90cf120cdd215e51c6a17a01a65bf3bf7bd55568a` |
| D1 | 80 | `1cba4398e7e63dc2e077648b2a038a767ffb10e5a0444435b07921723d89a920` |
| D2 | 80 | `6936bd214e8691786366ecbc80cfb1ae56231f2a1645016dc2e691164e8b6016` |
| D3 | 80 | `d0b3e4f45e4abe729899f981f85044140c6cef23e320f25aa0e9e29997ba60c9` |
| Minimal temporal | 80 | `6bc6421823371b9cad6140aad1046a3f9aebc2d4594e277b3601a3f4b6fc849e` |
| Fallback calibration | 8 | `b23b9a35bba1ff9313e71f75759e8107b3d23b54f765c5fe736094263ff17cde` |

五个 pilot 均为 8 cases × `C0-C7/N_style/N_history` = 80，前 8 条为 C0，余 72 条为其他条件；prompt/token/request hashes、native tokenizer records、固定参数、case/speaker/template ancestry、evidence/date/current/outdated/reference/aliases 均可重建。配对 controls token 等长，但这不证明语义中立。16-case fallback bank 为 8 calibration + 8 disjoint pilot cases；allocation seed 731901，construction seed 731902。

Stage A reproducibility manifest 在只读恢复 checkpoint 为 435/435 hashes 匹配。本次随后按治理要求追加 `docs/research_development_log.md`，并修正 `tests/test_p1_blinded_stage_a.py` 以阻止真实 key 解析；因此旧 Stage A seal 的最终重核为 433/435，唯一两个差异正是该 append-only log 和该安全测试，0 missing。冻结 scientific manifests、raw outputs、prompts、ledger、scorers 与 key bytes 没有差异；新的 recovery reproducibility manifest v2 封存修改后的 log/test 及差异原因。restricted key 仅做 hash 校验：43,620 bytes，SHA-256 `8ab628c1a74a7fbb3f09c0a8f266359ab32d6c9835db39f4afe3406647dc896f`，与冻结记录一致。

权威 ledger：A_C0 32、B_FACTORIAL 0、C_DIAGNOSTIC 40，共 72/160；余 88 = B_FACTORIAL 80 + C_DIAGNOSTIC 8。archived D0 reuse、tokenization、candidate manifests 和本次 Codex API/tool calls 均不计科学模型 generation。本次实际科学 inference：**0**；预算消耗：**0**。

## 7. 测试和错误记录

本次实际执行：

1. `p1_researcher_audit_integration.py validate`：PASS，32 records。
2. 最小日期/导入集：22 passed、0 failed；1 个既有 pytest `cache_dir` 配置警告。
3. 最终相关 P1 回归：126 passed、0 failed、1 skipped；skip 原因是 `tests/test_p1_recovery_2x2.py:113: Run requires actual annotation export`；同一既有配置警告仍存在。
4. Stage A candidate validator：PASS；当前 O/Q v2 raw audit：PASS。

最终回归覆盖 March-only、September-only、multi-date component binding、正确值错日期、outdated adoption、正确日期错实体、missing component、partial/contradictory answer、truncated 但语义完整、正确组件加未完成尾部说明、exact/frozen aliases、missing/unverifiable 分离、EOS 不证明完整性、token-limit 不自动等于任务失败。

恢复期间发生并已修复的一项非科学错误：首次启动完整回归的 wrapper 因新增隔离环境变量但遗漏 `import os`，在 pytest 启动前抛出 `NameError`；未运行测试、未写 evidence、未推理、未访问 key。补入 import 后原命令通过。

## 8. Stage B readiness

| 前置条件 | 状态 |
|---|---|
| 32 researcher records imported/validated | PASS |
| researcher identity recorded | PASS |
| original labels/scores preserved | PASS |
| AI proposals separate | PASS |
| temporal scorer audited | PASS；无新 defect/repair needed |
| regression tests | PASS：126 passed / 0 failed / 1 justified skip |
| scorer-version decision | PASS：保留 frozen v2；新 date scorer 不适用 |
| key integrity | PASS_BY_HASH_ONLY；旧自动化解析事件已披露 |
| frozen manifests/raw outputs | PASS |
| ledger/budget | PASS：72 used / 88 remaining |
| unblinding/selection/inference | NOT EXECUTED |

**最终状态：READY。** 下一项可授权的研究者动作是以后单独发出 Stage B 明确指令；本报告中对该指令的描述不构成激活。即使未来获得授权，若 live RAM 或 runtime identity preflight 不通过，也必须停止，不能绕过 3 GiB 门槛。

## 9. 科学限制

Minimal temporal fallback 只测 dated history 下的 outdated-answer adoption，不独立验证一般对话可靠性、coherence、linguistic/behavioral Persona Fidelity、真实说话者外部效度或一般模型能力。N controls 是 diagnostic controls；token matching 不等于 semantic neutrality。所有当前候选仍是 development material，不得表述为 confirmatory experiment。P6 负结果和无算法新颖性结论保持不变。

## 10. 本次修改与保持不变的对象

本次恢复续做仅：

- 修正累计 ledger 测试，使原 16-request diagnostic milestone 与后续 24-request O/Q recovery 的当前累计 40 明确分离；
- 增强日期绑定回归；
- 把真实 key 测试改为 hash-only / synthetic-key；
- 生成 versioned scorer audit v2、passing regression evidence v2、本报告和 reproducibility manifest；
- 追加真实开发 provenance 日志。

保持不变：研究者 v3 CSV、所有 researcher labels/comments、旧 AI proposals、historical automatic/AI scores、raw responses、references、trusted evidence、prompts、model settings、frozen manifests、authorization ledger、restricted key bytes、Git history。未 commit、未 push、未修改 Git identity。

建议提交信息（仅供研究者）：`Recover P1 reviewer audit and validate temporal scoring readiness`
