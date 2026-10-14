"""Known local baseline adaptations, not an original algorithm or model evaluation."""
import argparse
import copy
import re
import statistics
import time
import tracemalloc
from p1d_design import OUT,read,write,csvwrite,lookup,render,sha

METHODS=('all_history','history_removal','lexical_top1','time_filter','entity_time_filter')
def select(items,query,method):
    if method=='all_history':return list(items)
    if method=='history_removal':return []
    if method=='lexical_top1':
        tokens=set(re.findall(r'\w+',query['text'].lower()))
        score=lambda r:len(tokens & set(re.findall(r'\w+',r['text'].lower())))
        return sorted(items,key=lambda r:(-score(r),r['id']))[:1]
    if method=='time_filter':return [r for r in items if r['start']<=query['date']<=r['end']]
    if method=='entity_time_filter':return [r for r in items if r['entity']==query['entity'] and r['start']<=query['date']<=r['end']]
    raise ValueError('Unknown method')

def verify_structured(payload,facts,query,check_entity=True,check_time=True,check_delivery=True):
    """Accept only explicitly structured assertions. No free-text scoring or gold-answer field."""
    claims=payload['assertions'];labels=[];supported=set()
    for c in claims:
        candidates=[f for f in facts if f['predicate']==c['predicate'] and (not check_entity or f['entity']==c['entity']) and (not check_time or f['start']<=query['date']<=f['end'])]
        if not candidates:labels.append('Unverifiable');continue
        match=any(f['value']==c['value'] for f in candidates)
        if c.get('negated',False):match=not match
        labels.append('Correct' if match else 'Incorrect')
        if match and not c.get('negated',False) and c['entity']==query['entity']:supported.add(c['predicate'])
    factual='Incorrect' if 'Incorrect' in labels else 'Unverifiable' if not labels or 'Unverifiable' in labels else 'Correct'
    coverage=len(supported&set(query['required_predicates']))/len(query['required_predicates'])
    delivered=payload['speech_act']=='answer' if check_delivery else True
    return {'factual':factual,'supported_component_fraction':coverage,'task_success':delivered and coverage==1 and factual=='Correct',
        'delivery':delivered,'scope':'Structured-claim diagnostic only; unknown free text requires independent annotation.'}

def fixtures(case):
    q={'entity':case['target_entity'],'date':case['query_date'],'required_predicates':['locker','pickup_window']}
    good=[{'entity':q['entity'],'predicate':p,'value':lookup(case['facts'],q['entity'],p,q['date'])['value']} for p in q['required_predicates']]
    wrong=copy.deepcopy(good);wrong[0]['value']=lookup(case['facts'],case['other_entity'],'locker',q['date'])['value']
    stale=copy.deepcopy(good);stale[0]['value']=lookup(case['facts'],q['entity'],'locker','2048-01-01')['value']
    cases=[('correct_full',good,'answer','Correct',True),('correct_partial',good[:1],'answer','Correct',False),
        ('wrong_entity_value',wrong,'answer','Incorrect',False),('expired_value',stale,'answer','Incorrect',False),
        ('promise_with_correct_mentions',good,'promise','Correct',False),('no_answer',[],'promise','Unverifiable',False),
        ('negates_correct',[{**good[0],'negated':True}],'answer','Incorrect',False),
        ('unsupported_predicate',[{'entity':q['entity'],'predicate':'favorite_food','value':'rice'}],'answer','Unverifiable',False)]
    return [{'id':name,'query':q,'payload':{'assertions':claims,'speech_act':act},'authored_expected_factual':fc,'authored_expected_success':success,
        'provenance':'AUTHORED_SOFTWARE_FIXTURE_NOT_GENERATED_RESPONSE_OR_HUMAN_LABEL'} for name,claims,act,fc,success in cases]

def run():
    data=read(OUT/'development_examples_v2.json')['cases'];selection=[];prompts=[]
    for case in data:
        pool=[{**next(f for f in case['facts'] if f['id']==h['source_id']),'text':h['text']} for c,h in case['histories'].items() if h['source_id']]
        query={'text':case['question']+' '+case['fixed_context'],'entity':case['target_entity'],'date':case['query_date']}
        for method in METHODS:
            selected=select(pool,query,method)
            selection.append({'case_id':case['case_id'],'method':method,'retained_ids':[x['id'] for x in selected],
                'retained_target_query_valid':sum(x['entity']==query['entity'] and x['start']<=query['date']<=x['end'] for x in selected),
                'other_or_expired_retained':sum(not(x['entity']==query['entity'] and x['start']<=query['date']<=x['end']) for x in selected),
                'generated_answer_quality':None,'persona_fidelity_effect':None})
            text='\n'.join(x['text'] for x in selected)
            prompts.append({'case_id':case['case_id'],'method':method,'prompt':render(case,text),'generation_executed':False})
        prompts.append({'case_id':case['case_id'],'method':'evidence_priority_prompt','prompt':render(case,case['histories']['E1V0']['text'],priority=True),'generation_executed':False})
        prompts.append({'case_id':case['case_id'],'method':'trusted_evidence_only','prompt':render(case,'',persona=False),'generation_executed':False})
    bank=fixtures(data[0]);checks=[]
    for f in bank:
        for variant,opts in [('full',{}),('no_entity_check',{'check_entity':False}),('no_time_check',{'check_time':False}),('no_delivery_check',{'check_delivery':False})]:
            result=verify_structured(f['payload'],data[0]['facts'],f['query'],**opts)
            checks.append({'fixture':f['id'],'variant':variant,**result,'matches_authored_spec':result['factual']==f['authored_expected_factual'] and result['task_success']==f['authored_expected_success']})
    batches=[];tracemalloc.start()
    for _ in range(5):
        start=time.process_time_ns()
        for _ in range(100):
            for f in bank:verify_structured(f['payload'],data[0]['facts'],f['query'])
        batches.append((time.process_time_ns()-start)/(100*len(bank)))
    peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
    target=OUT/'offline_baselines'
    write(target/'selection_records_v1.json',selection);csvwrite(target/'selection_records_v1.csv',selection)
    write(target/'prompt_adaptations_v1.json',prompts);write(target/'authored_verifier_fixtures_v1.json',bank);csvwrite(target/'verifier_ablation_v1.csv',checks)
    summary={'generation_calls':0,'development_cases':16,'selection_methods':METHODS,'structured_fixtures':8,
        'ablation_matches':{v:sum(r['matches_authored_spec'] for r in checks if r['variant']==v) for v in ('full','no_entity_check','no_time_check','no_delivery_check')},
        'median_cpu_ns_per_verification':statistics.median(batches),'cpu_batches_ns':batches,'traced_python_peak_bytes':peak,
        'independent_accuracy':None,'model_reliability_gain':None,'persona_fidelity_gain':None,
        'classification':'ENGINEERING_ADAPTATION_OF_ESTABLISHED_FILTERING_AND_STRUCTURED_CHECKS',
        'limitation':'Structured entity/date/query supplied to all methods; no gold answer passed. Extracting structured assertions from real language remains unvalidated. Selection budgets differ, so no fair generation superiority claim.',
        'source_sha256':sha(__file__),'dataset_sha256':sha(OUT/'development_examples_v2.json')}
    write(target/'summary_v1.json',summary);print(summary)

if __name__=='__main__':argparse.ArgumentParser(description=__doc__).parse_args();run()
