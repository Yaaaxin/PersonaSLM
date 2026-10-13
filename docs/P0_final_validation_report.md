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

> **Current researcher-decision update:**24/24 new candidate decisions are registered as AI-assisted human review. N_style:6 REVISION_REQUIRED; History A:6 ACCEPT_NARROW; History B:6 REJECT_AS_NEUTRAL; History C:6 DIAGNOSTIC_ONLY. The official65-column conversion preserves336 supplied checks but has18 missing suitability labels,6 disallowed N/A labels and81 missing required field-quote associations. **P0 PARTIAL; P1 NOT STARTED;334 tests passed.** See [the current decision and acceptance report](P0_control_decision_registration_report.md). Earlier review-status statements below remain historical records.

> **Current update — 2026-10-12T21:09:15.271521+00:00: P0 PARTIAL; P1 NOT STARTED.** Final review v3 presents the unchanged24 candidates; all24 exact matches and444 original native tokenizations reconcile offline. New human review0/24 remains OPEN; original40/40 reviews remain complete. 307 tests pass. See [the current control validation report](P0_final_neutral_control_validation_report.md). Earlier dated evidence remains intact.

> **Current update — 2026-10-12T20:45:56.264380+00:00: P0 PARTIAL; P1 NOT STARTED.** Historical human review remains complete (40/40). New development controls have 24/24 exact tokenizer matches across six cases and four families, with 0/24 new human reviews; semantic acceptance is OPEN. The full suite passes 285 tests. See [the v2 control-development report](P0_control_development_report_v2.md). All earlier dated evidence below is retained.

> **Current assessment — 2026-10-12T20:13:26.793933+00:00:** Human annotation **PASS, 40/40 completed**; final review is AI-assisted and not blind. Semantic-control validity remains **PARTIAL / resolution OPEN**; researcher overall ratings are PASS 0 / PARTIAL 40 / FAILED 0. Overall **P0 PARTIAL; P1 NOT STARTED**. See the [current control acceptance report](P0_control_acceptance_report.md) and [researcher annotation report](P0_researcher_annotation_report.md). Tests: **263 passed**. All earlier status/readiness statements below are preserved dated history, including earlier 0/40 review counts.

# P0 Final Validation Report

**Latest policy assessment:** [P0_policy_acceptance_report.md](P0_policy_acceptance_report.md). Bounded instrumentation and evaluation-policy checks PASS; human neutral review OPEN (0/40). Overall PARTIAL. Earlier assessments are preserved as history.

**Current final-methodology update:** 16 new boundary-development responses, 134 preserved responses in total; P0 PARTIAL. The [current blocker classification](P0_remaining_blockers.md) distinguishes mandatory methodology from acceptable limitations and future work. Earlier sessions below remain historical evidence.

**Latest update:** see the [English methodology acceptance report](P0_methodology_acceptance_report.md) and the completion addendum at the end of this file: 118 total recorded generations, overall P0 PARTIAL. The earlier 100-generation session below is preserved as history.

2026-10-12。**Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**。Research Protocol v1.1；Controlled Empirical NLP Study；长期目标为 Real-Speaker Persona Modeling。

**最终决定：P0 研究验收 PARTIAL；真实 CPU adapter execution PASS；P1 BLOCKED。** 已审计研究者原 C0 的 20 次生成，另完成 C1、N_style、C3、N_history 各 20 次。没有重跑原 C0，没有实际聊天数据、LoRA 或新 Persona 算法。

## A. 实际推理结果及原 C0 审计

原 C0 为 `results/p0/20261012T163840-d0e467a28a4e4df89eb35ce788dfa917/`，UTC `16:38:40.710929` 至 `16:41:52.707548`。检查 manifest、271 个事件和 server.log；`audit-run` 退出 0。20 个不同 case IDs 分别关联 prompt、tokenization、generation request、raw、parser 和 case_result；没有用总请求数替代案例计数。

原始文件与本轮开始保存的 SHA-256 清单完全一致。所有新增审计另存，没有给旧 manifest 补造 Git、prompt hash 或内存字段。旧的缺少配置阻塞运行也保留。

下表仅为**保存的窄域城市规则输出**，不是一般事实准确率或人工语义真值：

