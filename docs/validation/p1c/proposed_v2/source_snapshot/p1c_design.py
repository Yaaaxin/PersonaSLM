"""Prospective P1c stimulus/reference and planning validation; never generates text."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import subprocess

ROOT=Path.cwd()
LOCAL=Path('results/p1c_design/v1')
PUBLIC=Path('docs/validation/p1c/proposed_v1')
DATA=Path('data/synthetic/p1c_development_proposed_v1.json')
VERSION='p1c_auxiliary_history_proposed_v1'
TEMPLATE='p1c_evidence_first_transcript_proposed_v1'
CONDITIONS={'R0T0':{'R':0,'T':0},'R0T1':{'R':0,'T':1},'R1T0':{'R':1,'T':0},'R1T1':{'R':1,'T':1},'N_history':{'R':None,'T':None},'H_none':{'R':None,'T':None}}

def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def text_hash(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def canonical(x):return text_hash(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')))
def write_json(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n')
def write_csv(p,rows):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
        w.writerows({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
def require(x,msg):
    if not x:raise ValueError(msg)

def baseline():
    require(not (LOCAL/'baseline.json').exists(),'Baseline already exists')
    files=[p for p in subprocess.check_output(['git','ls-files','-z'],text=True).split('\0') if p]
    historical={}
    for source,key in [('results/p1b_execution/v1/baseline.json','historical_local_files'),
                       ('docs/validation/p1b/calibration_v1/analysis_v1/execution_inventory_v1.json','run_artifact_hashes')]:
        historical.update(read(source)[key])
    result={'recorded_utc':now(),'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_status':subprocess.check_output(['git','status','--short'],text=True),
            'files':{p:sha(p) for p in files},'historical_artifacts':historical}
    write_json(LOCAL/'baseline.json',result)
    for name in ['docs/research_development_log.md','docs/related_work_novelty_matrix.md']:
        with (LOCAL/(Path(name).name+'.before')).open('xb') as f:f.write(Path(name).read_bytes())
    return {'repository_files':len(files),'historical_files':len(historical),'git':result['git_sha']}

def history_evidence():
    folder=Path('docs/validation/p1b/confirmed_analysis_v1');output=folder/'analysis_v1'
    reg=read(folder/'registration_v1.json');man=read(output/'analysis_reproducibility_manifest_v1.json')
    require(sha(reg['final_annotation']['path'])==reg['final_annotation']['sha256'],'Registered labels changed')
    for path,h in reg['sources'].items():require(sha(path)==h,'Review source changed: '+path)
    for name,h in man['files'].items():require(sha(output/name)==h,'Prior analysis changed: '+name)
    rows=read(output/'unblinded_analysis_dataset_v1.json')['rows'];old=read(output/'analysis_v1.json')
    spec=read(folder/'factorial_specification_v2.json');cells=defaultdict(dict)
    for r in rows:cells[r['case_id']][r['condition']]=r
    checked=[]
    for metric in ('factual_correct_label','temporal_correct_label','task_success','factual_assessable_binary','temporal_assessable_binary'):
        for contrast in ('C1-C0','C3-C0','H','SxH'):
            weights=spec['weights'][contrast];points=[]
            for cid,block in sorted(cells.items()):
                vals={}
                for cond,r in block.items():
                    if metric.startswith('temporal') and r['applicable_temporal_consistency']!='true':v=None
                    elif metric=='task_success':
                        n,d=map(int,r['confirmed_component_coverage'].split('/'))
                        v=float(r['confirmed_factual_consistency']=='Correct' and r['confirmed_answer_delivery']=='FULL_ANSWER' and n==d)
                    else:
                        axis='temporal_consistency' if metric.startswith('temporal') else 'factual_consistency'
                        label=r['confirmed_'+axis]
                        v=None if metric.endswith('binary') and label=='Unverifiable' else float(label=='Correct')
                    vals[cond]=v
                eligible=not metric.startswith('temporal') or block['C0']['applicable_temporal_consistency']=='true'
                terms=[cond for cond,w in weights.items() if w]
                d=sum(weights[c]*vals[c] for c in terms) if eligible and all(vals[c] is not None for c in terms) else None
                original=next(p for p in old['case_contrasts'] if p['policy']=='confirmed_span_sensitivity' and p['metric']==metric and p['contrast']==contrast and p['case_id']==cid)
                require(d==original['difference'],'Independent case contrast differs')
                points.append({'case_id':cid,'persona_id':block['C0']['persona_id'],'eligible':eligible,'difference':d})
            values=[p['difference'] for p in points if p['difference'] is not None]
            summary=next(p for p in old['effect_summary'] if p['policy']=='confirmed_span_sensitivity' and p['metric']==metric and p['contrast']==contrast and p['family']=='ALL')
            require(abs(statistics.mean(values)-summary['estimate'])<1e-12,'Effect differs')
            checked.append({'metric':metric,'contrast':contrast,'estimate':statistics.mean(values),
                'evaluable_cases':len(values),'eligible_cases':sum(p['eligible'] for p in points),
                'all_eligible_bounds':[summary['unknown_lower'],summary['unknown_upper']],
                'cluster_interval':[summary['lower'],summary['upper']],'case_values':points})
    inv=read('docs/validation/p1b/calibration_v1/analysis_v1/execution_inventory_v1.json')
    # Locate actual completed result event files from the pinned inventory.
    latencies=[]
    for p in inv['run_artifact_hashes']:
        if '/events/' in p and p.endswith('.json'):
            e=read(p)
            if e['kind']=='p1b_result':
                datum=e['data'];latencies.append(datum['latency_seconds'])
    require(len(latencies)==192,'Native latency inventory differs')
    return {'version':'p1c_p1b_evidence_recheck_v1','annotation_sha256':reg['final_annotation']['sha256'],
        'prior_manifest_sha256':sha(output/'analysis_reproducibility_manifest_v1.json'),
        'cases':len(cells),'speakers':len({r['persona_id'] for r in rows}),'recomputed_case_contrasts':len(checked)*24,
        'contrasts':checked,'runtime':{'requests':192,'total_response_seconds':sum(latencies),
                                    'mean_response_seconds':statistics.mean(latencies)},
        'interpretation':'Development package effects, not causal history mechanisms; observed Correct label is not assessed-only accuracy.'}

PERIODS=[('2042-01-01','2042-04-30'),('2042-05-01','2042-08-31'),('2042-09-01','2042-12-31')]
QUESTIONS=['What does this archived entry say?', 'What does the dated entry in the archive say?',
           'Can you read the dated entry from the archive?', 'What information is written in this archived entry?']
REPLIES=['The record lists my {predicate} as {value} for {start} through {end}.',
         'My {predicate} is recorded as {value} for the interval from {start} through {end}.',
         'For the interval from {start} through {end}, the entry records {value} as my {predicate}.',
         'The dated entry records {value} as my {predicate} from {start} through {end}, inclusive.']
NEUTRAL=[
    'This entry keeps the question beside the reply, preserving both parts of the exchange in their original order.',
    'The archive retains the question and its reply together in this entry, so the exchange can be read as a whole.',
    'This entry keeps the question beside its reply in the archive, with both parts recorded together and neither part separated from the exchange.',
    'The question appears first in this archive entry, followed by its reply. The two parts are kept together as the record of the exchange.',
    'The archive entry consists of a question followed by a reply. Both parts remain together in the record, and their order is retained for reading.',
    'This archive entry contains the question and the reply in the order in which they appear here. The record keeps the exchange together as a single item.',
    'Both parts of this exchange are kept in the archive entry. The question is followed by the reply, with the order retained and the entry kept as one item.',
    'The record places this question before its reply. Both are retained together in the archive entry, which preserves the exchange as one item rather than separating its two parts.']

def active_fact(case,R,T):
    predicate='parcel label' if R else 'music label'
    period=case['target_period'] if T else 0
    return next(f for f in case['facts'] if f['entity']==case['speaker_name'] and f['predicate']==predicate and f['period']==period)

def history_candidates(case,condition):
    if condition=='H_none':return [{'variant_id':0,'question_variant':None,'text':'','fact_id':None}]
    out=[]
    for qi,q in enumerate(QUESTIONS):
        for ri,reply in enumerate(NEUTRAL if condition=='N_history' else REPLIES):
            fact=None
            if condition!='N_history':
                fact=active_fact(case,**CONDITIONS[condition]);reply=reply.format(**fact)
            text=f"[Archive recorded 2042-12-01]\nArchivist: {q}\n{case['speaker_name']}: {reply}"
            out.append({'variant_id':len(out),'question_variant':qi,'text':text,'fact_id':fact['fact_id'] if fact else None})
    return out

def render(case,history):
    prefix=(f"Fictional dialogue. Evaluation reference date: {case['evaluation_date']}.\n"
            f"Target speaker: {case['speaker_name']} ({case['persona_id']}).\n"
            "Use the trusted scheduled records for the date named in the question. Validity endpoints are inclusive.\n"
            "TRUSTED EVIDENCE:\n"+case['trusted_evidence']+"\n\nADDITIONAL ARCHIVED DIALOGUE:\n")
    suffix='\n\nRECENT CONVERSATION:\n'+case['fixed_context']+'\nUser: '+case['question']+'\nAssistant:'
    return prefix+history+suffix

def ground_truth(case,facts=None):
    facts=case['facts'] if facts is None else facts
    def get(predicate,entity=case['speaker_name'],timeless=False):
        candidates=[f for f in facts if f['entity']==entity and f['predicate']==predicate and
                    (timeless or f['start']<=case['requested_date']<=f['end'])]
        require(len(candidates)==1,'Missing or nonunique supporting fact: '+predicate)
        return candidates[0]
    used=[]
    if case['family']=='route_integration':
        route=get('parcel route');room=get('destination room',route['value'],True)
        used=[route,room];answer=[room['value']]
    else:
        used=[get('collection desk')]
        if case['family']=='multiple_components':used.append(get('service day'))
        answer=[f['value'] for f in used]
    return {'components':answer,'fact_ids':[f['fact_id'] for f in used],
            'derivation':'Select target entity and inclusive requested-date interval'+(' then follow the route-to-room relation.' if case['family']=='route_integration' else '; return every requested field.')}

def build_cases():
    names=['Auden Vale','Celia North','Elian Moss','Greta Sable','Idris Fern','Nora Finch']
    families=['single_retrieval','multiple_components','route_integration']
    places=['Cobalt','Laurel','Harbor','Maple','Orchid','Silver']
    days=['Tuesday','Thursday','Saturday']
    cases=[]
    for i,name in enumerate(names):
        family=families[i//2];pid=f'p1c_speaker_{i+1:02d}'
        facts=[]
        def add(entity,predicate,value,k):
            start,end=PERIODS[k]
            facts.append({'fact_id':f'{pid}_f{len(facts)+1:02d}','entity':entity,'predicate':predicate,
                'value':value,'period':k,'start':start,'end':end})
        for k in range(3):
            if family=='route_integration':add(name,'parcel route',f'route {i+1}{k+1}',k)
            else:add(name,'collection desk',places[(i+k)%len(places)],k)
            if family=='multiple_components':add(name,'service day',days[(i+k)%3],k)
            add(name,'parcel label',['blue','green','red'][(i+k)%3],k)
            add(name,'music label',['green','red','blue'][(i+k)%3],k)
        if family=='route_integration':
            for k in range(3):
                facts.append({'fact_id':f'{pid}_f{len(facts)+1:02d}','entity':f'route {i+1}{k+1}',
                    'predicate':'destination room','value':places[(i+k)%len(places)],'period':None,
                    'start':'2042-01-01','end':'2042-12-31'})
        # A foil entity is explicit and equally visible in every arm. Not claimed as hard ambiguity.
        for k in range(3):add('Archive colleague '+str(i+1),'collection desk',places[(i+k+2)%len(places)],k)
        evidence='\n'.join(f"[{f['fact_id']}] {f['entity']}: {f['predicate']} = {f['value']}; valid {f['start']} through {f['end']}." for f in facts)
        for period,mode in [(1,'historical'),(2,'current')]:
            requested='2042-06-15' if mode=='historical' else '2042-12-15'
            target={'single_retrieval':'collection desk','multiple_components':'collection desk and service day','route_integration':'destination room for parcel collection'}[family]
            if i%2:q=f'For {requested}, what is {name}\'s assigned {target}?'
            else:q=f'Using the schedule for {requested}, give the {target} assigned to {name}.'
            case={'case_id':f'p1c_{i+1:02d}_{mode}','persona_id':pid,'speaker_name':name,'family':family,
                'question_template_id':f'{family}_wording_{i%2+1}','query_mode':mode,'target_period':period,
                'requested_date':requested,'evaluation_date':'2042-12-15','question':q,
                'fixed_context':'User: I have the dated schedule ready.\nAssistant: Which assignment would you like to check?',
                'facts':facts,'trusted_evidence':evidence,'prompt_template_version':TEMPLATE,
                'applicability':{k:True for k in ['response_relevance','factual_consistency','temporal_consistency','conversational_coherence',
                    'task_success','component_coverage','semantic_completeness','structural_status']},
                'persona_fidelity_applicability':False,'researcher_approval':'',
                'scope':'Synthetic prospective development; no outcome-based item selection; no confirmatory use.'}
            case['reference']=ground_truth(case);cases.append(case)
    return {'version':VERSION,'status':'PROPOSED_RESEARCHER_REVIEW_OPEN','language':'English','cases':cases,
        'allocation':{'speakers':6,'cases':12,'cases_per_speaker':2,'families':3,'conditions_per_case':6,'proposed_generations':72},
        'factors':'S=F=0. R is topical relation of auxiliary non-answer facts. T is validity at requested date, not truth.',
        'selection_rule':'All six fictional speakers, both requested-date strata, all three families; fixed before any responses.',
        'candidate_rule':{'active_variants_per_cell':16,'neutral_variants':32,'active_same_variant_required':True,
            'shared_archivist_question_required':True,'token_tolerance':0,
            'selection':'First active variant with equal native full-prompt lengths and a same-question neutral match. No expansion after observed counts; failures preserved.'},
        'generation_authorized':False,'confirmatory_material_created':False}

def validate_cases(data):
    cases=data['cases'];require(len(cases)==12 and len({c['case_id'] for c in cases})==12,'Case identity failure')
    old=read('data/synthetic/p1b_development_proposed_v2.json')['cases']
    require(not ({c['case_id'] for c in cases}&{c['case_id'] for c in old}),'Historical case reused')
    checks=[]
    for c in cases:
        require(ground_truth(c)==c['reference'],'Reference answer mismatch')
        require(not c['researcher_approval'],'Human approval must stay blank')
        require(c['requested_date'] in c['question'] and c['evaluation_date'] in render(c,''),'Reference dates missing')
        for f in c['facts']:
            date.fromisoformat(f['start']);date.fromisoformat(f['end']);require(f['start']<=f['end'],'Invalid interval')
        require(c['reference']['components']!=ground_truth({**c,'requested_date':'2042-02-01'})['components'],'Old-value shortcut')
        if c['query_mode']=='historical':
            require(c['reference']['components']!=ground_truth({**c,'requested_date':'2042-12-15'})['components'],'Newest-value shortcut')
        # Removing any needed fact destroys uniqueness/answerability: validation only, never a treatment.
        for needed in c['reference']['fact_ids']:
            try:ground_truth(c,[f for f in c['facts'] if f['fact_id']!=needed])
            except ValueError:pass
            else:raise ValueError('Claimed needed fact is not needed')
        for condition,factors in CONDITIONS.items():
            candidates=history_candidates(c,condition)
            for v in candidates:
                require(not any(answer.lower() in v['text'].lower() for answer in c['reference']['components']),'Answer leaked into history')
                text=render(c,v['text'])
                require(text.count(c['trusted_evidence'])==1 and text.count(c['question'])==1 and text.count(c['fixed_context'])==1,'Track A identity failure')
                if condition not in ('N_history','H_none'):
                    fact=active_fact(c,**factors)
                    valid=fact['start']<=c['requested_date']<=fact['end']
                    require(valid==bool(factors['T']),'T incorrectly routed')
                    require(fact['predicate'] not in ('collection desk','service day','parcel route','destination room'),'Direct answer property leaked')
            checks.append({'case_id':c['case_id'],'condition':condition,'variants':len(candidates),
                'reference_components':c['reference']['components'],'source_fact_ids':c['reference']['fact_ids'],
                'trusted_evidence_sha256':text_hash(c['trusted_evidence']),'question_sha256':text_hash(c['question']),
                'context_sha256':text_hash(c['fixed_context']),'evaluation_reference_sha256':canonical([c['requested_date'],c['evaluation_date'],c['reference']]),
                'structural_ground_truth_checks':'PASS','semantic_validity':'OPEN','human_approval':''})
    require(set(Counter(c['persona_id'] for c in cases).values())=={2},'Speaker allocation differs')
    return checks

def precision_simulations(repeats=1000, sizes=(6,48,96)):
    """Planning sensitivity on bounded paired contrasts; not fabricated model output."""
    seed=715003;rng=random.Random(seed);rows=[];m=2
    # Cluster-correlated Rademacher paired contrasts: exact marginal mean/SD,
    # exact within-speaker contrast ICC. Does not posit Bernoulli cell accuracy.
    for K in sizes:
        for endpoint,sd,scale in [('R_main',.25,1),('T_main',.25,1),('RxT',.5,2),('R_main_high_variance',.5,1),('RxT_high_variance',1.0,2)]:
            for rho in [0,.2,.5]:
                for effect in [0,.05,.10]:
                    estimates=[];halfwidths=[];coverage=0
                    for _ in range(repeats):
                        speaker_means=[]
                        for __ in range(K):
                            shared=rng.choice([-1,1])
                            same=rng.random()<rho
                            values=[effect+sd*(shared if same else rng.choice([-1,1])) for ___ in range(m)]
                            require(all(abs(v)<=scale for v in values),'Simulation outside possible contrast range')
                            speaker_means.append(statistics.mean(values))
                        estimate=statistics.mean(speaker_means)
                        hw=1.96*statistics.stdev(speaker_means)/math.sqrt(K)
                        estimates.append(estimate);halfwidths.append(hw);coverage+=abs(estimate-effect)<=hw
                    rows.append({'speakers':K,'cases_per_speaker':m,'contrast':endpoint,'assumed_case_sd':sd,'assumed_contrast_ICC':rho,
                        'assumed_effect':effect,'simulated_replicates':repeats,'mean_estimate':statistics.mean(estimates),
                        'mean_normal_halfwidth':statistics.mean(halfwidths),'simulated_normal_interval_coverage':coverage/repeats,
                        'analytical_1_96_halfwidth':1.96*sd*math.sqrt((1+(m-1)*rho)/(K*m)),
                        'bonferroni_6_normal_halfwidth':statistics.NormalDist().inv_cdf(1-.05/(2*6))*sd*math.sqrt((1+rho)/(K*m)),
                        'interpretation':'Assumption-only bounded contrast simulation, not power, achieved precision or observed model results.'})
    return {'version':'p1c_cluster_precision_sensitivity_v1','seed':seed,'repeats_per_scenario':repeats,
        'model':'With probability ICC, both case residuals share a speaker Rademacher draw; otherwise independent signs. Marginal variance SD^2; within-speaker contrast correlation ICC.',
        'limits':'Contrast-level planning, not a joint multi-endpoint response generator. Normal intervals are unreliable at six clusters; no population variances estimated.',
        'rows':rows}

def build():
    require(not PUBLIC.exists() and not DATA.exists(),'Preserve existing proposal')
    data=build_cases();checks=validate_cases(data);evidence=history_evidence();precision=precision_simulations()
    write_json(DATA,data);write_json(PUBLIC/'p1b_evidence_recheck_v1.json',evidence)
    write_json(PUBLIC/'manipulation_validation_v1.json',{'version':VERSION,'records':checks,'human_review':'OPEN'})
    write_json(PUBLIC/'condition_definitions_v1.json',{'conditions':CONDITIONS,'R':'Topical auxiliary fact vs unrelated auxiliary fact','T':'Valid vs expired at requested date',
        'weights':{'R':{'R0T0':-.5,'R0T1':-.5,'R1T0':.5,'R1T1':.5},
                  'T':{'R0T0':-.5,'R0T1':.5,'R1T0':-.5,'R1T1':.5},
                  'RxT':{'R0T0':1,'R0T1':-1,'R1T0':-1,'R1T1':1}},
        'simple_contrasts':['R1T0-R0T0','R1T1-R0T1','R1T1-R1T0','R0T1-R0T0'],
        'control_contrasts':[c+'-N_history' for c in CONDITIONS if c.startswith('R')]+['N_history-H_none'],
        'scope':'New prospective estimands; not relabelled prior H effects; not approved.'})
    write_json(PUBLIC/'precision_simulation_v1.json',precision)
    write_csv(PUBLIC/'precision_simulation_v1.csv',precision['rows'])
    write_json(PUBLIC/'precision_inputs_v1.json',{k:v for k,v in precision.items() if k!='rows'})
    write_json(PUBLIC/'ground_truth_v1.json',{'records':[{'case_id':c['case_id'],'requested_date':c['requested_date'],**c['reference'],
        'source_quotes':[line for line in c['trusted_evidence'].splitlines() if any('['+fid+']' in line for fid in c['reference']['fact_ids'])]} for c in data['cases']]})
    write_json(PUBLIC/'candidate_bank_v1.json',{'version':VERSION,'rule':data['candidate_rule'],'cases':[
        {'case_id':c['case_id'],'conditions':{condition:history_candidates(c,condition) for condition in CONDITIONS}} for c in data['cases']]})
    form=[];app=[]
    for c in data['cases']:
        form.append({'case_id':c['case_id'],'speaker':c['speaker_name'],'family':c['family'],'query_mode':c['query_mode'],
            'trusted_evidence':c['trusted_evidence'],'question':c['question'],'evaluation_date':c['evaluation_date'],'requested_date':c['requested_date'],
            'fixed_context':c['fixed_context'],'reference':c['reference'],
            **{'review_'+s:'' for s in ['evidence_sufficiency','unique_answer','date_interpretation','entity_clarity','no_answer_leakage',
                'topic_relevance_operationalization','auxiliary_fact_independence','history_naturalness','designed_demand','decision']},
            'supporting_quotations':'','reviewer_id':'','reviewed_utc':'','reviewer_notes':''})
        for condition in CONDITIONS:app.append({'case_id':c['case_id'],'condition':condition,**c['applicability'],'persona_fidelity':False})
    write_csv(PUBLIC/'stimulus_review_v1.csv',form);write_csv(PUBLIC/'applicability_v1.csv',app)
    seed=715001;order=[(c['case_id'],cond) for c in data['cases'] for cond in CONDITIONS];random.Random(seed).shuffle(order)
    write_json(PUBLIC/'configuration_proposal_v1.json',{'version':VERSION,'status':'PROPOSED_NOT_AUTHORIZED','dataset':DATA.as_posix(),'dataset_sha256':sha(DATA),
        'generation_authorized':False,'generation_requests_executed':0,'planned_development_requests':72,
        'S':0,'F':0,'primary_arm':'Qwen3.5-2B-Base Q4_K_M','backend':'llama.cpp b11573',
        'threads':4,'threads_batch':4,'n_gpu_layers':0,'n_ctx':4096,'n_predict':96,'temperature':0,'seed':42,
        'order_seed':seed,'proposed_order':order,'response_policy':'response_status_v1','evaluation_policy':'separate_axes_policy_v1',
        'manual_task_specific_scoring':True,'primary_family_proposed':'Temporal Incorrect-label incidence and task success under R,T,RxT; six tests Holm only at future confirmatory freeze',
        'structural_ambiguity':'Retain labels; conservative unknown values plus original-span sensitivity. Never choose later correct turns.',
        'independent_validation_allocations':[{'speakers':k,'cases':2*k,'requests':12*k,'base_proxy_minutes':12*k*evidence['runtime']['mean_response_seconds']/60} for k in [48,96]],
        'development_base_proxy_minutes':72*evidence['runtime']['mean_response_seconds']/60,
        'tokenizer_matching':'PENDING_NATIVE_OFFLINE_CHECK','neutral_review':'OPEN','researcher_decision':''})
    return {'cases':12,'speakers':6,'conditions':6,'proposed_requests':72,'new_generations':0}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['baseline','build']);args=p.parse_args()
    print(json.dumps(baseline() if args.action=='baseline' else build()))

if __name__=='__main__':main()
