"""Exactly authorized 144-request development calibration; no retries or smoke generations."""
import argparse
import base64
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import time

from personaslm.configuration import RuntimeConfig, preflight as file_preflight
from personaslm.inference import LlamaClient, normalize_result
from personaslm.journal import RunJournal, atomic_json, read_events, utc_now
from personaslm.p1b_calibration import writer_lock
from personaslm.provenance import sha256
from personaslm.response_status import classify_response
from personaslm.runner import validate_completion
from personaslm.server import ManagedServer, validate_server_properties

VERSION = 'p1d_budget_calibration_runner_v1'
MANIFEST = Path('docs/validation/p1d/scientific_validation_v1/budget_calibration_manifest_candidate_v2.json')
MANIFEST_SHA = '510e46b214dda23dea2a3e5462d44982d25b7a9db022626a7a5a1ba504d5e039'
OUT = Path('docs/validation/p1d/budget_calibration_v1')
AUTH = OUT / 'researcher_authorization_v1.json'
FROZEN = OUT / 'frozen_manifest_v2.json'
ROOT = Path('results/p1d_budget_calibration/development_v1')
DEV = Path('docs/validation/p1d/development_readiness_v1')
CELLS = ['E0V0','E0V1','E1V0','E1V1','D_procedural','H_none']
CASE_IDS = [f'p1d_dev_{i:02d}_{0 if i < 4 else 1}' for i in range(8)]

