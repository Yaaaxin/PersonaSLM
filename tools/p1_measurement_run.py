"""P1-only cumulative, category-capped execution. No retries or implicit warmup."""
import argparse
import ast
import base64
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

import p1_measurement_materials as m
s=m.s
OUT, ROOT = m.OUT, m.ROOT


def source_hashes():
    return s.sources() | {str(p):s.sha256(p) for p in (Path('tools/p1_measurement_run.py'),Path('tools/p1_measurement_materials.py'),Path('tools/p1_measurement_scoring.py'),Path('tools/p1_measurement_scoring_v2.py'),Path('tools/p1_measurement_diagnostic.py'))}


def cumulative():
    counts={k:0 for k in m.CAPS};ids=set();reservations={k:0 for k in m.CAPS}
    for p in sorted((ROOT/'attempts').glob('*.json')):
        a=s.load(p);category=a['category'];rid=a['request_id']
        s.require(category in counts and a['authorization_id']==m.AUTH_ID,'Unknown authorization/category')
        s.require(rid not in ids,'Duplicate request attempts');ids.add(rid);counts[category]+=1
    for p in sorted((ROOT/'claims').glob('*.json')):
        c=s.load(p);reservations[c['category']]+=c['maximum_attempts']
    for k in counts:
        s.require(counts[k]<=reservations[k]<=m.CAPS[k],'Category cap exceeded')
    s.require(sum(counts.values())<=160,'Total cap exceeded')
    return {'authorization_id':m.AUTH_ID,'attempted':counts,'reserved':reservations,
            'remaining_authorization':{k:m.CAPS[k]-counts[k] for k in counts},
            'remaining_unreserved':{k:m.CAPS[k]-reservations[k] for k in counts},
            'total_attempted':sum(counts.values()),'total_remaining':160-sum(counts.values()),
            'retry_policy':'Attempt files are exclusive and never removed. Ambiguous transport outcomes consume an attempt.'}


