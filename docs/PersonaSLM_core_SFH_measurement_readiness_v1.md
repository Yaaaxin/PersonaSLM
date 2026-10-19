# Core S/F/H measurement readiness after P5 — v1

Maintainer: Yaxin ZHENG. AI-assisted scientific development; human semantic confirmation remains pending. First submission target: PLOS ONE.


Protocol v1.1 remains the frozen baseline; v1.2 is proposed. The adopted P1d E/V addendum is unchanged, SHA-256 `1ea81f56548d6685fc0eb67bdc291283f0867e73008f8fd7e26eea432bc30319`. Its 144-speaker/288-case/2,016-request design is **NO-GO**. This is a separate development proposal, not an automatic amendment or confirmatory freeze.

| Work-tree branch | Evidence and current requirement |
| --- | --- |
| P0 | Historical PASS; preserve all records and version runtime compatibility |
| P1a | Original C0–C7 S/F/H exploration retained; independent replication missing |
| P1b | 192 development outputs, researcher-adopted AI annotations; complex-task delivery evidence retained |
| P1c | 72 adopted outputs / 16 exploratory contrasts; restricted history packages and boundary sensitivity retained |
| P1d | Adopted prospective E/V design; no validation inference; model/measurement/control/independence gates open |
| P2 | Evidence-availability Track B preparation only; never pooled with Track A |
| P3 | 144 Base budget + 16 Base format + 8 Instruct smoke development runs retained; no pure post-training effect |
| P4 | No authorized real-speaker study executed; consent/access, independent sampling and review needed |
| P5 | Eight authorized oracle outputs completed; AI headroom gate met, package-level interpretation only |
| P6 | Offline ESCP tied by strong simple rules, with higher measured CPU cost; no original algorithm established |

RQ1 concerns four distinct reliability dimensions; RQ2 S/F/H factors; RQ3 configuration/context; RQ4 observable localization. P1a/b and the following candidate address RQ1/2; current P1d E/V only addresses conditional history packages under fixed S/F. P3 supports exploratory configuration observations; P5 supports RQ4 headroom. No existing P1d plan independently identifies S, F, S×H or full model-by-factor interactions. See the retained [full RQ/H1–H5 mapping](PersonaSLM_research_programme_alignment_v1.md).

## Exact compact development candidate

Eight existing development cases, eight synthetic speakers, two cases in each of four task families. All eight S/F/H cells plus N_style and N_history: **80 requests**, not 80 independent subjects. The two extra cells are necessary for the specifically requested C1−N_style and C3−N_history comparisons. This is a compact chosen design, not a mathematically unique minimum or a precision-powered confirmatory sample.

Manifest: `docs/validation/core_sfh_readiness_v1/core_sfh_manifest_proposed_v1.json`; SHA-256 `0cdb9146306faeddddba85b896acbf2d49899c9a01a5d5e28751b62d787d64ae`. Same pinned Instruct GGUF/backend/template, CPU4/context4096, seed42/temp0/top-p1,96 output tokens,no retries; order seed716281. All 80 native token arrays match the official tokenizer and reconstruct prompts; range **1626–1849**,16 matched control pairs, no held-out overlap. Vocabulary checks issued no completions.

True C0 omits style, personal facts and optional historical quotations. The complete original 32-row E, current question, date, fixed context and reference remain identical within each case. H_none from prior diagnostics is not relabeled C0. Unlike the oracle, this proposal does **not** supply a reference-selected reduced ledger. The generic evidence-priority/one-answer instruction is a new fixed prompt realization, identical across these cells; comparison with earlier H_none is not a pure S/F/H effect.

S adds one of two existing brief/calm linguistic packages. F adds one authored shared hobby/preference package; it does not establish sensitivity to diverse personal facts. H supplies two dated unrelated conversations exhibiting conversational order. H includes lexical/style/behavioral cues, so history effects are implemented packages. There are eight names but only two linguistic specifications and shared task ancestry. The controls are coherent token-matched descriptive texts, **diagnostic only**, not validated neutral or information-equivalent history. Full materials and blank scientific decisions are in `candidate_materials_v1.json`.

