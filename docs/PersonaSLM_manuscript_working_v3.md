# Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models

Yaxin ZHENG

Working manuscript v3, 19 October 2026. Intended venue: PLOS ONE. Status: integrated exploratory empirical draft, **not submission-ready**. This version consolidates the English professional-dialogue evidence; it does not replace frozen protocols, earlier manuscripts or historical experiments. AI-assisted research engineering, analysis and drafting are documented in the research record. Human judgments remain attributable only to the actual evaluator.

## Abstract

Persona-conditioned dialogue requires separating perceived resemblance from relevance, factual support and computational cost. We examined an English professional-meeting corpus using five authentic speakers, two contexts per speaker, eight Style/Facts/History source-provision conditions and two style controls. Three small-model deployment configurations produced 300 responses: a historical Qwen3-0.6B configuration and matched Qwen2.5-1.5B Base and Instruct configurations. The first 100 responses received 99 genuine principal-researcher review records, each with three primary ordinal ratings; one response's judgment is unavailable. The actual 0–5 ordinal scale was documented retrospectively and differs from the original 0–3 protocol. No semantic ratings exist for the additional 200 responses.

In the historical configuration, Style's paired win-minus-loss advantage was negative for perceived relevance, coherence and linguistic resemblance under every allowed completion of the missing rating. The resemblance bound was −0.150 to −0.125; Facts increased resemblance but not relevance, and interaction directions depended on the ordinal cut. These are finite-sample exploratory perceptions, not population effects or established general Persona Fidelity. History increased mean response-call time by 3.127 and 2.965 seconds in the Base and Instruct configurations. A post-hoc raw-output analysis found repeated five-word windows in 78/100 Base and 1/90 evaluable Instruct responses; ten short Instruct outputs were inapplicable, not zero. This diagnostic does not establish semantic correctness. All reported arithmetic is linked to archived evidence, but no independent new-speaker validation has been completed. The defensible contribution is a bounded negative and heterogeneous empirical account with explicit measurement and efficiency limits, not discovery of the general personalization–reliability trade-off or a new algorithm.

## 1. Introduction

Speaking in a person's manner is not the same task as answering a question about that person. Nor does matching a linguistic marker establish relevance, coherent interaction or factual accuracy. PersonaSLM investigates how additional style descriptions, structured self-reports and conversational history affect continuations made as a real speaker. The population here is professional meeting dialogue, not fictional characters, invented biographies or a representative sample of everyday personalities.

Published research already describes reliability losses under personalization and warmth, persona drift, internal steering, persona-memory retrieval and post-generation alignment. Consequently, observing a negative style contrast or implementing a history filter is not inherently novel. The narrower empirical opportunity is to connect controlled source provision with distinct human-perceived outcomes, all factorial contrasts, speaker heterogeneity and actual CPU deployment cost. This study supplies limited evidence toward that opportunity rather than a first-ever claim or a complete answer to all research questions.

### 1.1 Research questions and protocol reconciliation

We use the current principal researcher's question numbering below. The original [Protocol v1.1](research_protocol_v1.1.md) remains unchanged: its RQ1 concerns reliability dimensions, RQ2 conditioning components, RQ3 model/context configurations, and RQ4 pipeline failures and oracle headroom. The current RQ1 combines original RQ2 with original RQ1 outcomes; current RQ2 focuses their historical/factual/temporal subset; current RQ3 retains configuration comparisons; current RQ4 emphasizes interventions also contemplated by the original pipeline and later-stage adaptation programme. We do not claim that these wordings or numbers were identical from inception.

| Current question | Evidence in this manuscript | Remaining boundary |
|---|---|---|
| RQ1: S/F/H main and interaction effects | Complete experimental grids; ordinal perceptions for one configuration; technical effects for two further configurations | Narrow source representation, five speakers, unvalidated semantic generalization |
| RQ2: History, factual/temporal reliability and contamination | History-associated perceived coherence/relevance and cost | No validated factual/temporal claim adjudication or controlled stale-information mechanism |
| RQ3: model size and Base/Instruct | Paired 1.5B deployment comparison for technical outcomes | New semantic review pending; no isolated training or size effect |
| RQ4: retrieval, ranking, LoRA and quality–efficiency | Existing quality/cost observations inform prerequisites | No executed intervention comparison or validated algorithm |

## 2. Related work and novelty boundary

### 2.1 Personalization and reliability

