"""Reconstruct budget observations and prepare masked AI/human measurement views."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import random
import statistics
import time

import p1d_budget_calibration as run
from p1d_design import csvwrite
from p1c_boundary_baselines import extract, METHODS
from p1d_boundary_locality import inspect

OUT=run.OUT/'measurement_v1'

def masked_materials(audit):
    cases={c['case_id']:c for c in run.load(run.DEV/'development_examples_v5.json')['cases']}
    ordered=list(audit['rows']);random.Random(716706).shuffle(ordered)
    view=[];mapping=[];structural=[]
    for i,item in enumerate(ordered,1):
        request=item['request'];r=item['result'];c=cases[request['case_id']];rid=f'BC{i:03d}'
        if r is None:raise ValueError('Incomplete execution; do not silently create a full 144-observation review')
        boundary=r['response_status']
        first=boundary['first_span']['text'] if boundary['unit_identifiable'] else ''
        view.append({'anonymous_response_id':rid,'question':c['question'],'requested_date':c['query_date'],
            'evaluation_date':c['evaluation_date'],'fixed_context':c['fixed_context'],'trusted_evidence':c['trusted_evidence'],
            'required_components':json.dumps(c['required_components']), 'persona_style':c['persona_profile'].split('. ',1)[-1],
            'primary_evaluation_text':first,'primary_text_sha256':run.th(first),
            'measurement_state':'ASSESSABLE' if boundary['unit_identifiable'] else 'BOUNDARY_UNRESOLVED',
            'relevance':'','factual':'','temporal':'','coherence':'','task_success':'','component_presence':'',
            'component_support':'','semantic_completeness':'','persona_fidelity':'','reviewer_id':'','researcher_decision':''})
        mapping.append({'anonymous_response_id':rid,'request_id':request['request_id'],'case_id':request['case_id'],
            'speaker_id':request['speaker_id'],'condition':request['condition'],'budget':request['max_new_tokens'],
            'family':request['family'],'request_sha256':request['request_sha256']})
        structural.append({'anonymous_response_id':rid,'raw_text':r['raw_response'],'raw_sha256':r['raw_text_sha256'],
            'original_first_span':boundary['first_span'],'original_status':boundary['status'],'original_reasons':boundary['reasons'],
            'unit_identifiable':boundary['unit_identifiable'],'native_termination':r['raw_termination'],
            'boundary_locality_diagnostic':inspect(r['raw_response'],r['raw_termination']),
            'independent_human_boundary':'','researcher_decision':''})
    return view,mapping,structural

def structural_summary(audit):
    rows=[];blocks=defaultdict(dict);summary={}
    for item in audit['rows']:
        q=item['request'];r=item['result']
        if r is None:continue
        b=r['response_status'];row={'request_id':q['request_id'],'case_id':q['case_id'],'speaker_id':q['speaker_id'],
            'family':q['family'],'condition':q['condition'],'budget':q['max_new_tokens'],'generated_tokens':r['generated_tokens'],
            'stop_reason':r['stop_reason'],'native_stop_type':r['raw_termination'].get('stop_type'),'structural_status':b['status'],'unit_identifiable':b['unit_identifiable'],
            'first_reply_chars':len(b['first_span']['text']),'raw_chars':len(r['raw_response']),'latency_seconds':r['latency_seconds']}
        rows.append(row);blocks[q['case_id'],q['condition']][q['max_new_tokens']]=r
    for budget in (96,192,256):
        group=[r for r in rows if r['budget']==budget]
        summary[budget]={'completed':len(group),'stop_reasons':dict(Counter(r['stop_reason'] for r in group)),
            'native_stop_types':dict(Counter(r['native_stop_type'] for r in group)),
            'structure':dict(Counter(r['structural_status'] for r in group)),'identifiable':sum(r['unit_identifiable'] for r in group),
            'generated_tokens':sum(r['generated_tokens'] for r in group),'latency_mean_seconds':statistics.mean(r['latency_seconds'] for r in group),
            'latency_median_seconds':statistics.median(r['latency_seconds'] for r in group),
            'latency_total_seconds':sum(r['latency_seconds'] for r in group),'semantic_ratings':'PENDING_AI_REVIEW_NOT_INFERRED_FROM_STRUCTURE'}
    pairs=[]
    for (cid,cell),group in blocks.items():
        for a,b in ((96,192),(96,256),(192,256)):
            if a not in group or b not in group:continue
            x,y=group[a],group[b];xt=x['generated_token_ids'];yt=y['generated_token_ids'];k=0
            while k<min(len(xt),len(yt)) and xt[k]==yt[k]:k+=1
            pairs.append({'case_id':cid,'condition':cell,'lower_budget':a,'higher_budget':b,'common_generated_token_prefix':k,
                'lower_is_token_prefix':k==len(xt),'lower_is_text_prefix':y['raw_response'].startswith(x['raw_response']),
                'first_span_text_equal':x['response_status']['first_span']['text']==y['response_status']['first_span']['text'],
                'identifiable_change':int(y['response_status']['unit_identifiable'])-int(x['response_status']['unit_identifiable']),
                'lower_status':x['response_status']['status'],'higher_status':y['response_status']['status'],
                'latency_difference_seconds':y['latency_seconds']-x['latency_seconds']})
    return rows,summary,pairs

def baseline_rows(items):
    rows=[]
    for rid,raw,native,reference in items:
        local=inspect(raw,native)
        for method in (*METHODS,'prefix_locality_diagnostic'):
            if method=='prefix_locality_diagnostic':
                x=local['local_prefix_candidate'];span=(x['start'],x['end']) if x else None
            else:span=extract(raw,native,method)
            text=raw[span[0]:span[1]] if span else None
            rows.append({'response_id':rid,'method':method,'candidate_start':span[0] if span else None,'candidate_end':span[1] if span else None,
                'candidate_text':text,'candidate_sha256':run.th(text) if text is not None else None,
                'original_identifiable':local['original_identifiable'],'original_status':local['original_status'],
                'matches_original_candidate_text':text is not None and text.strip()==reference.strip(),
                'independent_accuracy':None,'semantic_quality_gain':None})
    return rows

def historical_baseline():
    source=Path('docs/validation/p1c/calibration_v1/measurement_v1/structural_review_view_v1.csv')
    with source.open(encoding='utf-8-sig',newline='') as f:s=list(csv.DictReader(f))
    items=[(x['anonymous_response_id'],x['raw_full_continuation'],json.loads(x['native_termination']),x['raw_first_reply']) for x in s]
    rows=baseline_rows(items);out=run.OUT/'offline_baseline_v1';out.mkdir(parents=True,exist_ok=True)
    csvwrite(out/'p1c_boundary_comparison_v1.csv',rows)
    summary={m:{'candidates':sum(r['candidate_text'] is not None for r in rows if r['method']==m),
        'previously_unidentifiable_with_candidate':[r['response_id'] for r in rows if r['method']==m and not r['original_identifiable'] and r['candidate_text'] is not None],
        'independent_accuracy':None} for m in (*METHODS,'prefix_locality_diagnostic')}
    run.save(out/'summary_v1.json',{'source_sha256':run.sha256(source),'source':source.as_posix(),'methods':summary,
        'new_generations':0,'historical_labels_changed':False,'classification':'Known-method parsing adaptation; no original algorithm claim',
        'failure_test':'Late labels can veto earlier spans under the frozen parser; authored tests demonstrate the code property, empirical frequency is separately counted.'})
    print(json.dumps(summary,indent=2))

def prepare():
    audit=run.audit();run.require(audit['results']==audit['attempted']==audit['raw_responses']==144,'Calibration incomplete')
    OUT.mkdir(parents=True,exist_ok=True);run.save(OUT/'execution_integrity_v1.json',audit)
    view,mapping,structural=masked_materials(audit)
    csvwrite(OUT/'semantic_scoring_view_v1.csv',view);run.save(OUT/'withheld_treatment_budget_mapping_v1.json',mapping)
    run.save(OUT/'structural_boundary_view_v1.json',structural)
    rows,summary,pairs=structural_summary(audit)
    csvwrite(OUT/'structural_results_v1.csv',rows);run.save(OUT/'budget_structural_summary_v1.json',summary)
    csvwrite(OUT/'paired_prefix_diagnostics_v1.csv',pairs)
    baselines=baseline_rows([(r['anonymous_response_id'],r['raw_text'],r['native_termination'],r['original_first_span']['text']) for r in structural])
    csvwrite(OUT/'boundary_baseline_comparison_v1.csv',baselines)
    run.save(OUT/'review_provenance_v1.json',{'version':'p1d_budget_masked_review_v1','shuffle_seed':716706,'records':144,
        'manifest_sha256':run.MANIFEST_SHA,'source_integrity_sha256':run.sha256(OUT/'execution_integrity_v1.json'),
        'condition_budget_labels_in_semantic_view':False,'human_ratings':0,'analyst_masking_limit':'Analyst prepared execution inputs and can access mapping. Review file hides assignments/budgets; no independent or perfect blinding claim.',
        'rules':'Original first span when unit_identifiable; otherwise primary unknown. Alternative candidates separately reviewed. No structural status is a factual score.',
        'statistical_unit':'Eight paired development cases/speaker clusters; six conditions repeated per case, three caps. Not 144 independent participants.'})
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','historical-baseline']);a=p.parse_args()
    historical_baseline() if a.action=='historical-baseline' else prepare()
