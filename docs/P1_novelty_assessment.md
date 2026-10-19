# P1 Novelty Assessment - Exploratory Wave 1

Maintainer: Yaxin ZHENG. Official paper title and Research Protocol v1.1 are unchanged. The assessment distinguishes design differences from demonstrated contributions. No novelty finding follows merely from executing a 2B quantized model on CPU or using factorial terminology.

## Verified primary-source overlap

The seven official records and abstracts below were inspected for this P1 initialization. This verifies their metadata and the scoped descriptions below, not every numerical/full-text claim in the earlier supplied audit and not experimental replication. The [existing matrix](related_work_novelty_matrix.md) and [earlier detailed audit](PersonaSLM_related_work_novelty_audit_2026-10-12.md) remain preserved.

| Study and verified status | Direct methodological overlap | Concrete P1 difference and novelty risk |
|---|---|---|
| [Principled Personas: Defining and Measuring the Intended Effects of Persona Prompting on Task Performance](https://aclanthology.org/2025.emnlp-main.1364/), Luz de Araujo, Rottger, Hovy and Roth; EMNLP 2025 | Evaluates persona advantage, irrelevant-attribute robustness and fidelity across nine models and 27 tasks; effects are not uniformly harmful | P1 holds dated task evidence fixed while separating S/F/H packages. Detecting prompt sensitivity or using small models is already covered; new evidence would need stronger identification |
| [When Personalization Misleads: Understanding and Mitigating Hallucinations in Personalized LLMs](https://aclanthology.org/2026.findings-acl.395/), Sun et al.; Findings of ACL 2026 | Studies history-aligned factual distortion and proposes PFQABench/FPPS | P1 adds explicit first-reply/structural measurement and a development factorial intervention inventory. Generic personalization-induced hallucination is not new; no representation mechanism is established here |
| [One Persona, Many Cues, Different Results: How Sociodemographic Cues Impact LLM Personalization](https://aclanthology.org/2026.acl-long.2079/), Weeber, Neplenbroek, Batzner and Pado; ACL 2026 | Six cue forms, seven models and four tasks show that cue choice can change conclusions | P1 uses two same-intent realizations per category, but they belong to different speakers and cannot isolate paraphrase effects. H4 is a feasibility question with substantial overlap |
| [Decoupling Logic from Persona: Structural Immunity of Edge LLM Agents to Context Pollution](https://arxiv.org/abs/2610.09772v2), Nakatsu and Wang; arXiv v2 preprint | Distinguishes logical content from persona expression and reports structured-format failures in context-polluted 4B/8B model experiments | P1 retains the same inference path and audits free-form first replies under fixed evidence. Structure/content separation and edge deployment are not unprecedented; no architecture or adapter method is introduced |
| [TwinVoice: A Multi-dimensional Benchmark Towards Digital Twins via LLM Persona Simulation](https://aclanthology.org/2026.findings-acl.981/), Du et al.; **Findings of ACL 2026** | Separates memory, reasoning and linguistic/persona capabilities across social, interpersonal and narrative settings | P1 is a controlled fictional development study, not authentic-speaker fidelity validation. Multidimensional evaluation is established; the title's real-speaker target remains future external validation |
| [Persistent Personas? Role-Playing, Instruction Following, and Safety in Extended Interactions](https://aclanthology.org/2026.eacl-long.246/), Luz de Araujo et al.; EACL 2026 | Studies persona fidelity and instruction following over extended dialogue; reports context-dependent tradeoffs | P1 uses fixed short contexts and dated source facts, without free-running trajectories. A general fidelity/reliability tradeoff is not a new claim and is not measured here |
| [REALTALK: A 21-Day Real-World Dataset for Long-Term Conversation](https://arxiv.org/abs/2502.13270v1), Lee et al.; 2025 arXiv preprint | Authentic messaging supports persona simulation and memory-probing tasks; history-only simulation is difficult | P1 introduces no private data and cannot claim authentic-speaker generalization. Exact shared-evidence interventions differ from conversation resemblance; substantive external evidence is still absent |

The official TwinVoice record is Findings of ACL, refining the user's abbreviated ACL label. Third-party interpretations and causal explanations in papers are the authors' claims; none becomes a PersonaSLM result by citation. No code, private conversation or training artifact from these studies was imported.

## Testable contribution candidates

| Candidate contribution | Existing coverage | What differs substantively, if validated | Supporting observation | Falsifying / weakening observation | Current coverage and novelty risk |
|---|---|---|---|---|---|
| H1: S/H-dependent reliability changes under shared evidence | Persona/context interference and performance sensitivity already studied | Reproducible interaction after separating uncertainty, structure and factual content, then checking better controls | Consistent interaction across independently reviewed material and adequate speakers | Stable near-zero interaction with adequate precision, or disappearance under valid control alternatives | Eight cells are present; one model and 12 speakers are preliminary. Factorial design itself is not novel |
| H2: Factual and temporal effects dissociate | Personal memory distortion and long-context behavior already studied | Separately assessed temporal consistency with genuine past facts, shared current evidence and fixed reply units | Different paired endpoint changes supported by human evidence | Similar changes with adequate precision, or differences explained by annotation coverage | Temporal review is pending; no endpoint dissociation can yet be certified. High overlap risk |
| H3: Apparent effects chiefly concern response structure | Decoupling explicitly reports structured failures; P0 already identified continuation | A replicated condition-dependent measurement boundary in free-form dialogue, not a generic parser observation | Structural changes with independently stable semantic content, or condition-dependent full-output/first-span disagreement | No structural change, or all differences explained by fixed cap/template with no condition-specific variation | Frozen parser supports diagnosis; no model-mechanism claim. High novelty risk |
| H4: Estimates depend on style realization | Cue variation directly studied by Weeber et al. | A within-speaker independently randomized realization study under verified evidence could quantify a specific boundary | Effect changes across independently frozen equivalent realizations | Robustly equivalent estimates under that design | Current paired category realizations are confounded with speaker and task; this wave cannot isolate H4 |
| H5: Intervention effects depend on task family | Broad multitask persona studies and persona benchmarks already exist | Reproducible family-specific effects after balancing speaker, content relevance and measurement coverage | Heterogeneous paired changes surviving balanced follow-up | Similar effects with adequate precision or heterogeneity disappearing after controls | Three speakers per family; history relevance/family overlap remains. A longer experiment alone adds no novelty |

## Scientific interpretation and priorities

Negative, mixed and null results are useful exploratory evidence. A saturated structural indicator can produce zero estimated differences while leaving semantic questions unresolved; it does not establish equivalent model behavior. Pending annotations are a coverage limitation, not evidence of correctness or error. No pilot significance, priority or unprecedented-method claim is warranted.

The long-term priorities remain independent/interactive S/F/H effects; historical relevance, temporal status and presentation decomposition; structural versus semantic failures; model-size/post-training sensitivity; and authorized English real-speaker validation. Wave 1 manipulates only S/F/H. It does not independently cross historical relevance/time/presentation, model size or post-training, and does not execute P2-P6. Further work must be justified by information value and separately authorized rather than added to manufacture novelty.

The actual empirical feasibility results belong in the [wave report](P1_pilot_wave1_report.md). This assessment precludes interpreting partial semantic coverage or a restricted control comparison as proof of a new general phenomenon.

## Measurement-audit addendum: two additional primary studies

This is an additive literature and interpretation update, not a change to the executed wave's hypotheses. Primary arXiv abstracts and versioned HTML methods/results were inspected; neither study was experimentally reproduced and no released dataset/code was imported. The revised v1.2 r1 proposal remains unadopted. Its claims are checked against sources rather than treated as experimental authority.

| Verified study | Actual methods and reported outcomes | Overlap and implication for PersonaSLM |
|---|---|---|
| **What to Admit and How to Present: Governing Persistent Memory in LLM Agents**, Chang Liu and Deliang Ding, 2026, [arXiv:2610.11188v1](https://arxiv.org/abs/2610.11188v1); preprint, under review rather than accepted | [Methods/results](https://arxiv.org/html/2610.11188v1), sections 3–5: tests memory admission with whole-entry versus split typed units, then two presentations holding admitted verdicts fixed. Development uses four backbones and PersistBench subsets; external MemSyco-Bench has four tasks ×300 cases, a DeepSeek-V4-Pro generator/adjudicator and separate GLM-5.2 judge. Reports paired tests and multiplicity correction. Two admission pipelines reduce pooled judge-assessed failures by 6.7/8.8 percentage points, with personalization tradeoffs; the stronger preregistered success condition is not met. No shared-verdict presentation difference survives correction across the tested pairs. Human validation concerns the development rubric, not the external rubric. Assets are reported available, not independently reproduced here. | Direct overlap with memory interference, information admission and content-versus-presentation decomposition. The corrected null is limited to two tested renderings, not universal presentation equivalence. PersonaSLM's shared sufficient evidence and separate S/F/H/reliability coverage are operational differences; independent history-content/validity control would be needed to support a substantive extension. Current C3−N_history does not accomplish that decomposition. |
| **Wiki-Talkie: Multilingual Benchmarking of Persona-Based Agents on Real-World Discussions**, Dennis Fucci, Andrea Bacciu, Dong Liu, Weronika Łajewska and Saab Mansour, 2026, [arXiv:2610.08513v1](https://arxiv.org/abs/2610.08513v1); preprint, no accepted venue verified | [Methods/results](https://arxiv.org/html/2610.08513v1), sections 3–5: next-turn simulation uses Wikipedia Talk histories in five languages, fixed preceding comments, user profiles and inferred behavioral traits. Four anonymized frontier models receive base role, profile, behavior, behavior-plus-reasoning or prior-comment history prompts. Named model identities/parameter sizes are not disclosed. Evaluation emphasizes population dialogue-act/sentiment distributions (including distributional distances), with ROUGE-L/BERTScore as auxiliary measures. The authors report history strongest for similarity, profiles often degrading it, verbosity and positivity bias, and underrepresentation of negative/extreme sentiment. Population resemblance is not proof of individual-speaker fidelity. | Direct overlap with persona cue/history comparisons, real-user simulation and multidimensional behavior. PersonaSLM instead asks about source-supported reliability under fixed evidence; its current fictional cases do not establish authentic-speaker validity. Different language/model populations alone are weak novelty arguments. An authorized independent real-speaker transfer test remains prospective, not performed here. |

These full-text comparisons narrow the novelty space. They do not prove that no other paper studies our exact design. Earlier literature rows remain historical records; this audit rechecked official Principled Personas and When Personalization Misleads abstracts. A fresh retrieval of the Decoupling v2 abstract returned a cache error; its previously recorded verification is retained without claiming a new full-text check.

## Updated falsifiable contribution assessment

| Candidate | Existing coverage / concrete difference | Observation that would support it | Observation that would falsify or weaken it | Current evidence / risk |
|---|---|---|---|---|
| Measurement choice changes an apparent persona effect | Structural/content distinctions already exist. A useful extension would compare reproducible first-reply versus continuation interpretations with independent semantic judgments under shared evidence | An independently replicated condition-dependent divergence between structural and semantic estimates, traced to measured evaluation units | No meaningful estimate change, or a change explained entirely by a known generic parser/format defect | 78 CROSS_TURN outputs and an EOS enum issue alone establish no novel effect; semantic review is pending |
| S/F/H interactions survive measurement and control checks | Persona performance and cue sensitivity are established. A contribution needs identified, replicable interaction evidence rather than a factorial layout | Stable interaction estimates across independent speakers/realizations after resolving outcome coverage and package confounds | Near-zero estimates with adequate precision, or disappearance after matching/valid scoring | Average structural S×H is zero with opposite case changes; neither support nor falsification of the scientific hypothesis |
| History relevance and temporal validity affect different endpoints | Memory admission, personalization distortion and presentation are directly covered by prior work | Separate R/T interventions under identical sufficient evidence yield independently supported endpoint differences | No dissociation with informative uncertainty, or effects attributable to unequal facts/format/length | Present history package cannot isolate these mechanisms; approval and a new design are required |
| A reproducible configuration boundary limits conclusions | Model and prompt sensitivity are established. Specific externally validated measurement boundaries may still add information | Independent material shows a consistent structural/semantic boundary across a separately controlled Base/Instruct configuration comparison | Comparable behavior, or a boundary disappearing after template/length controls | One model only; post-training/template changes must not be conflated. Size or CPU deployment is not originality |
| Controlled findings transfer to real-speaker English tasks | Real-user persona simulation and behavioral evaluation are already represented by Wiki-Talkie, REALTALK and TwinVoice | Comparable reliability effects on authorized, independent real-speaker material with source-valid facts | Failure to transfer, showing a scoped synthetic boundary rather than a universal persona effect | No such experiment or private data collection occurred; future external validation cannot be claimed now |

The [measurement audit](P1_wave1_measurement_audit.md) distinguishes observed counts from these hypotheses. All five priorities remain potential research questions. A justified replication or well-bounded null result may be scientifically useful, but publication requires valid methods, appropriate evidence and claims; the [PLOS ONE criteria](https://journals.plos.org/plosone/s/criteria-for-publication) do not make a positive effect a prerequisite. Further generations need a specific information-value argument and researcher authorization.

## 2026-10-18 model-feasibility recovery novelty addendum

This addendum updates prospective contribution boundaries after primary-source review; it does not reinterpret frozen Wave 1 or Stage B outcomes. The structured review and source scope are preserved in `docs/validation/literature_monitor_v1/reviewed_ledger_v1.json` and `literature_checkpoint_2026-10-18_v1.json`. None of the cited findings was independently reproduced by PersonaSLM.

| Verified primary source | Material overlap | Required PersonaSLM adaptation |
|---|---|---|
| [Beyond similarity retrieval](https://link.springer.com/article/10.1007/s41060-026-01290-8), International Journal of Data Science and Analytics, 2026 | Defines governing persona-related facts; tests revisions and stale superseded facts; introduces SCR-T; and reports local CPU inference with quantized small open-weight models, including 1B–3B models in a format-controlled downstream experiment | Treat SCR-T or an information-equivalent supersession filter as a strong baseline before any temporal-provenance algorithm claim. Neither CPU-small-model deployment nor supersession resolution is novel by itself |
| [When Context Changes](https://arxiv.org/abs/2609.38866v1), arXiv 2026 | Defines stale binding as choosing an old value of the same variable after an update and studies information selection and an attention intervention | Preserve `OUTDATED_VALUE_ADOPTION` separately, but do not present the two Stage B old-value outputs as discovery of a new failure mechanism. Internal attention drift remains untested in PersonaSLM |
| [MemAdapter](https://arxiv.org/abs/2610.05162v1), arXiv 2026 | Uses counterfactual risk, context-aware reflection, and evidence-grounded reasoning to reduce unreliable effects from historical beliefs or preferences | Any later memory-suppression or evidence-selection method needs a concrete technical distinction, matched-information comparison, ablation, cost accounting, and independent evaluation |
| [Persona Following Is Not Selective Control](https://arxiv.org/abs/2609.35036v1), arXiv 2026 | Shows cross-attribute effects and a neutrality gap when one persona attribute is manipulated | Interpret S/F/H as complete prompt packages, not proven pure latent causes. Add prospective non-target manipulation checks; token matching alone remains insufficient evidence of semantic neutrality |
| [Back in Style](https://arxiv.org/abs/2610.10988v1), UserSim @ NeurIPS 2026 workshop | Represents persona style as observable linguistic rates and applies stylometry and lexicon diagnostics | Compare future linguistic-fidelity measures with these model-free diagnostics and genuine researcher labels; keep style fidelity, naturalness, and reliability separate |
| [Generalization saturation and reasoning divergence](https://www.sciencedirect.com/science/article/pii/S1566253526003568), Information Fusion 2026 | Directly studies persona-consistency versus reasoning-stability trade-offs and unintended persona-prompt effects on unrelated tasks | Broad claims that persona conditioning perturbs reasoning or creates a fidelity/reliability trade-off are no longer defensible as a unique contribution |

The strongest defensible contribution hypothesis is now deliberately narrow: estimate how complete S, F, and explicitly dated H conditioning packages, individually and interactively, change reliability under shared sufficient evidence in approximately 0.8B–3B CPU-deployed models, while reporting outdated-value adoption, persona fidelity, and CPU cost separately. No reviewed source in this bounded check was verified to combine that entire design. This is not a priority claim: factor isolation is not yet demonstrated, the viable-model screen is incomplete, the factorial has not executed, and no independent validation exists.

Algorithmic contribution remains unsupported. The ESCP negative result is preserved, P6 remains paused, and the new closest prior work raises rather than lowers the bar for activation. A future activation decision would require a replicated residual failure that persists after full-context, recency/current-value selection, SCR-T-style supersession, and an evidence-grounded memory baseline under equal information.

## 2026-10-18 selective-history and provenance review addendum

The versioned structured evidence for this update is
`docs/validation/literature_monitor_v1/primary_source_review_addendum_2026-10-18_v1.json`.
The review inspected the available full-text methods, experiments, results, appendices,
and limitations. It is AI-assisted primary-source review, not human confirmation or an
independent reproduction of any paper.

| Primary source | Closest overlap | Consequence for PersonaSLM |
|---|---|---|
| [Wiki-Talkie](https://arxiv.org/html/2610.08513v1) | Compares raw comment history, explicit profiles, and compressed behavioral descriptions for next-turn generation and population-level behavioral fidelity | PersonaSLM cannot claim the first history-versus-profile comparison or the first benefit of history for behavioral fidelity. Future comparisons need information- and token-matched history/summary controls and must not equate population resemblance with individual Persona Fidelity |
| [ReTurn](https://arxiv.org/html/2610.11948v2) | Uses matched direct and conversational views to distinguish base answerability from selective-history failure, and separates history-required from history-interfering tasks | Future H mechanism cohorts should prospectively include matched direct references, consistent/outdated conflict pairs, history-required reverse controls, and answer-identity errors. C0 failure alone is not evidence of a History effect; simple restatement and routing are required baselines |
| [Memory Echo / FPA](https://arxiv.org/html/2610.17763v1) | Tracks same-source memory families and combines one-representative-per-family serving, correction-conditioned eligibility, and authority-guided answer constraints | FPA is a direct P6 competitor. Broad temporal-provenance, source-family deduplication, conditional stale-memory suppression, and authority-gating claims are occupied prior art. Any later method must be technically distinct and beat FPA components, simple temporal filtering, and restatement under matched information |

FPA does not eliminate every possible algorithmic direction: its experiments concern
retrieval/write-back trace multiplication rather than static dated persona dialogue, and
do not jointly study validity intervals, uncertain provenance, S/F/H isolation, Persona
Fidelity constraints, or CPU-small-model deployment. Those differences are research
questions, not novelty evidence. P6 therefore remains paused. Implementing a renamed
provenance/suppression pipeline before identifying a replicated residual PersonaSLM
failure would be scientifically unjustified.

## 2026-10-18 post-restart evaluator-validity addendum

The post-restart frozen collector succeeded for all 13 metadata requests and produced a
217-record discovery snapshot. Of 26 stable IDs not present in the earlier same-day
snapshot, one warranted full-text review: [PersEvalBench](https://arxiv.org/abs/2610.19314v1).
The versioned evidence and primary-source hashes are recorded in
`docs/validation/literature_monitor_v1/primary_source_review_addendum_2026-10-18_v2.json`.
The older 14-record ledger and prior three-paper addendum remain byte-unchanged.

PersEvalBench directly narrows broad evaluator novelty claims. It prospectively fixes
whether user information should persist, transfer, or cease to apply, then tests
directional `Right`/`Under`/`Over` judgments on 403 matched scenarios, including stale or
superseded use. Its reported human reference covers 100 scenarios and has 83.5% exact
agreement (Cohen's kappa 0.72); the largest reported gap is under-personalization
recognition (94.4% for each human annotator versus 63.9% for the strongest reported LLM
evaluator). Gold evidence access and structured prompts do not remove the failure.
Pairwise comparison is substantially easier, but exposes the contrast and does not recover
error direction. These are paper-reported results, not PersonaSLM reproductions.

Consequently, PersonaSLM cannot claim priority for evaluator-side testing of appropriate
persona use, controlled stale/superseded-use errors, or LLM-judge confusion between under-
and over-personalization. Future S/F/H work must not use an LLM judge as its sole semantic
endpoint. The primary review should remain condition-blinded and pointwise, retain
direction-specific current/outdated/omitted-or-incomplete/unsupported categories, and
report false alarms, abstention or unverifiable coverage, and genuine human agreement.
Matched pairwise judgments can be a secondary sensitivity analysis only. This adaptation
changes no historical gate or completed experiment.

## 2026-10-18 temporal-state and publication-status delta

The versioned structured evidence for this bounded update is
`docs/validation/literature_monitor_v1/primary_source_review_addendum_2026-10-18_v3.json`.
The earlier v1 and v2 addenda remain unchanged. This update records primary-source claims
and publication status; it does not independently reproduce any paper result.

| Source and verified status | Prior-art boundary | Immediate consequence |
|---|---|---|
| [TEM: Temporal State Tracking Memory](https://arxiv.org/html/2610.21900v1), arXiv:2610.21900v1, preprint | Versioned source-linked facts, source ordering, explicit historical labels, hybrid event/original-turn evidence, and compact temporal evidence are implemented and ablated. The paper reports 420 state-update questions over 60 personas and a fixed-budget LoCoMo comparison, but uses 4B-20B backbones and an A100 40 GB GPU | Temporal versioning, historical marking, and compact provenance-aware evidence are occupied components. Any PersonaSLM method needs matched session-RAG, no-label/source-order, and full-TEM or information-equivalent baselines, plus Persona Fidelity and CPU cost |
| [FEB-30](https://arxiv.org/html/2610.22209v1), arXiv:2610.22209v1, preprint | Separates intrinsic memory-state quality from downstream QA and reports substantial divergence between them | A history intervention must archive and score selected/stored evidence state separately from final response correctness; final answers alone cannot validate the mechanism |
| [Explaining Roles of Experts in MoE LLMs for Personalization](https://arxiv.org/html/2610.22127v1), arXiv:2610.22127v1, under-review preprint | Uses crosscoders, activation patching, and expert steering to localize personalization behavior in MoE models | First causal localization or expert-level disentanglement of personalization is not an available claim. Its architectures and training cost make it a novelty boundary, not an immediate local-CPU baseline |
| [Assessing inter-rater agreement among large language model judges](https://doi.org/10.1016/j.techfore.2026.124894), *Technological Forecasting and Social Change*, formal journal article | Reports poor-to-moderate agreement and material non-compliance among three LLM persona judges. The 2026 online record and January 2027 issue are one DOI record, not two publications | Multi-LLM agreement is not human validation. Genuine blinded human semantic review and judge non-compliance reporting remain necessary |
| [Personalized dialogue generation based on social game data collection and two-stage response generation model](https://doi.org/10.1007/s10791-026-10687-9), *Discover Computing*, formal journal article | Introduces the Homeland dialogue data and a selective persona-predictor/compression/generation pipeline | Selective persona-attribute prediction and compression are established comparators; data availability, consent, and reproduction must be verified before use |
| [Towards proactive detection of user-side implicit conflicts in human-LLM dialogue](https://doi.org/10.1016/j.eswa.2026.134687), *Expert Systems with Applications*, formal journal record | Title, authors, venue and DOI were verified, but the method and results were not available for primary full-text review | Retain as a review-queue novelty risk; do not infer a conflict-detection mechanism from the title |

The current history-intrusion novelty boundary is therefore stricter than the previous
FPA-only statement. ReTurn already covers matched history-help/history-harm diagnosis;
FPA covers source-family deduplication, correction-conditioned eligibility and authority
gating; memory-governance work covers admission/presentation; TEM covers versioned state,
source ordering, historical labels and compact evidence; and FEB-30 covers internal-state
versus final-answer evaluation. A simple stale-history filter, temporal tag, provenance
gate, deduplication rule, admission gate, authority instruction, or renamed combination is
not a defensible algorithmic contribution.

A remaining testable gap is narrower: an information-matched S/F/H factorial on
approximately 0.8B-3B CPU-deployed models that jointly measures reliability and
linguistic/behavioral Persona Fidelity. A later algorithm would additionally need a
replicated residual failure after strong simple and published baselines, separate internal
state and response scoring, equal information access, ablations, CPU latency/RAM, and
independent validation. This is a prospective gap, not evidence of novelty or efficacy.

## 2026-10-19 disjoint surface-validation consequence

The prospectively frozen 24-case, 168-response synthetic validation did not reproduce the
earlier same-bank declarative-history association as a stable pooled benefit. Registered
declarative-minus-raw point estimates were 0.0000 for preferred-current selection and
+0.0139 for any-current selection, with task-family effects in both directions. This is
negative evidence against promoting declarative rendering from a simple prompt baseline to
an algorithmic contribution.

The registered irrelevant-H-minus-no-H automatic estimate was -0.1875 on both endpoints,
but a separately labelled post-hoc audit found exact system-format placeholder copying in
24/144 History-conditioned outputs and 0/24 no-H outputs. Twenty-three placeholder outputs
were automatically scored `NONE`; all 23 nevertheless contained the preferred canonical
name in the first sentence and none contained the nonpreferred name. This is a reproducible
measurement/realization mechanism in the tested configuration, not evidence that History
causes semantic persona unreliability, not a novel memory algorithm, and not human-validated
Persona Fidelity. Any future intervention must first show a residual semantic failure after
genuine blinded review; automatic anchor insertion or constrained formatting alone would be
metric repair or a known structured-generation baseline, not defensible novelty.

## 2026-10-19 real-speaker and longitudinal-memory addendum

This targeted primary-source review complements, rather than repeats, the completed
daily metadata collection. Its structured record is
`docs/validation/literature_monitor_v1/primary_source_review_addendum_2026-10-19_v1.json`.

| Source and verified status | Direct overlap | Consequence for PersonaSLM |
|---|---|---|
| [RealPersonaChat](https://aclanthology.org/2023.paclic-1.85/), PACLIC 2023 formal proceedings; [v1.0.0 corpus](https://github.com/nu-dialogue/real-persona-chat) | 233 genuine participants, participant-authored ten-sentence personas, repeated timestamped Japanese dialogues, public-release consent and ethics approval | This is a legitimate aggregate real-speaker development path, not permission to impersonate individuals. PersonaSLM must keep speaker/partner partitions disjoint, exclude demographic and personality-scale predictors, preserve raw data locally, and publish only aggregate evidence. |
| [RealCompanion](https://arxiv.org/html/2610.01780v3), arXiv v3 preprint, no peer-reviewed venue verified; [controlled dataset card](https://huggingface.co/datasets/Quislab/RealCompanion) | Ten consented human-AI relationships over 36--120 days; evidence-linked profiles, personas and reply items; explicit retrieval-restraint measurement. Released wording is rewritten, access is restricted, and training or redistribution is prohibited. | Selective-memory, abstention/restraint, and evidence-linked persona reconstruction are occupied research space. Rewritten text cannot validate linguistic style fidelity. PersonaSLM must not claim novelty for deciding whether history matters or for simple memory filtering. |

The RealPersonaChat development diagnostic tests only whether a frozen nonlexical
style instrument detects cross-partner speaker signal. It does not establish model
Persona Fidelity, a conditioning effect, or independent validation. RealCompanion
was not downloaded or used for an experiment.
