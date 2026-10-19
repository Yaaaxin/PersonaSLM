"""Exactly eight authorized Instruct attempts; no warmup, retries or hidden smoke calls."""
import argparse
import base64
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
import p1d_budget_calibration as b
import p1d_format_calibration as f
from p1d_instruct_template_check import render, messages_for_base
from personaslm.observations import memory_observation
from personaslm.server import server_command

SOURCE=Path('docs/validation/p1d/instruct_preparation_v3/minimal_instruct_smoke_manifest_proposed_v1.json')
SHA='ba63c30a9868b94b47f8f79dd774ac0627d56113810ffd4db08eb63af0374b91'
MODEL_SHA='0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc'
OUT=Path('docs/validation/p1d/instruct_smoke_v1')
ROOT=Path('results/p1d_instruct_smoke/development_v1')
FROZEN=OUT/'frozen_manifest_v1.json'
AUTH=OUT/'researcher_authorization_v1.json'
load,save,sha256,th,require=b.load,b.save,b.sha256,b.th,b.require

@dataclass(frozen=True)
class Runtime:
    model_file:str
    model_sha256:str
    server_file:str
    model_label:str='Qwen3.5-2B-Instruct-Q4_K_M-third-party-development'
    engine_revision:str='0f701c882'
    endpoint:str='http://127.0.0.1:8080'
    threads:int=4
    n_ctx:int=4096
    max_new_tokens:int=96
    seed:int=42
    timeout:float=180.0
    startup_timeout:float=120.0
    prompt_template:str='explicit_official_nonthinking_token_ids_v1'
    def as_dict(self):return asdict(self)

def config(plan):
    m=plan['model']
    return Runtime(m['model_file'],m['model_sha256'],m['backend_file'])

def command(plan):
    return server_command(config(plan))+['--no-warmup','--no-mmproj','--spec-type','none',
        '--chat-template-file',str(Path(plan['template_path']).resolve()),
        '--chat-template-kwargs','{"enable_thinking":false}']

