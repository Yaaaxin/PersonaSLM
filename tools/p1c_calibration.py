"""Approved P1c manifest adapter using the validated native CPU transport and journal."""
import argparse
import base64
import json
from pathlib import Path
import platform
import shutil
import subprocess
import time

import p1c_decision_compatibility as approvals
import p1c_decisions as p
import p1c_design as d
from personaslm.configuration import RuntimeConfig, preflight as file_preflight
from personaslm.inference import LlamaClient, normalize_result
from personaslm.journal import RunJournal, atomic_json, read_events
from personaslm.p1b_calibration import writer_lock
from personaslm.provenance import require_local_path, repository_root, sha256
from personaslm.response_status import classify_response
from personaslm.runner import validate_completion
from personaslm.server import ManagedServer, validate_server_properties

VERSION='p1c_calibration_adapter_v1'
RUN_ROOT=Path('results/p1c_calibration/development_v1')
REGISTRATION=approvals.OUTPUT/'registration/registration_v1.json'
AUTHORIZATION=Path('docs/validation/p1c/authorization_v2/researcher_consolidated_approval_v1.json')
DECODING={'cache_prompt':False,'n_predict':96,'return_tokens':True,'seed':42,'stop':[],
          'stream':False,'temperature':0.0,'top_p':1.0}


def load(path):return p.decision_json(path)


def key(row):
    return str(row['sequence_index'])+':'+('/'.join(row['request_identity']))


def sources():
    paths=list(Path('src/personaslm').glob('*.py'))+[Path(__file__),Path('tools/p1c_decisions.py'),
        Path('tools/p1c_decision_compatibility.py'),Path('tools/p1c_design.py'),Path('configs/p1_wave1_v1.json')]
    return {f.resolve().relative_to(repository_root()).as_posix():sha256(f) for f in paths}


def runtime(plan):
    config=RuntimeConfig.load(Path('configs/p1_wave1_v1.json'))
    check=file_preflight(config)
    d.require(check['status']=='PASS','Model file preflight failed')
    cfg=plan['configuration']
    d.require(config.model_file==plan['model_file'] and config.server_file==plan['backend_file'],'Runtime file path differs')
    for name in ('threads','n_ctx','seed'):
        d.require(getattr(config,name)==cfg[name], 'Runtime configuration differs: '+name)
    d.require(config.max_new_tokens==cfg['n_predict']==96 and cfg['threads_batch']==4 and cfg['n_gpu_layers']==0,'CPU/budget differs')
    d.require(plan['generation_parameters']==DECODING,'Decoding differs')
    d.require(check['model']['sha256']==cfg['model_sha256'] and check['server']['sha256']==cfg['backend_sha256'],'Runtime binary digest differs')
    return config,check


def preflight():
    gate=approvals.gate(REGISTRATION,AUTHORIZATION)
    d.require(gate['status']=='GO','Researcher gate is not GO')
    plan=load(p.MANIFEST);_,identity=runtime(plan)
    free=shutil.disk_usage(repository_root()).free
    d.require(free>=1024**3,'Less than 1 GiB free for conservative raw logging reserve')
    return {'version':VERSION,'status':'PASS','checked_utc':d.now(),'gate':gate,'identity':identity,
            'disk_free_bytes':free,'minimum_log_reserve_bytes':1024**3,'source_hashes':sources(),
            'manifest_sha256':p.MANIFEST_SHA,'authorization_sha256':sha256(AUTHORIZATION),
            'registration_sha256':sha256(REGISTRATION),'new_generations':0,
            'live_gate':'Verify all 72 token arrays on the owned pinned server before any completion.'}


def result_from_response(row,response,latency):
    token_audit=validate_completion(response,row['input_token_ids'])
    normalized=normalize_result(response);count=response.get('tokens_predicted')
    d.require(type(count) is int and 0<=count<=96,'Invalid actual generation count')
    if normalized['token_ids_status']=='returned':
        d.require(len(normalized['generated_token_ids'])==count,'Generated token ID/count mismatch')
    boundary=classify_response(normalized['raw_response'],normalized['raw_termination'],declared_stops=())
    return {'request_key':key(row),'frozen_request':row,**normalized,'generated_tokens':count,
            'latency_seconds':latency,'input_token_audit':token_audit,'response_status':boundary,
            'raw_text_sha256':d.text_hash(normalized['raw_response']),
            'first_reply_sha256':d.text_hash(boundary['first_span']['text']),
            'parsed_response':boundary['first_span']['text'],
            'semantic_evaluation':{'status':'AWAITING_HUMAN_REVIEW','applicability':row['applicability'],
                'axis_policy':'separate_axes_policy_v1','labels':{},'structural_status_is_not_factual_judgment':True},
            'error':None}