| 条件 | 实际独立案例 | raw 非空 / 空 | Parser preserved / 失败 | 原规则 correct / incorrect / unknown | 后端 stop |
|---|---:|---:|---:|---:|---|
| C0 | 20 | 20 / 0 | 20 / 0 | 20 / 0 / 0 | limit × 20 |
| C1 | 20 | 20 / 0 | 20 / 0 | 20 / 0 / 0 | limit × 20 |
| N_style | 20 | 20 / 0 | 20 / 0 | 20 / 0 / 0 | limit × 20 |
| C3 | 20 | 20 / 0 | 20 / 0 | 6 / 14 / 0 | limit × 20 |
| N_history | 20 | 20 / 0 | 20 / 0 | 20 / 0 / 0 | limit × 20 |

合计 100 次已保存生成，其中 80 次为本轮新增；每次后端报告 generated tokens=96，返回 96 个输出 IDs。请求/响应/案例链一致，无 HTTP 生成失败、输入计数错误或上下文截断。原 C0 每例 76–81 输入 tokens。具体字段和实际原文见 [P0_case_audit.json](validation/P0_case_audit.json)。

**评分器审计限制：**C3 的 14 条原规则判错均须复核。其中 9 条命中 dated “lived in … in YEAR” 的疑似误判模式，另 5 条涉及省略时态的生成问答、`back then` 或 `was living`，见 [机器筛查](validation/P0_evaluator_review.json) 与 [逐例技术补充](validation/P0_evaluator_review_addendum.md)。例如回答正确给出 Rennes，再续写 “lived in Nantes in 2025”，legacy 规则把旧城市再次出现误当成当前冲突候选。**不能把 14 直接解释为已确认事实错误数，也不能自动把它们全改判正确。**人工真实错误数尚未确定。

许多输出继续自编多轮问答、年龄/职业或更早年份事实。当前城市首答看似正确，不代表额外内容有依据。原文完整保留；没有截取好看的首句或按输出好坏选择案例。

## B. 模型身份和固定来源

详见 [P0_model_provenance_report.md](P0_model_provenance_report.md)。

| 层级 | 状态 | 证据 |
|---|---|---|
| File Integrity Verification | PASS | 本地 GGUF 1,270,808,256 bytes；SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` |
| GGUF Metadata Verification | PASS | 实际加载 GGUF V3，architecture qwen35，Base，Q4_K Medium，320 tensors |
| Published Artifact Identification | PASS | 第三方 aashish1904/Qwen3.5-2B-Base-GGUF；固定 revision `765d2baaa04dbb8d6df3e78af571e6beaa4373d7`；公开 API 的 LFS 摘要/大小独立匹配 |
| Upstream Model Lineage Verification | PARTIAL | 声明上游 Qwen/Qwen3.5-2B-Base；官方 Base 用途及本地元数据相符，但转换/量化过程没有独立证明 |

llama.cpp 实际版本 `0.6.0-dev (build 11573, commit 0f701c882)`；exe SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` 与预期一致。文件名和本地配置标签均未被当作单独身份依据。固定 revision 的 README HTTP 404 保留；API 200 不覆盖该失败。

## C. CPU 环境与实测成本

| 项目 | 实际观察 | 范围 / 限制 |
|---|---|---|
| CPU | AMD Ryzen 7 PRO 5850U with Radeon Graphics，8 physical cores / 16 logical processors | CIM 只读查询与 llama.cpp CPU 名称相符 |
| RAM | 内存条安装容量 16 GiB；OS 可见 12,698,714,112 bytes，约 11.83 GiB | 分别记录，未推断差额用途 |
| OS | Windows 10 Professionnel，10.0.19045，64-bit | CIM 观测时间 `2026-10-12T19:04:23.7088598+02:00` |
| 推理线程 | 日志 `n_threads=4 (n_threads_batch=4)` | HTTP 服务另有 15 个工作线程；“4 线程”指模型推理线程池，不是进程总线程数 |
| 上下文 | 实际 `n_ctx=4096`、`n_ctx_seq=4096`、单 slot | 模型训练元数据 262144 不等于本次可用上下文 |
| CPU-only | 实际 `offloaded 0/25 layers to GPU`，model/KV/RS/compute buffers 均为 CPU | 参数 `n_gpu_layers=0` 与观测相互佐证，不仅凭命令行宣称 |
| 新运行内存 | 96 次成功 Windows API 观测；available physical 1,004,601,344–1,900,142,592 bytes；观察到的最高 peak working set 2,486,325,248 bytes | 这些来自 8 个新生成进程；不是 C0 历史内存；不等于持续采样的所有系统峰值 |

