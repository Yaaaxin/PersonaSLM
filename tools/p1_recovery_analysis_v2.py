"""Deterministic descriptive O/Q summaries; no human-label gate bypass."""
from collections import Counter
import csv
import json
from pathlib import Path
from statistics import mean, median, pvariance
import p1_recovery_v2 as r
import p1_recovery_gate_v2 as gate

s,d,OUT=r.s,r.d,r.OUT
METRICS={'task_success':('automatic_score','ai_assisted_label'),
         'factual':('automatic_factual','AI_factual'),
         'temporal':('automatic_temporal','AI_temporal'),
         'semantic_completeness':('automatic_completeness','AI_completeness')}


def read_rows():
    with (OUT/'consolidated_researcher_review_v2.csv').open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def agreement(rows,a,b):
    comparable=[x for x in rows if x[a] not in ('',None) and x[b] not in ('',None)]
    return {'agreement':sum(x[a]==x[b] for x in comparable),'denominator':len(comparable),
        'uncovered':len(rows)-len(comparable),
        'confusion_automatic_to_AI':dict(Counter(x[a]+' -> '+x[b] for x in comparable)),
        'disagreements':[{'case_id':x['case_id'],'condition':x['condition'],'automatic':x[a],'AI':x[b]} for x in comparable if x[a]!=x[b]]}


def summarize(rows):
    out={'n':len(rows),'audited_task_success':None,'researcher_confirmed':0,
         'AI_success':sum(x['ai_assisted_label']=='Success' for x in rows),
         'automatic_success':sum(x['automatic_score']=='Success' for x in rows),
         'task_agreement':agreement(rows,'automatic_score','ai_assisted_label'),
         'distributions':{k:dict(Counter(x[k] or 'NOT_SCORED' for x in rows)) for k in
             ('ai_assisted_label','AI_factual','AI_temporal','AI_completeness','AI_relevance','AI_coherence','original_structural_status','native_stop')},
         'components':{k:sum(int(x[k]) for x in rows) for k in ('required_components','AI_delivered_components','AI_supported_components')},
         'latency_seconds':{'mean':mean(float(x['latency_seconds']) for x in rows),'median':median(float(x['latency_seconds']) for x in rows),
             'min':min(float(x['latency_seconds']) for x in rows),'max':max(float(x['latency_seconds']) for x in rows)}}
    out['metric_agreement']={metric:agreement(rows,*cols) for metric,cols in METRICS.items()}
    out['ordinal_variance']={k:{'n':len(rows),'population_descriptive_variance':pvariance(float(x[k]) for x in rows),
        'score5_count':sum(x[k]=='5' for x in rows)} for k in ('AI_relevance','AI_coherence')}
    out['failure_tags']=dict(Counter(tag for x in rows for tag in json.loads(x['proposed_failure_type'])))
    out['missing_records']=sum(x['record_state']=='NOT_GENERATED' for x in rows)
    out['empty_outputs']=sum(not x['model_output'].strip() for x in rows)
    return out


