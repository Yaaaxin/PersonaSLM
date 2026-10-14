# Related-work and novelty monitor ? v4 (P1d)

Maintainer: Yaxin ZHENG. Additive update; v1?v3 remain unchanged.

The [machine-readable matrix](validation/p1d/proposed_v1/related_work_matrix_v4.json) records ten primary-source comparisons, exact versions, author lists, methods, experimental assumptions, models, metrics, cost and limitations. Its [CSV](validation/p1d/proposed_v1/related_work_matrix_v4.csv) supports inspection. Main method and experiment sections were inspected; implementation replication and complete appendix verification remain outstanding. This targeted search is not exhaustive.

| Work | Verified publication status | Remaining distinguishing evidence |
| --- | --- | --- |
| [When Personalization Misleads: Understanding and Mitigating Hallucinations in Personalized LLMs](https://aclanthology.org/2026.findings-acl.395.pdf) | PEER REVIEWED FINDINGS ACL | Direct interference/fidelity overlap. Test whether supplied-ledger entity/time failures persist against steering, not merely history removal. |
| [What to Admit and How to Present: Governing Persistent Memory in LLM Agents](https://arxiv.org/html/2610.11188v1) | PREPRINT V1 | Direct overlap with gating and evidence conflicts. Match retained content/budget and measure utility before originality claims. |
| [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/html/2410.10813v2) | PEER REVIEWED ICLR | Time filtering is established. Compare query-date/entity joins and retained useful memory at equal budgets. |
| [Chain-of-Verification Reduces Hallucination in Large Language Models](https://aclanthology.org/2024.findings-acl.212.pdf) | PEER REVIEWED FINDINGS ACL | Answer verification already exists; compare component delivery and damage to correct content. |
| [RARR: Researching and Revising What Language Models Say, Using Language Models](https://aclanthology.org/2023.acl-long.910.pdf) | PEER REVIEWED ACL | Evidence verification is prior art. Closed-ledger revision needs no-search and equal-call baselines. |
| [Persistent Personas? Role-Playing, Instruction Following, and Safety in Extended Interactions](https://aclanthology.org/2026.eacl-long.246.pdf) | PEER REVIEWED EACL | History/fidelity trade-offs established; validate short-ledger effects independently and retain fidelity endpoint. |
| [TwinVoice: A Multi-dimensional Benchmark Towards Digital Twins via LLM Persona Simulation](https://aclanthology.org/2026.findings-acl.981.pdf) | PEER REVIEWED FINDINGS ACL | Multidimensional fidelity is established; independent ledger reliability and boundary validity remain separate questions. |
| [Wiki-Talkie: Multilingual Benchmarking of Persona-Based Agents on Real-World Discussions](https://arxiv.org/html/2610.08513v1) | PREPRINT V1 | History conditioning already studied; new contribution requires fixed-evidence reliability and governed external validation. |
| [Decoupling Logic from Persona: Structural Immunity of Edge LLM Agents to Context Pollution](https://arxiv.org/html/2610.09772v2) | PREPRINT V2 | Separation and measurement discrepancies overlap directly. Test user-facing benefit under matched compute and independent boundaries. |
| [LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues](https://arxiv.org/html/2605.12493v1) | PREPRINT V1 VENUE UNVERIFIED | Evidence presence versus use is already studied; fixed short evidence is a controlled complement, not new retrieval invention. |

The search additionally located LongMemEval-V2 through the original benchmark authors' repository. Its full pipeline is outside the current short-ledger CPU scope; it is a relevant competitor for evidence-use claims, not a locally reproduced baseline. No new public/private conversational data were imported.

P1d novelty status remains UNVERIFIED for any proposed original algorithm. The possible empirical contribution is independent measurement of scoped entity/time competition, robust to boundary interpretation and distinct task/factual endpoints. P1c alone supports neither that replication nor a pure relevance/temporal mechanism. See the [algorithm assessment](P1d_algorithmic_opportunity_assessment.md) for falsifiable candidates and rejected claims.
