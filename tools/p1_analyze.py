"""Offline, immutable wave audit and descriptive analysis; no model calls."""
import base64
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
import random
from statistics import mean,median

from personaslm.conditioning import FACTORIAL
from personaslm.inference import normalize_result
from personaslm.journal import atomic_json,read_events,utc_now
from personaslm.p1 import PilotCase,evaluate_pilot,paired_factorial
from personaslm.provenance import sha256,fingerprint
from personaslm.response_status import text_hash,STATUSES
from personaslm.runner import validate_completion

PUBLIC=Path('docs/validation/p1');SESSION=Path('results/p1_wave1/development_v1')
CATEGORIES=('Correct','Incorrect','Unverifiable','Not Applicable')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write_csv(p,rows):
    with p.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def summarize(rows, family=None):
    result={}
    planned=12 if family is None else 3
    factual_planned=9 if family is None else (0 if family=='C' else 3)
    temporal_planned=6 if family is None else (3 if family in 'AD' else 0)
    for condition in FACTORIAL:
        group=[r for r in rows if r['condition']==condition]
        eligible=[r for r in group if r['applicability']['factual_consistency']]
        auto=[r for r in eligible if r['family'] in 'AD']
        fact=Counter(r['evaluation']['factual_support']['label'] for r in group)
        auto_counts=Counter(r['evaluation']['factual_support']['label'] for r in auto)
        evaluated=fact['Correct']+fact['Incorrect']
        result[condition]={'planned':planned,'received_and_parsed':len(group),
            'structural':{k:sum(r['evaluation']['response_completeness']['status']==k for r in group) for k in STATUSES},
            'factual':{'eligible':factual_planned,'observed_eligible':len(eligible),'conclusively_classified':evaluated,
                'unscorable_or_uncertain':len(eligible)-evaluated,'categories':{k:fact[k] for k in CATEGORIES},
                'bounded_automatic_scope':len(auto),'bounded_automatic_counts':{k:auto_counts[k] for k in CATEGORIES},
                'stable_fact_human_pending':sum(r['family']=='B' for r in group),
                'missing_eligible':factual_planned-len(eligible),'primary_denominator':factual_planned,'general_accuracy_estimated':False},
            'temporal':{'eligible':temporal_planned,'human_evaluated':0,'pending':sum(r['applicability']['temporal_consistency'] for r in group),'effect_estimate':None},
            'relevance':{'eligible':planned,'human_evaluated':0,'pending':len(group),'effect_estimate':None},
            'coherence':{'eligible':planned,'human_evaluated':0,'pending':len(group),'effect_estimate':None},
            'tokens':{'total':sum(r['generated_tokens'] for r in group),'mean':mean(r['generated_tokens'] for r in group) if group else None},
            'latency_seconds':{'mean':mean(r['latency_seconds'] for r in group) if group else None,
                'median':median(r['latency_seconds'] for r in group) if group else None}}
    return result

def contrasts(rows, planned_speakers=12):
    by_case=defaultdict(dict)
    for row in rows:
        if row['condition'] in by_case[row['case_id']]:raise ValueError('Duplicate observed factorial cell')
        by_case[row['case_id']][row['condition']]=row
    paired=[];metrics=[*STATUSES,'generated_tokens']
    for cid,cells in sorted(by_case.items()):
        if set(cells)!=set(FACTORIAL):
            paired.append({'case_id':cid,'status':'INCOMPLETE','observed_conditions':list(cells),'contrasts':None});continue
        row=next(iter(cells.values()));values={}
        for metric in metrics:
            scores={c:(r['generated_tokens'] if metric=='generated_tokens' else int(r['evaluation']['response_completeness']['status']==metric)) for c,r in cells.items()}
            values[metric]=paired_factorial(scores)
        transitions={name:{'reference':cells['C0']['evaluation']['factual_support']['label'],
            'conditioned':cells[condition]['evaluation']['factual_support']['label'],
            'eligible':row['applicability']['factual_consistency']} for name,condition in [('C1-C0','C1'),('C3-C0','C3')]}
        paired.append({'case_id':cid,'persona_id':row['persona_id'],'family':row['family'],'status':'COMPLETE_CELLS',
            'structural_contrasts':values,'factual_transitions':transitions,'semantic_effect_claim':False})
    full=[p for p in paired if p['status']=='COMPLETE_CELLS'];aggregate={}
    for metric in metrics:
        points=[p['structural_contrasts'][metric] for p in full]
        aggregate[metric]={'speakers':len(points),'planned_speakers':planned_speakers,'simple':{},'average_main_effects':{},'interactions':{}}
        for key in ['C1-C0','C3-C0']:
            vals=[p[key] for p in points]
            aggregate[metric]['simple'][key]={'mean':mean(vals) if vals else None,'observed_range':[min(vals),max(vals)] if vals else None,'values':vals}
        for key in 'SFH':aggregate[metric]['average_main_effects'][key]=mean(p['average_main_effects'][key] for p in points) if points else None
        for key in ['SxF','SxH','FxH','SxFxH']:aggregate[metric]['interactions'][key]=mean(p['difference_in_differences'][key] for p in points) if points else None
    return {'paired_cases':paired,'structural_factorial_summaries':aggregate,'significance_test_performed':False,
        'uncertainty':'Raw paired values/ranges only; no population-equivalence or confirmatory-significance claim. Cells within each speaker are correlated.',
        'semantic_contrasts':'Factual transitions retained; unresolved judgments preclude general accuracy effects. Temporal/relevance/coherence comparisons await human annotation.'}

