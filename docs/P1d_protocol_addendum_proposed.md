# P1d prospective protocol addendum — p1d_addendum_proposed_v1

Maintainer and final scientific decision authority: Yaxin ZHENG.

Status: **PROPOSED, NOT ADOPTED, NO INFERENCE AUTHORIZED**. Historical Research Protocol v1.1 and approved P1c supplements remain unchanged. Research Protocol v1.2 Revised Proposed r1 is a planning reference only.

## Research questions and hypotheses

Under identical sufficient trusted evidence, how do entity match and requested-time match of auxiliary historical claims affect dialogue reliability and task completion? Does independent boundary adjudication change the measured contrasts? Do findings transfer across task/date strata and a separately configured same-family instruction model while preserving narrow persona fidelity?

Primary tests concern E, V and E×V package contrasts, with two-sided hypotheses; no sign is assumed from P1c. Proposed practical relevance thresholds are 10 percentage points for average effects and 20 for interaction. Pure topical relevance, pure temporal cognition and internal memory-selection mechanisms are not claimed. A separate non-answer relevance/date-attestation diagnostic is described but not selected for execution.

## Population, interventions and independent boundary

Recommend 144 new synthetic English speakers, two independent cases each, four balanced families and equal current/historical queries. Six conditions per case are E0V0/E0V1/E1V0/E1V1/D_procedural/H_none. E1V1 is an explicit answer-supporting positive control; D_procedural remains diagnostic unless semantic neutrality is independently established. Preserve constant ledger, question, reference date, fixed context and answer requirements across all cells. All historical propositions must be true for their stated intervals. Main effects are averaged over the other factor; interaction is a difference in differences, not an inferred latent mechanism.

The exact 16 weight vectors are in `validation/p1d/proposed_v1/contrast_specification_v1.json`. Their order is four factorial cells followed by diagnostic/no-history. E = (−.5,−.5,+.5,+.5,0,0); V = (−.5,+.5,−.5,+.5,0,0); E×V = (+1,−1,−1,+1,0,0). Four fixed-factor simple contrasts, eight active-versus-baseline contrasts and diagnostic-minus-no-history complete the registry. These are new P1d weights, not a change to P1c's registry.

All 16 current development examples and every P0/P1/P1b/P1c case are excluded from independent evaluation. New independent domains/templates, speakers, value permutations and material review must be frozen before outputs. No validation data are used for algorithm tuning. Independent validation means new outcomes on prospectively fixed materials, not automatically real-world population generalization.

## Outcomes, annotation and statistics

Primary endpoints are temporal Incorrect-label incidence on the frozen eligible denominator and complete task success, each with E/V/E×V: one six-comparison family. Factual Correct/Incorrect/Unverifiable incidence, relevance, coherence, component presence/support, semantic completeness, structure and persona fidelity are reported separately. All cases are eligible for each defined metric; unknown boundary/interpretation, administrative missingness and N/A remain separate. No composite reliability index. No Unverifiable-to-Incorrect coercion. Structural continuation is not factual error.

The exact proposed policy is `validation/p1d/proposed_v1/analysis_policy_proposal_v1.json`, with rubric details in `P1d_task_and_metric_design.md`. Preserve original signed weights for unknown-outcome bounds; no silent cell renormalization. Assessed-only accuracy and complete-case contrasts are explicitly selection-sensitive alternatives. Use within-case pairing, equal speaker aggregation, 10,000 whole-speaker bootstrap sensitivity draws (seed 716201), leave-one-speaker-out and family/date analyses. Report ordinary and six-comparison Bonferroni intervals; do not use descriptive differences as significance. Ordinal distributions and sign/rank sensitivity supplement descriptive means.

Independent review follows `P1d_independent_annotation_plan.md`. Prospective primary comparisons can become confirmatory only after material, rubric, model and analysis freeze and explicit approval. Measurement pilots, model sensitivity, auxiliary contrasts, algorithm development and this current proposal remain exploratory. If the prerequisites fail, do not retrospectively relabel the resulting development experiment as confirmatory.

## Models, resources and stopping

The proposed Base arm has 1,728 requests; an independently frozen same-family Instruct subset has 288 requests on 24 paired speaker clusters. Total prospective scope: 2,016 requests. There is no frozen execution manifest yet and **zero requests are authorized by this proposal**. Keep Base identity and 96-token reference configuration; record official instruction template and every differing model/tokenizer/stop parameter. Local Instruct quantization/backend compatibility remains unverified.

The sample recommendation follows the recorded 216-configuration grid and selected stress simulation, not P1c effect sizes. Unknown outcomes can prevent useful identification even at this N. No interim effect-based expansion, early success stopping or no-history-correctness filtering. A material integrity/runtime failure stops the affected execution; preserve partial results and use a separately approved immutable resume policy. No retry under changed parameters. Budget, templates, endpoint changes or control replacement after freeze require a versioned amendment.

## Algorithms and reproducibility

Offline known-method implementations may use development-only fixtures. Future generated baseline comparisons must hold cases, evidence and candidate/verification budgets fixed, report extra calls and compare strong simple methods plus feasible published adaptations. Never label an adapted filter as full FPPS/CoVe/RARR replication. Persona fidelity, damage to correct answers, full delivery, cost and boundary sensitivity are mandatory method outcomes. No new inference or training is authorized here.

Freeze dataset/model/backend/template/tokenizer/code hashes, all prompts/IDs, condition order (proposed seed 716301), raw logs and evaluation masking map. Independent materials remain untouched after evaluation. Publish code/data sufficient for reproduction subject to licenses and data governance; no real private conversations are currently included. Preserve failed hypotheses and all historical outputs. Git commits/pushes and public release remain researcher controlled.

## Approval and execution gate

One consolidated packet binds this addendum, policy, contrasts, model proposal and material limitations by SHA-256. Approval of this exact addendum adopts only the prospective plan; it does not certify unreviewed controls or authorize an absent frozen manifest. Before execution: independently reviewed bank and measurement policy, complete source/token checks, verified model arms, approved final immutable request manifest and explicit bounded authorization are required. These are the user's formal-protocol and frozen-execution gates, not additional software-enum approvals.