class Server(b.ManagedServer):
    def __init__(self,plan,journal):
        super().__init__(config(plan),journal);self.plan=plan
    def __enter__(self):
        argv=command(self.plan);uri=urlsplit(self.config.endpoint)
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:probe.bind((uri.hostname,uri.port))
        env={k:v for k,v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')}
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
        self.journal.write('server_launch',{'argv':argv,'environment_policy':'remove LLAMA_ARG_* overrides','warmup':False})
        try:
            self.log_handle=(self.journal.directory/'server.log').open('xb')
            self.process=subprocess.Popen(argv,stdout=self.log_handle,stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,env=env,cwd=Path.cwd(),creationflags=flags)
            self.journal.write('server_process',{'pid':self.process.pid})
            deadline=time.monotonic()+self.config.startup_timeout
            health=b.LlamaClient(self.config.endpoint,timeout=2,audit=self.journal.write)
            while time.monotonic()<deadline:
                if self.process.poll() is not None:raise RuntimeError('Server exited during startup; preserve server.log')
                try:
                    if health.request('/health').get('status')=='ok':
                        self.journal.write('memory_observation',memory_observation(self.process.pid));return self
                except HTTPError as exc:
                    if exc.code!=503:raise
                except (URLError,TimeoutError,ConnectionError):pass
                time.sleep(.1)
            raise TimeoutError('Startup deadline exceeded')
        except BaseException:
            self.__exit__(None,None,None);raise

def sources():
    paths=list(Path('src/personaslm').glob('*.py'))+[Path(__file__),Path('tools/p1d_budget_calibration.py'),
        Path('tools/p1d_format_calibration.py'),Path('tools/p1d_instruct_template_check.py')]
    return {p.resolve().relative_to(Path.cwd()).as_posix():sha256(p) for p in paths}

def validate_plan(plan):
    require(plan['version']=='p1d_instruct_smoke_proposed_v1' and plan['proposed_requests']==8,'Wrong manifest scope')
    require(plan['model']['model_sha256']==MODEL_SHA,'Wrong model')
    for k,v in {'threads':4,'threads_batch':4,'ctx':4096,'gpu_layers':0,'mtp':False,'vision':False,'warmup':False}.items():
        require(plan['model'][k]==v,'Runtime field changed: '+k)
    require(sha256(Path(plan['template_path']))==plan['template_sha256'],'Template changed')
    require(sha256(SOURCE.parent/'local_candidate_metadata_v1.json')==plan['candidate_metadata_sha256'],'Candidate metadata changed')
    require(sha256(SOURCE.parent/'native_development_tokenizer_v1.json')==plan['native_tokenizer_evidence_sha256'],'Native evidence changed')
    rows=plan['requests']; require(len(rows)==len({r['request_id'] for r in rows})==8,'Request count/ID')
    require({r['case_id'] for r in rows}==set(b.CASE_IDS),'Wrong dev cases')
    cases={c['case_id']:c for c in load(b.DEV/'development_examples_v5.json')['cases']}
    heldout={c['case_id'] for c in load('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')['cases']}
    require(not heldout.intersection(b.CASE_IDS),'Heldout overlap')
    previous={r['request_id']:r for r in load(b.FROZEN)['requests']}
    template=Path(plan['template_path']).read_text(encoding='utf-8')
    for i,row in enumerate(rows):
        require(row['order']==i and row['request_id']=='p1d_instruct_smoke_v1_'+row['case_id'],'Order/identity changed')
        require(row['request_sha256']==th(json.dumps({k:v for k,v in row.items() if k!='request_sha256'},sort_keys=True,separators=(',',':'))),'Request hash')
        for k,v in {'condition':'H_none','max_new_tokens':96,'seed':42,'temperature':0,'top_p':1,'stop':[],
                    'ignore_eos':False,'cache_prompt':False,'parse_special':True,'split':'DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION'}.items():
            require(row[k]==v,'Row configuration changed: '+k)
        c=cases[row['case_id']];old=previous[row['historical_base_request_id']]
        require(c['independent_validation'] is False and c['split']==row['split'],'Not development')
        require(old['request_sha256']==row['historical_base_request_sha256'] and old['condition']=='H_none' and old['max_new_tokens']==96,'Wrong comparator')
        require(c['speaker_id']==row['speaker_id']==old['speaker_id'] and row['reference']==c['required_components']==old['reference'],'Case/ref changed')
        require(row['messages']==messages_for_base(old['prompt']) and row['prompt']==render(template,row['messages']),'Task/template rendering changed')
        require(row['prompt_sha256']==th(row['prompt']) and row['input_token_ids_sha256']==th(str(row['input_token_ids'])),'Input hashes')
        require(len(row['input_token_ids'])==row['input_tokens'] and row['context_remaining']==4096-96-row['input_tokens']>=0,'Input capacity')
    native=load(SOURCE.parent/'native_development_tokenizer_v1.json')
    require(len(native['rows'])==8 and native['parse_special'] is True,'Native scope')
    for r in native['rows']:require(sha256(Path(r['path']))==r['sha256'],'Native log changed')
    return {'requests':8,'cases':8,'speakers':8,'heldout_overlap':0,'historical_reference':'exact IDs; not independent replication'}

def register():
    require(sha256(SOURCE)==SHA,'HASH MISMATCH: inference prohibited')
    require(not AUTH.exists() and not FROZEN.exists(),'Registration exists; verify without repetition')
    require(not (ROOT/'claim.json').exists() and not list((ROOT/'runs').glob('*')),'Prior execution allocation exists: do not repeat')
    checks=validate_plan(load(SOURCE));OUT.mkdir(parents=True,exist_ok=True)
    with FROZEN.open('xb') as handle:handle.write(SOURCE.read_bytes())
    save(AUTH,{'version':'p1d_instruct_smoke_authorization_v1','researcher':'Yaxin ZHENG','decision':'AUTHORIZED',
        'source':'Explicit user message: Research Programme Alignment, Instruct Feasibility, Core Factorial Restoration, and Original Algorithm Development, section 8',
        'human_decision_timestamp':None,'registered_utc':b.utc_now(),'manifest_sha256':SHA,'model_sha256':MODEL_SHA,
        'maximum_attempts':8,'time_limit_minutes':45,'scope':'Existing eight development cases, H_none, 96-token cap, exact registered order and template.',
        'partial_conversion_lineage':'Explicitly accepted by researcher for development feasibility only; not confirmatory inference.',
        'prohibitions':['retry','other inference','training','main validation cohort'],'semantic_adoption':False,'existing_execution_found':False})
    tracked=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
    save(OUT/'source_preservation_baseline_v1.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'initial_git_status':subprocess.check_output(['git','status','--short'],text=True),
        'recorded_utc':b.utc_now(),'tracked_sha256':{p:sha256(Path(p)) for p in tracked if p and Path(p).is_file()}})
    return {'status':'REGISTERED',**checks}