def inventory(plan,segments):
    attempted=[];raw={};results={}
    for events in segments:
        started_here=set();raw_here=set()
        for event in events:
            kind=event['kind'];data=event['data']
            if kind=='p1c_generation_started':
                d.require(len(attempted)<72 and data==plan['requests'][len(attempted)],'Duplicate/unplanned/reordered attempt')
                rid=key(data);d.require(rid not in attempted,'Duplicate request');attempted.append(rid);started_here.add(rid)
            elif kind=='p1c_raw_generation':
                rid=data['request_key'];d.require(rid in started_here and rid not in raw,'Raw without unique local attempt')
                raw[rid]=data;raw_here.add(rid)
            elif kind=='p1c_result':
                rid=data['request_key'];d.require(rid in raw_here and rid not in results,'Result without unique local raw')
                results[rid]=data
    return {'attempted':attempted,'raw':raw,'results':results,'pending':plan['requests'][len(attempted):]}


def segments(root,claim):
    ordered=[]
    for folder in (root/'runs').glob('*'):
        manifest=load(folder/'manifest.json')
        d.require(manifest['claim']==claim,'Run claim mismatch')
        ordered.append((manifest['segment_index'],folder,manifest))
    ordered.sort(key=lambda r:r[0])
    d.require([r[0] for r in ordered]==list(range(1,len(ordered)+1)),'Segment order differs')
    return ordered


def live_preflight(plan,config,client,journal):
    props=client.request('/props');binding=validate_server_properties(props,config)
    d.require(binding['build_info']=='b11573-0f701c882','Loaded backend differs')
    journal.write('tokenizer_binding',{'props':props,'validation':binding})
    for row in plan['requests']:
        ids=client.tokenize(row['prompt'])
        d.require(ids==row['input_token_ids'] and len(ids)+96<=4096,'Live tokenization/context mismatch')
        journal.write('p1c_live_prompt_verified',row)
    journal.write('live_preflight_pass',{'requests_verified':72,'generation_requests_so_far':0})


def run(preflight_path,resume=False):
    prepared=load(preflight_path);fresh=preflight();plan=load(p.MANIFEST)
    d.require(prepared['status']=='PASS' and all(prepared[k]==fresh[k] for k in
              ('source_hashes','manifest_sha256','authorization_sha256','registration_sha256')),'Preflight binding changed')
    config,identity=runtime(plan);root=require_local_path(RUN_ROOT)
    with writer_lock(root):
        claim={k:fresh[k] for k in ('source_hashes','manifest_sha256','authorization_sha256','registration_sha256')}
        claim.update(preflight_sha256=sha256(preflight_path),maximum_total_attempts=72)
        if (root/'claim.json').exists():
            d.require(resume and load(root/'claim.json')==claim,'Existing run requires explicit identical resume')
        else:
            d.require(not resume and not list((root/'runs').glob('*')),'Unexplained prior run')
            atomic_json(root/'claim.json',claim)
        old=segments(root,claim);histories=[];links=[]
        for _,folder,m in old:
            d.require(m['prior_segments']==links,'Prior segment binding differs')
            histories.append(read_events(folder))
            links.append({'path':folder.relative_to(repository_root()).as_posix(),'manifest_sha256':sha256(folder/'manifest.json'),
                          'events':{f.name:sha256(f) for f in (folder/'events').glob('*.json')}})
        inv=inventory(plan,histories)
        d.require(bool(inv['pending']),'No unattempted requests; no rerun authorized')
        journal=RunJournal(root/'runs',{'phase':'P1c','adapter_version':VERSION,'claim':claim,
            'segment_index':len(old)+1,'prior_segments':links,'frozen_manifest':plan,
            'authorization':load(AUTHORIZATION),'review_registration':load(REGISTRATION),
            'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_status':subprocess.check_output(['git','status','--short'],text=True),
            'python':platform.python_version(),'platform':platform.platform(),'configuration':plan['configuration'],
            'request_alias_definition':'sequence_index:case_id/condition; alias of unchanged original identity, not a new assignment',
            'resume_policy':'Never retry attempted/uncertain sends; continue only original unattempted suffix.'})
        for name,sha in claim['source_hashes'].items():
            target=journal.directory/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(Path(name).read_bytes())
            d.require(sha256(target)==sha,'Snapshot source differs')
        active=None;status='BLOCKED'
        try:
            journal.write('preflight',fresh)
            with ManagedServer(config,journal) as server:
                client=LlamaClient(config.endpoint,timeout=config.timeout,audit=journal.write)
                live_preflight(plan,config,client,journal)
                print(json.dumps({'live_preflight':'PASS','request_tokens_verified':72}),flush=True)
                for row in inv['pending']:
                    server.assert_running();active=key(row)
                    journal.write('p1c_generation_started',row)
                    started=time.monotonic()
                    response=client.complete(row['input_token_ids'],seed=42,max_new_tokens=96)
                    latency=time.monotonic()-started
                    journal.write('p1c_raw_generation',{'request_key':active,'response':response,'latency_seconds':latency})
                    result=result_from_response(row,response,latency);journal.write('p1c_result',result)
                    print(json.dumps({'request':active,'response_status':result['response_status']['status'],'generated_tokens':result['generated_tokens']}),flush=True)
                    active=None
                server.assert_running();validate_server_properties(client.request('/props'),config)
                _,after=runtime(plan);d.require(after==identity,'Postflight model/backend changed')
                journal.write('postflight',after)
            status='PASS'
        except BaseException as exc:
            status='PARTIAL' if active else 'BLOCKED'
            journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_key':active})
        events=read_events(journal.directory)
        summary={'status':status,'attempted':sum(e['kind']=='p1c_generation_started' for e in events),
                 'responses_received':sum(e['kind']=='p1c_raw_generation' for e in events),
                 'results':sum(e['kind']=='p1c_result' for e in events),'human_semantic_labels':0,
                 'run_directory':journal.directory.relative_to(repository_root()).as_posix()}
        journal.finish(**summary);atomic_json(journal.directory/'summary.json',summary)
        return summary