逐请求 HTTP 墙钟时间（包括后端请求处理及往返）如下；详细 native prompt/eval timings 同时保存。这些是工程观察，期间有测试/审计活动，不用于条件速度效应推断。

| 条件 | 输入 tokens 范围 | 逐请求延迟范围（秒） |
|---|---:|---:|
| C0 | 76–81 | 8.545–11.953 |
| C1 | 114–119 | 8.408–9.214 |
| N_style | 114–119 | 8.399–10.690 |
| C3 | 117–123 | 8.516–10.703 |
| N_history | 117–123 | 8.288–9.538 |

原 C0 verbosity 较低，能观察 4 个 threadpool 线程、4096 slot 和模型路径，缺少详细 buffer/offload 和内存记录。新 tokenizer/控制运行开启 verbosity 4 以补充真实 CPU 证据，不把后来观测冒充 C0 当时测量。

## D. Real Tokenizer Validation

受控同一 llama-server 进程的 `http://127.0.0.1:8080/tokenize` 与 `/completion` 绑定同一 `/props.model_path` 和 build。全部 100 例保存的 tokenizer IDs = prepared IDs = 请求中的 IDs；实际 evaluated token **数量**一致，truncated=false。

后端 response 的 `prompt` 是解码字符串，**100 例均未返回 evaluated input ID 数组**。因此“后端内部逐 token 评估 IDs 与输入独立核对”仍为 PARTIAL，不使用输出 IDs 或重新 tokenization 假冒缺失字段。输出 token IDs 则真实返回，每例 96 个。

特殊 token 探针：`Hello` 为 `[9419]`；切换 add_special 不增添 BOS。字面 `<|endoftext|>` 在 parse_special=false 下返回 `[27,91,8426,703,419,91,29]`，true 下为 `[248044]`。案例 001 C0 prompt 的四种 add/parse 组合均为 78 tokens；GGUF 的 add_bos_token=false 与观察相符。实际生成策略仍为 true/false，不因探针更改。

## E. Controlled Token Matching

全部 20 例先冻结，再对 C1–N_style、C3–N_history 各 20 对用实际完整模板计数。所有条件的可信证据位于同一模板位置（指令之后、附加上下文之前），证据文本/摘要、当前问题和固定 recent conversation 保持不变。逐对 case_id、reference/neutral condition、两边计数、差值、matching_status、evidence hash、template version 均在 [P0_control_matching.json](validation/P0_control_matching.json)。

| 验证轮次 | style 结果 | history 结果 | 处理 |
|---|---|---|---|
| v1 原 Cartesian 枚举 | 20 对失败；256 次/例，best delta −3 | 20 对 delta=0，14 例第 7 次、6 例第 15 次成功 | 零生成；保留全部候选和请求 |
| v2 交错句数 | 20 对仍失败；256 次/例，best delta −1 | 复用已成功结果 | 零生成；继续保留失败 |
| v3 multiset 枚举 | 20 对 delta=0，第 169 次/例成功 | 复用已成功结果 | 冻结通过结果，生成前再核对实际 IDs |

诊断是候选预算覆盖问题：原枚举优先耗尽短文本，交错后仍因相同句子排列消耗预算。最终只调整遍历，减少重复排列；没有放宽 **tolerance=0** 或增大 **max_candidates=256**，没有改变句子库、证据、问题、句数上限或按模型回答调参。P0 候选构造修正不证明中性操纵有效。

## F. Neutral Semantic Audit

**PARTIAL，独立人工判断 0/40。** 技术检查/逐文本审阅未发现已知城市答案泄漏、相互矛盾的新个人事实、明确强风格命令、证据/问题改变或相对 reference 新增日期。实际中性文本仅有三种形态，逐例文本及问题见结构化审计。

N_style 的文本为：

```text
The page is plain. This is a text record. The heading is printed above the text. The heading is printed above the text.
```