def preflight(*, check_headroom=True):
    require(sha256(SOURCE)==sha256(FROZEN)==SHA,'Exact authorized hash changed')
    auth=load(AUTH);require(auth['decision']=='AUTHORIZED' and auth['manifest_sha256']==SHA and auth['maximum_attempts']==8,'Authorization invalid')
    plan=load(FROZEN);checks=validate_plan(plan);cfg=config(plan);identity=b.file_preflight(cfg)
    require(identity['status']=='PASS' and identity['model']['sha256']==MODEL_SHA and identity['server']['sha256']==plan['model']['backend_sha256'],'Binary mismatch')
    dlls=load(b.FROZEN)['native_tokenizer_identity'];folder=Path(cfg.server_file).parent
    require({p.name:sha256(p) for p in folder.glob('*.dll')}==dlls['dll_hashes'],'DLL mismatch')
    require(sha256(folder/'llama-tokenize.exe')==dlls['tokenizer_sha256'],'Tokenizer binary mismatch')
    memory=memory_observation(os.getpid())
    if check_headroom:
        require(memory.get('system',{}).get('available_physical',0)>=3*1024**3,'Less than 3 GiB available memory; do not infer')
    require(shutil.disk_usage('.').free>1024**3,'Less than 1 GiB output reserve')
    return {'status':'PASS','checked_utc':b.utc_now(),'checks':checks,'identity':identity,'configuration':cfg.as_dict(),
        'server_command':command(plan),'manifest_sha256':SHA,'authorization_sha256':sha256(AUTH),'source_hashes':sources(),
        'native_identity':dlls,'memory_before_run':memory,'live_gate':'All eight parse_special=true token arrays must match before any completion'}

def payload(row):
    return {**f.payload(row),'ignore_eos':False}

def inventory(plan,events):
    attempts=[];raw={};results={}
    for event in events:
        d=event['data']
        if event['kind']=='instruct_generation_started':
            require(len(attempts)<8 and d==plan['requests'][len(attempts)],'Repeated/reordered/unplanned attempt')
            attempts.append(d['request_id'])
        elif event['kind']=='instruct_raw_generation':
            require(d['request_id'] in attempts and d['request_id'] not in raw,'Unbound/repeated raw')
            raw[d['request_id']]=d
        elif event['kind']=='instruct_result':
            require(d['request_id'] in raw and d['request_id'] not in results,'Unbound/repeated result')
            results[d['request_id']]=d
    return attempts,raw,results

