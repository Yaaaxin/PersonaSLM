# P0 evaluator review addendum

2026-10-12。本记录为 Automated development tools 对已保存原文的技术审阅，**不是独立人工标注**。没有改写任何原评分或模型输出。

[机器筛查文件](P0_evaluator_review.json) 标记了 9 条含 “lived in … in YEAR” 的疑似时态误判。另有 5 条 `incompatible_city_also_asserted` 未命中该表达式，但同样需要对话级复核。全部 14 条都是 C3，完整原文、输入和原判定在 [逐例审计](P0_case_audit.json)，可按 condition/case_id 查找。

| Case ID | 实际原文片段 | 技术审阅问题 | 人工判定 |
|---|---|---|---|
| synthetic_006 | `In Rouen.`；随后 `User: Where did the person live in 2025?` / `Assistant: In Tours.` | 过去时间在生成的 User 句中，回答本身省略时态；不能把 Tours 自动视为当前城市断言；更早年份的额外断言可能无依据 | 未完成 |
| synthetic_008 | `Nancy`；随后 `User: Where did the person live back then?` / `Assistant: Metz`，再重复回答 `Nancy` | 首次当前答案与后续自编历史问答应分别分析；后续历史回答之间也可能不一致 | 未完成 |
| synthetic_014 | `In Toulouse.`；随后 `User: Where did the person live in 2025?` / `Assistant: In Bordeaux.` | 与 006 相同，时间由生成对话上下文表达；附带早年断言尚未核实 | 未完成 |
| synthetic_018 | `Nancy`；随后 `User: Where did the person live back then?` / `Assistant: Metz`，再重复回答 `Nancy` | 与 008 相同；原始多轮续写保留，不截取首句来改变评分 | 未完成 |
| synthetic_019 | `Alice is currently living in Orleans.`；随后 `Alice was living in Reims back then.` | `was living in ... back then` 不在 legacy 规则的过去时表达式覆盖范围内 | 未完成 |

原评分汇总仍是 C3 correct=6、incorrect=14、unknown=0。9 条机器标记加这 5 条技术审阅，不能自动改成 “14 条评分器误判” 或 “20 条真正正确”。尤其生成的额外历史年份和自由续写可能包含不同类型的无依据内容，需独立审阅后才可做语义结论。

后续应版本化修订城市/时态规则、增加 dated-past 与跨生成轮次的回归案例，并在原 raw 上保存新的离线评分版本；不得覆盖本轮评分或为了得到 PASS 改动既定实验分母。本轮不实施 P1 效应分析。