def validate(category):
    s.require(category in m.CAPS,'Unregistered category')
    path=OUT/(category+'_manifest_v1.json');plan=s.load(path)
    bindings=s.load(OUT/('C_DIAGNOSTIC_binding_v1.json' if category=='C_DIAGNOSTIC' else 'manifest_bindings_v1.json'))
    s.require(s.sha256(path)==bindings[category],'Manifest changed')
    auth=s.load(OUT/'authorization_v1.json')
    s.require(auth['authorization_id']==m.AUTH_ID and auth['category_caps']==m.CAPS and auth['maximum_new_attempts']==160,'Authorization changed')
    s.require(plan['category']==category and plan['authorization_id']==m.AUTH_ID and plan['phase']=='P1' and plan['independent_validation'] is False,'Scope violation')
    for key,file in [('materials_sha256','materials_v1.json'),('policy_sha256','measurement_policy_v1.json'),('authorization_sha256','authorization_v1.json')]:
        s.require(s.sha256(OUT/file)==plan[key],'Bound source changed: '+file)
    cases=s.load(OUT/'materials_v1.json')['cases'];m.validate_cases(cases)
    cs={c['case_id']:c for c in cases};rows=plan['requests']
    s.require(len(rows)==len({r['request_id'] for r in rows})==plan['proposed_requests']<=m.CAPS[category],'Inventory count')
    if category=='C_DIAGNOSTIC':
        s.require(s.sha256(Path(plan['diagnostic_policy_path']))==plan['diagnostic_policy_sha256'],'Diagnostic policy changed')
        dp=s.load(plan['diagnostic_policy_path'])
        s.require(dp['automatic_v2_sha256']==s.sha256(Path('tools/p1_measurement_scoring_v2.py')),'Diagnostic scorer changed')
        s.require(len(rows)==16 and {r['case_id'] for r in rows}=={f'p1_measure_calibration_{i:02d}' for i in range(8)},'Diagnostic scope')
        s.require(all(r['condition']=='C0' for r in rows),'Diagnostic factor contamination')
        for cid in {r['case_id'] for r in rows}:s.require({r['diagnostic_arm'] for r in rows if r['case_id']==cid}=={'concise','date_slots'},'Diagnostic arms')
    parent=s.load(s.FROZEN)
    s.require(plan['model']==parent['model'] and plan['template_sha256']==parent['template_sha256'],'Model substitution')
    template=Path(plan['template_path']).read_text(encoding='utf-8')
    s.require(s.sha256(Path(plan['template_path']))==plan['template_sha256'],'Template mismatch')
    for i,(r,log) in enumerate(zip(rows,plan['native_tokenizer_logs'])):
        c=cs[r['case_id']]
        s.require(c['pool']==('factorial' if category=='B_FACTORIAL' else 'calibration'),'Pool violation')
        expected_id=c['case_id']+'_diagnostic_'+r['diagnostic_arm'] if category=='C_DIAGNOSTIC' else c['case_id']+'_'+r['condition']
        s.require(r['order']==i and r['request_id']==expected_id,'Request identity')
        expected_factors=list(m.CELLS[r['condition']]) if r['condition'] in m.CELLS else None
        s.require(r['factors']==expected_factors,'Factor routing')
        expected=m.content(c,r['condition'],c['diagnostic_controls'].get(r['condition']))
        if category=='C_DIAGNOSTIC':
            from p1_measurement_diagnostic import diagnostic_content
            expected=diagnostic_content(c,r['diagnostic_arm'])
            old=next(x for x in s.load(OUT/'A_C0_manifest_v1.json')['requests'] if x['case_id']==c['case_id'])
            s.require(r['parent_request_id']==old['request_id'] and r['parent_request_sha256']==old['request_sha256'],'Diagnostic comparator')
        s.require(r['messages']==[{'role':'user','content':expected}] and r['prompt']==s.render(template,r['messages']),'Prompt assembly')
        s.require(r['reference']==c['reference'] and r['speaker_id']==c['speaker_id'] and r['applicability']==c['applicability'],'References/applicability')
        for k,v in {'seed':42,'temperature':0.,'top_p':1.,'stop':[],'cache_prompt':False,'ignore_eos':False,'parse_special':True,'max_new_tokens':96,'split':'DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION'}.items():
            s.require(r[k]==v,'Unregistered setting: '+k)
        s.require(r['request_sha256']==s.th(json.dumps({k:v for k,v in r.items() if k!='request_sha256'},sort_keys=True,separators=(',',':'))),'Request hash')
        s.require(r['prompt_sha256']==s.th(r['prompt']) and r['input_token_ids_sha256']==s.th(str(r['input_token_ids'])),'Prompt/token hash')
        s.require(len(r['input_token_ids'])==r['input_tokens'] and r['context_remaining']==4096-96-r['input_tokens']>0,'Token capacity')
        s.require(s.sha256(Path(log['path']))==log['sha256'],'Native log changed')
        n=s.load(log['path']);s.require(n['returncode']==0 and n['prompt']==r['prompt'] and ast.literal_eval(n['stdout'].strip())==r['input_token_ids'],'Native tokens differ')
    if category=='A_C0':s.require(all(r['condition']=='C0' for r in rows),'Not C0')
    elif category=='B_FACTORIAL':
        for cid in {r['case_id'] for r in rows}:
            group={r['condition']:r for r in rows if r['case_id']==cid}
            s.require(set(group)==set(m.CELLS)|{'N_style','N_history'},'Factorial cell coverage')
            for k in ('evidence_sha256','reference_sha256','question_sha256','context_sha256','evaluation_date','speaker_id'):
                s.require(len({r[k] for r in group.values()})==1,'Paired invariant changed')
            for control,active in [('N_style','C1'),('N_history','C3')]:
                s.require(group[control]['input_tokens']==group[active]['input_tokens'],'Diagnostic length differs')
    return plan