重复句子以及共享的 `Speaker style profile:` 标题可能影响输出风格。N_history 保留 `Historical dialogue (2025-05-12)` 和 User/Alice 标签；正文是 `The page is plain.` 或 `This is a text record.` 配合 `The heading is printed above the text.`。日期是有意保持的格式控制，不应解释成已经去除全部时间语义。

[40 条盲审文件](validation/P0_neutral_blinded_review.jsonl) 隐藏 condition/model/output，保留证据、问题和实际附加文本；人工字段均为 null。映射另存本地，文本形式仍可能暴露条件类型，因此不能声称完全盲化或已经获得人工 agreement。

## G. Generation / Parser Audit

真实观察：preserved=100，direct_eos=0，stop_without_visible_text=0，newline_truncation=0，parsing_or_filter_removed=0，raw/parsed 空=0。全部 stop_type=limit，96 输出 tokens；没有观测到真实 EOS 首 token 空响应。五种机制的实现有合成单元测试，但合成演示不算真实出现频率。

原始响应在解析前持久化；Parser 仅做已记录的去首尾空白等操作，保留自编多轮续写。Backend finish reason、generated IDs、native timings、HTTP latency、Parser 分类及窄域 evaluation 同时保存。长度停止是既定解码上限，不能误标为 newline_truncation 或生成崩溃。

## H. Reproducibility Audit

9 个生成 run 的完整日志链通过，两次离线重建所得输入和 Parser/评分结构一致；3 个 tokenizer journal 也通过（10801、10391、6903 个事件）。原 C0 的 273 个文件（manifest、271 events、server.log）逐文件 SHA 与初始清单一致。

新运行保存 Git SHA/dirty、源码/工具快照、精确 JSONL、模型/后端摘要、实际 prompt 和摘要、IDs、seed/参数、时间、内存、raw/parsed/评分。C0 缺少 Git runtime state、内嵌数据/源码和运行时内存；prompt SHA 在旁路标为事后重建。公开派生报告不包含完整原始归档包。详见 [可复现性报告](P0_reproducibility_report.md)。

`replay-run` 已实际测试；它不调用模型，不证明输出确定性。没有重复生成来追求相同结果，没有给旧记录补造 provenance。

## I. Automated Tests

`.\.venv\Scripts\python.exe -m pytest -q`：**123 passed，0 failed，0 warnings，exit 0**。pytest 时间 **18.97s**，捕获进程墙钟 **20.55s**，UTC `17:16:04.402013`–`17:16:24.951856`。先前 113/119/122 的各轮真实结果保留；不将软件替身测试算作模型实验。

## J. Final Acceptance and K. Remaining Blockers

[完整逐要求验收表](P0_acceptance_checklist.md) 区分 PASS / PARTIAL / BLOCKED。整体 **PARTIAL**，不签署 P0 research PASS。

1. 完成中性语义独立人工审阅，判断重复句子、style heading 和日期包装的残余影响；当前 40 条尚无人工判定。
2. 对原评分器的 14 条 C3 判错做独立复核；版本化修订 dated-past/生成多轮上下文规则后，仅追加新的离线评分结果，保留原判定。
3. 补充第三方量化的上游固定权重、转换/量化配方及独立核验证据；二进制公开身份已核实，保真度未核实。
4. 明确接受或补充 evaluated input IDs 的后端证据缺口；当前只能核对实际提交 IDs、解码文本和评估数量。
5. 旧 C0 的 Git dirty/commit 和运行时内存无法从现有记录恢复为当时测量；必须作为历史限制保留。新运行已补齐工程记录，后续原始归档分发仍由研究者安排。

旧 `.pytest_cache` ACL 问题、没有日志数字签名/自动恢复等操作限制也保留。P0 的观察不支持 Persona 改善或损害可靠性、history/style 导致错误、一般事实准确率或真实说话者建模能力结论。

## L. Run Inventory and Files

新运行均在 `results/p0_validation/20261012T164648/controlled_runs/`，首批/扩展不重叠：

| 条件 | 001–003 run ID | 004–020 run ID |
|---|---|---|
| C1 | `20261012T170623-1fbff71fcc3a46bd9d5f9df9973792dd` | `20261012T170849-65b0427279ef4b9c9d9d627104764189` |
| N_style | `20261012T170654-853f132c954a4ac085058567c7df04b5` | `20261012T171126-7da62ccbcf6d48bdb31263e7a6ca4522` |
| C3 | `20261012T170725-050387bc4d014a54b75c6ad8dbe803f5` | `20261012T171425-49348e3925ff452f9069004c011878c9` |
| N_history | `20261012T170756-124bed2004264404b7fd1bb21884347a` | `20261012T171723-dae18c8d3eba4c9c9a7e31f5f1c5ba99` |

