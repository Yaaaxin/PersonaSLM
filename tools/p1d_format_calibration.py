"""Hash-bound 16-attempt format diagnostic. No retries, inference outside run, or source edits."""
import argparse
import base64
from collections import defaultdict
import json
from pathlib import Path
import platform
import shutil
import subprocess
import time
import p1d_budget_calibration as b
from p1d_format_diagnostic_proposal import reframe

MANIFEST = Path('docs/validation/p1d/final_preparation_v1/format_diagnostic_manifest_proposed_v1.json')
MANIFEST_SHA = '3f0e68b0fbe4cf5abfeab3bef9f6fbc39460b9219d118500ccc10d6fda121523'
OUT = Path('docs/validation/p1d/format_calibration_v1')
ROOT = Path('results/p1d_format_calibration/development_v1')
FROZEN = OUT/'frozen_manifest_v1.json'
AUTH = OUT/'researcher_authorization_v1.json'
STOPS = ['\nUser:', '\nAssistant:', '\nUSER:', '\nASSISTANT:']
ARMS = ['F_user_marker', 'F_user_marker_stops']
load, save, require, sha256, th = b.load, b.save, b.require, b.sha256, b.th

def source_hashes():
    paths = list(Path('src/personaslm').glob('*.py')) + [Path('tools/p1d_format_calibration.py'),
        Path('tools/p1d_budget_calibration.py'),Path('tools/p1d_format_diagnostic_proposal.py'),Path('configs/p1_wave1_v1.json')]
    return {p.as_posix():sha256(p) for p in sorted(paths)}

def validate_plan(plan):
    require(plan['version']=='p1d_format_diagnostic_proposed_v1' and plan['proposed_requests']==16,'Wrong proposal')
    require(sha256(b.FROZEN)==plan['source_budget_manifest_sha256']==b.MANIFEST_SHA,'Historical manifest changed')
    old = load(b.FROZEN)
    b.validate_plan(old)
    require(plan['model']==old['model'] and plan['native_tokenizer_identity']==load(MANIFEST)['native_tokenizer_identity'],'Model/tokenizer changed')
    require(plan['source_qualification_sha256']==sha256(b.OUT/'analysis_v1/budget_qualification_v1.json'),'Qualification source changed')
    require(plan['source_format_comparison_sha256']==sha256(MANIFEST.parent/'frozen_prompt_format_comparison_v1.json'),'Format source changed')
    cases = {c['case_id']:c for c in load(b.DEV/'development_examples_v5.json')['cases']}
    heldout = {c['case_id'] for c in load('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')['cases']}
    refs = {r['request_id']:r for r in old['requests']}
    rows = plan['requests']; groups=defaultdict(list)
    require(len(rows)==len({r['request_id'] for r in rows})==16,'Request count/uniqueness')
    require({r['case_id'] for r in rows}==set(b.CASE_IDS) and not heldout.intersection(b.CASE_IDS),'Development identity/overlap')
    for i,r in enumerate(rows):
        require(r['order']==i and r['condition']=='H_none' and r['max_new_tokens']==96,'Order/condition/cap')
        require(r['diagnostic_arm'] in ARMS,'Unknown arm')
        require(r['request_id']==f"p1d_format_dev_v1_{r['case_id']}_{r['diagnostic_arm']}",'Request ID')
        require(r['request_sha256']==th(json.dumps({k:v for k,v in r.items() if k!='request_sha256'},sort_keys=True,separators=(',',':'))),'Request hash')
        c=cases[r['case_id']]; prev=refs[r['historical_comparator_request_id']]
        require(c['independent_validation'] is False and c['split']=='DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION','Not development')
        require(prev['condition']=='H_none' and prev['max_new_tokens']==96 and prev['case_id']==r['case_id'],'Wrong historical match')
        require(r['historical_comparator_request_sha256']==prev['request_sha256'],'Historical request changed')
        require(r['prompt']==reframe(prev['prompt'],c['question']) and r['prompt_sha256']==th(r['prompt']),'Prompt changed')
        for key in ('speaker_id','reference','reference_sha256','evidence_sha256','question_sha256','context_sha256','seed','temperature','top_p','cache_prompt'):
            require(r[key]==prev[key],'Scientific/decode input differs: '+key)
        require(r['stop']==([] if r['diagnostic_arm']==ARMS[0] else STOPS),'Unregistered stops')
        require(len(r['input_token_ids'])==r['input_tokens'] and th(str(r['input_token_ids']))==r['input_token_ids_sha256'],'Token hash/count')
        require(r['context_remaining']==4096-r['input_tokens']-96 and r['context_remaining']>=0,'Context overflow')
        groups[r['case_id']].append(r)
    for rows in groups.values():
        require({r['diagnostic_arm'] for r in rows}==set(ARMS),'Missing arm')
        omit={'order','request_id','request_sha256','diagnostic_arm','stop'}
        require({k:v for k,v in rows[0].items() if k not in omit}=={k:v for k,v in rows[1].items() if k not in omit},'Arms differ beyond stops')
    tokenlog=load(MANIFEST.parent/'format_diagnostic_tokenizer_validation_v1.json')
    require(tokenlog['actual_native_calls']==8,'Wrong native tokenizer inventory')
    for rec in tokenlog['logs']:require(sha256(Path(rec['path']))==rec['sha256'],'Native tokenizer log changed')
    return {'requests':16,'cases':8,'speakers':8,'unique_prompts':8,'heldout_overlap':0,
        'within_new_pair_change':'stop strings only','historical_change':'current User marker and optionally stops',
        'input_tokens':[min(r['input_tokens'] for r in plan['requests']),max(r['input_tokens'] for r in plan['requests'])]}