Preserved primary simple contrasts: C1−C0, C3−C0, C1−N_style, C3−N_history. Separately report average S/F/H, S×F, S×H, F×H, S×F×H; H1 at F=0 is `(C5−C3)−(C1−C0)`. The exact 12 weights are in the candidate; they do not replace the **16 E/V comparisons**. H2 remains diagnostic package work; H3 separates structural/semantic states; H4 and H5 require independent realizations/speakers/templates and are not established by this development run.

The registered necessary readiness criterion remains 8/8 identifiable complete C0 answers; accuracy is reported separately. Review all cell-level delivery/fidelity opportunities and boundary failures. A failed conditioned cell is not automatically proof of model inadequacy or a Persona mechanism. Maintain the full 80-request denominator, categorical distributions and paired case contributions. Unknown cells do not get renormalized factorial weights. With eight purposive speakers/two cases per family, bootstrap and leave-one-speaker-out are descriptive sensitivity only; do not report confirmatory significance. Shared templates limit external inference beyond speaker clustering.

Estimated CPU wall time from older full-ledger mean: about **28 minutes for 80 requests**, with a prespecified 60-minute ceiling; this is a planning estimate, not measured future latency. No new 80-request authorization is present. Oracle success is necessary headroom evidence, not a guarantee that this full-ledger design passes. If inadequate, retain results and prepare a specific evidence-presentation/model amendment rather than automatically scaling P1d.

## Persona Fidelity and measurement validity

`fidelity_v2/` adds eight authored challenges and separate blind fidelity/quality panels. Counterexamples cover wrong-but-stylish, correct-but-incompatible, correct historical fact without current answer, recalled history with wrong conversational order, preserved persona with a promise, and improved task delivery with lost persona cues. These are construction tests, not empirical validation. Linguistic and Behavioral Fidelity use separate 1–5 rubrics, evidence spans and alternative scores; no composite score and no factual-accuracy proxy.

Target references in the core materials are disjoint from the optional dialogue examples. The fidelity panel is not shown the task answer or correctness rating; the quality panel is not shown persona targets. Short replies may be insufficient opportunities; do not silently force low fidelity or N/A. The original eight-word diagnostic is not a validated threshold. Blindness is incomplete when style/content reveals conditions. No second reviewer, human rating or agreement statistic is fabricated. Independent reviewers, when available, must rate before AI keys and adjudication. If unavailable, narrow the measurement claim explicitly.

## P1d defects, independence and publication requirements

`consequential_defect_register_v1.csv` and `targeted_material_evidence_v1.json` preserve exact examples and resolutions. The bank remains 288 AI VALID_WITH_LIMITATIONS, 288 diagnostic controls, zero researcher adoptions; the previous 64-case/64-control stratified review package is reused. No new reference-answer defect was established in this targeted review, so no bank rewrite is justified. Source hashes were checked against the census. E1V1 literal answer support, adjacent chain shortcuts, target/template covariance and procedural-control priming remain restrictions.

Existing E/V precision simulations are retained. Their assumptions are not observed ICCs and do not justify a different core S/F/H sample. Independent core validation requires a new prospective contrast-specific precision calculation with crossed speaker/template/ancestor dependence, missingness and LF/BF applicability. Main endpoints, multiplicity and practical thresholds must be decided before a confirmatory freeze, not chosen from these eight successes.

Manuscript-ready methods commitment: distinguish native termination, identifiable candidate span, independent completeness review, factual claim support and final-task delivery. Analyze paired cases under fixed valid evidence; describe exact intervention packages, denominators, uncertainty sources and annotation provenance. Treat faithful persona expression as separate from correctness. Preserve null and failed experiments. A publishable empirical path needs independently authored/counterbalanced cases, independent measurement evidence, verified model lineage, sufficient contrast precision and honest controls; P5 and the authored rubric do not establish publication readiness.