源码变更：`cli.py`、`matching.py`、`runner.py`、`server.py`，新增 `observations.py`、`reproducibility.py`、`run_audit.py`。测试：`test_matching.py`、`test_runner.py`、新增 `test_run_audit.py`。工具：`tools/p0_capture.py`、`p0_validate.py`、`p0_review_controls.py`、`p0_fetch_provenance.py`、`p0_export_evidence.py`。

文档：README、P0_status、P0_real_inference_report、P0_acceptance_checklist、research_development_log；新增本报告、P0_reproducibility_report、P0_model_provenance_report 和 `docs/validation/P0_*` 派生证据/盲审材料。AGENTS、协议、annotation guidelines、合成数据和原始 C0 未修改。完整实际命令/时间/退出码和失败在 [开发日志](research_development_log.md) 及本地命令 JSON，公开索引见 [P0_final_commands.json](validation/P0_final_commands.json)。

## M. Suggested Commit Message

`Complete P0 CPU validation and reproducibility audits`

所有变更留待研究者审阅并提交。Automated development tools 没有 commit、push、改写历史或修改作者配置。

## 2026-10-12 Methodology Completion Addendum

Recorded: 2026-10-12T18:06:22.204470+00:00. Earlier history is retained.

The latest decision is **PARTIAL**. See the complete English [requirement table](P0_methodology_acceptance_report.md), [budget diagnostic](P0_generation_budget_diagnostic.md), [C3 evaluation audit](P0_evaluation_audit_v2.md), and [human review instructions](P0_neutral_review_instructions.md).

The previously completed 100 responses remain untouched. The lexicographically first three synthetic cases under C0/C3 were frozen before 18 new generations at 96/192/256 tokens. All 18 reached their respective limits, returned nonempty raw text, and were classified as parser-preserved; none reported EOS/EOG. Initial replies were followed by generated dialogue continuations. Raising the cap alone did not establish natural termination. No template, stop sequence, sampling parameter, trusted evidence, question or predeclared applicability was changed.

The 40 historical neutral matches retain zero token difference. A new English CSV/JSON review packet includes all six requested checks, with zero completed human ratings. C3's 14 original incorrect responses have a separate versioned audit: 2 historical city contradictions, 11 unverifiable whole-output city assessments, and 1 supported assessment. All 14 hit the length limit; their legacy current-conflict reasons are not supported as current-city conflicts. Those overlapping diagnostics do not justify rewriting all 14 as correct or treating the old count as scientific ground truth.

All 19 journals verified; all 15 generation runs / 118 responses reconstructed identically on two passes. All 13 historical inventories stayed unchanged. New manifests record Git SHA `8ffe1fdeb64ccc85182d2ff983b514940ecb6f70`, dirty=true, and exact source/tool/data snapshots. Tests: 147 passed, 0 failed, 0 warnings; exit 0; pytest 18.07s, process 18.937s. The failed intermediate negation regression remains in the command archive.

The [English language-scope addendum](research_protocol_v1.1_language_scope_addendum.md) applies prospectively. Historical experiments and language metadata were not rewritten or translated. Original English synthetic provenance is recorded in the diagnostic freeze. Human semantics, response-boundary validation, independent evaluation adjudication, upstream quantization fidelity, missing evaluated input IDs and historical C0 provenance gaps remain qualified. No P1, LoRA, MimooPet access, commit or push occurred.

## 2026-10-12 Final Methodological Validation Addendum

Recorded 2026-10-12T18:43:52.286335+00:00. Historical sections retained.

**Overall P0: PARTIAL. P1: BLOCKED.** The latest assessment is [Remaining Blockers](P0_remaining_blockers.md), which explicitly separates mandatory methodological blockers from acceptable documented limitations and later research. Natural EOS, a fully reproduced upstream quantization pipeline, and an unsupported backend evaluated-ID interface are not blanket P0 prerequisites.

