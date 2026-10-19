# P5 oracle diagnostic — scientific report v1

Maintainer: Yaxin ZHENG. AI-assisted scientific development; human semantic confirmation remains pending. First submission target: PLOS ONE.


Phase P5 / RQ4 / H3. Question: can the same pinned Instruct configuration deliver required answers when a reference-aware selector presents only the sufficient evidence witnesses? This is **not** a Persona-effect experiment: H_none contains a profile/style instruction and is not C0.

The original 32-row ledger is already sufficient. The oracle retains 1–3 original rows with literal reference values, selected using required-component source IDs and chain predecessors. Evidence content, competing entities/intervals, prompt length, positions and salience change jointly. Questions, references, fixed context, profile, model, template, seed, decoding and output cap remain identical. All eight oracle prompts contain the required answer values. Thus success can involve direct copying; it does not establish independent reasoning, pure evidence sufficiency, retrieval failure or a uniquely localized mechanism.

AI-assisted item review, not researcher-confirmed scores:

| Endpoint | Historical full ledger | Oracle package |
| --- | ---: | ---: |
| Successful generation | 8/8 | 8/8 |
| Native EOS | 7/8 | 8/8 |
| Token-budget termination | 1/8 | 0/8 |
| Identifiable first-response candidate | 8/8 | 8/8 |
| Complete requested-answer form | 5/8 | 8/8 |
| Task Success | 2/8 | 8/8 |
| Required components present | 8/14 | 14/14 |
| Required components supported | 3/14 | 14/14 |
| Factual Correct / Incorrect / Unverifiable | 2 / 6 / 0 | 8 / 0 / 0 |
| Temporal Correct / Incorrect / Unverifiable | 2 / 5 / 1 | 8 / 0 / 0 |

| Development case | Historical task | Oracle task | Historical present / supported | Oracle present / supported |
| --- | --- | --- | --- | --- |
| p1d_dev_04_1 | Failure | Success | 2 / 0 | 2 / 2 |
| p1d_dev_03_0 | Success | Success | 2 / 2 | 2 / 2 |
| p1d_dev_01_0 | Failure | Success | 2 / 0 | 2 / 2 |
| p1d_dev_07_1 | Success | Success | 1 / 1 | 1 / 1 |
| p1d_dev_05_1 | Failure | Success | 0 / 0 | 2 / 2 |
| p1d_dev_02_0 | Failure | Success | 0 / 0 | 2 / 2 |
| p1d_dev_06_1 | Failure | Success | 0 / 0 | 2 / 2 |
| p1d_dev_00_0 | Failure | Success | 1 / 0 | 1 / 1 |

The primary candidate span is the entire output in every new item. Role-marker and conventional first-turn extraction find no continuation to remove; EOS alias sensitivity changes no text. Baseline method agreement is not independent boundary accuracy. The eight original AMBIGUOUS labels are preserved. Semantic proposals separately supply YES completeness; they do not rewrite structural labels.

Factual and temporal claims were compared item by item with their exact rows and requested dates. Owen's `locker 105` is a surface form of Locker 105; Tessa's present-tense clauses inherit the historical requested date; Ellis's explicit interval-containment assertion is supported. Arlo supplies both final nodes after a correct intermediate locker. Quinn is correctly resolved from fixed context, and its new text equals the historical reply. Details, alternatives and evidence citations are in `validation/p5/oracle_diagnostic_v1/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv`.

Response Relevance and Conversational Coherence are separately proposed as 5 for all eight; Ellis's repeated answer permits alternative relevance 4. Their lack of observed variation limits discrimination. Narrow brief/calm style compatibility is not validated broad Linguistic Fidelity; Behavioral Fidelity was not predefined and is not retrofitted. Human rating fields remain blank. Assessors saw model/configuration; the proposals are not a completed blinded human review.

The descriptive paired task-incidence change is **+75 percentage points** (six improvements, two ties, no declines). Whole-speaker resampling (one case each, 10,000 draws, seed 716291) gives a **50–100 pp sensitivity interval**. Eight purposive speakers and shared task ancestry cannot justify guaranteed population coverage; no significance or independent replication claim is made. Components are not independent observations. The earlier Cleo role-scope alternative does not change its lack of task delivery. No uncertain outcome is silently dropped or counted as Incorrect.

**Decision:** the strict 8/8 identifiable-complete-answer headroom gate is met by AI proposals, with human adoption pending. Full-ledger adequacy, S/F/H measurement, third-party provenance and confirmatory readiness are not established. Return to the core programme; do not launch 2,016 validation requests or adopt the oracle selector as a deployable algorithm.

## Algorithmic Opportunity Assessment

1. **Observed Failure Modes:** original wrong-period values, false absence assertions and incomplete answers disappear in this reduced-evidence package; this narrows the development problem but does not identify which package component matters.
2. **Existing Methods and Published Prior Art:** ordinary entity/time filtering and LongMemEval-style temporal retrieval are strong baselines; Zep, Mem0, FC/PS, FPPS, CoVe and RARR overlap with proposed evidence/admission/verification components. See the v8 novelty matrix.
3. **Potential Algorithmic Improvements:** no new algorithm justified by eight oracle successes. Test non-oracle selectors only against equal-information, cost-matched baselines in a separately authorized development experiment.
4. **Validation Feasibility:** typed checks remain offline; future extraction, generation, fidelity and CPU costs must all be counted. Independent cases and boundary judgments are needed.
5. **Publication Value:** configuration-specific measurement headroom and negative algorithm results can support a rigorous methods narrative. They are not a publication-ready discovery or evidence of a new mechanism.