def run(preflight_path):
    fresh=preflight();stored=load(preflight_path);plan=load(FROZEN)
    for k in ('manifest_sha256','authorization_sha256','source_hashes','configuration','server_command'):
        require(fresh[k]==stored[k],'Preflight binding changed: '+k)
    with b.writer_lock(ROOT):
        require(not (ROOT/'claim.json').exists() and not list((ROOT/'runs').glob('*')),'Existing allocation: no repeat/retry')
        claim={k:fresh[k] for k in ('manifest_sha256','authorization_sha256','source_hashes')}
        claim.update(maximum_attempts=8,preflight_sha256=sha256(preflight_path));save(ROOT/'claim.json',claim)
        journal=b.RunJournal(ROOT/'runs',{'phase':'P1d/P3 Instruct development feasibility','rq':['RQ3','RQ4'],
            'scientific_purpose':'Model/template adequacy for future persona factorial measurement; no persona effect from H_none.',
            'claim':claim,'frozen_manifest':plan,'authorization':load(AUTH),'configuration':config(plan).as_dict(),
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_status':subprocess.check_output(['git','status','--short'],text=True),'python':platform.python_version(),'platform':platform.platform()})
        for path,digest in claim['source_hashes'].items():
            dest=journal.directory/'source_snapshot'/path;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as handle:handle.write(Path(path).read_bytes())
            require(sha256(dest)==digest,'Source snapshot mismatch')
        started=time.monotonic();active=None;status='BLOCKED'
        try:
            journal.write('preflight',fresh)
            with Server(plan,journal) as server:
                client=b.LlamaClient(config(plan).endpoint,timeout=180,audit=journal.write)
                props=client.request('/props');validation=b.validate_server_properties(props,config(plan))
                require(validation['build_info']=='b11573-0f701c882','Wrong backend build')
                journal.write('effective_server_defaults',{'props':props,'validation':validation})
                for row in plan['requests']:
                    tokens=client.request('/tokenize',{'content':row['prompt'],'add_special':True,'parse_special':True,'with_pieces':False})['tokens']
                    require(tokens==row['input_token_ids'],'Live native tokenizer differs; no completion allowed')
                    journal.write('live_prompt_verified',{'request_id':row['request_id'],'token_ids_sha256':th(str(tokens))})
                journal.write('live_preflight_pass',{'prompts':8,'completed_inference':0})
                print(json.dumps({'live_preflight':'PASS','planned':8}),flush=True)
                for row in plan['requests']:
                    remaining=45*60-(time.monotonic()-started)
                    require(remaining>0,'45-minute limit reached; no further requests')
                    server.assert_running();client.timeout=min(180,remaining)
                    active=row['request_id'];journal.write('instruct_generation_started',row)
                    tick=time.monotonic();response=client.request('/completion',payload(row));elapsed=time.monotonic()-tick
                    journal.write('instruct_raw_generation',{'request_id':active,'response':response,'latency_seconds':elapsed})
                    derived=f.result(row,response,elapsed);journal.write('instruct_result',derived)
                    print(json.dumps({'order':row['order'],'id':active,'tokens':derived['generated_tokens'],'stop':derived['stop_reason'],
                        'status':derived['response_status']['status'],'seconds':round(elapsed,2)}),flush=True)
                    active=None
                server.assert_running();b.validate_server_properties(client.request('/props'),config(plan))
                after=preflight(check_headroom=False);require(after['identity']==fresh['identity'] and after['source_hashes']==fresh['source_hashes'],'Postflight change')
                journal.write('postflight',after)
            status='PASS'
        except BaseException as exc:
            status='PARTIAL' if active else 'BLOCKED'
            journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_id':active})
        events=b.read_events(journal.directory);attempts,raw,results=inventory(plan,events)
        summary={'status':status,'attempted':len(attempts),'responses_received':len(raw),'results':len(results),
            'elapsed_seconds':time.monotonic()-started,'run_directory':journal.directory.as_posix(),'human_semantic_ratings':0}
        journal.finish(**summary);save(journal.directory/'summary.json',summary);return summary

def audit():
    require(sha256(SOURCE)==sha256(FROZEN)==SHA,'Manifest changed')
    folders=list((ROOT/'runs').glob('*'));require(len(folders)==1,'Unexpected run count')
    folder=folders[0];events=b.read_events(folder);plan=load(FROZEN)
    require(load(folder/'manifest.json')['claim']==load(ROOT/'claim.json'),'Claim mismatch')
    attempts,raw,results=inventory(plan,events)
    sent=[e['data']['payload'] for e in events if e['kind']=='http_request' and e['data']['route']=='/completion']
    require(sent==[payload(r) for r in plan['requests'][:len(attempts)]],'Actual payload/order/count changed')
    bodies=[json.loads(base64.b64decode(e['data']['body_base64'])) for e in events if e['kind']=='http_response' and e['data']['route']=='/completion' and e['data'].get('status')==200]
    require(bodies==[r['response'] for r in raw.values()],'HTTP bytes changed')
    rows=[]
    for row in plan['requests']:
        rid=row['request_id'];derived=f.result(row,raw[rid]['response'],raw[rid]['latency_seconds']) if rid in raw else None
        if rid in results:require(derived==results[rid],'Derived result differs')
        rows.append({'request':row,'result':derived,'state':'COMPLETED' if rid in results else 'RAW_RECOVERABLE' if rid in raw else 'ATTEMPTED_UNRESOLVED' if rid in attempts else 'UNATTEMPTED'})
    return {'version':'p1d_instruct_smoke_integrity_v1','run_directory':folder.as_posix(),'manifest_sha256':SHA,
        'attempted':len(attempts),'results':len(results),'http_responses_verified':len(bodies),'rows':rows,'new_generations':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['register','preflight','run','audit'])
    parser.add_argument('--output',type=Path);parser.add_argument('--preflight',type=Path);args=parser.parse_args()
    if args.action=='register':value=register()
    elif args.action=='run':
        if not args.preflight:parser.error('--preflight required')
        value=run(args.preflight)
    else:
        if not args.output:parser.error('--output required')
        value=preflight() if args.action=='preflight' else audit();save(args.output,value)
    print(json.dumps({k:v for k,v in value.items() if k not in ('rows','identity','source_hashes','native_identity','memory_before_run')},indent=2))
    if value.get('status') in ('PARTIAL','BLOCKED'):raise SystemExit(2)
