"""Descriptive P1 measurement analysis, with explicit AI-only provenance."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import statistics
import p1_measurement_run as r
from p1_measurement_scoring import score as v1,agreement,wilson
from p1_measurement_scoring_v2 import score as v2
from p1d_design import csvwrite

METRICS=('factual','temporal','task_success','semantic_completeness','relevance','coherence','linguistic_fidelity','behavioral_fidelity','delivered','supported','stale_adoption')


def metric_stats(rows,key):
    vals=[x.get(key) for x in rows];scored=[v for v in vals if v is not None and v!='Missing' and v!='NOT_APPLICABLE']
    counts=dict(Counter(str(v) for v in scored));n=len(scored)
    numeric=all(isinstance(v,(int,float)) for v in scored) and bool(scored)
    return {'assigned':len(vals),'applicable':sum(v!='NOT_APPLICABLE' for v in vals),'N_A':sum(v=='NOT_APPLICABLE' for v in vals),
        'missing':sum(v=='Missing' for v in vals),'unscored_opportunity_or_abstention':sum(v is None for v in vals),
        'scored':n,'distribution':counts,'numeric_sample_variance':statistics.variance(scored) if numeric and n>1 else None,
        'label_incidence_population_variance':{k:(v/n)*(1-v/n) for k,v in counts.items()} if n else {},
        'largest_category_fraction':max(counts.values())/n if n else None,
        'zero_observable_variation':len(counts)<=1 if n else None,
        'ordinal_floor_fraction':sum(v==1 for v in scored)/n if numeric and key in ('relevance','coherence','linguistic_fidelity','behavioral_fidelity') else None,
        'ordinal_ceiling_fraction':sum(v==5 for v in scored)/n if numeric and key in ('relevance','coherence','linguistic_fidelity','behavioral_fidelity') else None,
        'interpretation':'No observed variation is not a zero treatment effect; inspect scoring coverage, task diversity and opportunity.'}


def analyze(category):
    dest=r.OUT/category/'measurement_v1';evidence=r.s.load(dest/'masked_evidence_v1.json')
    ai=r.s.load(dest/'AI_proposals_UNCONFIRMED_v1.json');key=r.s.load(dest/'protected_condition_mapping_v1.json')
    byid={x['review_id']:x for x in ai};mapping={x['review_id']:x for x in key}
    cases={c['case_id']:c for c in r.s.load(r.OUT/'materials_v1.json')['cases']}
    audit=r.s.load(dest/'execution_integrity_v1.json');native={x['request']['request_id']:x['result'] for x in audit['rows']}
    original=[];aligned=[];revised=[];joined=[];disagreements=[]
    for x in evidence:
        rid=x['review_id'];a=byid[rid];k=mapping[rid];c=cases[k['case_id']]
        r.s.require(a['raw_sha256']==x['raw_sha256'] and a['evaluation_text']==x['raw_output'],'AI text binding mismatch')
        r.s.require(a['researcher_decision']=='' and a['human_timestamp'] is None,'Fabricated confirmation')
        p=v1(x['first_reply_candidate'],c,x['original_structural_status']['unit_identifiable'])
        q=v1(x['raw_output'],c,a['boundary_identifiable_proposal']);z=v2(x['raw_output'],c,a['boundary_identifiable_proposal'])
        original.append({'review_id':rid,**p});aligned.append({'review_id':rid,**q});revised.append({'review_id':rid,**z})
        joined.append({**a,**k,'speaker_id':c['speaker_id'],'family':c['family'],'burden_rows':c['burden_rows'],
            'construction_ancestor':c['construction_ancestor'],'date_type':c['date_type'],
            'original_structural_status':x['original_structural_status']['status'],'native_stop':x['native_stop'],
            'empty':not bool(x['raw_output'].strip()),'latency_seconds':native[k['request_id']]['latency_seconds']})
        for metric in METRICS:
            if z.get(metric)!=a.get(metric):disagreements.append({'review_id':rid,'metric':metric,'automatic_v2':z.get(metric),
                'AI':a.get(metric),'raw_output':x['raw_output'],'AI_reason':a['claim_and_task_reason'],
                'automatic_trace':z.get('evidence'),'human_decision':'','human_timestamp':None})
    tables={'automatic_v1_original_boundary':original,'automatic_v1_review_text':aligned,'automatic_v2_review_text':revised,
            'joined_AI_proposals':joined,'disagreements':disagreements}
    for name,data in tables.items():r.s.save(dest/(name+'_v1.json'),data)
    csvwrite(dest/'consequential_disagreements_v1.csv',disagreements)
    metric={k:metric_stats(ai,k) for k in METRICS}
    comparisons={name:{k:agreement([x.get(k) for x in data],[x.get(k) for x in ai]) for k in METRICS}
                 for name,data in [('v1_original_boundary',original),('v1_review_text',aligned),('v2_review_text',revised)]}
    byfamily={f:{'n':len(xs:=[x for x in joined if x['family']==f]),'success':sum(x['task_success']=='Success' for x in xs),
                 'complete':sum(x['semantic_completeness']=='YES' for x in xs),'supported':sum(x['supported'] for x in xs),
                 'required':sum(x['required'] for x in xs)} for f in sorted({x['family'] for x in joined})}
    events=r.s.b.read_events(Path(audit['run_directory']))
    memory=[x['data']['process'].get('working_set',0) for x in events if x['kind']=='memory_observation' and x['data'].get('process')]
    successes=sum(x['task_success']=='Success' for x in ai)
    summary={'category':category,'phase':'P1','annotation_status':'AI_ASSISTED_UNCONFIRMED','human_ratings':0,'attempts':audit['attempted'],
        'successful_requests':audit['results'],'failed_requests':audit['attempted']-audit['results'],'retries':0,
        'task_success':successes,'n':len(ai),'task_success_rate':successes/len(ai),'Wilson_95_descriptive_iid_approximation':wilson(successes,len(ai)),
        'uncertainty_limit':'Synthetic shared templates violate a simple population-iid interpretation. This interval is descriptive, not guaranteed population coverage.',
        'delivered':sum(x['delivered'] for x in ai),'supported':sum(x['supported'] for x in ai),'required':sum(x['required'] for x in ai),
        'semantic_complete':sum(x['semantic_completeness']=='YES' for x in ai),'identifiable_AI_proposed':sum(x['boundary_identifiable_proposal'] for x in ai),
        'original_structural':dict(Counter(x['original_structural_status'] for x in joined)),
        'native_stops':dict(Counter(x['native_stop'] for x in joined)),'empty':sum(x['empty'] for x in joined),
        'mean_latency_seconds':statistics.mean(x['latency_seconds'] for x in joined),
        'total_output_tokens':sum(x['generated_tokens'] for x in native.values()),'peak_working_set_observed':max(memory) if memory else None,
        'metrics':metric,'agreement':comparisons,'task_families':byfamily,
        'FC_task_label_concordance':sum((x['factual']=='Correct')==(x['task_success']=='Success') for x in ai)/len(ai),
        'RR_CC_exact_concordance':sum(x['relevance']==x['coherence'] for x in ai)/len(ai),
        'source_hashes':{str(p):r.s.sha256(p) for p in (dest/'masked_evidence_v1.json',dest/'AI_proposals_UNCONFIRMED_v1.json',dest/'execution_integrity_v1.json',Path('tools/p1_measurement_scoring.py'),Path('tools/p1_measurement_scoring_v2.py'))}}
    if category=='C_DIAGNOSTIC':
        arms={}
        for arm in ('concise','date_slots'):
            xs=[x for x in joined if x['diagnostic_arm']==arm]
            families={f:sum(x['task_success']=='Success' for x in xs if x['family']==f) for f in byfamily}
            complete=sum(x['semantic_completeness']=='YES' for x in xs)
            arms[arm]={'n':len(xs),'success':sum(x['task_success']=='Success' for x in xs),'complete':complete,
                'family_success':families,'qualified':complete>=7 and all(x['boundary_identifiable_proposal'] for x in xs) and all(n>=1 for n in families.values())}
        summary['arms']=arms
        summary['selected_arm']=next((arm for arm in ('concise','date_slots') if arms[arm]['qualified']),None)
    r.s.save(dest/'summary_v1.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('metrics','agreement','source_hashes')},indent=2))
    return summary


def report_A(summary):
    dest=r.OUT/'A_C0'/'measurement_v1';plan=r.s.load(r.OUT/'A_C0_manifest_v1.json');audit=r.s.load(dest/'execution_integrity_v1.json')
    metrics=summary['metrics'];agree=summary['agreement']['v2_review_text']
    lines=['# P1 C0 difficulty calibration — consolidated milestone v1','',
        'Maintainer: Yaxin ZHENG. Phase: P1 measurement development only. All semantic judgments are AI-assisted proposals; zero researcher confirmations and zero independent human ratings.',
        '', '## Research purpose and prospective design', '',
        'Establish true C0 difficulty, answer measurement coverage and evaluator limitations before the core S/F/H pilot. Thirty-two distinct synthetic development speakers/cases cross four task families, four ledger sizes (8/12/16/20 rows) and two replications. C0 contains no S/F/H optional blocks. It is not the previous H_none condition. The eight-case factorial pool was fixed before these outputs and has disjoint speakers, questions, answer-code inventory and evidence records. The pools share four construction ancestors and two style specifications; names are not evidence of independent linguistic populations.',
        '', 'No cases were removed to reach the provisional 80–95% target. The target was not a hard gate. All 32 cases remain; v1.1 and the adopted P1d E/V addendum remain unchanged, while v1.2 remains proposed. This P1 development bank does not replace or freeze the formal P1d bank.',
        '', '## Engineering evidence', '',
        f"Manifest: `docs/validation/p1/measurement_pilot_v1/A_C0_manifest_v1.json`, SHA-256 `{r.s.sha256(r.OUT/'A_C0_manifest_v1.json')}`.",
        f"Raw run: `{audit['run_directory']}`. {summary['attempts']} attempts, {summary['successful_requests']} successful, {summary['failed_requests']} failed, zero retries. Native stops: {summary['native_stops']}; output tokens: {summary['total_output_tokens']}; mean latency {summary['mean_latency_seconds']:.3f} seconds; observed peak process working set {summary['peak_working_set_observed']} bytes. These are observations, not independent hardware benchmarks.",
        f"Model `{plan['model']['model_file']}` SHA-256 `{plan['model']['model_sha256']}`; backend b11573 SHA-256 `{plan['model']['backend_sha256']}`. CPU only, four threads, context 4096, seed42, temperature0, top-p1,96 output tokens, no custom stops/cache/warmup/retries. Official nonthinking template SHA-256 `{plan['template_sha256']}`. Partial third-party conversion lineage remains a development-only limitation.",
        'All native input arrays matched the official tokenizer and the live server. Actual input range: 553–1251 tokens. Full prompts, token IDs, native outputs, base64 HTTP bodies, source snapshots, effective server properties, memory observations, errors and hashes remain in the journal. Available RAM passed the unchanged 3 GiB preflight. No external process was stopped.',
        '', '## Scientific observations', '',
        f"AI-proposed task success: **{summary['task_success']}/{summary['n']} ({100*summary['task_success_rate']:.2f}%)**. Descriptive Wilson95% interval: [{100*summary['Wilson_95_descriptive_iid_approximation'][0]:.2f}%, {100*summary['Wilson_95_descriptive_iid_approximation'][1]:.2f}%]. This iid approximation does not guarantee population coverage for shared synthetic templates.",
        f"Complete requested-answer forms: {summary['semantic_complete']}/32; delivered components: {summary['delivered']}/{summary['required']}; supported components: {summary['supported']}/{summary['required']}. An explicit but false unavailability answer is treated as delivered answer content, not supported content (AM004/AM031); the opposite completeness interpretation is retained for human review. AM017 contains a supported March assertion and a conflicting March assertion; its supported component is not successful final delivery.",
        f"Original parser statuses remain {summary['original_structural']}. All 32 first-response candidates are AI-proposed identifiable. Attribute headings triggered parser ambiguity; EOS alias incompatibility and semantic certification are distinct. The 11 budget-ended continuations must not be automatically marked factually wrong or incomplete. No original label or raw text was changed.",
        '', '| Task family | Success | Complete form | Supported components |','| --- | ---: | ---: | ---: |']
    for f,v in summary['task_families'].items():lines.append(f"| {f} | {v['success']}/{v['n']} | {v['complete']}/{v['n']} | {v['supported']}/{v['required']} |")
    lines+=['', 'The dated-comparison family has a task-success floor (0/8). Errors include expired or not-yet-valid values, reversed date assignments, a wrong entity, false unavailability and incomplete explanations. This is a measurement/model adequacy concern, not a persona effect; C0 has no persona treatment.',
        '', '## Metric discrimination and evaluator audit', '', '| Metric | AI distribution | Scored | Numeric variance | Auto v2 / AI agreement |','| --- | --- | ---: | ---: | --- |']
    for k in METRICS:
        x=metrics[k];a=agree[k];lines.append(f"| {k} | {json.dumps(x['distribution'])} | {x['scored']} | {x['numeric_sample_variance']} | {a['agreement']}/{a['paired_comparable']} |")
    lines+=['', f"FC Correct and task Success coincide item by item in this observed calibration ({summary['FC_task_label_concordance']:.0%}); separate human-readable construct judgments and authored counterexamples are retained. Complete wrong answers occur, so completeness and correctness discriminate. RR/CC exact concordance is {summary['RR_CC_exact_concordance']:.2%}; their ceiling concentration limits resolution. LF is narrow, AI-proposed and not independently validated; BF has no answer/acknowledgment ordering opportunity and therefore no scores, not zero fidelity.",
        'The frozen v1 automatic scorer had shared FC/TC assignment in its restricted grammar and missed explicitly labeled code syntax. Its source and every score remain preserved. Version2 separates temporal scope and recognizes declared type labels without changing any output. Both versions are compared on the identical AI-proposed evaluation spans; a separate v1 original-parser view exposes extraction dependency. Shared reference answers and shared proposed spans mean this is system agreement, not independent evaluation accuracy. Prose/date attachment still requires semantic review. AM020/AM024 retain temporal Unverifiable due to entity/time attribution uncertainty.',
        '', '## Decision and next bounded diagnostic', '',
        'Do not start the 80-request pilot yet. A single 16-request category-C diagnostic is prospectively registered on calibration indices00–07, with unchanged evidence/question/references: concise output and date-slot output instruction packages. No pilot cases are selected or removed. Selection rules are fixed before diagnostic outputs; if neither arm qualifies, preserve NO-GO rather than optimize until an accuracy target is reached.',
        '', '## P5 closeout and research tree', '',
        'P5 engineering is completed: the existing eight oracle outputs are not rerun. Existing AI task proposals remain 2/8 historical Instruct versus8/8 oracle, unconfirmed. Full/reduced evidence were both sufficient; content, length, position, salience and literal answer exposure changed. No pure retrieval, sufficiency or Persona effect is identified. The existing eight-item paired comparison and semantic evidence package are reused for researcher review; no new P5 inference or algorithm work occurs.',
        'P0 PASS/frozen; P1 ACTIVE; P2/P3/P4 PAUSED; P5 diagnostic completed with semantic confirmation outstanding; P6 PAUSED. The negative ESCP result is preserved; no new algorithm is developed. The central S/F/H question, separate reliability/fidelity dimensions and future constrained P6 objective remain recorded.',
        '', '## Limitations and reproduction', '',
        'Evidence source numbering and B-versus-D value prefixes can reveal target/distractor structure; only four shared administrative-task ancestors exist. Burden changes jointly with generated record content, so a pure context-length effect is not identified. These materials are development-only and unsuitable for independent validation claims. Future independent work needs independently authored/counterbalanced templates, target-value coding, requested-date balance, independent metric-specific annotation and precision planning with speaker/template dependencies.',
        'Reproduce without inference: `.venv/Scripts/python.exe tools/p1_measurement_run.py audit --category A_C0 --output <new-workspace-path.json>`. The generation command was `.venv/Scripts/python.exe tools/p1_measurement_run.py run --category A_C0 --preflight docs/validation/p1/measurement_pilot_v1/A_C0_preflight_v1.json`; replay is prohibited because the32-request allocation is spent. Scores, witnesses, alternatives and blank human fields are in `docs/validation/p1/measurement_pilot_v1/A_C0/measurement_v1/`. Targeted tests:38 passed after scoring independence and syntax corrections;39 passed after adding the category-C scientific-invariance check. Earlier failures are preserved in the final development record.', '']
    path=Path('docs/P1_C0_measurement_calibration_report_v1.md')
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('category',choices=['A_C0','C_DIAGNOSTIC']);a=p.parse_args()
    result=analyze(a.category)
    if a.category=='A_C0':report_A(result)