def register():
    require(sha256(MANIFEST)==MANIFEST_SHA,'AUTHORIZED MANIFEST HASH MISMATCH: no inference')
    checks=validate_plan(load(MANIFEST))
    require(not FROZEN.exists() and not AUTH.exists(),'Existing registration must be preserved')
    OUT.mkdir(parents=True,exist_ok=True)
    with FROZEN.open('xb') as f:f.write(MANIFEST.read_bytes())
    save(AUTH,{'version':'p1d_format_authorization_v1','researcher':'Yaxin ZHENG','decision':'AUTHORIZED',
        'decision_source':'Explicit user instruction: PersonaSLM — P1d Format Diagnosis, Model Readiness and Scientific Acceleration',
        'researcher_decision_timestamp':None,'registered_utc':b.utc_now(),'manifest_sha256':MANIFEST_SHA,
        'maximum_attempts':16,'scope':'Eight registered development cases, H_none, two frozen format/stop configurations, 96-token cap, Base CPU only.',
        'prohibited':['additional retries or generations','Instruct inference','independent validation cohort','training'],
        'semantic_adoption':'No adoption of prior 144 AI assessments or future format assessments.',
        'original_proposal_status':'Preserved; this separate explicit authorization is operative.','checks':checks})
    tracked=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
    save(OUT/'historical_preservation_baseline_v1.json',{'created_utc':b.utc_now(),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'tracked_sha256':{p:sha256(Path(p)) for p in tracked if p and Path(p).is_file()}})
    return {'status':'REGISTERED',**checks}

def preflight():
    require(sha256(MANIFEST)==sha256(FROZEN)==MANIFEST_SHA,'Authorized manifest changed')
    auth=load(AUTH)
    require(auth['decision']=='AUTHORIZED' and auth['maximum_attempts']==16 and auth['manifest_sha256']==MANIFEST_SHA,'Authorization mismatch')
    plan=load(FROZEN); checks=validate_plan(plan); model=plan['model']
    require(sha256(Path(model['source_config']))==model['source_config_sha256'],'Config changed')
    config=b.RuntimeConfig.load(Path(model['source_config'])); identity=b.file_preflight(config)
    require(identity['status']=='PASS' and identity['model']['sha256']==model['model_sha256'] and identity['server']['sha256']==model['backend_sha256'],'Binary mismatch')
    require(config.threads==4 and config.n_ctx==4096 and config.seed==42 and config.max_new_tokens==96,'Runtime mismatch')
    directory=Path(config.server_file).parent; native=plan['native_tokenizer_identity']
    require(sha256(directory/'llama-tokenize.exe')==native['tokenizer_sha256'],'Tokenizer mismatch')
    require({p.name:sha256(p) for p in directory.glob('*.dll')}==native['dll_hashes'],'DLL mismatch')
    require(shutil.disk_usage('.').free>=1024**3,'Insufficient log reserve')
    return {'status':'PASS','checked_utc':b.utc_now(),'checks':checks,'identity':identity,
        'manifest_sha256':MANIFEST_SHA,'authorization_sha256':sha256(AUTH),'source_hashes':source_hashes(),
        'live_gate':'Eight prompt token arrays must match before any completion.'}