def require(value, message):
    if not value: raise ValueError(message)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def th(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()

def save(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    atomic_json(Path(path), obj)

def source_hashes():
    paths = sorted(Path('src/personaslm').glob('*.py')) + [Path(__file__),Path('configs/p1_wave1_v1.json')]
    return {p.as_posix() if not p.is_absolute() else p.relative_to(Path.cwd()).as_posix():sha256(p) for p in paths}

def validate_plan(plan):
    require(plan['version']=='p1d_budget_manifest_candidate_v2','Wrong version')
    cases = {c['case_id']:c for c in load(DEV/'development_examples_v5.json')['cases']}
    candidates = load('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')['cases']
    heldout = {c['case_id'] for c in candidates}
    prompts = {(p['case_id'],p['condition']):p for p in load(DEV/'development_prompts_v5.json')}
    rows=plan['requests']; require(len(rows)==144,'Wrong request count')
    require(len({r['request_id'] for r in rows})==144,'Duplicate ID')
    require({r['case_id'] for r in rows}==set(CASE_IDS),'Development identities differ')
    require(not heldout.intersection(CASE_IDS),'Held-out case contamination')
    grouped=defaultdict(list)
    for i,r in enumerate(rows):
        require(r['order']==i,'Execution order differs')
        require(r['condition'] in CELLS and r['max_new_tokens'] in (96,192,256),'Allocation differs')
        c=cases[r['case_id']]; p=prompts[r['case_id'],r['condition']]
        require(c['independent_validation'] is False and c['split']=='DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION','Not development')
        require(r['request_id']==f"p1d_budget_dev_v1_{r['case_id']}_{r['condition']}_b{r['max_new_tokens']}",'Request identity differs')
        require(r['request_sha256']==th(json.dumps({k:v for k,v in r.items() if k!='request_sha256'},sort_keys=True,separators=(',',':'))),'Request digest differs')
        for k in ('prompt','prompt_sha256','input_token_ids','input_tokens','speaker_id','reference','reference_sha256'):
            require(r[k]==p[k],'Source prompt differs: '+k)
        require(r['prompt_sha256']==th(r['prompt']),'Prompt digest differs')
        require(r['input_token_ids_sha256']==th(str(r['input_token_ids'])),'Token digest differs')
        require(len(r['input_token_ids'])==r['input_tokens'],'Token count differs')
        require(r['evidence_sha256']==th(c['trusted_evidence']) and r['question_sha256']==th(c['question']) and r['context_sha256']==th(c['fixed_context']),'Scientific inputs differ')
        require(r['reference']==c['required_components'],'Answer differs')
        require(r['seed']==42 and r['temperature']==0 and r['top_p']==1 and r['cache_prompt'] is False and r['stop']==[],'Decoding changed')
        require(r['input_tokens']+r['max_new_tokens']<=4096,'Context overflow')
        grouped[r['case_id'],r['condition']].append(r)
    require(len(grouped)==48,'Wrong paired blocks')
    for group in grouped.values():
        require(sorted(r['max_new_tokens'] for r in group)==[96,192,256],'Missing budget')
        invariant=[{k:v for k,v in r.items() if k not in ('order','request_id','request_sha256','max_new_tokens','context_remaining')} for r in group]
        require(all(r==invariant[0] for r in invariant),'Budget groups not comparable')
    return {'requests':144,'development_cases':8,'speakers':len({r['speaker_id'] for r in rows}),'unique_prompts':48,'heldout_overlap':0,'input_tokens':[min(r['input_tokens'] for r in rows),max(r['input_tokens'] for r in rows)]}

def register():
    require(sha256(MANIFEST)==MANIFEST_SHA,'AUTHORIZED MANIFEST HASH MISMATCH: stop inference')
    plan=load(MANIFEST); checks=validate_plan(plan)
    require(not AUTH.exists() and not FROZEN.exists(),'Authorization/freeze already exists')
    OUT.mkdir(parents=True,exist_ok=True)
    with FROZEN.open('xb') as f: f.write(MANIFEST.read_bytes())
    require(sha256(FROZEN)==MANIFEST_SHA,'Freeze copy mismatch')
    save(AUTH,{'version':'p1d_budget_researcher_authorization_v1','researcher':'Yaxin ZHENG',
        'decision':'AUTHORIZED','decision_source':'Explicit user instruction: PersonaSLM — P1d Bounded CPU Calibration, Scientific Validation and Final Execution Preparation',
        'researcher_decision_timestamp':None,'registered_utc':utc_now(),'manifest_path':MANIFEST.as_posix(),
        'manifest_sha256':MANIFEST_SHA,'frozen_copy':FROZEN.as_posix(),'maximum_attempts':144,
        'scope':'Exactly eight registered development cases x six conditions x budgets 96, 192, 256; Base CPU only.',
        'prohibited':['1728 independent Base requests','288 Instruct requests','additional generation or training','silent retries'],
        'conditions':'Successful mandatory preflight; unchanged inputs/settings except registered output caps; no automatic main-policy amendment.',
        'original_manifest_status':'Preserved historical proposal status; this separate authorization is operative.', 'checks':checks})
    tracked=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
    save(OUT/'historical_preservation_baseline_v1.json',{'created_utc':utc_now(),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'status':subprocess.check_output(['git','status','--short'],text=True),
        'tracked_sha256':{p:sha256(Path(p)) for p in tracked if p and Path(p).is_file()}})
    return {'status':'REGISTERED','manifest_sha256':MANIFEST_SHA,**checks}

def preflight():
    require(sha256(MANIFEST)==sha256(FROZEN)==MANIFEST_SHA,'Authorized manifest integrity failure')
    auth=load(AUTH);require(auth['decision']=='AUTHORIZED' and auth['maximum_attempts']==144 and auth['manifest_sha256']==MANIFEST_SHA,'Authorization mismatch')
    plan=load(FROZEN);checks=validate_plan(plan)
    for path,digest in plan['source_sha256'].items():require(sha256(Path(path))==digest,'Changed source: '+path)
    model=plan['model'];config=RuntimeConfig.load(Path(model['source_config']))
    require(sha256(Path(model['source_config']))==model['source_config_sha256'],'Configuration changed')
    identity=file_preflight(config);require(identity['status']=='PASS','Model/backend preflight failed')
    require(identity['model']['sha256']==model['model_sha256'] and identity['server']['sha256']==model['backend_sha256'],'Binary identity differs')
    require(config.threads==4 and config.n_ctx==4096 and config.seed==42 and config.max_new_tokens==96,'Runtime differs')
    directory=Path(config.server_file).parent
    require(sha256(directory/'llama-tokenize.exe')==plan['native_tokenizer_identity']['tokenizer_sha256'],'Tokenizer differs')
    require({p.name:sha256(p) for p in directory.glob('*.dll')}==plan['native_tokenizer_identity']['dll_hashes'],'DLL set differs')
    require(shutil.disk_usage('.').free>=1024**3,'Insufficient log reserve')
    return {'version':VERSION,'status':'PASS','checked_utc':utc_now(),'checks':checks,'identity':identity,
            'source_hashes':source_hashes(),'manifest_sha256':MANIFEST_SHA,'authorization_sha256':sha256(AUTH),
            'live_gate':'All 48 unique prompt token arrays must match owned backend before any completion.'}

def result(row,response,latency):
    audit=validate_completion(response,row['input_token_ids']);normal=normalize_result(response)
    n=response.get('tokens_predicted');require(type(n) is int and 0<=n<=row['max_new_tokens'],'Invalid generated count')
    if normal['token_ids_status']=='returned':require(len(normal['generated_token_ids'])==n,'Generated token count differs')
    boundary=classify_response(normal['raw_response'],normal['raw_termination'],declared_stops=())
    return {'request_id':row['request_id'],'request_sha256':row['request_sha256'],**normal,'generated_tokens':n,
        'latency_seconds':latency,'input_token_audit':audit,'response_status':boundary,
        'raw_text_sha256':th(normal['raw_response']),'first_reply_sha256':th(boundary['first_span']['text']),
        'semantic_status':'AI_ASSESSMENT_PENDING_NO_HUMAN_RATINGS'}

def inventory(plan,histories):
    attempted=[];raw={};results={}
    for events in histories:
        for e in events:
            k=e['kind'];d=e['data']
            if k=='p1d_budget_generation_started':
                require(len(attempted)<144 and d==plan['requests'][len(attempted)],'Repeated/reordered/unplanned attempt')
                attempted.append(d['request_id'])
            elif k=='p1d_budget_raw_generation':
                rid=d['request_id'];require(rid in attempted and rid not in raw,'Unbound/duplicate raw');raw[rid]=d
            elif k=='p1d_budget_result':
                rid=d['request_id'];require(rid in raw and rid not in results,'Unbound/duplicate result');results[rid]=d
    return attempted,raw,results

def run(preflight_path,resume=False):
    fresh=preflight();prepared=load(preflight_path);plan=load(FROZEN)
    for k in ('source_hashes','manifest_sha256','authorization_sha256'):
        require(prepared[k]==fresh[k],'Preflight binding changed: '+k)
    config=RuntimeConfig.load(Path(plan['model']['source_config']))
    with writer_lock(ROOT):
        claim={k:fresh[k] for k in ('source_hashes','manifest_sha256','authorization_sha256')}
        claim.update(preflight_sha256=sha256(preflight_path),maximum_attempts=144)
        if (ROOT/'claim.json').exists():require(resume and load(ROOT/'claim.json')==claim,'Existing claim requires identical explicit resume')
        else:
            require(not resume and not list((ROOT/'runs').glob('*')),'Unexplained run history')
            save(ROOT/'claim.json',claim)
        previous=sorted((ROOT/'runs').glob('*'));histories=[];links=[]
        for folder in previous:
            m=load(folder/'manifest.json');require(m['claim']==claim and m['prior_segments']==links,'Segment binding mismatch')
            histories.append(read_events(folder));links.append({'path':folder.as_posix(),'manifest_sha256':sha256(folder/'manifest.json'),'events':{p.name:sha256(p) for p in (folder/'events').glob('*.json')}})
        attempted,raw,results=inventory(plan,histories)
        require(set(attempted)==set(raw)==set(results),'Unresolved attempted request: no automatic resume')
        pending=plan['requests'][len(attempted):];require(pending,'Allocation exhausted; no rerun')
        journal=RunJournal(ROOT/'runs',{'phase':'P1d development budget calibration','version':VERSION,'claim':claim,
            'prior_segments':links,'frozen_manifest':plan,'authorization':load(AUTH),'configuration':config.as_dict(),
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_status':subprocess.check_output(['git','status','--short'],text=True),'python':platform.python_version(),'platform':platform.platform()})
        for path,digest in claim['source_hashes'].items():
            target=journal.directory/'source_snapshot'/path;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(Path(path).read_bytes())
            require(sha256(target)==digest,'Source copy differs')
        active=None;status='BLOCKED';started_run=time.monotonic()
        previous_elapsed=sum(e['data'].get('elapsed_seconds',0) for h in histories for e in h if e['kind']=='run_finished')
        try:
            journal.write('preflight',fresh)
            with ManagedServer(config,journal) as server:
                client=LlamaClient(config.endpoint,timeout=config.timeout,audit=journal.write)
                props=client.request('/props');binding=validate_server_properties(props,config)
                require(binding['build_info']=='b11573-0f701c882','Backend build changed')
                journal.write('effective_server_defaults',{'props':props,'validation':binding,'overrides':'LlamaClient.complete pinned payload; per-request n_predict only planned variation'})
                seen=set()
                for row in plan['requests']:
                    if row['prompt_sha256'] in seen:continue
                    require(client.tokenize(row['prompt'])==row['input_token_ids'],'Live tokenizer mismatch')
                    journal.write('p1d_budget_live_prompt_verified',{'prompt_sha256':row['prompt_sha256'],'input_token_ids_sha256':row['input_token_ids_sha256'],'input_tokens':row['input_tokens']})
                    seen.add(row['prompt_sha256'])
                require(len(seen)==48,'Wrong unique prompt count')
                journal.write('live_preflight_pass',{'unique_prompts':48,'planned_requests':144,'generation_attempts_so_far':len(attempted)})
                print(json.dumps({'live_preflight':'PASS','unique_prompts':48,'pending':len(pending)}),flush=True)
                for row in pending:
                    require(time.monotonic()-started_run+previous_elapsed<6*3600,'Six-hour ceiling; preserve unattempted suffix')
                    server.assert_running();active=row['request_id']
                    journal.write('p1d_budget_generation_started',row)
                    start=time.monotonic();response=client.complete(row['input_token_ids'],seed=row['seed'],max_new_tokens=row['max_new_tokens']);latency=time.monotonic()-start
                    journal.write('p1d_budget_raw_generation',{'request_id':active,'response':response,'latency_seconds':latency})
                    derived=result(row,response,latency);journal.write('p1d_budget_result',derived)
                    print(json.dumps({'completed_order':row['order'],'budget':row['max_new_tokens'],'status':derived['response_status']['status'],'tokens':derived['generated_tokens'],'seconds':round(latency,2)}),flush=True)
                    active=None
                server.assert_running();validate_server_properties(client.request('/props'),config)
                after=preflight();require(after['identity']==fresh['identity'] and after['source_hashes']==fresh['source_hashes'],'Postflight changed')
                journal.write('postflight',after)
            status='PASS'
        except BaseException as exc:
            status='PARTIAL' if active else 'BLOCKED'
            journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_id':active})
        events=read_events(journal.directory)
        summary={'status':status,'attempted':sum(e['kind']=='p1d_budget_generation_started' for e in events),
            'responses_received':sum(e['kind']=='p1d_budget_raw_generation' for e in events),'results':sum(e['kind']=='p1d_budget_result' for e in events),
            'elapsed_seconds':time.monotonic()-started_run,'run_directory':journal.directory.as_posix(),'human_semantic_ratings':0}
        journal.finish(**summary);save(journal.directory/'summary.json',summary)
        return summary

def audit():
    require(sha256(MANIFEST)==sha256(FROZEN)==MANIFEST_SHA,'Manifest changed')
    plan=load(FROZEN);histories=[];links=[];http_count=0
    for folder in sorted((ROOT/'runs').glob('*')):
        m=load(folder/'manifest.json');require(m['prior_segments']==links and m['claim']==load(ROOT/'claim.json'),'Segment binding differs')
        events=read_events(folder);histories.append(events)
        http=[json.loads(base64.b64decode(e['data']['body_base64'])) for e in events if e['kind']=='http_response' and e['data']['route']=='/completion' and e['data'].get('status')==200]
        raws=[e['data']['response'] for e in events if e['kind']=='p1d_budget_raw_generation'];require(http==raws,'Raw HTTP/result mismatch');http_count+=len(http)
        links.append({'path':folder.as_posix(),'manifest_sha256':sha256(folder/'manifest.json'),'events':{p.name:sha256(p) for p in (folder/'events').glob('*.json')}})
    attempted,raw,results=inventory(plan,histories);rows=[]
    for r in plan['requests']:
        rid=r['request_id'];derived=result(r,raw[rid]['response'],raw[rid]['latency_seconds']) if rid in raw else None
        if rid in results:require(derived==results[rid],'Reconstruction mismatch')
        rows.append({'request':r,'result':derived,'state':'COMPLETED' if rid in results else 'RAW_RECOVERABLE' if rid in raw else 'ATTEMPTED_UNRESOLVED' if rid in attempted else 'UNATTEMPTED'})
    return {'version':'p1d_budget_execution_integrity_v1','manifest_sha256':MANIFEST_SHA,'attempted':len(attempted),'results':len(results),'raw_responses':len(raw),'http_responses_verified':http_count,'segments':links,'rows':rows,'new_generations':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['register','preflight','run','audit'])
    parser.add_argument('--output',type=Path);parser.add_argument('--preflight',type=Path);parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    if args.action=='register':value=register()
    elif args.action=='run':
        if not args.preflight:parser.error('--preflight required')
        value=run(args.preflight,args.resume)
    else:
        if not args.output:parser.error('--output required')
        value=preflight() if args.action=='preflight' else audit();save(args.output,value)
    print(json.dumps({k:v for k,v in value.items() if k not in ('rows','segments','source_hashes','identity')},indent=2))
    if value.get('status','PASS') in ('BLOCKED','PARTIAL'):raise SystemExit(2)
