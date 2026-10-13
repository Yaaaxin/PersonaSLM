"""Freeze, tokenize and execute only the researcher-authorized P1 factorial wave."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import time
from personaslm.conditioning import build_prompt
from personaslm.configuration import RuntimeConfig,preflight
from personaslm.inference import LlamaClient,normalize_result
from personaslm.journal import RunJournal,atomic_json,read_events,utc_now
from personaslm.p1 import PilotCase,validate_dataset,wave_order,neutral_pool,evaluate_pilot,ORDER_SEED,ROUTING_VERSION
from personaslm.provenance import sha256,fingerprint,require_local_path
from personaslm.reproducibility import source_snapshot
from personaslm.response_status import text_hash
from personaslm.runner import validate_completion
from personaslm.server import ManagedServer,validate_server_properties

DATA=Path('data/synthetic/p1_development_v1.json')
PUBLIC=Path('docs/validation/p1')
SESSION=Path('results/p1_wave1/development_v1')
MODEL='ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994'
BACKEND='71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846'
CONFIG=Path('configs/p1_wave1_v1.json')
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def snapshot():
    value=source_snapshot(DATA)
    value['p1_tool_sources']={p.as_posix():{'sha256':sha256(p),'utf8':p.read_bytes().decode('utf-8')} for p in sorted(Path('tools').glob('p1_*.py'))}
    value['evaluation_rules']='response_status_v1 and separate_axes_policy_v1; p1_endpoint_routing_v1 selects city-only automatic scoring or pending human review'
    return value
def pinned(config):
    result=preflight(config)
    if result['status']!='PASS' or result['model']['sha256']!=MODEL or result['server']['sha256']!=BACKEND:
        raise ValueError('Pinned model/backend preflight failed')
    if config.threads!=4 or config.n_ctx!=4096 or config.max_new_tokens!=96 or config.token_tolerance!=0 or config.seed!=42:
        raise ValueError('Wave1 runtime settings differ from the authorized freeze')
    return result
def check_sources(design):
    for name,digest in design['source_snapshot']['source_sha256'].items():
        if sha256(Path('src/personaslm')/name)!=digest:raise ValueError('Frozen source changed: '+name)
    for name,value in design['source_snapshot']['p1_tool_sources'].items():
        if sha256(Path(name))!=value['sha256']:raise ValueError('Frozen P1 tool changed: '+name)
    if sha256(DATA)!=design['dataset_sha256'] or sha256(CONFIG)!=design['configuration_sha256']:
        raise ValueError('Frozen dataset/configuration changed')

def freeze():
    data=read(DATA);validation=validate_dataset(data);config=RuntimeConfig.load(Path('configs/p0_runtime.local.json'));check=pinned(config)
    atomic_json(CONFIG,config.as_dict())
    cases={r['case_id']:PilotCase(r) for r in data['cases']};requests=[]
    for item in wave_order(data):
        c=cases[item['case_id']];prompt=build_prompt(c,item['condition'])
        requests.append({**item,'prompt':asdict(prompt),'prompt_sha256':text_hash(prompt.text),
            'trusted_evidence_sha256':text_hash(c.trusted_evidence),'question_sha256':text_hash(c.question),'applicability':c.applicability})
    controls=[]
    for cid in sorted({r['case_id'] for r in requests}):
        c=cases[cid]
        for condition,reference in [('N_style','C1'),('N_history','C3')]:
            controls.append({'case_id':cid,'condition':condition,'reference':reference,
                'bounded_candidates':[{'index':i,'text':text,'prompt':asdict(build_prompt(c,condition,neutral_override=text))} for i,text in enumerate(neutral_pool(c,condition))],
                'selection':'First exact match in frozen order; if none, report best absolute difference, never relax zero tolerance',
                'human_review_status':'OPEN','matched_generation_authorized':False})
    plan=Path('docs/P1_experiment_plan.md')
    if not plan.is_file():raise ValueError('Predeclare scientific plan before freeze')
    tests=read(SESSION/'engineering/pre_generation_tests_final.json')
    if tests['exit_code']!=0:raise ValueError('Tests must pass before freeze')
    value={'version':'p1_wave1_design_v1','phase':'P1','track':'A','created_utc':utc_now(),
        'authorization':'Researcher authorized P1 development and 12 x 8 CPU wave; no later wave or neutral generation',
        'dataset_version':data['version'],'dataset_sha256':sha256(DATA),'dataset':data,'configuration':config.as_dict(),
        'configuration_sha256':sha256(CONFIG),'model_sha256':MODEL,'backend_sha256':BACKEND,
        'preflight':json.loads(json.dumps(check).replace(str(Path.cwd()).replace('\\','\\\\')+'\\\\','')),
        'hardware_observation':read(SESSION/'materials/hardware_observation_verified.json'),
        'hardware_observation_sha256':sha256(SESSION/'materials/hardware_observation_verified.json'),
        'source_snapshot':snapshot(),'protocol_sha256':sha256(Path('docs/research_protocol_v1.1.md')),
        'experiment_plan_sha256':sha256(plan),'experiment_plan_utf8':plan.read_text(encoding='utf-8'),
        'tests_capture_sha256':sha256(SESSION/'engineering/pre_generation_tests_final.json'),
        'allocation_seed':data['allocation_seed'],'condition_order_seed':ORDER_SEED,
        'order_policy':'Shuffle case blocks, then independently shuffle eight conditions per block; fresh input IDs and cache_prompt=false',
        'prompt_template_version':'transcript_base_v1','response_policy':'response_status_v1','evaluation_policy':'separate_axes_policy_v1','routing_version':ROUTING_VERSION,
        'decoding':{'n_predict':96,'temperature':0.0,'top_p':1.0,'seed':42,'cache_prompt':False,'stop':[],'return_tokens':True,'stream':False},
        'requests':requests,'control_pools':controls,'manipulation_validation':validation,
        'resume_policy':'New immutable segment; skip all previously attempted requests, even without response; no automatic retries of failed/uncertain attempts. Essential instrumentation failure stops segment.',
        'maximum_factorial_requests':96,'neutral_requests_authorized':0,'confirmatory':False}
    value['freeze_id']=fingerprint(value);atomic_json(PUBLIC/'wave1_design_v1.json',value)
    print(json.dumps({'frozen_requests':len(requests),'control_pools':len(controls),'freeze_id':value['freeze_id']}))

def prepare():
    design=read(PUBLIC/'wave1_design_v1.json');check_sources(design)
    if (PUBLIC/'wave1_manifest_v1.json').exists():raise FileExistsError('Wave already prepared')
    config=RuntimeConfig(**design['configuration']);check=pinned(config)
    journal=RunJournal(SESSION/'runs',{'phase':'P1','operation':'tokenizer_preparation_only','design_sha256':sha256(PUBLIC/'wave1_design_v1.json'),
        'configuration':config.as_dict(),'generation_parameters':None,'reconstruction':snapshot()})
    journal.write('preflight',check);requests=[];control_results=[]
    try:
        with ManagedServer(config,journal) as server:
            client=LlamaClient(config.endpoint,timeout=config.timeout,audit=journal.write)
            props=client.request('/props');identity=validate_server_properties(props,config)
            journal.write('tokenizer_binding',{'properties':props,'validation':identity,'policy':{'add_special':True,'parse_special':False,'with_pieces':False}})
            for row in design['requests']:
                ids=client.tokenize(row['prompt']['text'])
                if len(ids)+96>4096:raise ValueError('Context budget exceeded')
                prepared={**row,'input_token_ids':ids,'input_tokens':len(ids)}
                requests.append(prepared);journal.write('factorial_prompt_tokenized',prepared)
            refs={(r['case_id'],r['condition']):r for r in requests}
            for pool in design['control_pools']:
                reference=refs[(pool['case_id'],pool['reference'])];attempts=[]
                for candidate in pool['bounded_candidates']:
                    ids=client.tokenize(candidate['prompt']['text'])
                    attempt={**candidate,'token_ids':ids,'token_count':len(ids),'difference':len(ids)-reference['input_tokens'],'prompt_sha256':text_hash(candidate['prompt']['text'])}
                    attempts.append(attempt);journal.write('control_candidate_tokenized',{'case_id':pool['case_id'],'condition':pool['condition'],**attempt})
                exact=next((a for a in attempts if a['difference']==0),None);best=min(attempts,key=lambda a:abs(a['difference']))
                result={k:v for k,v in pool.items() if k!='bounded_candidates'}
                result.update(reference_tokens=reference['input_tokens'],reference_prompt_sha256=reference['prompt_sha256'],attempts=attempts,
                    selected=exact,best_observed=best,matching_status='PASS' if exact else 'FAILED',candidate_count=len(attempts),human_review_status='OPEN')
                control_results.append(result);journal.write('control_match_result',result)
            post=pinned(config);journal.write('postflight',post)
            if post!=check:raise ValueError('Artifact identity changed')
        journal.finish('PASS',factorial_prompts=len(requests),control_exact_matches=sum(r['selected'] is not None for r in control_results),completion_requests=0)
        manifest={'version':'p1_wave1_manifest_v1','phase':'P1','created_utc':utc_now(),'design_sha256':sha256(PUBLIC/'wave1_design_v1.json'),
            'dataset_sha256':design['dataset_sha256'],'prompt_template_version':design['prompt_template_version'],
            'model_sha256':MODEL,'backend_sha256':BACKEND,'configuration':design['configuration'],'decoding':design['decoding'],
            'response_policy':design['response_policy'],'evaluation_policy':design['evaluation_policy'],'routing_version':ROUTING_VERSION,
            'git':snapshot()['git'],'requests':requests,'tokenizer_run':journal.directory.as_posix(),
            'tokenizer_policy':{'endpoint':'/tokenize','add_special':True,'parse_special':False,'with_pieces':False},
            'source_snapshot':design['source_snapshot'],'maximum_requests':96,'neutral_control_generation':'BLOCKED pending required new human semantic review'}
        manifest['manifest_id']=fingerprint(manifest);atomic_json(PUBLIC/'wave1_manifest_v1.json',manifest)
        atomic_json(PUBLIC/'control_matching_v1.json',{'version':'p1_control_matching_v1','created_utc':utc_now(),
            'run_directory':journal.directory.as_posix(),'design_sha256':sha256(PUBLIC/'wave1_design_v1.json'),'results':control_results,'human_review_status':'OPEN','completion_requests':0})
        print(json.dumps({'preparation':'PASS','factorial_prompts':len(requests),'exact_controls':sum(r['selected'] is not None for r in control_results),
            'controls':len(control_results),'human_review':'OPEN','run_directory':journal.directory.as_posix()}))
    except Exception as exc:
        journal.write('failure',{'type':type(exc).__name__,'message':str(exc)});journal.finish('BLOCKED',completion_requests=0);raise

def pending_requests(requests,prior_events):
    allowed={r['request_id'] for r in requests};attempted=[]
    for events in prior_events:attempted.extend(e['data']['request_id'] for e in events if e['kind']=='p1_generation_started')
    if len(attempted)!=len(set(attempted)) or set(attempted)-allowed:raise ValueError('Invalid prior attempt inventory')
    return [r for r in requests if r['request_id'] not in attempted]

def run(prior):
    design=read(PUBLIC/'wave1_design_v1.json');check_sources(design);manifest=read(PUBLIC/'wave1_manifest_v1.json')
    if manifest['design_sha256']!=sha256(PUBLIC/'wave1_design_v1.json'):raise ValueError('Design binding mismatch')
    if fingerprint({k:v for k,v in manifest.items() if k!='manifest_id'})!=manifest['manifest_id']:raise ValueError('Manifest fingerprint mismatch')
    config=RuntimeConfig(**manifest['configuration']);check=pinned(config);claim=SESSION/'materials/generation_claim.json'
    if claim.exists() and not prior:raise ValueError('Wave already claimed; inspect original run and use explicit --resume')
    if not claim.exists():atomic_json(claim,{'created_utc':utc_now(),'manifest_sha256':sha256(PUBLIC/'wave1_manifest_v1.json'),'max_total_attempts':96})
    previous=[]
    existing=[p.parent.resolve() for p in (SESSION/'runs').glob('*/manifest.json') if read(p).get('operation')=='factorial_generation']
    if set(existing)!={Path(p).resolve() for p in prior}:raise ValueError('Resume must list every existing wave generation segment')
    for p in prior:
        prior_path=require_local_path(Path(p));m=read(prior_path/'manifest.json')
        if m.get('wave_manifest_sha256')!=sha256(PUBLIC/'wave1_manifest_v1.json'):raise ValueError('Resume manifest differs')
        previous.append(read_events(prior_path))
    pending=pending_requests(manifest['requests'],previous)
    if not pending:raise ValueError('No unattempted requests remain')
    journal=RunJournal(SESSION/'runs',{'phase':'P1','operation':'factorial_generation','wave_manifest_sha256':sha256(PUBLIC/'wave1_manifest_v1.json'),
        'wave_manifest':manifest,'design_sha256':sha256(PUBLIC/'wave1_design_v1.json'),'configuration':config.as_dict(),
        'generation_parameters':design['decoding'],'resume_from':prior,'request_ids':[r['request_id'] for r in pending],
        'reconstruction':snapshot(),'python':platform.python_version(),'os':platform.platform(),'cpu':platform.processor(),
        'hardware_observation':design['hardware_observation']})
    journal.write('preflight',check);attempted=received=completed=0;cases={r['case_id']:PilotCase(r) for r in read(DATA)['cases']}
    try:
        with ManagedServer(config,journal) as server:
            client=LlamaClient(config.endpoint,timeout=config.timeout,audit=journal.write)
            props=client.request('/props');journal.write('tokenizer_binding',{'properties':props,'validation':validate_server_properties(props,config)})
            for row in pending:
                prompt=build_prompt(cases[row['case_id']],row['condition'])
                if prompt.text!=row['prompt']['text'] or text_hash(prompt.text)!=row['prompt_sha256']:raise ValueError('Frozen prompt changed')
                if client.tokenize(prompt.text)!=row['input_token_ids']:raise ValueError('Real tokenizer no longer matches frozen input IDs')
                if row['input_tokens']+96>4096:raise ValueError('Context limit exceeded')
                journal.write('p1_prompt_verified',row)
            for row in pending:
                server.assert_running();started=time.monotonic();journal.write('p1_generation_started',row);attempted+=1
                response=client.complete(row['input_token_ids'],seed=42,max_new_tokens=96);received+=1;latency=time.monotonic()-started
                journal.write('p1_raw_generation',{'request_id':row['request_id'],'response':response,'latency_seconds':latency})
                token_audit=validate_completion(response,row['input_token_ids']);normalized=normalize_result(response);generated=response.get('tokens_predicted')
                if type(generated) is not int or not 0<=generated<=96:raise ValueError('Missing or invalid actual output token count')
                if normalized['token_ids_status']=='returned' and len(normalized['generated_token_ids'])!=generated:raise ValueError('Output token IDs/count mismatch')
                evaluation=evaluate_pilot(cases[row['case_id']],normalized['raw_response'],normalized['raw_termination'])
                result={**row,**normalized,'generated_tokens':generated,'latency_seconds':latency,'token_audit':token_audit,'evaluation':evaluation,
                    'parsed_response':evaluation['response_completeness']['first_span']['text'],
                    'parser_operations':{'removed_prefix':evaluation['response_completeness']['removed_prefix'],'first_span':evaluation['response_completeness']['first_span'],
                        'excluded_continuation':evaluation['response_completeness']['excluded_tail']},'error':None}
                journal.write('p1_result',result);completed+=1
                print(json.dumps({'completed_in_segment':completed,'planned_in_segment':len(pending),'request_id':row['request_id'],
                    'response_status':evaluation['response_completeness']['status'],'factual_label':evaluation['factual_support']['label']}),flush=True)
            server.assert_running();finalprops=client.request('/props');validate_server_properties(finalprops,config)
            if finalprops.get('build_info')!=props.get('build_info'):raise ValueError('Backend changed')
            post=pinned(config);journal.write('postflight',post)
            if post!=check:raise ValueError('Artifact identity changed')
        summary={'status':'PASS','scope':'P1 factorial adapter execution; semantic review pending','attempted':attempted,'received':received,'completed':completed,'real_inference_performed':True}
    except Exception as exc:
        journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'attempted':attempted,'received':received,'completed':completed})
        summary={'status':'PARTIAL' if completed else 'BLOCKED','attempted':attempted,'received':received,'completed':completed,'error':str(exc),'real_inference_performed':True if received else (None if attempted else False)}
    journal.finish(**summary);atomic_json(journal.directory/'summary.json',summary);print(json.dumps({'run_directory':journal.directory.as_posix(),**summary}),flush=True)
    if summary['status']!='PASS':raise SystemExit(2)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','prepare','run']);parser.add_argument('--resume',action='append',default=[]);args=parser.parse_args()
    if args.action=='run':run(args.resume)
    else:globals()[args.action]()