def payload(row):
    return {'prompt':row['input_token_ids'],'n_predict':96,'temperature':0.0,'top_p':1.0,'seed':row['seed'],
        'cache_prompt':False,'stop':row['stop'],'return_tokens':True,'stream':False}

def result(row,response,latency):
    audit=b.validate_completion(response,row['input_token_ids']); normal=b.normalize_result(response)
    n=response.get('tokens_predicted')
    require(type(n) is int and 0<=n<=96,'Invalid generated count')
    # Stop strings can remove suffix token IDs. Retain native count and returned IDs separately.
    returned=len(normal['generated_token_ids']) if normal['generated_token_ids'] is not None else None
    require(returned is None or returned<=n,'Returned token count exceeds generated count')
    if normal['stop_reason']!='stop_sequence' and normal['token_ids_status']=='returned':require(returned==n,'Token count mismatch')
    if normal['stop_reason']=='stop_sequence':require(normal['raw_termination'].get('stopping_word') in row['stop'],'Undeclared stop')
    boundary=b.classify_response(normal['raw_response'],normal['raw_termination'],declared_stops=row['stop'])
    return {'request_id':row['request_id'],'request_sha256':row['request_sha256'],**normal,'generated_tokens':n,
        'returned_token_count':returned,'native_minus_returned_tokens':None if returned is None else n-returned,
        'latency_seconds':latency,'input_token_audit':audit,'response_status':boundary,
        'raw_text_sha256':th(normal['raw_response']),'first_reply_sha256':th(boundary['first_span']['text']),
        'semantic_status':'AI_ASSESSMENT_PENDING_NO_HUMAN_RATINGS'}

def inventory(plan,events):
    attempted=[]; raw={}; results={}
    for e in events:
        d=e['data']
        if e['kind']=='format_generation_started':
            require(len(attempted)<16 and d==plan['requests'][len(attempted)],'Repeated/unplanned/reordered attempt')
            attempted.append(d['request_id'])
        elif e['kind']=='format_raw_generation':
            rid=d['request_id'];require(rid in attempted and rid not in raw,'Unbound raw');raw[rid]=d
        elif e['kind']=='format_result':
            rid=d['request_id'];require(rid in raw and rid not in results,'Unbound result');results[rid]=d
    return attempted,raw,results