The response unit remains unresolved across the intended development scope. Four newly authored English cases, disjoint from the historical case IDs/speakers, were frozen before 16 requests at a fixed 96-token budget. T0/T1 use the existing transcript without/with role stops; T2/T3 request a literal end marker without/with its stop. All 16 requests completed. T0/T2/T3 reached 96; T1 stopped at 9/23/9/11 tokens. EOS/EOG 0. Supplementary structure checks pass 2/4 in each of T0/T1 and 0/4 in T2/T3. The original v1 check missed uppercase USER in one ordinary task; its old classifications and raw payloads remain unchanged alongside the supplementary correction. A literal-role challenge also remains invalid; no extra experiments were run to manufacture a pass. See [termination diagnostics](P0_response_termination_diagnostics.md).

A complete reply is operationally a nonempty, bounded assistant turn with no extra role turns or delimiter/content ambiguity, followed by a separate check of whether it completes the requested components. Token limits, punctuation and factual correctness do not alone establish this. Backend string stops are allowable recorded interventions when validated. Current examples support only a restricted observed scope; no online revised case-insensitive/escaping rule has been adopted.

The new [English annotation form v3](P0_neutral_annotation_form_v3.md) exposes case/condition/reference IDs, actual neutral text, full-prompt token counts/differences, evidence and six PASS/FAIL/UNCERTAIN fields plus reviewer notes. All 40 remain blank. The form is unblinded as requested; software imports are versioned, hashed, immutable and traceable. A real empty-form CLI import was rejected without creating a review. Positive import tests are explicitly simulated test doubles, not human judgments.

The new [evaluation v3 audit](P0_evaluation_validity_v3.md) distinguishes Correct, Incorrect, Unverifiable and Not Applicable. Independent synthetic checks cover the six requested categories, inapplicability and conflicting source facts. All 24 declared contract checks pass; a separate regression additionally preserves the v2 foreign-subject failure. Six of 22 development texts expose v2 scope problems. The historical 14 C3 results remain unchanged, with separately saved v3 counts 2 Incorrect/11 Unverifiable/1 Correct. No unsupported claim was silently converted to Incorrect. V3 remains a narrow English residence-claim audit, not general semantic truth or an automatically selected production evaluator.

Mandatory closure: validate the intended reply boundary, complete independent review of all 40 controls and resolve issues, and freeze a scoring unit/policy consistent with that boundary. P1 does not require retrospective human relabeling of every old diagnostic or a perfect general-purpose automatic judge. P0's bounded software checks are useful but do not authorize a scientific comparison yet.


## 2026-10-12 Frozen Response and Evaluation Policy Acceptance

Recorded 2026-10-12T19:19:43.094673+00:00. The [current English acceptance report](P0_policy_acceptance_report.md) provides the full checklist and evidence. **P0 PARTIAL; P1 BLOCKED; neutral-control human review OPEN (0/40).** Earlier statuses below/above remain dated historical records.

Frozen `response_status_v1` and `separate_axes_policy_v1` passed their scoped instrumentation checks. Software holdout: 24/24 classifications and spans, six AMBIGUOUS, 75% decided coverage; author-specified software expectations, not human semantic accuracy. Six new real responses: 5 CROSS_TURN and 1 AMBIGUOUS; all hit the 96-token cap, EOS/EOG zero. Actual real-output classification accuracy is unavailable without independent labels. Policy sources did not change after holdout access; the original four development examples were not reused for prompt optimization.

The new scoring unit is the identifiable first reply/prefix, with exact raw/excluded text retained. Separate factual categories, completeness, relevance, temporal consistency and coherence are stored. New bounded factual accounting: 1 Correct, 0 Incorrect, 5 Unverifiable, 0 Not Applicable; no scalar accuracy/effect claim. Legacy scores remain untouched. Unsupported claims and incomplete outputs are not automatically wrong.

The mandatory outstanding action is independent neutral-control review and resolution of findings. Natural termination, general semantic accuracy, upstream quantization fidelity and unavailable backend input-ID arrays are scope-qualified limitations. The policy-definition and bounded instrumentation work is now complete; future use must retain logged versions and independent annotation routing. Tests: **223 passed, 0 failed, 0 warnings reported, 13.28s, exit 0**. All 20 old journals are byte-identical, the new journal replays twice identically, and 140 raw responses are retained across 17 generation runs.
