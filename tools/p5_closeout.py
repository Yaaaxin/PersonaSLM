"""Build the P5 scientific record and one concrete next-decision packet.

No model calls, protocol adoption, human annotation or automatic authorization.
"""
import argparse
import copy
import csv
import json
from pathlib import Path
import subprocess
import p5_oracle_run as p
from p1d_design import csvwrite

CORE=Path('docs/validation/core_sfh_readiness_v1')
KILL=Path('docs/validation/p6/escp_kill_test_v1')
META='Maintainer: Yaxin ZHENG. AI-assisted scientific development; human semantic confirmation remains pending. First submission target: PLOS ONE.\n\n'

def doc(name,text):
    path=Path('docs')/name;p.require(not path.exists(),'Do not overwrite '+str(path))
    path.write_text(text,encoding='utf-8',newline='\n')

def build():
    m=p.load(p.OUT/'measurement_v1/summary_v1.json');audit=p.load(p.OUT/'execution_integrity_v1.json')
    run=Path(audit['run_directory']);runmeta=p.load(run/'manifest.json');plan=p.load(p.FROZEN)
    core=p.load(CORE/'core_sfh_manifest_proposed_v1.json');validation=p.load(CORE/'validation_v1.json')
    kill=p.load(KILL/'summary_v1.json');paired=p.load(p.OUT/'measurement_v1/paired_historical_comparison_v1.json')
    prior=Path('docs/validation/p1d/scientific_validation_v1');census=p.load(prior/'scientific_audit_summary_v1.json')
    for source,h in census['source_sha256'].items():p.require(p.sha(Path(source))==h,'P1d candidate source changed')
    case_rows=list(csv.DictReader((prior/'case_scientific_review_v1.csv').open(encoding='utf-8-sig')))
    controls=list(csv.DictReader((prior/'control_semantic_risks_v1.csv').open(encoding='utf-8-sig')))
    p.require(len(case_rows)==len(controls)==288,'Scientific inventory changed')
    p.require(all(not r['researcher_decision'] for r in case_rows) and all(not r['human_decision'] for r in controls),'Unexpected adoption; inspect rather than overwrite')
    representative=[]
    for family in ('single_fact','multi_component','relational_integration','context_followup'):
        r=next(x for x in case_rows if x['family']==family)
        representative.append({k:r[k] for k in ('case_id','family','exact_supporting_evidence','entity_interpretation','task_limitation','restricted_interpretation')})
    p.save(CORE/'targeted_material_evidence_v1.json',{'source_hashes':census['source_sha256'],
        'representatives':representative,'control_example':controls[0],'human_confirmations':0,
        'method':'Targeted reinspection of consequential existing findings; not a second 288-case independent audit.',
        'bank_changed':False})
    defects=[
      ('sampling','288 cases / 247 question strings / 16 abstract templates / four shared ancestors',
       'Name-level clusters do not identify general linguistic-template population effects.',
       'Restrict target population to constructed templates, or independently author and cross new templates before freeze.',True),
      ('control','Procedural archive quotations prime checking, omission and first-person narrative; dates absent.',
       'Length equality cannot identify a fully controlled semantic history effect.',
       'Retain diagnostic-only classification; strict neutrality would need separate semantic validation.',False),
      ('entity_validity','E changes entity/value/lexical cues; V changes interval/value.',
       'Package effects only, even with mathematically valid factorial weights.',
       'Preserve adopted estimands; any mechanism-isolating redesign is a prospective amendment.',False),
      ('positive_answer_support','E1V1 copies complete answer in 72 single-fact cases, one component in 144 cases, chain entry in 72.',
       'Answer copying can succeed; not pure interference or latent reasoning.',
       'Retain declared positive controls and separately report task-family contribution.',False),
      ('integration_shortcut','Linked entity values occur adjacently in ledger blocks.',
       'Correct final chain values do not prove sequential reasoning.',
       'Keep current task label with limitation; independent shuffled-link diagnostic would require versioned materials.',False),
      ('model','Full-ledger Instruct AI task success 2/8; oracle 8/8 changes multiple properties.',
       'Oracle adequacy cannot certify full P1d or full S/F/H readiness.',
       'Use bounded core development before a confirmatory model-policy amendment; do not expand Base cohort.',True),
      ('measurement','No independent human boundary or LF/BF ground truth; old shared-label limitation retained.',
       'AI adoption is not inter-rater reliability; narrow style checks are not validated Persona Fidelity.',
       'Use separated panels, blinded actual raters where available, applicability/uncertainty and source spans.',True),
    ]
    csvwrite(CORE/'consequential_defect_register_v1.csv',[{'id':k,'evidence':ev,'consequence':cons,'resolution':res,
        'can_resolve_before_freeze':True,'substantive_new_design_or_adoption_needs_confirmation':gate,
        'current_case_correction':None,'original_bank_preserved':True,'researcher_decision':''} for k,ev,cons,res,gate in defects])
    # Carry all previous candidates forward, preserving the earlier negative findings.
    oldreg=Path('docs/validation/research_alignment_v1/algorithm_opportunity_registry_v7.json')
    reg=copy.deepcopy(p.load(oldreg));reg['version']='algorithm_opportunity_registry_v8'
    reg['parent']={'path':oldreg.as_posix(),'sha256':p.sha(oldreg)}
    for e in reg['entries']:
        if e['id']=='boundary':e['observed_failure']='P5: eight native EOS candidates; frozen labels remain AMBIGUOUS. Alias normalization alone does not certify semantic completion.'
        if e['id']=='temporal_entity':e['proposed_algorithm']='Oracle package executed; AI task success 2/8 to 8/8. Reference-aware reduction is not deployable retrieval or a novel algorithm.'
        if e['id']=='answer_components':e['observed_failure']='Historical full-ledger errors retained; oracle supplies 14/14 components versus 8/14 present and 3/14 supported previously, AI-only.'
        if e['id']=='ESCP':
            e['classification']='ENGINEERING_ADAPTATION_NO_INCREMENTAL_ADVANTAGE'
            e['fair_comparison']='New 16 adversarial cases: equal-output elementary rules exactly match support, conflict, component and admission diagnostics.'
            e['cpu_cost']=kill['cpu_cost'];e['remaining_gap']='No demonstrated residual computational or model benefit; free-text extraction and generated fidelity remain untested.'
    reg['negative_findings_preserved'].append('New equal-output simple-rule baseline ties all sixteen additional authored fixtures and uses less median CPU time; no original ESCP contribution demonstrated.')
    reg['primary_source_review']={'path':'docs/related_work_novelty_matrix_monitor_v8.md','status':'built in this milestone'}
    p.save(CORE/'algorithm_opportunity_registry_v8.json',reg)
    pairs='\n'.join('| '+r['case_id']+' | '+r['old_task']+' | '+r['oracle_task']+' | '+str(r['old_present'])+' / '+str(r['old_supported'])+' | '+str(r['oracle_present'])+' / '+str(r['oracle_supported'])+' |' for r in paired)
    doc('P5_oracle_engineering_report_v1.md','# P5 oracle diagnostic — engineering record v1\n\n'+META+f'''
Phase P5 / RQ4. Exactly **8 successful CPU requests, 0 failures, 0 retries**. This is development evidence, not P1d independent validation. The originally supplied `p1d` directory was a path typo: the existing `p5` manifest matched the authorized hash exactly. No source was moved or substituted.

- Original manifest: `docs/validation/p5/oracle_evidence_proposed_v1/oracle_evidence_manifest_proposed_v1.json`.
- Frozen byte-identical copy: `docs/validation/p5/oracle_diagnostic_v1/frozen_manifest_v1.json`.
- SHA-256: `{p.SHA}`.
- Authorization: `docs/validation/p5/oracle_diagnostic_v1/researcher_authorization_v1.json`; actual registration time is software provenance, human decision time is null.
- Raw run: `{run.as_posix()}`. `events/` contains append-only hashed HTTP request/response records, base64 native bodies, input/output IDs, process telemetry and every result; `manifest.json` preserves original config, Git state and source snapshots. Logs and `summary.json` remain in this run.

The intended upstream model is Qwen/Qwen3.5-2B, revision `965dcc54bc9c0591873df0e9869c056a54d323d1`; the actual third-party Q4_K_M artifact is the unchanged lmstudio candidate. Conversion-source lineage remains only partially verified, accepted for development only.

| Pinned item | SHA-256 |
| --- | --- |
| GGUF | `{p.s.MODEL_SHA}` |
| llama-server b11573-0f701c882 | `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| llama-tokenize | `{plan['tokenizer_sha256']}` |
| Official chat template | `{plan['template_sha256']}` |

CPU only, four generation/batch threads, 4,096 context, 96 output tokens, seed 42, temperature 0, top-p 1, cache_prompt false, no custom stops, no ignored EOS, no warmup/speculative/vision generation. Request order is the original manifest order. Live server tokens matched all eight native records before the first completion. Input length 182–303 tokens; no input truncation. All returned generated token IDs were retained.

Initial memory preflights failed the unchanged 3 GiB physical-headroom gate. No completion was sent during those failures. The researcher released memory; final preflight passed. No unrelated process was stopped. Failure records remain beside the successful preflight. System-memory conditions differ from the older Instruct run, so timing is descriptive rather than an isolated evidence-length efficiency effect.

Native terminations: **8 eos**, 0 output-budget stops; last returned token 248046 in each output. Generated tokens total **{m['total_generated_tokens']}**. Mean request wall time **{m['mean_latency_seconds']:.4f} s**; run elapsed **{p.load(run/'summary.json')['elapsed_seconds']:.4f} s** including setup/checks. Observed peak server working set **{m['peak_process_working_set_observed']:,} bytes**, based on {m['memory_observations']} samples / cumulative process peak telemetry; not a claim of complete system peak RAM. See `engineering_inventory_v1.json` for per-request timings, hashes, counts and order.

The frozen parser labels remain **8 AMBIGUOUS with 8 identifiable candidate spans**. It expects `eog`, while the runtime reports `eos`; even the separately saved alias sensitivity stays AMBIGUOUS because COMPLETE also requires a separate text-bound semantic review. Neither alias normalization nor terminal punctuation creates human boundary truth.

Executed commands: `.venv/Scripts/python.exe tools/p5_oracle_run.py register`, `preflight --output docs/validation/p5/oracle_diagnostic_v1/preflight_v1.json`, then `run --preflight docs/validation/p5/oracle_diagnostic_v1/preflight_v1.json`. The exclusive claim prevents reuse; these are reproduction records, **not permission to rerun**. Safe offline reconstruction: `audit --output <new unused JSON path>`. Measurement source is `tools/p5_oracle_measurement.py`; it refuses changed output text. Tests and preservation results are in this milestone's reproducibility manifest.
''')
    doc('P5_oracle_scientific_report_v1.md','# P5 oracle diagnostic — scientific report v1\n\n'+META+f'''
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
{pairs}

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
''')
    doc('related_work_novelty_matrix_monitor_v8.md','# Related work / novelty monitor v8 — P5 and ESCP kill test\n\n'+META+'''
This focused update retains [v7](related_work_novelty_matrix_monitor_v7.md), its bibliographic details and earlier full-methods inspection. This milestone revisited the primary Zep, Mem0 and FC/PS method/experiment sections and verified the ACL records of FPPS, CoVe and RARR. No published implementation was reproduced by the local rule comparator.

| Direct prior art | Verified overlap / methodological consequence |
| --- | --- |
| [Zep, arXiv:2501.13956v1](https://arxiv.org/html/2501.13956v1), 2025 preprint; peer review not verified | Episode/entity/community graph, source edges, world-valid and transaction times, conflict invalidation, hybrid retrieval and reranking already cover much of evidence-state attribution. Methods use model-based extraction; DMR/LongMemEval tests do not establish equivalence to CPU-only typed fixtures. |
| [Mem0, arXiv:2504.19413v1](https://arxiv.org/html/2504.19413v1), 2025 preprint; peer review not verified | Extraction plus ADD/UPDATE/DELETE/NOOP, graph conflicts and dual retrieval overlap with state management. GPT-4o-mini extraction/update and embedding/Neo4j infrastructure are material computational assumptions. LOCOMO evaluation excludes its adversarial category; this is not evidence that Mem0 fails our cases. |
| [What to Admit and How to Present, arXiv:2610.11188v1](https://arxiv.org/html/2610.11188v1), 2026 preprint | FC compiles situated attributes; PS splits memories into typed units with allowed uses, excluding denied content. Shared verdicts separate admission from rendering. Reported personalization losses and unmet external gates make fidelity preservation an existing problem, not an ESCP novelty claim. Larger generators/adjudicators differ from the local setup. |
| [When Personalization Misleads / FPPS](https://aclanthology.org/2026.findings-acl.395/), Findings ACL 2026, DOI 10.18653/v1/2026.findings-acl.395 | Direct competing reliability/personalization objective; layer/probe/activation steering is not replicated by evidence-priority prompting. Requires compatible activation access and separate probe development. |
| [LongMemEval](https://arxiv.org/html/2410.10813v2), ICLR 2025 (v7 lineage) | Temporal expansion, indexing and evidence reading are relevant retrieval baselines. The oracle package supplies privileged source IDs; its gain is not a selector comparison. |
| [CoVe](https://aclanthology.org/2024.findings-acl.212/), Findings ACL 2024; [RARR](https://aclanthology.org/2023.acl-long.910/), ACL 2023 | Planned independent verification and evidence-backed revision are prior art. Equal total generation and retrieval budgets, answer preservation and fidelity must be evaluated; a deterministic component checker is not either full method. |

TwinVoice, Persistent Personas?, Wiki-Talkie and Decoupling Logic from Persona retain their v7 status and overlap; no new acceptance or algorithm claim is inferred. The present comparison establishes **functional overlap and a local null contribution**, not universal equivalence or superiority over published systems.

Required differentiation experiment: independently extracted evidence and claims, separate LF/BF panels, full S/F/H coverage, equal candidate/token budgets, total CPU/RAM, strong removal/relevance/BM25/entity-time/component baselines and faithful published implementations where feasible. No current ESCP component has demonstrated an incremental mechanism or Pareto advantage. Originality remains unsupported.
''')
    doc('ESCP_prior_art_kill_test_v1.md','# ESCP prior-art kill test v1\n\n'+META+f'''
Phase P6 / RQ2 and RQ4. The formal candidate remains [ESCP v1](ESCP_candidate_specification_v1.md), including its multi-objective reliability/fidelity/CPU constraints. This update does not rename known rules or add a new algorithm.

| Candidate component | Closest method / simple baseline | New falsification evidence | Remaining gap |
| --- | --- | --- | --- |
| Evidence-state attribution | Zep source-linked graphs; relational joins | Same entity/attribute witnesses and diagnostic outputs | Free-text attribution errors and cost untested |
| Temporal provenance | Zep bi-temporal state; LongMemEval time filtering; interval/as-of predicates | Boundary dates and assertion cutoff handled equally by ordinary rules | No computational distinction established |
| Entity/value conflicts | Mem0 graph/update conflict handling; equality/set cardinality | Forged priority cannot override E; contradictory trusted values remain unresolved in both | No learned conflict advantage |
| Conditional persona admission | FC/PS typed permissions; whitelist/archive/quarantine | Equal admission groups, preserved style/behavior channels | Generated fidelity is unmeasured |
| Answer-component verification | Structured checks, CoVe, RARR | Correct intermediate, false extra claim, promise, abstention and semantic uncertainty distinguished equally | Extraction and model repair not tested |
| Persona preservation | History removal retaining S/F; faithful steering/admission comparators | Removing all persona empties channels; retaining them preserves only metadata | No measured linguistic/behavioral quality benefit |

## Observed Failure Modes

Historical Instruct errors motivate localization; the new oracle answers do not demonstrate persona interference. Original 16 fixtures and timing records remain intact. Sixteen **additional authored** adversarial fixtures test knowledge-as-of cutoffs, historical validity, inclusive endpoints, wrong entity/component, recollection versus answer, mixed correct/false claims, extra unsupported claims, abstention, unknown scope, unknown provenance, duplicate evidence and partial delivery.

## Existing Methods and Published Prior Art

The v8 matrix supplies primary sources and publication status. `tools/escp_kill_test.py` implements a plain relational rule baseline with the **same complete output contract** as ESCP: per-claim labels, support/conflict IDs, required-component states, abstention and task decision. It is neither a second annotator nor a reproduction of the larger published pipelines.

## Potential Algorithmic Improvements

Both implementations match all **16/16** new authored expectations, and their diagnostics are identical. Their admission channels are also identical. Therefore, the current proposed novelty is **not supported**. Do not add complexity without a residual failure beyond this baseline. Equal algorithmic information is privileged typed input, so no free-text capability or actual answer-recovery gain follows.

Both checks scan evidence for each claim: O(number of claims × evidence atoms), plus component matching. Indexing these joins would be a known engineering optimization, not a novel method. Future falsifiable claims must identify a different guarantee, extraction robustness or independently measured tradeoff; equal known rules falsify the present incremental-gain claim.

## Validation Feasibility

Three process-CPU batches of 5,000 × 16 cases: ESCP median **{kill['cpu_cost']['escp']['median']/1000:.3f} microseconds/case**, equal-output rules **{kill['cpu_cost']['equal_output_simple_rules']['median']/1000:.3f} microseconds/case**. Parsing, I/O and generation are excluded. No timing confidence claim or cross-machine speed guarantee is made. Earlier unequal-output timing is preserved, not substituted.

Ablations for entity/time/conflict/delivery remain in the original fixture records; new cases show that ordinary assertion-cutoff and speech-act predicates already cover the proposed extension. Channel retention is a falsification aid, not a measured Persona Fidelity cost. No algorithm inference was executed. Future independent evaluation needs real extraction, full costs, independent fidelity review and disjoint cases. Use no-persona, full-history, history removal, seeded random, relevance/BM25, entity-time and component checking baselines before expensive published adaptations.

## Publication Value

Current level: engineering adaptation and negative algorithm result. No replicated limitation of published methods or original contribution has been established. Preserve this result and prioritize the controlled empirical S/F/H study. PLOS ONE readiness still requires independent scientific evidence, not a renamed algorithm or passing fixtures.
''')
    doc('PersonaSLM_core_SFH_measurement_readiness_v1.md','# Core S/F/H measurement readiness after P5 — v1\n\n'+META+f'''
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

Manifest: `docs/validation/core_sfh_readiness_v1/core_sfh_manifest_proposed_v1.json`; SHA-256 `{validation['manifest_sha256']}`. Same pinned Instruct GGUF/backend/template, CPU4/context4096, seed42/temp0/top-p1,96 output tokens,no retries; order seed716281. All 80 native token arrays match the official tokenizer and reconstruct prompts; range **1626–1849**,16 matched control pairs, no held-out overlap. Vocabulary checks issued no completions.

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
''')
    files=[p.OUT/'measurement_v1/AI_proposals_UNCONFIRMED_v1.csv',p.OUT/'measurement_v1/boundary_alias_sensitivity_v1.json',
           CORE/'core_sfh_manifest_proposed_v1.json',CORE/'candidate_materials_v1.json',CORE/'fidelity_v2/rubric_proposed_v2.json',
           CORE/'consequential_defect_register_v1.csv',Path('docs/PersonaSLM_core_SFH_measurement_readiness_v1.md')]
    bindings={x.as_posix():p.sha(x) for x in files};p.save(CORE/'next_decision_bindings_v1.json',bindings)
    table='\n'.join('| `'+path+'` | `'+h+'` |' for path,h in bindings.items())
    doc('P1d_P5_next_scientific_decision_packet_v1.md','# P1d / P5 consolidated next scientific decision — v1\n\n'+META+f'''
**Completed:** the exactly authorized P5 eight-request diagnostic; no repeat of the earlier eight Instruct outputs and no main-cohort or P6 inference. **Current main P1d decision: NO-GO.** P5's limited answer-delivery criterion is met by AI proposals, not final human ratings.

The [engineering record](P5_oracle_engineering_report_v1.md), [scientific report](P5_oracle_scientific_report_v1.md), [core readiness design](PersonaSLM_core_SFH_measurement_readiness_v1.md) and [ESCP kill test](ESCP_prior_art_kill_test_v1.md) form one review packet. Previous adopted protocols and completed experiment permissions are not reopened.

| Concrete file/version | SHA-256 |
| --- | --- |
{table}

## One consolidated researcher decision

1. **Measurement scope:** accept with documented limitations, correct specified items, or defer the eight P5 AI proposals. Acceptance means researcher-adopted AI assistance, not independent human annotation. Preserve original AMBIGUOUS labels and alias-only sensitivity; native EOS alone does not certify semantic completeness. Prior full-ledger proposals remain AI-only unless explicitly included in adoption; no implicit retroactive adoption.
2. **Next bounded experiment:** authorize the exact **80-request core S/F/H development manifest**, request a specified revision, or defer. Recommended: authorize with its documented diagnostic-control, two-style/shared-F, ancestry, partial GGUF lineage and measurement limitations, after reviewing the linked prospective rubric/materials. This tests true C0–C7 readiness with fixed full evidence, plus the two named diagnostic controls; it is not independent confirmation or an adoption of Instruct as the primary confirmatory model. Model hash `{p.s.MODEL_SHA}`; backend b11573 hash `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; CPU4/context4096/96 tokens/seed42/temp0/top-p1; no retries,60-minute cap. Estimated ~28 minutes, uncertain.
3. **Main P1d / algorithm scope:** retain NO-GO for 1,728 Base + 288 Instruct validation requests and all algorithm generation. No new algorithmic inference is recommended by the equal-output null result. Existing 288-case/64-stratified review remains available; no claim that sampling that form individually confirms every case. A future confirmatory model/core-factorial amendment must separately resolve provenance, independent templates, validated measurements, controls, precision and freezing.

The genuinely mandatory gates come from the researcher's latest instructions: section 10 prohibits the next experiment without separate authorization; sections 11–12 reserve genuine human measurement/material decisions; section 20 requires a consolidated next-step decision. This is not an additional software-enum or routine engineering approval. Approval of item 2 permits only its 80 requests after successful preflight; rejection/deferment preserves all current evidence and permits continued offline work. This packet itself contains **no approval**.

Researcher decision fields: item 1 ______; item 2 ______; corrections/scope ______; researcher ______; supplied decision timestamp ______. Do not invent a timestamp if one is not supplied. The packet SHA and final preservation/test seal are recorded in `validation/p5/oracle_diagnostic_v1/reproducibility_manifest_v1.json`.
''')
    print(json.dumps({'reports':6,'core_manifest_sha256':validation['manifest_sha256'],
        'decision_packet_sha256':p.sha(Path('docs/P1d_P5_next_scientific_decision_packet_v1.md'))}))

if __name__=='__main__':build()