def run(preflight_path):
    fresh=preflight(); prepared=load(preflight_path); plan=load(FROZEN)
    for k in ('source_hashes','manifest_sha256','authorization_sha256'):require(fresh[k]==prepared[k],'Preflight binding changed: '+k)
    config=b.RuntimeConfig.load(Path(plan['model']['source_config']))
    with b.writer_lock(ROOT):
        require(not (ROOT/'claim.json').exists() and not list((ROOT/'runs').glob('*')),'Existing attempt allocation: refuse rerun/retry')
        claim={k:fresh[k] for k in ('source_hashes','manifest_sha256','authorization_sha256')}
        claim.update(preflight_sha256=sha256(preflight_path),maximum_attempts=16)
        save(ROOT/'claim.json',claim)
        journal=b.RunJournal(ROOT/'runs',{'phase':'P1d authorized development format diagnostic','claim':claim,
            'frozen_manifest':plan,'authorization':load(AUTH),'configuration':config.as_dict(),
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'python':platform.python_version(),'platform':platform.platform()})
        for p,digest in claim['source_hashes'].items():
            dest=journal.directory/'source_snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(Path(p).read_bytes())
            require(sha256(dest)==digest,'Source copy mismatch')
        started=time.monotonic(); active=None; status='BLOCKED'
        try:
            journal.write('preflight',fresh)
            with b.ManagedServer(config,journal) as server:
                client=b.LlamaClient(config.endpoint,timeout=config.timeout,audit=journal.write)
                props=client.request('/props');binding=b.validate_server_properties(props,config)
                require(binding['build_info']=='b11573-0f701c882','Wrong backend build')
                journal.write('effective_server_defaults',{'props':props,'validation':binding})
                seen=set()
                for row in plan['requests']:
                    if row['prompt_sha256'] in seen:continue
                    require(client.tokenize(row['prompt'])==row['input_token_ids'],'Live tokenizer mismatch')
                    journal.write('live_prompt_verified',{'prompt_sha256':row['prompt_sha256'],'input_token_ids_sha256':row['input_token_ids_sha256']})
                    seen.add(row['prompt_sha256'])
                require(len(seen)==8,'Wrong live prompt count')
                journal.write('live_preflight_pass',{'prompts':8,'planned_requests':16})
                print(json.dumps({'live_preflight':'PASS','pending':16}),flush=True)
                for row in plan['requests']:
                    require(time.monotonic()-started<45*60,'45-minute ceiling; preserve unattempted suffix')
                    server.assert_running();active=row['request_id'];journal.write('format_generation_started',row)
                    t=time.monotonic();response=client.request('/completion',payload(row));latency=time.monotonic()-t
                    journal.write('format_raw_generation',{'request_id':active,'response':response,'latency_seconds':latency})
                    derived=result(row,response,latency);journal.write('format_result',derived)
                    print(json.dumps({'order':row['order'],'arm':row['diagnostic_arm'],'tokens':derived['generated_tokens'],'stop':derived['stop_reason'],'status':derived['response_status']['status'],'seconds':round(latency,2)}),flush=True)
                    active=None
                server.assert_running();b.validate_server_properties(client.request('/props'),config)
                after=preflight();require(after['identity']==fresh['identity'] and after['source_hashes']==fresh['source_hashes'],'Postflight changed')
                journal.write('postflight',after)
            status='PASS'
        except BaseException as exc:
            status='PARTIAL' if active else 'BLOCKED'
            journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_id':active})
        events=b.read_events(journal.directory); attempted,raw,results=inventory(plan,events)
        summary={'status':status,'attempted':len(attempted),'responses_received':len(raw),'results':len(results),
            'elapsed_seconds':time.monotonic()-started,'run_directory':journal.directory.as_posix(),'human_semantic_ratings':0}
        journal.finish(**summary);save(journal.directory/'summary.json',summary)
        return summary

def audit():
    require(sha256(MANIFEST)==sha256(FROZEN)==MANIFEST_SHA,'Manifest changed')
    folders=list((ROOT/'runs').glob('*'));require(len(folders)==1,'Unexpected run count')
    folder=folders[0];events=b.read_events(folder);plan=load(FROZEN)
    require(load(folder/'manifest.json')['claim']==load(ROOT/'claim.json'),'Claim changed')
    attempted,raw,results=inventory(plan,events)
    requests=[e['data']['payload'] for e in events if e['kind']=='http_request' and e['data']['route']=='/completion']
    require(requests==[payload(r) for r in plan['requests'][:len(attempted)]],'Actual payload changed')
    bodies=[json.loads(base64.b64decode(e['data']['body_base64'])) for e in events if e['kind']=='http_response' and e['data']['route']=='/completion' and e['data'].get('status')==200]
    require(bodies==[r['response'] for r in raw.values()],'Raw HTTP body mismatch')
    rows=[]
    for row in plan['requests']:
        rid=row['request_id'];derived=result(row,raw[rid]['response'],raw[rid]['latency_seconds']) if rid in raw else None
        if rid in results:require(derived==results[rid],'Result reconstruction mismatch')
        rows.append({'request':row,'result':derived,'state':'COMPLETED' if rid in results else 'RAW_RECOVERABLE' if rid in raw else 'ATTEMPTED_UNRESOLVED' if rid in attempted else 'UNATTEMPTED'})
    return {'version':'p1d_format_execution_integrity_v1','manifest_sha256':MANIFEST_SHA,'attempted':len(attempted),
        'results':len(results),'raw_responses':len(raw),'http_responses_verified':len(bodies),'run_directory':folder.as_posix(),
        'rows':rows,'new_generations':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['register','preflight','run','audit'])
    parser.add_argument('--output',type=Path);parser.add_argument('--preflight',type=Path);args=parser.parse_args()
    if args.action=='register':value=register()
    elif args.action=='run':
        if not args.preflight:parser.error('--preflight required')
        value=run(args.preflight)
    else:
        if not args.output:parser.error('--output required')
        value=preflight() if args.action=='preflight' else audit();save(args.output,value)
    print(json.dumps({k:v for k,v in value.items() if k not in ('rows','identity','source_hashes')},indent=2))
    if value.get('status') in ('PARTIAL','BLOCKED'):raise SystemExit(2)
