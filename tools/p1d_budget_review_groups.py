"""Deduplicate identical masked measurement inputs, not independent observations."""
import argparse
import json
from pathlib import Path
import random
from collections import defaultdict
import p1d_budget_calibration as b

OUT=b.OUT/'ai_review_working_v1'

def current_groups():
    plan=b.load(b.FROZEN);qmap={r['request_id']:r for r in plan['requests']}
    ordered=list(plan['requests']);random.Random(716706).shuffle(ordered)
    anon={r['request_id']:f'BC{i:03d}' for i,r in enumerate(ordered,1)}
    cases={c['case_id']:c for c in b.load(b.DEV/'development_examples_v5.json')['cases']}
    groups={}
    for folder in sorted((b.ROOT/'runs').glob('*')):
        for path in sorted((folder/'events').glob('*.json')):
            event=b.load(path)
            if event['kind']!='p1d_budget_result':continue
            r=event['data'];q=qmap[r['request_id']];c=cases[q['case_id']];boundary=r['response_status']
            text=boundary['first_span']['text'] if boundary['unit_identifiable'] else ''
            value={'question':c['question'],'requested_date':c['query_date'],'evaluation_date':c['evaluation_date'],
                'fixed_context':c['fixed_context'],'trusted_evidence':c['trusted_evidence'],'facts':c['facts'],
                'required_components':c['required_components'],'persona_style':c['persona_profile'].split('. ',1)[-1],
                'primary_text':text,'primary_text_sha256':b.th(text),'measurement_state':'ASSESSABLE' if boundary['unit_identifiable'] else 'BOUNDARY_UNRESOLVED'}
            key=b.th(json.dumps(value,sort_keys=True,separators=(',',':')))
            if key not in groups:groups[key]={'group_id':key,**value,'anonymous_members':[],'source_result_events':[]}
            groups[key]['anonymous_members'].append(anon[r['request_id']]);groups[key]['source_result_events'].append({'path':path.as_posix(),'sha256':b.sha256(path)})
    return groups

def export():
    groups=current_groups();known=set()
    for p in OUT.glob('review_batch_*.json'):
        known.update(x['group_id'] for x in b.load(p)['groups'])
    new=[v for k,v in groups.items() if k not in known];new.sort(key=lambda x:x['group_id'])
    if not new:
        print(json.dumps({'new_groups':0,'current_total_groups':len(groups)}));return
    batch=len(list(OUT.glob('review_batch_*.json')))+1
    b.save(OUT/f'review_batch_{batch:03d}.json',{'version':'masked_measurement_input_groups_v1','groups':new,
        'scope':'Identical evidence/question/date/context/style/span groups only. Every original request remains a separate observation.',
        'created_utc':b.utc_now(),'conditions_or_budgets_exposed':False,'human_decisions':0})
    print(json.dumps({'batch':batch,'new_groups':len(new),'current_total_groups':len(groups)}))
    for x in new:
        print(json.dumps({k:v for k,v in x.items() if k not in ('trusted_evidence','facts','source_result_events')},ensure_ascii=False))

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args();export()