def audit():
    d.require(sha256(p.MANIFEST)==p.MANIFEST_SHA,'Frozen manifest differs')
    plan=load(p.MANIFEST);root=require_local_path(RUN_ROOT);claim=load(root/'claim.json')
    old=segments(root,claim);histories=[];links=[];http_responses=0
    for _,folder,manifest in old:
        d.require(manifest['prior_segments']==links,'Prior-segment audit differs')
        events=read_events(folder);histories.append(events)
        for event in events:
            if event['kind']=='http_response' and event['data']['route']=='/completion' and event['data'].get('status')==200:
                body=base64.b64decode(event['data']['body_base64']);value=json.loads(body.decode('utf-8'));http_responses+=1
                raws=[e['data']['response'] for e in events if e['kind']=='p1c_raw_generation']
                d.require(value in raws,'Raw HTTP bytes do not match persisted response')
        links.append({'path':folder.relative_to(repository_root()).as_posix(),'manifest_sha256':sha256(folder/'manifest.json'),
                      'events':{f.name:sha256(f) for f in (folder/'events').glob('*.json')}})
    inv=inventory(plan,histories);rows=[]
    for row in plan['requests']:
        rid=key(row);raw=inv['raw'].get(rid);saved=inv['results'].get(rid)
        derived=result_from_response(row,raw['response'],raw['latency_seconds']) if raw else None
        if saved:d.require(saved==derived,'Parser reconstruction differs: '+rid)
        rows.append({'request_key':rid,'technical_status':'COMPLETED' if saved else 'RAW_RECOVERABLE' if raw else 'ATTEMPTED_NO_RAW' if rid in inv['attempted'] else 'UNATTEMPTED','result':derived})
    return {'version':'p1c_execution_reconstruction_v1','manifest_sha256':p.MANIFEST_SHA,'planned':72,
            'attempted':len(inv['attempted']),'raw_responses':len(inv['raw']),'results':len(inv['results']),
            'http_response_bytes_verified':http_responses,'segments':links,'rows':rows,'new_generations':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['preflight','run','audit'])
    parser.add_argument('--output',type=Path);parser.add_argument('--preflight',type=Path);parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.action=='run':
        if not args.preflight:parser.error('Bound preflight required')
        result=run(args.preflight,args.resume)
    else:
        if not args.output:parser.error('Fresh output required')
        result=preflight() if args.action=='preflight' else audit();atomic_json(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','segments','source_hashes','gate','identity')},indent=2))
    if result.get('status','PASS')!='PASS':raise SystemExit(2)