def preflight(category, resources=True):
    plan=validate(category);cfg=s.config(plan);identity=s.b.file_preflight(cfg)
    s.require(identity['status']=='PASS' and identity['model']['sha256']==s.MODEL_SHA and identity['server']['sha256']==plan['model']['backend_sha256'],'Model/backend identity')
    native=plan['native_tokenizer_identity'];folder=Path(cfg.server_file).parent
    s.require(s.sha256(folder/'llama-tokenize.exe')==native['tokenizer_sha256'],'Tokenizer identity')
    s.require({p.name:s.sha256(p) for p in folder.glob('*.dll')}==native['dll_hashes'],'Native DLL identity')
    mem=s.memory_observation(os.getpid());available=mem.get('system',{}).get('available_physical',0)
    if resources:s.require(available>=3*1024**3,f'RAM preflight: {available} bytes available; at least 3221225472 required. No inference.')
    s.require(shutil.disk_usage('.').free>=1024**3,'Insufficient output reserve')
    if category=='B_FACTORIAL':
        gate=s.load(OUT/'calibration_measurement_gate_v1.json')
        s.require(gate['decision']=='GO_DEVELOPMENT_PILOT' and gate['pilot_manifest_sha256']==s.sha256(OUT/'B_FACTORIAL_manifest_v1.json'),'Scientific readiness gate not passed')
        for p,h in gate['evidence_sha256'].items():s.require(s.sha256(Path(p))==h,'Scientific gate source changed')
    ledger=cumulative()
    return {'status':'PASS','category':category,'checked_utc':s.b.utc_now(),'manifest_sha256':s.sha256(OUT/(category+'_manifest_v1.json')),
        'authorization_sha256':s.sha256(OUT/'authorization_v1.json'),'source_hashes':source_hashes(),'identity':identity,
        'configuration':cfg.as_dict(),'server_command':s.command(plan),'memory_before':mem,'ledger':ledger,
        'live_gate':'All native prompt tokens and effective CPU context configuration verified before completion calls.'}


def inventory(plan,events):
    attempts=[];raw={};results={}
    for e in events:
        d=e['data'];rid=d.get('request_id') if isinstance(d,dict) else None
        if e['kind']=='p1_generation_started':
            s.require(len(attempts)<len(plan['requests']) and d==plan['requests'][len(attempts)],'Unplanned/reordered attempt')
            attempts.append(rid)
        elif e['kind']=='p1_raw_generation':
            s.require(rid in attempts and rid not in raw,'Raw response lineage');raw[rid]=d
        elif e['kind']=='p1_result':
            s.require(rid in raw and rid not in results,'Result lineage');results[rid]=d
    return attempts,raw,results