def main():
    dataset=read(Path('data/synthetic/p1_development_v1.json'));cases={r['case_id']:PilotCase(r) for r in dataset['cases']}
    manifest=read(PUBLIC/'wave1_manifest_v1.json');wanted={r['request_id']:r for r in manifest['requests']}
    if len(wanted)!=96:raise ValueError('Incorrect wave denominator')
    all_rows=[];attempts=[];audits=[];http_pairs=[]
    for path in sorted((SESSION/'runs').glob('*/manifest.json')):
        meta=read(path)
        if meta.get('operation')!='factorial_generation':continue
        if not (path.parent/'summary.json').exists():raise ValueError('Run is still active; do not analyze incomplete live stream')
        if meta['wave_manifest_sha256']!=sha256(PUBLIC/'wave1_manifest_v1.json'):raise ValueError('Wave manifest changed')
        events=read_events(path.parent);raw={};pending=None;responses={};current=None;native_ids={};token_pending=None;verified_inputs=[]
        for event in events:
            d=event['data'];kind=event['kind']
            if kind=='http_request' and d['route']=='/tokenize':
                if token_pending is not None:raise ValueError('Unpaired tokenization')
                token_pending=d['payload']
                if {k:v for k,v in token_pending.items() if k!='content'}!={'add_special':True,'parse_special':False,'with_pieces':False}:
                    raise ValueError('Tokenizer special-token policy changed')
            if kind=='http_response' and d['route']=='/tokenize':
                if token_pending is None or d['status']!=200:raise ValueError('Missing native tokenizer response')
                ids=json.loads(base64.b64decode(d['body_base64']))['tokens']
                native_ids[text_hash(token_pending['content'])]=ids;token_pending=None
            if kind=='p1_prompt_verified':
                if d!=wanted[d['request_id']] or native_ids[d['prompt_sha256']]!=d['input_token_ids']:raise ValueError('Native tokenizer reconstruction mismatch')
                verified_inputs.append(d['request_id'])
            if kind=='p1_generation_started':
                current=d['request_id'];attempts.append(current)
                if d!=wanted[current]:raise ValueError('Started request differs from manifest')
                if current not in verified_inputs:raise ValueError('Generation began without verified tokenizer input')
            if kind=='http_request' and d['route']=='/completion':
                if pending is not None:raise ValueError('Unpaired completion')
                expected={'prompt':wanted[current]['input_token_ids'],**manifest['decoding']}
                if d['payload']!=expected:raise ValueError('Actual decoding/input differs from freeze')
                pending=current
            if kind=='http_response' and d['route']=='/completion':
                if pending is None:raise ValueError('Unexpected completion response')
                if d['status']==200:
                    body=base64.b64decode(d['body_base64']);responses[pending]=json.loads(body)
                    http_pairs.append({'request_id':pending,'response_body_sha256':__import__('hashlib').sha256(body).hexdigest(),
                        'latency_seconds':d.get('elapsed_seconds'),'http_status':d['status'],'event_sequence':event['sequence']})
                pending=None
            if kind=='p1_raw_generation':
                if d['response']!=responses[d['request_id']]:raise ValueError('Saved raw differs from native bytes')
                raw[d['request_id']]=d
            if kind=='p1_result':
                row=d;rid=row['request_id'];original=raw[rid]['response'];case=cases[row['case_id']]
                for key,value in wanted[rid].items():
                    if row[key]!=value:raise ValueError('Result input changed')
                if row['token_audit']!=validate_completion(original,row['input_token_ids']):raise ValueError('Input token mismatch')
                normalized=normalize_result(original)
                if any(row[k]!=v for k,v in normalized.items()):raise ValueError('Raw normalization mismatch')
                first=evaluate_pilot(case,row['raw_response'],row['raw_termination'])
                second=evaluate_pilot(case,row['raw_response'],row['raw_termination'])
                if first!=second or first!=row['evaluation']:raise ValueError('Frozen parser/evaluator reconstruction mismatch')
                all_rows.append(row)
        audits.append({'run_directory':path.parent.as_posix(),'events':len(events),'chain_valid':True,
            'native_inputs_reconstructed':len(verified_inputs),
            'manifest_sha256':sha256(path),'summary':read(path.parent/'summary.json'),
            'file_hashes':{p.relative_to(path.parent).as_posix():sha256(p) for p in path.parent.rglob('*') if p.is_file()}})
    if len(attempts)!=len(set(attempts)) or len(attempts)>96:raise ValueError('Duplicate or unauthorized attempt')
    if len({r['request_id'] for r in all_rows})!=len(all_rows):raise ValueError('Duplicate result')
    summary=summarize(all_rows);paired=contrasts(all_rows)
    aggregate={'version':'p1_wave1_analysis_v1','created_utc':utc_now(),'analysis_type':'exploratory_descriptive_only',
        'wave_manifest_sha256':sha256(PUBLIC/'wave1_manifest_v1.json'),'dataset_sha256':sha256(Path('data/synthetic/p1_development_v1.json')),
        'source_sha256':sha256(Path(__file__)),'planned_requests':96,'attempted_requests':len(attempts),'completed_results':len(all_rows),
        'missing_request_ids':sorted(set(wanted)-{r['request_id'] for r in all_rows}),
        'conditions':summary,'by_family':{f:summarize([r for r in all_rows if r['family']==f],f) for f in 'ABCD'},
        'family_paired_analysis':{f:contrasts([r for r in all_rows if r['family']==f],3) for f in 'ABCD'},
        'observed_structure':dict(Counter(r['evaluation']['response_completeness']['status'] for r in all_rows)),
        'stop_reasons':dict(Counter(r['stop_reason'] for r in all_rows)),
        'raw_empty':sum(not r['raw_response'].strip() for r in all_rows),'total_generated_tokens':sum(r['generated_tokens'] for r in all_rows),
        'limit_reached':sum(r['generated_tokens']==96 for r in all_rows),'latency_seconds':{'min':min(r['latency_seconds'] for r in all_rows),
            'max':max(r['latency_seconds'] for r in all_rows),'mean':mean(r['latency_seconds'] for r in all_rows),'median':median(r['latency_seconds'] for r in all_rows)},
        'paired_analysis':paired,'run_audits':audits,'native_completion_pairs':http_pairs,
        'same_saved_inputs_and_evaluations_reconstructed_twice':True,'human_outcome_reviews_completed':0,'neutral_generation_requests':0,
        'limitations':['Fixed small development set; one quantized Base model; no significance or equivalence claim',
            'Semantic annotation pending; automatic factual grammar only supports canonical residence assertions',
            'Length cap and structural censoring separate from truth; no C0-correct selection',
            'Names, styles and task families partly confounded; H relevance depends on task family',
            'Shared workstation with concurrent documentation work; latency is observed cost, not an isolated hardware benchmark']}
    atomic_json(PUBLIC/'wave1_results_v1.json',{'version':'p1_wave1_results_v1','rows':all_rows,'source_wave_sha256':sha256(PUBLIC/'wave1_manifest_v1.json')})
    atomic_json(PUBLIC/'wave1_analysis_v1.json',aggregate)
    reviews=[];key=[];shuffled=list(all_rows);random.Random(713097).shuffle(shuffled)
    for i,row in enumerate(shuffled,1):
        case=cases[row['case_id']];rid=f'P1R{i:03d}';boundary=row['evaluation']['response_completeness']
        reviews.append({'review_version':'p1_output_review_v1','review_id':rid,'raw_sha256':text_hash(row['raw_response']),
            'trusted_evidence':case.trusted_evidence,'reference_fact_ledger':json.dumps(case.record['facts']),
            'question':case.question,'fixed_recent_context':'\n'.join(case.context),'evaluation_date':case.evaluation_date,
            'applicability':json.dumps(case.applicability),'raw_output':row['raw_response'],'proposed_first_reply':row['parsed_response'],
            'excluded_continuation':boundary['excluded_tail'],'reply_unit_identifiable':'','semantic_completeness':'',
            'factual_label':'','temporal_label':'','relevance_1_to_5':'','coherence_1_to_5':'','evidence_quotations':'',
            'reviewer_id':'','review_assistance':'','reviewed_utc':'','notes':''})
        key.append({'review_id':rid,'request_id':row['request_id'],'condition':row['condition'],'model':'Qwen3.5-2B-Base Q4_K_M'})
    write_csv(PUBLIC/'output_review_v1.csv',reviews)
    atomic_json(PUBLIC/'output_review_key_v1.json',{'version':'p1_output_review_key_v1','administrator_only':True,'rows':key,'masking_not_completed_blind_review':True})
    print(json.dumps({'planned':96,'attempted':len(attempts),'completed':len(all_rows),'structure':aggregate['observed_structure'],
        'stops':aggregate['stop_reasons'],'tokens':aggregate['total_generated_tokens'],'outcome_human_reviews':0}))

if __name__=='__main__':main()
