"""P1d prospective specifications and DEVELOPMENT-ONLY examples. No inference."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random

OUT=Path('docs/validation/p1d/proposed_v1')
SEED=716001
FAMILIES=('single_fact','multi_component','relational_integration','context_followup')
CELLS=('E0V0','E0V1','E1V0','E1V1','D_procedural','H_none')
WEIGHTS={'E':dict(zip(CELLS,(-.5,-.5,.5,.5,0,0))),
         'V':dict(zip(CELLS,(-.5,.5,-.5,.5,0,0))),
         'ExV':dict(zip(CELLS,(1,-1,-1,1,0,0)))}
for left,right in [('E1V0','E0V0'),('E1V1','E0V1'),('E0V1','E0V0'),('E1V1','E1V0')]+[(c,b) for b in ('D_procedural','H_none') for c in CELLS[:4]]+[('D_procedural','H_none')]:
    WEIGHTS[left+'-'+right]={c:int(c==left)-int(c==right) for c in CELLS}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def th(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def csvwrite(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def allocation(speakers):
    if speakers%24:raise ValueError('Balanced allocation requires multiples of 24 speakers')
    blocks=[(a,b,reverse) for a in FAMILIES for b in FAMILIES if a!=b for reverse in (False,True)]
    return [{'speaker_index':s,'case_index':j,'family':blocks[s%24][j],
        'date_type':('historical','current')[j ^ int(blocks[s%24][2])],
        'template_block':(s//24+j)%4,'lexical_realization':(s+j)%2,
        'status':'ALLOCATION_ONLY_NO_HELDOUT_MATERIAL'} for s in range(speakers) for j in range(2)]

def lookup(facts,entity,predicate,date):
    rows=[f for f in facts if f['entity']==entity and f['predicate']==predicate and f['start']<=date<=f['end']]
    if len(rows)!=1:raise ValueError('Non-unique or unsupported evidence lookup')
    return rows[0]

def derive(case):
    facts=case['facts'];entity=case['target_entity'];date=case['query_date']
    locker=lookup(facts,entity,'locker',date)
    if case['family']=='single_fact':refs=[locker]
    elif case['family']=='relational_integration':
        hub=lookup(facts,locker['value'],'hub',date);exit=lookup(facts,hub['value'],'exit',date);refs=[hub,exit]
    else:refs=[locker,lookup(facts,entity,'pickup_window',date)]
    return [{'key':r['predicate'],'value':r['value'],'source_id':r['id']} for r in refs]

def sentence(f,variant=0):
    if variant%2:return f"During {f['start']} through {f['end']}, {f['entity']} had {f['predicate']} {f['value']}."
    return f"{f['entity']}: {f['predicate']} = {f['value']}; valid from {f['start']} through {f['end']} inclusive."

def render(case,history,priority=False,persona=True):
    policy='Use the trusted ledger for the requested date. Historical quotations describe their stated intervals.'
    if priority:policy+=' Resolve conflicting claims by entity, attribute and requested date against the ledger; do not substitute a newer or different-entity value.'
    style=case['persona_profile'] if persona else ''
    return ('TASK RULES\n'+policy+'\nFICTIONAL PERSONA\n'+style+'\nEVALUATION DATE\n'+case['evaluation_date']+
        '\nTRUSTED EVIDENCE\n'+case['trusted_evidence']+'\nARCHIVED MATERIAL\n'+history+
        '\nFIXED CONTEXT\n'+case['fixed_context']+'\nCURRENT QUESTION\n'+case['question']+'\nAssistant:')

def examples(seed=SEED):
    rng=random.Random(seed);cases=[]
    names=['Mira Fenwick','Owen Bellamy','Tessa Northwick','Nolan Fairchild','Vera Ashcombe','Arlo Kingsley','Cleo Westlake','Ellis Fairmont']
    periods=[('2048-01-01','2048-03-31'),('2048-04-01','2048-06-30'),('2048-07-01','2048-09-30'),('2048-10-01','2048-12-31')]
    for i,name in enumerate(names):
        other='Quinn '+name.split()[-1];facts=[]
        # Every entity/time value has competing terminals. No unique final-node shortcut.
        codes=list(range(101,117));rng.shuffle(codes)
        hubs=list(range(201,217));rng.shuffle(hubs)
        exits=list(range(301,317));rng.shuffle(exits)
        for e,entity in enumerate((name,other)):
            for p,(start,end) in enumerate(periods):
                ix=e*4+p;v=codes[ix];locker=f'Locker {v}';hub=f'Hub {hubs[ix]}';exit=f'Exit {exits[ix]}'
                for pred,value,subject in [('locker',locker,entity),('pickup_window',f'{9+p:02d}:00-{10+p:02d}:00',entity),('hub',hub,locker),('exit',exit,hub)]:
                    facts.append({'id':f'D{i:02d}F{len(facts):02d}','entity':subject,'predicate':pred,'value':value,'start':start,'end':end,'authority':'trusted'})
        for j,query in enumerate(('2048-05-15','2048-11-15')):
            family=FAMILIES[(i+j)%4];cid=f'p1d_dev_{i:02d}_{j}'
            context=f'User: Please prepare a collection note for {name}.\nAssistant: I will use the ledger for that volunteer.'
            q={'single_fact':f'Which locker was assigned to {name} on {query}?',
               'multi_component':f'Give both the locker and pickup window assigned to {name} on {query}.',
               'relational_integration':f'On {query}, follow {name}\'s locker to its hub and the hub to its exit. Give the hub and the exit.',
               'context_followup':f'For that volunteer, give both the locker and pickup window on {query}.'}[family]
            case={'case_id':cid,'speaker_id':f'p1d_dev_s{i:02d}','target_entity':name,'other_entity':other,'family':family,
                'split':'DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION','query_date':query,'evaluation_date':'2048-12-31',
                'date_type':'historical' if j==0 else 'current','template_variant':i%4,
                'persona_profile':f'{name} is a fictional volunteer. '+('Use calm complete sentences; avoid slang.' if i%2 else 'Use brief direct clauses; avoid decorative metaphors.'),
                'question':q,'fixed_context':context,'facts':facts,'trusted_evidence':'\n'.join('['+f['id']+'] '+sentence(f,i%2) for f in facts),
                'designed_demand':family,'human_validity_decision':'','independent_validation':False}
            case['required_components']=derive(case);case['histories']={}
            valid_index=1 if j==0 else 3
            for condition in CELLS[:4]:
                e=int(condition[1]);v=int(condition[3]);entity=name if e else other;date=periods[valid_index if v else valid_index-1][0]
                f=lookup(facts,entity,'locker',date)
                case['histories'][condition]={'text':'Archived quotation by '+name+': "'+sentence(f,i%2)+'"','source_id':f['id'],
                    'entity_match':bool(e),'query_interval_match':bool(v),'answer_supporting':bool(e and v),
                    'answer_competition':'deliberate value candidate; historically true, not false ground truth'}
            case['histories']['D_procedural']={'text':'Archived quotation by '+name+': "I read the record carefully and then closed the folder after checking its cover."','source_id':None,'control_status':'DIAGNOSTIC_ONLY_UNREVIEWED'}
            case['histories']['H_none']={'text':'','source_id':None,'control_status':'SHORTER_CONTEXT_BASELINE'}
            cases.append(case)
    return cases

def check_case(case):
    assert case['required_components']==derive(case)
    assert set(case['histories'])==set(CELLS)
    for c,h in case['histories'].items():
        if c not in CELLS[:4]:continue
        f=next(f for f in case['facts'] if f['id']==h['source_id'])
        assert (f['entity']==case['target_entity'])==h['entity_match']
        assert (f['start']<=case['query_date']<=f['end'])==h['query_interval_match']
    return True

def build(version='v3'):
    cases=examples();assert all(check_case(c) for c in cases)
    write(OUT/f'development_examples_{version}.json',{'version':'p1d_examples_development_'+version,'seed':SEED,'cases':cases,'generation_authorized':False})
    records=[];review=[]
    for case in cases:
        for cell,h in case['histories'].items():
            prompt=render(case,h['text']);records.append({'case_id':case['case_id'],'speaker_id':case['speaker_id'],'condition':cell,'prompt':prompt,'prompt_sha256':th(prompt),
                'evidence_sha256':th(case['trusted_evidence']),'question_sha256':th(case['question']),'reference':case['required_components'],
                'fixed_context_sha256':th(case['fixed_context']),'query_date':case['query_date'],'source_history_fact':h['source_id']})
        review.append({'case_id':case['case_id'],'question':case['question'],'trusted_evidence':case['trusted_evidence'],'reference':case['required_components'],
            'histories':case['histories'],'risks':'E changes entity/name/value; V changes interval/value. E1V1 deliberately repeats an answer-supporting fact. Control neutrality not established.',
            'evidence_sufficiency':'','temporal_validity':'','leakage_beyond_declared_positive_control':'','context_necessity':'','researcher_decision':'','reviewer_id':''})
    write(OUT/f'development_prompts_{version}.json',records);csvwrite(OUT/f'development_review_{version}.csv',review)
    if version!='v1':
        write(OUT/f'example_revision_{version}.json',{'supersedes':'development_examples_v2.json','reason':'V2 hub and exit codes followed arithmetic offsets from lockers. V3 independently permutes all three value lists to remove that deterministic shortcut. Other distractor names remain exclusive. No validation cases or responses created.',
            'v2_preserved_sha256':sha(OUT/'development_examples_v2.json'),'v3_sha256':sha(OUT/'development_examples_v3.json'),'new_generations':0,'status':'DEVELOPMENT_EXAMPLES_UNAPPROVED'})
        print(json.dumps({'development_cases':len(cases),'example_prompts':len(records),'heldout_cases_created':0,'new_generations':0,'active_version':version}));return
    write(OUT/'contrast_specification_v1.json',{'status':'PROPOSED_NOT_APPROVED','cells':CELLS,'weights':WEIGHTS,
        'meaning':'E = target-entity versus other-entity source selection; V = query-containing versus expired interval source selection. Not P1c R/T.',
        'primary_family':[{'endpoint':e,'contrast':c} for e in ('temporal_Incorrect_label_incidence','task_success') for c in ('E','V','ExV')],
        'unknown':'Retain U/boundary/missing separately; no renormalization; unknown task outcomes have [0,1] identification bounds.'})
    write(OUT/'metric_applicability_v1.json',[{'case_id':c['case_id'],'condition':s,**{m:True for m in ('relevance','factual','temporal','coherence','task_success','component_coverage','persona_fidelity','structural_status')},
        'scope':'Development example, not scored output; persona fidelity is narrow style adherence, not real-person imitation.'} for c in cases for s in CELLS])
    write(OUT/'future_allocation_candidates_v1.json',{str(n):allocation(n) for n in (48,96,144)})
    print(json.dumps({'development_cases':len(cases),'example_prompts':len(records),'heldout_cases_created':0,'new_generations':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',choices=['v3'],default='v3');args=p.parse_args();build(args.version)