def run(category, preflight_path):
    fresh=preflight(category);stored=s.load(preflight_path);plan=validate(category)
    for k in ('manifest_sha256','authorization_sha256','source_hashes','configuration','server_command'):
        s.require(fresh[k]==stored[k],'Preflight binding changed: '+k)
    with s.b.writer_lock(ROOT):
        ledger=cumulative();cp=ROOT/'claims'/(category+'.json')
        s.require(not cp.exists(),'This batch has a prior allocation; no repeat or automatic retry')
        s.require(len(plan['requests'])<=ledger['remaining_unreserved'][category],'Insufficient category authorization')
        claim={'authorization_id':m.AUTH_ID,'category':category,'maximum_attempts':len(plan['requests']),
               'manifest_sha256':fresh['manifest_sha256'],'preflight_sha256':s.sha256(preflight_path),'source_hashes':fresh['source_hashes']}
        s.save(cp,claim)
        journal=s.b.RunJournal(ROOT/'runs',{'phase':'P1 measurement development','category':category,'claim':claim,
            'authorization':s.load(OUT/'authorization_v1.json'),'frozen_manifest':plan,'configuration':s.config(plan).as_dict(),
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_status':subprocess.check_output(['git','status','--short'],text=True),'python':platform.python_version(),'platform':platform.platform()})
        for path,digest in fresh['source_hashes'].items():
            dest=journal.directory/'source_snapshot'/path;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(Path(path).read_bytes())
            s.require(s.sha256(dest)==digest,'Source snapshot mismatch')
        active=None;status='BLOCKED';tick=time.monotonic()
        try:
            journal.write('preflight',fresh)
            with s.Server(plan,journal) as server:
                client=s.b.LlamaClient(s.config(plan).endpoint,timeout=180,audit=journal.write)
                props=client.request('/props');v=s.b.validate_server_properties(props,s.config(plan))
                s.require(v['build_info']=='b11573-0f701c882','Runtime backend mismatch')
                journal.write('effective_server_defaults',{'props':props,'validation':v})
                for r in plan['requests']:
                    ids=client.request('/tokenize',{'content':r['prompt'],'add_special':True,'parse_special':True,'with_pieces':False})['tokens']
                    s.require(ids==r['input_token_ids'],'Live tokenizer mismatch; no generation permitted')
                    journal.write('live_prompt_verified',{'request_id':r['request_id'],'token_hash':s.th(str(ids))})
                print(json.dumps({'live_preflight':'PASS','category':category,'requests':len(plan['requests'])}),flush=True)
                for r in plan['requests']:
                    remaining=3600-(time.monotonic()-tick);s.require(remaining>0,'Batch time ceiling reached')
                    server.assert_running();client.timeout=min(180,remaining);active=r['request_id']
                    # Exclusive durable attempt reservation precedes the potentially ambiguous HTTP call.
                    s.save(ROOT/'attempts'/(active+'.json'),{'authorization_id':m.AUTH_ID,'category':category,'request_id':active,
                        'request_sha256':r['request_sha256'],'reserved_utc':s.b.utc_now(),'run_directory':journal.directory.as_posix()})
                    journal.write('p1_generation_started',r)
                    t=time.monotonic();response=client.request('/completion',s.payload(r));elapsed=time.monotonic()-t
                    journal.write('p1_raw_generation',{'request_id':active,'response':response,'latency_seconds':elapsed})
                    result=s.f.result(r,response,elapsed);journal.write('p1_result',result)
                    journal.write('memory_observation',s.memory_observation(server.process.pid))
                    print(json.dumps({'order':r['order'],'request_id':active,'tokens':result['generated_tokens'],
                                      'stop':result['stop_reason'],'seconds':round(elapsed,2),'text':result['raw_response']}),flush=True)
                    active=None
                after=preflight(category,False)
                s.require(after['identity']==fresh['identity'] and after['source_hashes']==fresh['source_hashes'],'Postflight source/binary change')
                journal.write('postflight',after)
            status='PASS'
        except BaseException as exc:
            status='PARTIAL' if active else 'BLOCKED';journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_id':active})
        a,raw,res=inventory(plan,s.b.read_events(journal.directory))
        summary={'status':status,'category':category,'attempted':len(a),'responses_received':len(raw),'results':len(res),
                 'elapsed_seconds':time.monotonic()-tick,'run_directory':journal.directory.as_posix(),'human_semantic_ratings':0,'cumulative':cumulative()}
        journal.finish(**summary);s.save(journal.directory/'summary.json',summary)
        return summary


def audit(category):
    plan=validate(category)
    runs=[p for p in (ROOT/'runs').glob('*') if s.load(p/'manifest.json')['category']==category]
    s.require(len(runs)==1,'Expected exactly one batch run')
    folder=runs[0];events=s.b.read_events(folder);attempts,raw,res=inventory(plan,events)
    sent=[e['data']['payload'] for e in events if e['kind']=='http_request' and e['data']['route']=='/completion']
    s.require(sent==[s.payload(r) for r in plan['requests'][:len(attempts)]],'HTTP inventory differs')
    bodies=[json.loads(base64.b64decode(e['data']['body_base64'])) for e in events if e['kind']=='http_response' and e['data']['route']=='/completion' and e['data'].get('status')==200]
    s.require(bodies==[r['response'] for r in raw.values()],'Raw HTTP preservation failure')
    rows=[]
    for r in plan['requests']:
        rid=r['request_id'];v=s.f.result(r,raw[rid]['response'],raw[rid]['latency_seconds']) if rid in raw else None
        if rid in res:s.require(res[rid]==v,'Derived result changed')
        rows.append({'request':r,'result':v,'state':'COMPLETED' if rid in res else 'ATTEMPTED_UNRESOLVED' if rid in attempts else 'UNATTEMPTED'})
    return {'category':category,'manifest_sha256':s.sha256(OUT/(category+'_manifest_v1.json')),'run_directory':folder.as_posix(),
            'attempted':len(attempts),'results':len(res),'rows':rows,'cumulative':cumulative(),'new_generations':0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['preflight','run','audit','ledger'])
    p.add_argument('--category',choices=list(m.CAPS));p.add_argument('--output',type=Path);p.add_argument('--preflight',type=Path);a=p.parse_args()
    try:
        if a.action=='run':v=run(a.category,a.preflight)
        elif a.action=='preflight':v=preflight(a.category)
        elif a.action=='audit':v=audit(a.category)
        else:v=cumulative()
    except Exception as exc:
        v={'status':'BLOCKED','action':a.action,'category':a.category,'error':str(exc),'recorded_utc':s.b.utc_now(),
           'memory':s.memory_observation(os.getpid()),'new_generations':0}
        if a.output:s.save(a.output,v)
        print(json.dumps(v,indent=2));raise SystemExit(2)
    if a.output:s.save(a.output,v)
    print(json.dumps({k:x for k,x in v.items() if k not in ('rows','identity','source_hashes')},indent=2))