def analyze():
    rows=read_rows();panel=[x for x in rows if x['condition'] in ('D0','D1','D2','D3')]
    s.require(len(rows)==56 and len(panel)==32 and len({x['request_id'] for x in rows})==56,'Review inventory')
    s.require(all(not x[k] for x in rows for k in x if k.startswith('researcher_')),'Unexpected human decisions: do not treat as AI source')
    by={c:[x for x in panel if x['condition']==c] for c in ('D0','D1','D2','D3')}
    s.require(all(len(v)==8 for v in by.values()),'Paired denominator')
    out={'scope':'AI-assisted descriptive feasibility observations, not audited gate decisions or Persona effects',
         'conditions':{c:summarize(v) for c,v in by.items()},
         'family':{fam:{c:summarize([x for x in v if x['task_family']==fam]) for c,v in by.items()} for fam in sorted({x['task_family'] for x in panel})},
         'panel':summarize(panel),
         'original32':summarize([x for x in rows if x['condition'] in ('D0','C0_AUDIT_ONLY')]),
         'decision':gate.decide(panel),'case_pairs':[],
         'paired_O_descriptions':{},
         'Q_comparison':'Q0 and Q1 have different component/task estimands. No common competence effect is estimated.',
         'fidelity':{'linguistic':None,'behavioral':None,'state':'NOT_MEASURABLE','zero_imputation':False},
         'identification':'8 paired selected development cases, two per family; shared construction and lexical ancestry. D0 is archived, not contemporaneously randomized. No population interval or significance test.'}
    for cid in sorted({x['case_id'] for x in panel}):
        items={x['condition']:x for x in panel if x['case_id']==cid}
        out['case_pairs'].append({'case_id':cid,'task_family':items['D0']['task_family'],
            'conditions':{c:{k:x[k] for k in ('ai_assisted_label','automatic_score','AI_completeness','AI_factual','AI_temporal','AI_supported_components','required_components','request_id')} for c,x in items.items()}})
    for name,a,b in [('O_with_Q0','D0','D1'),('O_with_Q1','D2','D3')]:
        diffs=[int(p['conditions'][b]['ai_assisted_label']=='Success')-int(p['conditions'][a]['ai_assisted_label']=='Success') for p in out['case_pairs']]
        out['paired_O_descriptions'][name]={'AI_case_differences':diffs,'mean_difference':mean(diffs),
            'improved':diffs.count(1),'worsened':diffs.count(-1),'unchanged':diffs.count(0),
            'scope':'Unconfirmed descriptive paired package comparison; no causal mechanism or population inference.'}
    aud=s.load(OUT/'execution_integrity_v2.json');run=Path(aud['run_directory']);events=s.b.read_events(run)
    mem=[e['data'] for e in events if e['kind']=='memory_observation'];results=[x['result'] for x in aud['rows']]
    out['engineering']={'attempted':aud['attempted'],'results':aud['results'],'failures':aud['attempted']-aud['results'],
        'stops':dict(Counter(x['stop_reason'] for x in results)),'structural':dict(Counter(x['response_status']['status'] for x in results)),
        'output_tokens':dict(Counter(x['generated_tokens'] for x in results)),
        'native_returned_token_difference':dict(Counter(x['native_minus_returned_tokens'] for x in results)),
        'latency_seconds':{'sum':sum(x['latency_seconds'] for x in results),'mean':mean(x['latency_seconds'] for x in results)},
        'memory':{'samples':len(mem),'minimum_available_physical':min(x['system']['available_physical'] for x in mem),
            'max_sampled_working_set':max(x['process']['working_set'] for x in mem),
            'reported_peak_working_set':max(x['process']['peak_working_set'] for x in mem),
            'scope':'Existing 3 GiB gate is pre-load available RAM, not a continuous post-load reserve. Runtime samples are reported without changing the threshold. Whole-machine/OS measurements are not isolated causal costs.'},
        'run_directory':run.as_posix(),'live_prompt_checks':sum(e['kind']=='live_prompt_verified' for e in events)}
    fresh={x['request_id']:x for x in s.load(OUT/'AI_proposals_UNCONFIRMED_v2.json')}
    out['D0_reinspection_differences']=[]
    for x in by['D0']:
        for key,col in [('task_success','ai_assisted_label'),('factual','AI_factual'),('temporal','AI_temporal'),('semantic_completeness','AI_completeness'),('relevance','AI_relevance'),('coherence','AI_coherence'),('delivered','AI_delivered_components'),('supported','AI_supported_components')]:
            if str(fresh[x['request_id']][key])!=x[col]:
                out['D0_reinspection_differences'].append({'case_id':x['case_id'],'metric':key,'retained_original':x[col],
                    'fresh_AI_reinspection':fresh[x['request_id']][key],'status':'Not adopted; original source retained'})
    s.save(OUT/'descriptive_analysis_UNCONFIRMED_v2.json',out)
    s.save(OUT/'authorization_ledger_v2.json',r.old.cumulative()|{'recorded_utc':s.b.utc_now(),
        'current_scope_attempts':24,'fallback_attempts':0,'pilot_attempts':0,
        'restrictions':'No allocation transfer; remaining8 diagnostic only conditionally activated after negative audited O/Q gate. B80 requires separate pilot authorization.'})
    return out


if __name__=='__main__':
    x=analyze()
    print(json.dumps({'conditions':{k:{j:v[j] for j in ('AI_success','automatic_success','task_agreement','components','distributions')} for k,v in x['conditions'].items()},'engineering':x['engineering'],'D0_reinspection_differences':x['D0_reinspection_differences']},indent=2))
