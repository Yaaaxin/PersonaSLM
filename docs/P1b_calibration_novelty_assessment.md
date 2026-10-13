# P1b Measurement Evidence and Novelty Assessment

Maintainer: Yaxin ZHENG. Formal experimental baseline: Protocol v1.1. Protocol v1.2 Revised Proposed r1 remains prospective and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Development evidence only; no new inference.

## Evidence level

Current findings establish preserved outputs, transcript continuation, sparse structural transitions and a need to distinguish supported assertions from delivered answers. Human semantic effects remain unknown. The existing [novelty matrix](related_work_novelty_matrix.md) is preserved. This update uses primary records/abstracts and an official template, not an exhaustive systematic review or replication. Newly accessed pages and the failed retrieval are listed in [source access evidence](validation/p1b/measurement_audit_v1/literature_access_v1.json).

| Prior work | Direct overlap | What P1b does and does not add |
|---|---|---|
| [Principled Personas: Defining and Measuring the Intended Effects of Persona Prompting on Task Performance](https://aclanthology.org/2025.emnlp-main.1364/), de Araujo et al., EMNLP2025 | Persona advantage, robustness to irrelevant attributes and fidelity are already evaluated | A shared-evidence S/F/H bank with explicit measurement units is a design choice, not new evidence of generic persona sensitivity |
| [When Personalization Misleads: Understanding and Mitigating Hallucinations in Personalized LLMs](https://aclanthology.org/2026.findings-acl.395/), Sun et al., Findings ACL2026 | Studies history-aligned factual distortion and proposes FPPS/PFQABench | Date/content review may reveal a scoped pattern, but cannot identify representational entanglement or claim first discovery of personalization hallucinations |
| [One Persona, Many Cues, Different Results](https://aclanthology.org/2026.acl-long.2079/), Weeber et al., ACL2026 | Compares persona cues and shows sensitivity of conclusions | Single style realizations and wrapper choices require replication; prompt sensitivity itself is established |
| [What to Admit and How to Present](https://arxiv.org/abs/2610.11188v1), Liu and Ding, preprint2026 | Separates memory admission from presentation and reports trade-offs | Current H packages confound these dimensions; no isolated temporal/relevance mechanism is demonstrated |
| [LongMemEval](https://arxiv.org/abs/2410.10813v2), Wu et al., ICLR2025 | Temporal reasoning, updates and memory-use evaluation already exist | Sufficient common evidence can rule out missing-evidence explanations, but not all selection or utilization alternatives |
| [Wiki-Talkie](https://arxiv.org/abs/2610.08513v1), Fucci et al., preprint2026 | Real discussion next-turn persona conditioning and behavioral distribution evaluation | Our fictional English bank has no demonstrated authentic-speaker external validity; no private dataset was imported |
| [TwinVoice](https://aclanthology.org/2026.findings-acl.981/), Du et al., Findings ACL2026 | Multiple real-world persona dimensions and separate capabilities | Separating fidelity, reasoning and memory is already established; our current measurements do not establish real-speaker fidelity |
| [Persistent Personas?](https://aclanthology.org/2026.eacl-long.246/), EACL2026 | Extended role-playing and instruction-following evaluation | A high role-transition rate is not itself novel; meaningful first-reply consequences require outcome review |
| [Decoupling Logic from Persona](https://arxiv.org/abs/2610.09772v2) | Repository's earlier literature audit records direct decomposition overlap | Fresh retrieval returned an internal error; do not claim fresh full-text verification or borrow a mechanism as a current finding |

## Falsifiable contribution tests

| Prospective claim | Additional evidence needed | Result that would weaken it | Novelty risk |
|---|---|---|---|
| S×H changes reliability under identical sufficient evidence | Valid separate semantic labels, paired interactions, independent persona/task realizations and useful clustered precision | Stable near-zero interaction within a prospectively useful equivalence margin, or effects explained by unresolved package differences | High: factorial design alone is established |
| Structural-versus-semantic measurement changes interpretation of persona effects | Human-confirmed first units, all denominators, versioned full-output sensitivity with separately defined unit, independent replication | Same supported conclusions across valid units and sufficient coverage | Plausible scoped contribution; generic parser failures are not new |
| Historical relevance/temporal validity explains a conditional pattern | An explicitly approved relevance×temporal-status diagnostic holding presentation/evidence constant | No precise conditional differences or disappearance after content/position controls | High overlap with temporal memory and admission work |
| Operational Base/native-chat configuration changes measurement feasibility | Pinned separate checkpoint/template arm and same-case blinded semantic coverage comparison | No useful coverage gain, or apparent improvement caused by excluding uncertain outputs | Model sensitivity is established; contribution requires interpretable boundary evidence |
| Findings generalize beyond synthetic cases | Authorized independent English real-speaker material, provenance and separate fidelity assessment | Failure to replicate under external material, reported as a scope limit | Strong existing persona-simulation overlap |

No claim above is accepted by completing192 generations. CPU deployment, parameter size, higher error counts and an eight-cell design are not originality evidence. Zero contrasts and negative or mixed outcomes remain reportable. A precise independent boundary or qualified replication could be useful to PLOS ONE even without a new algorithm; there is no promise of publication.

## Algorithmic Opportunity Assessment

Existing retrieval, temporal filtering, native chat formatting and factual verification are necessary baselines. Current evidence supports measuring failure types before choosing mitigation; it does not justify algorithm implementation. See [the assessment](P1b_calibration_algorithmic_opportunity.md) for decision conditions.