[Persistent Personas?](https://aclanthology.org/2026.eacl-long.246/) studies extended fictional-role interaction, whereas [When Personalization Misleads](https://aclanthology.org/2026.findings-acl.395/) addresses factual errors associated with personal histories and proposes risk-conditioned activation interventions. [Ibrahim et al.](https://www.nature.com/articles/s41586-026-10410-0) study general warmth rather than individual-speaker resemblance. These formal publications rule out claiming first discovery of a broad personalization–reliability trade-off. They do not automatically validate this study's speaker-likeness instrument or show that its narrow Style representation causes hallucinations.

[Atomic-level persona evaluation](https://aclanthology.org/2025.findings-acl.1349/) distinguishes local trait expression from consistency across generations, while [personalization safety–utility research](https://aclanthology.org/2025.naacl-long.565/) investigates demographic conditioning. The distinction between personalizing an assistant *to* a user and generating *as* a speaker matters. Neither a demographic category nor an assigned personality trait is an authentic speaker history. Our natural dialogues improve that aspect of ecological relevance while retaining severe sampling and measurement limits.

### 2.2 Intervention mechanisms are occupied prior art

[Style Modulation Heads](https://proceedings.mlr.press/v306/izawa26a.html) localizes activation interventions. [Persona Switch](https://aclanthology.org/2026.findings-eacl.101/) selects between persona and neutral reasoning continuations; [Jekyll & Hyde](https://aclanthology.org/2025.findings-ijcnlp.51/) provides an earlier candidate-comparison approach. [Persona Vectors](https://arxiv.org/abs/2507.21509) also supplies direct activation-control precedents. These mechanisms are not new merely because PersonaSLM has not implemented them. In particular, removing F/H from one candidate can remove relevant evidence, violating information comparability in a source-provision task.

[Memory-Driven Role-Playing](https://aclanthology.org/2026.findings-acl.1175/) studies structured persona knowledge and boundary-aware prompting. [Temporal Semantic Memory](https://aclanthology.org/2026.findings-acl.1496/) distinguishes utterance time from fact validity. [Post Persona Alignment](https://aclanthology.org/2025.findings-emnlp.1098/), formally published in 2025, uses response-guided retrieval and revision. Generic structure, temporal filtering or draft–retrieve–revise therefore does not constitute a new algorithm here.

The recent [5%-history preprint](https://arxiv.org/abs/2610.14952) examines relevance-filtered context. Its absence of a detected full-history difference is not a prespecified equivalence test, and reducing input characters is not itself measured CPU acceleration. [Multi-objective persona internalization](https://doi.org/10.1016/j.knosys.2026.116335) is a direct journal competitor for real-person knowledge adaptation; accessible publisher material describes public figures and a 12B model, not the present local 1.5B setting. Its full methodology was not accessible in this review, so detailed reproducibility and evaluation validity remain unverified.

### 2.3 Scope of the literature assessment

The [three primary-source evidence notes](validation/p1/english_novelty_synthesis_v1/literature_cluster_a_v1.txt) ([B](validation/p1/english_novelty_synthesis_v1/literature_cluster_b_v1.txt), [C](validation/p1/english_novelty_synthesis_v1/literature_cluster_c_v1.txt)) distinguish methods, populations, human references, resource requirements and limitations. All ten requested bibliographic identities were verified; preprint and publication versions are linked, not counted as replications. Most detailed readings used formal full texts. The Style Modulation Heads method reading used primary arXiv v2, without establishing byte/text equivalence to the final PMLR PDF. The KBS full methods were not verified; Persona Vectors' current formal acceptance was not reverified. No cited method was locally reproduced. This is a targeted review through 19 October 2026, not an exhaustive systematic review or a guarantee of priority.

The integrated source-provision/ordinal/CPU evidence is provisionally classified as a **partially novel candidate empirical scope under this targeted review**, not established priority. The exact contribution still requires stronger semantic and independent-speaker evidence. No algorithm presently qualifies as potentially novel on both technical distinction and empirical support.

## 3. Materials and methods

### 3.1 Authentic English source material and ethics

We use the ICSI original English meeting transcripts, distributed through the official Edinburgh site. The archived [qualification record](validation/p1/english_real_speaker_stage_v1/icsi_qualification_v1.json) binds the exact archive and official release pages. The modern [distribution license](https://groups.inf.ed.ac.uk/ami/icsi/license.shtml) is CC BY 4.0; historical archive notices are retained. Attribution is to the ICSI Meeting Corpus and its creators, described by [Janin et al.](https://www.ee.columbia.edu/~dpwe/pubs/icassp03-janin.pdf). Corpus participation procedures are not consent specifically to this later speaker-simulation study. Copyright permission does not settle every privacy or personality-right question, and no new ethics approval is invented.

The five development speakers are all qualifying speakers from a bounded, pre-generation source-curation pass, not a random sample. Qualification required source-supported professional self-reports, separate style material, usable earlier conversation and interpretable current contexts, with privacy exclusions. Each speaker supplies two contexts. Speakers share meetings, partners and topics. Selection for available self-reports further restricts generalization. References were seen during source curation; they are withheld from model prompts, not claimed unseen by study designers.

This is local, pseudonymous professional-dialogue research, not identity enrichment, deployment impersonation or whole-person biography modeling. Source dialogue, generated continuations, speaker IDs and review mappings remain private. Quoting individual utterances is unnecessary for the public results. Source/privacy auditing was AI-assisted and is not an ethics-board determination or a guarantee against re-identification.

A later frozen ICSI validation-source screen yielded no qualifying independent cohort; a separate AMI expansion screen failed its minimum eligibility rule. Neither threshold was weakened. These are bounded selection failures, not proof that the entire corpora are unusable. The 58 Japanese reserved speakers remain untouched and do not provide English validation. No new-speaker experimental replication is reported.

### 3.2 Source-provision design

The [English development registration](validation/p1/english_real_speaker_stage_v1/protocol_v1.json) crosses three additions to a common current conversation:

- **S:** four earlier-speech rates—contractions, hesitation fillers, tentative expressions and question turns. This is a narrow style description, not a complete speaker model or a validated behavioral personality representation.
- **F:** dated professional self-report paraphrases curated from actual sources. These are not independently verified or necessarily current biographical truths.
- **H:** authentic earlier dialogue with source dates preceding the current context. H naturally contains stylistic and factual information; an earlier statement's truth is not assumed to persist.

All conditions contain the same eight authentic preceding turns, ending before target onset. C0 therefore already contains speaker cues: it means no *additional* S/F/H package, not persona-free text. The authentic continuation is excluded from every prompt and is not a unique gold answer. The task is one continuation of a fixed multi-turn context, not a freely evolving multi-session consistency experiment.

| English label | S | F | H | Original v1.1 label for these factors |
|---|---:|---:|---:|---|
| C0 | 0 | 0 | 0 | C0 |
| C1 | 1 | 0 | 0 | C1 |
| C2 | 0 | 1 | 0 | C2 |
| C3 | 1 | 1 | 0 | C4 |
| C4 | 0 | 0 | 1 | C3 |
| C5 | 1 | 0 | 1 | C5 |
| C6 | 0 | 1 | 1 | C6 |
| C7 | 1 | 1 | 1 | C7 |

The English registrations use S/F/H as bits 1/2/4. The C3/C4 crosswalk is explicit; no historical labels were rewritten. Factorial analyses use factor codes rather than assuming historical label equivalence.

Each context also receives M_STYLE (another development speaker's style) and N_STYLE (pooled development style), both with F=H=1. These matched-schema controls are not original-protocol token-matched placebo N_style/N_history; there is no N_history here. Donor rates are analytic controls, not claims of chronologically deployable donor information. No donor lexical examples or target answer are supplied. Conditions share instructions, headings and token ceilings but not identical input length. No padding, output-dependent matching or post-hoc prompt repair is applied.

This exploratory amendment estimates **provision of source packages**, not pure latent S/F/H mechanisms. It is not execution of original Track A's identical task-sufficient trusted evidence design, nor a full stale/conflict/oracle Track B. H's mixed content and varying information quantity are central interpretation limits, not minor nuisances to be erased statistically.

### 3.3 Models, execution and provenance

The historical experiment used official Qwen3-0.6B Q8_0, revision `23749fefcc72300e3a2ad315e1317431b06b590a`, without thinking or custom stop strings. Its complete 100-response evidence includes an archived safe interruption/resume without repetition. The subsequent [prospective paired protocol](validation/p1/english_model_comparison_v1/prospective_protocol_v1.json) reused the identical speakers, contexts, source material and control assignments for Qwen2.5-1.5B Base and Instruct: 100 responses each, not independent test cases.

| Deployment | Pinned GGUF revision | Weight SHA-256 |
|---|---|---|
| Qwen2.5-1.5B Base, Q4_K_M | `4d8150eba159047c0ad5f72a8473e4ad60419c4a` | `ea47cef917fa77a3458206d0848f81dd033dfb859bbb3b176bf6006d3b620814` |
| Qwen2.5-1.5B Instruct, Q4_K_M | `531cb7a27c3ad23c7d9c69d2d7a9de562ce55bcd` | `f86985a0e8b549680da4cf43a037bb185c4ec8d1ee07cce52c1720f848b7c972` |

Static non-imatrix GGUFs are published by mradermacher from the Apache-2.0 upstream models. Exact conversion commands/upstream quantizer provenance are incomplete, explicitly separate from pinned-weight inference repeatability. Source versions, original metadata, vocabulary/merges, special tokens, native tokenization and prompt bytes are bound in the archived manifests. Dirty executable source hashes supplement the recorded Git revision; a source commit alone is not the complete execution identity.

All configurations use 2,048-token context, 128-new-token ceiling, four CPU threads, temperature 0, top-p 1 and seed 42, with no hidden generation warmup or retries. The paired study uses pinned llama.cpp b11573 CPU server, SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. Base receives a plain completion transcript; Instruct receives its verified official chat template. Both paired configurations use the same case-specific next-role stop strings. Native EOS behavior differs. This comparison concerns checkpoint-plus-interface deployment, not isolated instruction-training causation. Comparing historical 0.6B with 1.5B also changes family, quantization, occasion and stopping policy; it is not a controlled scale experiment.

Condition order is prespecified and cyclic within case, reversed for the second context. Base ran before Instruct in fixed model blocks. Host load, execution order and light concurrent host activity limit causal cross-model time attribution. No parallel model processes were used. Frozen RAM safety envelopes were enforced by official controllers; no old threshold was lowered or unrelated application terminated. Timing means completion-call wall time on a CPU backend, not CPU process time, energy or end-to-end model acquisition. Process-lifetime peak working set is not a condition-specific causal memory outcome.

### 3.4 Genuine human evaluation and deviations

The principal researcher supplied genuine judgments for 99 of the historical 100 responses. The displayed package masked condition assignments, and the researcher affirmed manual blind rating; project independence and absence of prior exposure are not established. The researcher was involved in the project and had prior material/report exposure. We do not claim double blinding, external independent evaluation or inter-rater reliability.

The frozen original rubric specified 0–3. The researcher subsequently clarified that the actual ratings used 0–5: higher is better, 0 is a valid lowest category and 5 the highest; 1–4 are ordered categories without precise verbal anchors. This is a retrospective instrument deviation, not prospective registration of the actual scale. Original ratings, errors and rubric remain unchanged; no conversion to 0–3 or invented intermediate anchors was made. One response's judgment remains UNAVAILABLE.

Only three primary domains have admissible ordered ratings: relevance, local conversational coherence and perceived linguistic resemblance to authentic earlier examples. These do not establish behavioral Persona Fidelity, factual correctness, historical truth or temporal consistency. Secondary fields and claim/evidence annotations are insufficiently validated and are not repaired or used to infer those outcomes. Paired wins below are derived from pointwise ratings, not a separately collected direct human-preference experiment.

The additional 200 responses have a separate prospectively specified 0–5 rubric and a mixed, model-and-condition-masked package with common case dossiers. Genuine review is pending. The protected new mapping has not been opened for this synthesis. A multiple-missing/applicability-aware analysis must be frozen before joining new ratings; the historical single-missing implementation cannot simply be assumed valid for arbitrary NA patterns.

### 3.5 Statistical estimands and uncertainty

Main ordinal effects compare factor-on versus factor-off within speaker, context and other-factor stratum, reporting wins, ties, losses and net advantage P(win)−P(loss). For each domain and all five ordinal cuts k=1,…,5, we also analyze the binary outcome 1(rating≥k). Every nonempty subset A of {S,F,H} has contrast `2 × mean[(product of ±1 factor codes in A) × outcome]`, first within context, then equally across contexts and speakers. Interaction scaling is therefore factorial-scaled, not an unscaled difference-in-differences. Cuts are neither selected as success thresholds nor averaged into a cardinal score.

The unavailable historical rating is enumerated over all six allowed categories separately for each domain. Resulting bounds preserve the full allocated finite-sample estimand. They are logical missing-outcome bounds, not imputations, confidence intervals or simultaneous cross-domain confidence regions. Complete-speaker estimates target a different subset and are reported separately. Speaker profiles and leave-one-speaker-out (LOO) ranges describe heterogeneity/influence, not calibrated sampling uncertainty. Five shared-meeting speakers do not justify treating 300 responses as independent subjects. No confirmatory p-values or calibrated population confidence intervals are claimed; earlier unsuccessful confirmatory-calibration studies remain negative.

Technical outcomes use the same complete-speaker factorial arithmetic. Ordinal quality and nominal faster/equal/slower signs can be cross-tabulated where ratings exist; no rating-per-second utility ratio is constructed. Length, token count, copying and stopping metadata are not semantic endpoints.

### 3.6 Post-hoc repetition and empty-response diagnostics

A bounded [analysis scope](validation/p1/english_novelty_synthesis_v1/analysis_scope_v1.json) was fixed after generation and previous analyses but before extracting these additional measurements. All 300 responses were included; nothing was regenerated. Native empty-string and whitespace-only counts are distinct from absent generations. Existing English word extraction is case-folded; repeated contiguous five-word windows yield `(windows−unique windows)/windows`, with an additional any-repeat indicator. Fewer than five extracted words is inapplicable, not zero.

An equal-opportunity sensitivity uses exactly the first 20 extracted words for responses having at least 20. It reduces variable opportunity within the selected prefix, but selecting on output length is post-treatment conditioning. It is not causal length adjustment or representative of short outputs. Repeated phrases can be legitimate; this metric is literal recurrence, not a validated semantic degeneration or fidelity measure. Two counting implementations agree but share lexical extraction. All seven contrasts and all controls are retained, including undefined contrasts when no complete speaker exists.

## 4. Results

### 4.1 Complete observations and human coverage

Each configuration has 80 factorial and 20 style-control outputs, totaling 300 recorded responses to English-language requests. Human primary-domain coverage is 99/100 for the historical configuration and 0/200 for the paired new configurations. Technical output availability does not imply verified output language, semantic completion or applicability. All 300 native responses are nonempty and non-whitespace-only; this does not establish completion or relevance.

### 4.2 Ordinal source-provision effects in the historical configuration

The following bounds apply to all five speakers with the one unavailable judgment preserved. Units are net probability advantage, not mean scale points.

| Domain | S | F | H |
|---|---|---|---|
| Relevance | [−.150, −.125] | [−.075, −.025] | [.000, .050] |
| Coherence | [−.100, −.075] | [−.050, .000] | [−.075, −.025] |
| Linguistic resemblance | [−.150, −.125] | [.075, .125] | [−.025, .025] |

The narrow S representation does not establish general benefit in any of these perceptions. F's positive resemblance direction coexists with a negative relevance direction. H does not establish positive resemblance and has negative coherence net direction. These statements apply to this evaluator, finite source-constrained cohort and historical configuration, not all authentic speakers or all style representations.

All 105 domain-by-effect-by-cut profiles are retained. In the compact display below, the five entries correspond to cuts 1 through 5. P/N means strictly positive/negative under every missing completion; ZP/ZN includes zero on the corresponding side. They do **not** indicate statistical significance.

| Effect | Relevance | Coherence | Linguistic resemblance |
|---|---|---|---|
| S | N N N N ZN | N N N N ZP | N N N P N |
| F | ZP P P ZN N | ZP ZP P P ZN | ZP ZP P P P |
| H | P N ZN P ZP | P P N ZN ZN | P P ZN ZP ZP |
| SF | ZP P P P P | ZP ZP P P P | ZP ZP P P P |
| SH | P P N N ZP | P P P N N | P P P ZP N |
| FH | ZN N N ZP P | ZN ZN N N P | ZN ZN ZP ZN P |
| SFH | ZN N ZP P P | ZN ZN N ZP ZP | ZN ZN ZP ZN P |

For example, S/resemblance is positive at cut 4, [.025,.050], despite its negative net advantage. SH/coherence reverses direction across cuts. No single favorable cut or interaction summarizes the full ordered distribution, and no uniform synergy or stochastic-dominance claim follows. Exact category distributions and bounds are in the [ordinal analysis](validation/p1/english_human_ordinal_v1/ordinal_analysis_v1.json).

### 4.3 Style controls, speaker heterogeneity and cost

C7 versus mismatched style has 2 wins, 8 ties and 0 losses; versus pooled style, 1/9/0; versus no style at F=H=1, 2/6/2. These counts happen to coincide across all three domains, which are correlated ratings rather than three replications. Zero net advantage over no style is not evidence of equivalence. The five speaker net values for this comparison are −1,0,0,.5,.5: averaging masks opposing outcomes.

For S/resemblance, the four complete speakers have net values −.500,−.250,−.125,.125, mean −.1875 and LOO mean range [−.291667,−.083333]. This is subset influence evidence, not a full-cohort confidence interval. Complete-case and full-allocation bounds can differ in direction and must not be interchanged.

In the historical configuration all 40 H-on technical pairs are slower. Relevance and resemblance judgments nevertheless include wins, ties and losses. Existing call-time main effects are +.504, +.257 and +2.053 seconds for S/F/H. Input processing represents 81.83% of aggregate call time; S reduces average output by 5.525 tokens while increasing call time. Shorter outputs therefore do not imply lower cost in this deployment. The [ordinal joint analysis](validation/p1/english_human_ordinal_v1/integrated_analysis_v1.txt) preserves missingness in the quality-by-latency tables; it supplies no causal mediation or cardinal quality/cost utility.

### 4.4 Base/Instruct technical comparison

| Quantity, across 100 responses each | Base | Instruct |
|---|---:|---:|
| Mean input tokens | 496.32 | 509.32 |
| Mean output tokens | 104.06 | 35.58 |
| Mean call time, s | 11.140920 | 7.676109 |
| Mean native prefill time, s | 5.438218 | 5.664629 |
| Mean native decode time, s | 5.676271 | 1.980513 |
| Native EOS / token limit / word stop | 16 / 73 / 11 | 98 / 2 / 0 |
| Observed process-lifetime peak working set, bytes | 2,515,021,824 | 2,347,663,360 |

Mean native timing components need not sum exactly to measured call time. Token limits and EOS are native stopping descriptions, not incomplete/complete semantic labels. The paired configurations differ strongly in output length and stopping behavior; fixed model order and interface differences prevent pure training-cause attribution.

All seven response-call-time factorial contrasts (seconds) are:

| Contrast | Base | Instruct |
|---|---:|---:|
| S | .874282 | 1.522565 |
| F | .421609 | .496915 |
| H | 3.126709 | 2.964881 |
| SF | .012541 | .288265 |
| SH | −.231787 | .116517 |
| FH | .139341 | −.346776 |
| SFH | −.706523 | −.333300 |

H increases call time for all five speakers in each configuration. The between-model H-cost difference changes direction under speaker deletion, so it is not a stable superiority claim. Exact condition summaries, native components, speaker profiles, controls and matched configuration contrasts are in the [technical analysis](validation/p1/english_model_comparison_v1/technical_analysis_v1.json). Human quality differences remain unmeasured for these 200 outputs.

### 4.5 Literal recurrence and applicability

| Configuration | Any repeated five-word window | Mean excess ratio (evaluable outputs) | First-20-word mean (evaluable outputs) |
|---|---|---|---|
| Historical 0.6B | 0/93; 7 NA | .000000 (93) | .000000 (26) |
| 1.5B Base | 78/100; 0 NA | .624975 (100) | .273522 (93) |
| 1.5B Instruct | 1/90; 10 NA | .007843 (90) | .000000 (65) |

The paired Instruct-minus-Base excess difference is −.609505 over 90 mutually evaluable cells. On the 60 pairs with both outputs at least 20 words, its fixed-prefix difference is −.266667. Differential applicability remains substantial. No speaker retains a complete matched factorial grid for the prefix endpoint, so full complete-speaker prefix factorial differences are unavailable. Calling them zero would manufacture evidence.

Base full-response excess S/F/H effects are −.009576,−.020940,+.045550; their LOO ranges each cross zero. SF and SFH effects are −.045708 and −.088700 with negative LOO ranges, but these post-hoc lexical contrasts are not confirmation of a semantic interaction mechanism. The Instruct and historical configurations each retain only two complete speakers for this endpoint. Complete-subset zero contrasts do not establish zero full-cohort effects. The [new diagnostic analysis](validation/p1/english_novelty_synthesis_v1/response_diagnostics_v1.json) and [integrated findings](validation/p1/english_novelty_synthesis_v1/integrated_findings_v1.txt) retain all condition outcomes, contrasts, applicability and sensitivity results.

Literal recurrence in the Base deployment is a reproducible technical observation deserving genuine coherence evaluation. It does not show what the human quality ranking will be, whether repeated technical phrases are erroneous, or whether an algorithm repairs a persona-specific failure. No repetition penalty, post-hoc trimming or regenerated substitute was applied.

## 5. Discussion

### 5.1 Supported empirical contribution

The completed grids permit interpretable finite-sample comparisons of real-speaker source provision. The historical ratings show a negative S net direction, domain-dependent F/H behavior and crossing ordinal interaction profiles. Correct style's occasional advantage over another or pooled speaker description does not establish benefit over providing no extra style. This distinguishes the present negative finding from the untested claim that richer, better-founded speaker representations never help.

The paired deployments add cost, native behavior and literal-recurrence evidence on identical source cases. These results constrain overconfident model comparisons: a faster, less repetitive configuration is not yet a semantically superior persona model. Likewise, the extra cost of H is measured, but factual contamination is not. The distinction between measurable processing consequences and unmeasured semantic benefit is substantive to a quality–efficiency study, not permission to substitute technical metrics for quality.

### 5.2 What is not established

The study does not establish generalized Persona Fidelity, externally verified factual accuracy, temporal contamination, multi-session consistency, a pure model-size effect, a pure instruction-tuning effect, or a retrieval/ranking/LoRA benefit. It does not replicate Nature's warmth intervention or FPPS's hallucination mechanism merely because a Style rating is negative. It does not establish a first-ever factorial persona study, a population effect or publication readiness.

The genuine evaluator is not independent; retrospective scale clarification, unanchored intermediate categories and incomplete domain coverage limit semantic interpretation. Five selected speakers sharing meetings and topics are not 300 independent people. Exposure during source selection and development prevents relabeling later same-context model runs as independent validation. Differential metric applicability, post-treatment prefix selection, native stop differences and fixed model order prevent several tempting causal claims. LOO influence and missing-outcome bounds address specific uncertainty components, not all of these threats.

### 5.3 Algorithm decision and subsequent research

We compared three plausible next routes: consolidate existing empirical evidence, implement an algorithm, or collect another model/cohort. Consolidation was selected because the existing evidence is substantial and directly relevant, while the new model quality comparison still lacks genuine ratings. Ordinary relevance filtering, temporal retrieval, candidate selection and activation steering have close precedents. There is no justified technical distinction plus semantic failure target supporting a new method at present.

The decision is **GO** for the bounded empirical route, **PIVOT** from broad novelty claims to precise comparisons, and **STOP** spending generations on technical proxies alone. No original algorithm has been developed or validated. A future intervention needs an actual semantic failure, equal source access, a meaningful retrieval pool, strong simple and published baselines, controlled ablations and full inference/preprocessing costs. A lower repetition statistic alone is not an adequate objective.

The next high-information action is genuine review of the already generated 200 mixed responses, followed by a pre-join missingness/applicability-aware ordinal analysis and matched quality/cost comparison. Only then should a separately qualified English cohort or falsifiable intervention consume the protected validation allocation. This sequence does not prohibit unrelated valid work; it identifies the absent evidence needed for the next *semantic comparative* claim. It does not require rerunning the completed experiments.

## 6. Reproducibility and data availability

Registrations, exact prompts, token IDs, model/backend hashes, source snapshots, native HTTP outputs, journal chains, execution receipts, original ratings and analysis code are retained. Public artifacts expose safe aggregate results and hash bindings, not raw speaker dialogue or mappings. Analysis reproduction rechecks raw journals and separately implemented arithmetic; it is distinct from generation reproduction, independent raters and independent experimental validation. Bit-identical generation across different environments is not guaranteed. Public clone-only reproduction remains **PARTIAL** because private evidence and acquired native/model artifacts are not distributed with the source.

| Evidence | Authoritative artifact and SHA-256 |
|---|---|
| Historical human ordinal result | [ordinal_analysis_v1.json](validation/p1/english_human_ordinal_v1/ordinal_analysis_v1.json), `a562e7249706f8982916c6959d577bc24fc94f1d46d490881b1b365d5c5f616d` |
| Paired technical result | [technical_analysis_v1.json](validation/p1/english_model_comparison_v1/technical_analysis_v1.json), `cd55e86eea86deab451252ace4e08cb4e872e7f9d22f45264bffdfda7ba362ae` |
| Post-hoc recurrence/empty diagnostics | [response_diagnostics_v1.json](validation/p1/english_novelty_synthesis_v1/response_diagnostics_v1.json), `59f082df6474dd3bb1ea95786d0a351f4dac6a3754b7587b0d0f37b7f630dab2` |
| Final executed resource receipt | [instruct_execution_receipt_v1.json](validation/p1/english_model_comparison_v1/instruct_execution_receipt_v1.json), `0e71d1f083ddf467ab829b887acae52b113aeddc2b9c62e9ef97abfa0a749ce1` |

The [new raw-to-result commands](validation/p1/english_novelty_synthesis_v1/integrated_findings_v1.txt) use the existing private analysis environment; offline fixtures do not require human data. Earlier human and model-comparison reproduction instructions remain in their respective result directories. Scope and implementation were hash-locked before the diagnostic extraction; repeated verification recalculated the archived outputs without new inference. Shared lexical extraction is explicitly not an independently validated semantic measurement instrument.

The current synthesis consumed zero new generations or human judgments. Cumulative authorization use remains 988/1200 generations and 6367.387376899885/72000 inference seconds. Of 212 remaining generations, 160 are reserved for qualified independent validation; the other 52 are not a quota to spend. No Git staging, commit or push is automated. Prior local protected backups do not imply remote or off-device archival safety. No background model run is implied after handoff.

## 7. Conclusion

English authentic-speaker S/F/H source provision produced negative and heterogeneous perceived-quality patterns in one small-model development configuration and clear processing-cost effects in two further configurations. The additional Base/Instruct outputs show markedly different native generation and literal-repetition behavior, but their semantic comparison remains pending. These findings support a constrained empirical account, not a universal reliability–persona trade-off discovery, a validated original algorithm or complete coverage of the research questions. Genuine comparative semantic review and a qualified independent English cohort are the decisive remaining steps toward a stronger paper.

## References and source-status record

The linked evidence notes contain full author lists, method/appendix locators, publication/preprint cross-links and access limitations. The following are bibliographic entries, not independent replications:

1. de Araujo PH et al. Persistent Personas? Role-Playing, Instruction Following, and Safety in Extended Interactions. EACL 2026:5329–5359. [doi:10.18653/v1/2026.eacl-long.246](https://aclanthology.org/2026.eacl-long.246/).
2. Sun Z et al. When Personalization Misleads: Understanding and Mitigating Hallucinations in Personalized LLMs. Findings of ACL 2026:8041–8060. [doi:10.18653/v1/2026.findings-acl.395](https://aclanthology.org/2026.findings-acl.395/).
3. Izawa Y et al. Steering at the Source: Style Modulation Heads for Robust Persona Control. ICML 2026, PMLR 306:50230–50271. [Official proceedings](https://proceedings.mlr.press/v306/izawa26a.html).
4. Wang K et al. Memory-Driven Role-Playing: Evaluation and Enhancement of Persona Knowledge Utilization in LLMs. Findings of ACL 2026:23475–23510. [doi:10.18653/v1/2026.findings-acl.1175](https://aclanthology.org/2026.findings-acl.1175/).
5. Su M et al. Beyond Dialogue Time: Temporal Semantic Memory for Personalized LLM Agents. Findings of ACL 2026:29935–29951. [doi:10.18653/v1/2026.findings-acl.1496](https://aclanthology.org/2026.findings-acl.1496/).
6. Kim J, Yang N, Jung K. Persona Switch: Mixing Distinct Perspectives in Decoding Time. Findings of EACL 2026:1955–1967. [doi:10.18653/v1/2026.findings-eacl.101](https://aclanthology.org/2026.findings-eacl.101/).
7. Ibrahim L, Hafner FS, Rocher L. Training language models to be warm can reduce accuracy and increase sycophancy. Nature 2026;652:1159–1165. [doi:10.1038/s41586-026-10410-0](https://www.nature.com/articles/s41586-026-10410-0).
8. Cho S, Park S, Kim JH. Internalizing persona knowledge in small language models via multi-objective contrastive learning. Knowledge-Based Systems 2026;347:116335. [doi:10.1016/j.knosys.2026.116335](https://doi.org/10.1016/j.knosys.2026.116335). Full-method verification incomplete.
9. Chen Y-P et al. Post Persona Alignment for Multi-Session Dialogue Generation. Findings of EMNLP 2025:20184–20192. [doi:10.18653/v1/2025.findings-emnlp.1098](https://aclanthology.org/2025.findings-emnlp.1098/); arXiv:2506.11857 is the linked preprint.
10. Hayashi E, Shin A. Do Personalized LLMs Need the Whole Conversation? Matching the Full History with Only 5% of Its Text via Relevance-Filtered Context. [arXiv:2610.14952v1](https://arxiv.org/abs/2610.14952), 10 October 2026. Verified preprint, not verified formal publication.
11. Shin J et al. Spotting Out-of-Character Behavior: Atomic-Level Evaluation of Persona Fidelity in Open-Ended Generation. Findings of ACL 2025:26312–26332. [doi:10.18653/v1/2025.findings-acl.1349](https://aclanthology.org/2025.findings-acl.1349/).
12. Vijjini AR et al. Exploring Safety-Utility Trade-Offs in Personalized Language Models. NAACL 2025:11316–11340. [doi:10.18653/v1/2025.naacl-long.565](https://aclanthology.org/2025.naacl-long.565/).
13. Kim J, Yang N, Jung K. Persona is a Double-Edged Sword: Rethinking the Impact of Role-play Prompts in Zero-shot Reasoning Tasks. Findings of IJCNLP-AACL 2025:848–862. [doi:10.18653/v1/2025.findings-ijcnlp.51](https://aclanthology.org/2025.findings-ijcnlp.51/).
14. Chen R et al. Persona Vectors: Monitoring and Controlling Character Traits in Language Models. [arXiv:2507.21509v3](https://arxiv.org/abs/2507.21509). Formal acceptance not reverified in this assessment.
15. Janin A et al. The ICSI Meeting Corpus. ICASSP 2003. [Primary paper](https://www.ee.columbia.edu/~dpwe/pubs/icassp03-janin.pdf); [official corpus license](https://groups.inf.ed.ac.uk/ami/icsi/license.shtml).
