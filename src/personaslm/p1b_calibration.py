"""Manifest-bound P1b adapter. Offline checks never launch an inference server."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import platform
import subprocess
import time

from .configuration import RuntimeConfig, preflight as file_preflight
from .inference import LlamaClient, normalize_result, validate_token_ids
from .journal import RunJournal, atomic_json, read_events, utc_now
from .p1b import canonical_hash, hash_text
from .p1b_readiness import audit, requests, validate_reviews
from .provenance import require_local_path, repository_root, sha256
from .response_status import classify_response
from .runner import validate_completion
from .scientific_closure import reconcile_tokenizations
from .server import ManagedServer, validate_server_properties

VERSION = 'p1b_calibration_adapter_v1'
MANIFEST = Path('docs/validation/p1b/final_review_v1/calibration_manifest_v2.json')
MANIFEST_SHA = 'd73ceb403148b01f7b2c83a51a20165fdd625658e50c04a7ce0caa118ab22869'
DATA = Path('data/synthetic/p1b_development_proposed_v2.json')
DATA_SHA = 'fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6'
MODEL_SHA = 'ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994'
BACKEND_SHA = '71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846'
ROUTING = Path('docs/validation/p1b/final_v1/evaluation_routing_v1.json')
MASTER = Path('docs/validation/p1b/final_v1/stimulus_review_v2.csv')
RUN_ROOT = Path('results/p1b_calibration/development_v1')
DECODING = {'cache_prompt':False,'n_predict':96,'return_tokens':True,'seed':42,
            'stop':[],'stream':False,'temperature':0.0,'top_p':1.0}
AXES = ('response_relevance','factual_consistency','temporal_consistency','conversational_coherence')


def load(path):
    return json.loads(require_local_path(path).read_text(encoding='utf-8'))


def csv_records(path):
    import csv
    with require_local_path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); rows=list(reader)
        if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError('CSV headers missing or duplicated')
    if any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError('CSV row width differs')
    return rows


def validate_plan(data, plan):
    """Validate exact cells/order/inputs independently of a filename or status."""
    audit(data)
    if plan['dataset_sha256']!=DATA_SHA or plan['generation_parameters']!=DECODING:
        raise ValueError('Frozen dataset or decoding differs')
    expected=requests(data)
    if len(plan['requests'])!=192 or len(expected)!=192:
        raise ValueError('Exactly 192 requests required')
    for planned, actual in zip(expected,plan['requests']):
        ignored={'input_token_ids','input_token_count','tokenizer_preflight','context_fit'}
        if any(actual.get(k)!=v for k,v in planned.items() if k not in ignored):
            raise ValueError('Frozen prompt/order/factors/applicability mismatch')
        ids=validate_token_ids(actual['input_token_ids'],allow_empty=False)
        if type(actual['input_token_count']) is not int or len(ids)!=actual['input_token_count']:
            raise ValueError('Token count mismatch')
        if canonical_hash(ids)!=actual['token_ids_sha256'] or hash_text(actual['prompt'])!=actual['prompt_sha256']:
            raise ValueError('Token or prompt hash mismatch')
        if len(ids)+96>4096 or actual['remaining_context_after_output_budget']!=4096-len(ids)-96:
            raise ValueError('Context overflow or accounting mismatch')
    if (plan['order_seed']!=714001 or plan['response_status_version']!='response_status_v1'
        or plan['evaluation_policy_version']!='separate_axes_policy_v1'
        or plan['evaluation_routing_version']!='p1b_manual_semantic_routing_proposed_v1'
        or plan['neutral_control_requests']!=0 or plan['executed_requests']!=0 or plan['execution_authorized'] is not False):
        raise ValueError('Frozen scope or policies differ')
    return {'cases':24,'requests':192,'factorial_inputs':'PASS','order_seed':714001,
            'factual_eligible':192,'temporal_eligible':sum(r['applicability']['temporal_consistency'] for r in plan['requests'])}


def pinned_runtime(plan):
    config=RuntimeConfig.load(Path('configs/p1_wave1_v1.json'))
    rendered={**config.as_dict(),'prompt_template':'p1b_transcript_proposed_v1','threads_batch':4,'n_gpu_layers':0}
    if rendered!=plan['configuration']:
        raise ValueError('Transport configuration differs; legacy template is not used to render prompts')
    check=file_preflight(config)
    if check['status']!='PASS' or check['model']['sha256']!=MODEL_SHA or check['server']['sha256']!=BACKEND_SHA:
        raise ValueError('Pinned model/backend file identity mismatch')
    return config,check


def offline_preflight():
    """Reconcile already-observed native tokenization. No network or process launch."""
    if sha256(require_local_path(MANIFEST))!=MANIFEST_SHA or sha256(require_local_path(DATA))!=DATA_SHA:
        raise ValueError('Frozen manifest/dataset byte hash differs')
    plan=load(MANIFEST); data=load(DATA)
    checks=validate_plan(data,plan)
    folder=MANIFEST.parent
    proof=load(folder/'tokenizer_verification_v1.json')
    run=require_local_path(Path(proof['run_directory']))
    if proof['new_manifest_sha256']!=MANIFEST_SHA or proof['model_sha256']!=MODEL_SHA or proof['backend_sha256']!=BACKEND_SHA:
        raise ValueError('Native tokenizer provenance differs')
    if sha256(run/'manifest.json')!=proof['run_manifest_sha256'] or sha256(run/'server.log')!=proof['server_log_sha256']:
        raise ValueError('Native tokenizer log changed')
    if {p.name:sha256(p) for p in (run/'events').glob('*.json')}!=proof['event_hashes']:
        raise ValueError('Native tokenizer event bytes changed')
    events=read_events(run)
    if any(e['kind']=='http_request' and e['data']['route']=='/completion' for e in events):
        raise ValueError('Unexpected completion in tokenizer-only provenance')
    observed=[e['data'] for e in events if e['kind']=='p1b_prompt_tokenized']
    if observed!=plan['requests'] or reconcile_tokenizations(events,[(r['prompt'],r['input_token_ids']) for r in observed])!=192:
        raise ValueError('Native tokenizer input reconstruction differs')
    for p,h in plan['source_hashes'].items():
        if sha256(require_local_path(Path(p)))!=h:
            raise ValueError('Original tokenizer/rendering source changed: '+p)
    routing=load(ROUTING)
    if routing['city_scorer_allowed'] or routing['automatic_semantic_scorer'] is not None:
        raise ValueError('Unsupported automatic semantic scoring requested')
    _,identity=pinned_runtime(plan)
    # Public return is portable; complete absolute-path file checks stay in local captures if needed.
    return {**checks,'version':VERSION,'technical_readiness':'PASS','scientific_review':'PENDING',
        'inference_authorization':'PENDING','manifest_sha256':MANIFEST_SHA,'dataset_sha256':DATA_SHA,
        'model_sha256':identity['model']['sha256'],'backend_sha256':identity['server']['sha256'],
        'backend_build':proof['binding']['build_info'],'native_tokenizations_reconciled':192,
        'token_range':[min(r['input_token_count'] for r in observed),max(r['input_token_count'] for r in observed)],
        'evidence_scope':'Current file hashes plus replay of prior real native tokenizations; no new live server observation',
        'new_server_launches':0,'new_generation_requests':0,'new_tokenizer_requests':0,
        'live_pre_generation_gate':'Recheck all 192 prompt IDs on the owned pinned backend before any completion',
        'routing_sha256':sha256(require_local_path(ROUTING))}


def semantic_pending(case, raw=None, backend=None):
    """No city grammar or answer-substring scoring for the new task families."""
    boundary=classify_response(raw,backend,declared_stops=()) if raw is not None else None
    axes={}
    for axis in AXES:
        eligible=case['applicability'][axis]
        axes[axis]={'eligible':eligible,'label':('PENDING' if eligible else 'Not Applicable'),
                    'rating':None,'assessment_status':('AWAITING_HUMAN_REVIEW' if raw is not None else 'NO_RESPONSE') if eligible else 'INAPPLICABLE',
                    'missing_response':raw is None,'unit_identifiable':boundary['unit_identifiable'] if boundary else None,
                    'rule':'Task-specific evidence and proposition dates; no structural-status correctness penalty'}
    return {'axis_policy':'separate_axes_policy_v1','routing_version':'p1b_manual_semantic_routing_proposed_v1',
            'applicability':dict(case['applicability']),'response_status':boundary,
            'semantic_completeness':{'label':None,'assessment_status':'AWAITING_HUMAN_REVIEW'},
            'axes':axes,'factual_categories':['Correct','Incorrect','Unverifiable','Not Applicable'],
            'annotation_state_is_not_a_factual_category':True,'persona_fidelity_scored':False,
            'expected_answer':case['expected_answer'],'evaluation_date':case['evaluation_date'],
            'trusted_evidence':case['trusted_evidence'],'question':case['question'],
            'task_family':case['task_family'],'primary_denominator_retained':True}


def result_from_response(row, case, response, latency):
    token_audit=validate_completion(response,row['input_token_ids'])
    normalized=normalize_result(response)
    count=response.get('tokens_predicted')
    if type(count) is not int or not 0<=count<=96:
        raise ValueError('Actual generated token count missing or invalid')
    if normalized['token_ids_status']=='returned' and len(normalized['generated_token_ids'])!=count:
        raise ValueError('Generated ID/count mismatch')
    evaluation=semantic_pending(case,normalized['raw_response'],normalized['raw_termination'])
    boundary=evaluation['response_status']
    return {**row,**normalized,'generated_tokens':count,'latency_seconds':latency,'token_audit':token_audit,
            'evaluation':evaluation,'parsed_response':boundary['first_span']['text'],
            'parser_operations':{k:boundary[k] for k in ('first_span','removed_prefix','excluded_tail')},
            'error':None}


def attempt_one(row, case, client, journal):
    """Write-ahead attempt and raw bytes precede every validation/transformation."""
    journal.write('p1b_generation_started',row)
    started=time.monotonic()
    response=client.complete(row['input_token_ids'],seed=42,max_new_tokens=96)
    latency=time.monotonic()-started
    journal.write('p1b_raw_generation',{'request_id':row['request_id'],'response':response,'latency_seconds':latency})
    result=result_from_response(row,case,response,latency)
    journal.write('p1b_result',result)
    return result


def resume_inventory(plan, segments):
    """At most one attempt per planned ID. Uncertain sends never retry silently."""
    attempted=[]; results={}; raw={}
    ids=[r['request_id'] for r in plan['requests']]
    for events in segments:
        local_started=set(); local_raw=set()
        for event in events:
            k=event['kind']; d=event['data']
            if k=='p1b_generation_started':
                rid=d['request_id']
                if rid in attempted or rid not in ids:
                    raise ValueError('Duplicate or unplanned attempt')
                if d!=plan['requests'][len(attempted)]:
                    raise ValueError('Attempt input/order differs')
                attempted.append(rid); local_started.add(rid)
            elif k=='p1b_raw_generation':
                rid=d['request_id']
                if rid not in local_started or rid in raw:
                    raise ValueError('Raw response lacks unique attempt')
                raw[rid]=d; local_raw.add(rid)
            elif k=='p1b_result':
                rid=d['request_id']
                if rid not in local_raw or rid in results:
                    raise ValueError('Result lacks unique raw response')
                results[rid]=d
    return {'attempted_ids':attempted,'results':results,'raw':raw,
            'pending':plan['requests'][len(attempted):],
            'attempted_without_result':[r for r in attempted if r not in results]}


def verify_authorization(auth, review, master, preflight, *, actual_review_hash, actual_preflight_hash):
    if auth.get('authorized') is not True or auth.get('final_decision_authority')!='researcher':
        raise ValueError('Explicit researcher inference authorization is missing')
    if auth.get('researcher_id')!='Yaxin_ZHENG' or not auth.get('decision_source','').strip():
        raise ValueError('Researcher identity and real decision source are required')
    expected={'manifest_sha256':MANIFEST_SHA,'dataset_sha256':DATA_SHA,'max_total_attempts':192,
              'review_registration_sha256':actual_review_hash,'preflight_sha256':actual_preflight_hash,
              'adapter_version':VERSION,'allow_automatic_retries':False}
    if any(type(auth.get(k)) is not type(v) or auth.get(k)!=v for k,v in expected.items()):
        raise ValueError('Authorization is not bound to this exact bounded plan and review')
    if preflight.get('technical_readiness')!='PASS' or preflight.get('manifest_sha256')!=MANIFEST_SHA:
        raise ValueError('Valid non-generation preflight required')
    if review.get('manifest_sha256')!=MANIFEST_SHA or review.get('dataset_sha256')!=DATA_SHA:
        raise ValueError('Review applies to different stimuli')
    if review.get('interpretation_confirmed') is not True or review.get('evaluation_routing_confirmed') is not True:
        raise ValueError('Limited scientific interpretation and scoring routing remain unconfirmed')
    if not validate_reviews(master,review.get('records',[]))['all_accepted']:
        raise ValueError('Every stimulus must be accepted')


def source_inventory():
    root=repository_root()
    files=sorted((root/'src/personaslm').glob('*.py'))+[root/'tools/p1b_calibration.py',
           root/'tools/p1b_review_proposal.py',root/'docs/research_protocol_v1.1.md',
           root/'configs/p1_wave1_v1.json',root/ROUTING]
    return {p.relative_to(root).as_posix():sha256(p) for p in files}


def ordered_segments(root, claim):
    """Use explicit sequence numbers; UUID directory names are not chronological."""
    segments=[]
    for directory in require_local_path(root/'runs').glob('*'):
        if not directory.is_dir():
            raise ValueError('Unexpected run artifact')
        manifest=load(directory/'manifest.json')
        index=manifest.get('segment_index')
        if manifest.get('claim')!=claim or type(index) is not int or index<1:
            raise ValueError('Segment claim/index mismatch')
        segments.append((index,directory,manifest))
    segments.sort(key=lambda row:row[0])
    if [r[0] for r in segments]!=list(range(1,len(segments)+1)):
        raise ValueError('Duplicate or missing segment index')
    return [(directory,manifest) for _,directory,manifest in segments]


@contextmanager
def writer_lock(folder):
    folder=require_local_path(folder); folder.mkdir(parents=True,exist_ok=True)
    path=folder/'active_writer.lock'
    # A stale lock after a hard process kill is deliberately not removed automatically.
    with path.open('x',encoding='utf-8') as f:
        f.write(json.dumps({'pid':os.getpid(),'created_utc':utc_now()})); f.flush(); os.fsync(f.fileno())
    try:
        yield
    finally:
        path.unlink()


def run_authorized(authorization, review_path, preflight_path, *, resume=False):
    """Only called by the explicit run command after independent review/authorization."""
    auth_path=require_local_path(authorization); review_path=require_local_path(review_path); preflight_path=require_local_path(preflight_path)
    auth=load(auth_path); review=load(review_path); prepared=load(preflight_path)
    verify_authorization(auth,review,csv_records(MASTER),prepared,
                         actual_review_hash=sha256(review_path),actual_preflight_hash=sha256(preflight_path))
    if prepared.get('source_hashes')!=source_inventory():
        raise ValueError('Execution source changed after preflight; revalidate a separate preflight record')
    offline_preflight()
    plan=load(MANIFEST); cases={c['case_id']:c for c in load(DATA)['cases']}
    config,check=pinned_runtime(plan)
    root=require_local_path(RUN_ROOT)
    with writer_lock(root):
        claim={'manifest_sha256':MANIFEST_SHA,'authorization_sha256':sha256(auth_path),
               'review_sha256':sha256(review_path),'preflight_sha256':sha256(preflight_path),
               'source_hashes':source_inventory(),'maximum_total_attempts':192}
        claim_path=root/'claim.json'
        if claim_path.exists():
            if not resume or load(claim_path)!=claim:
                raise ValueError('Existing wave needs explicit resume with identical authorization/source binding')
        else:
            if resume or list((root/'runs').glob('*')):
                raise ValueError('Missing claim or unexplained run segments')
            atomic_json(claim_path,claim)
        previous=[]; links=[]
        for directory,m in ordered_segments(root,claim):
            if m.get('prior_segments')!=links:
                raise ValueError('Historical segment provenance changed')
            events=read_events(directory); previous.append(events)
            links.append({'directory':directory.relative_to(repository_root()).as_posix(),
                          'manifest_sha256':sha256(directory/'manifest.json'),
                          'event_hashes':{p.name:sha256(p) for p in (directory/'events').glob('*.json')}})
        inventory=resume_inventory(plan,previous)
        if not inventory['pending']:
            raise ValueError('No unattempted requests remain; audit failures offline, never rerun successful outputs')
        git={'sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             'status':subprocess.check_output(['git','status','--short'],text=True)}
        journal=RunJournal(root/'runs',{'phase':'P1b','operation':'development_calibration_generation','adapter_version':VERSION,
            'claim':claim,'segment_index':len(previous)+1,'authorization':auth,'review_registration':review,'frozen_manifest':plan,
            'git':{**git,'dirty':bool(git['status'].strip())},'prior_segments':links,
            'pending_request_ids':[r['request_id'] for r in inventory['pending']],
            'cpu_configuration':plan['configuration'],'decoding':DECODING,
            'python':platform.python_version(),'os':platform.platform(),'cpu_reported':platform.processor(),
            'unavailable_hardware_observations':'No independent new physical CPU/RAM inventory; runtime log and process memory retained'})
        for name,h in claim['source_hashes'].items():
            p=require_local_path(Path(name)); content=p.read_bytes()
            destination=journal.directory/'source_snapshot'/name; destination.parent.mkdir(parents=True,exist_ok=True)
            with destination.open('xb') as f: f.write(content)
            if sha256(destination)!=h:
                raise ValueError('Source changed while snapshotting')
        attempted=received=completed=0; active=None
        try:
            journal.write('preflight',check)
            with ManagedServer(config,journal) as server:
                client=LlamaClient(config.endpoint,timeout=config.timeout,audit=journal.write)
                props=client.request('/props'); binding=validate_server_properties(props,config)
                if binding['build_info']!='b11573-0f701c882':
                    raise ValueError('Pinned loaded backend build differs')
                journal.write('tokenizer_binding',{'properties':props,'validation':binding})
                # Complete this entire live check before any generation in each segment.
                for row in plan['requests']:
                    ids=client.tokenize(row['prompt'])
                    if ids!=row['input_token_ids'] or len(ids)+96>4096:
                        raise ValueError('Live tokenizer changed or context overflow')
                    journal.write('p1b_live_prompt_verified',row)
                for row in inventory['pending']:
                    server.assert_running(); active=row['request_id']
                    attempted+=1
                    result=attempt_one(row,cases[row['case_id']],client,journal)
                    received+=1; completed+=1
                    print(json.dumps({'request_id':active,'segment_completed':completed,
                        'structural_status':result['evaluation']['response_status']['status'],'semantic_scoring':'PENDING'}),flush=True)
                    active=None
                server.assert_running()
                end_props=client.request('/props'); validate_server_properties(end_props,config)
                if end_props.get('build_info')!=props.get('build_info'):
                    raise ValueError('Loaded backend changed')
                _,after=pinned_runtime(plan); journal.write('postflight',after)
                if after!=check:
                    raise ValueError('Model/backend identity changed')
            status='PASS'
        except BaseException as exc:
            status='PARTIAL' if attempted else 'BLOCKED'
            journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_id':active})
        # Count persisted observations, including a raw reply rejected by validation.
        observed=read_events(journal.directory)
        attempted=sum(e['kind']=='p1b_generation_started' for e in observed)
        received=sum(e['kind']=='p1b_raw_generation' for e in observed)
        summary={'status':status,'scope':'Adapter segment execution only; human response assessment pending',
                 'attempted':attempted,'responses_received':received,'results':completed,
                 'resume_required':status!='PASS','real_inference_performed':True if received else (None if attempted else False)}
        journal.finish(**summary); atomic_json(journal.directory/'summary.json',summary)
        return journal.directory,summary


def audit_segments(plan, cases, segments):
    inventory=resume_inventory(plan,segments)
    rows=[]
    for row in plan['requests']:
        rid=row['request_id']; saved=inventory['results'].get(rid); raw=inventory['raw'].get(rid)
        derived=None; error=None
        if raw is not None:
            try:
                derived=result_from_response(row,cases[row['case_id']],raw['response'],raw['latency_seconds'])
            except (ValueError,KeyError,TypeError) as exc:
                error=str(exc)
        if saved is not None and saved!=derived:
            raise ValueError('Saved parser/evaluation reconstruction differs')
        status=('COMPLETED' if saved else 'RAW_RECOVERABLE_WITHOUT_GENERATION') if derived else (
            'RAW_INVALID' if raw else 'ATTEMPTED_NO_RAW_RESPONSE' if rid in inventory['attempted_ids'] else 'UNATTEMPTED')
        rows.append({'request_id':rid,'case_id':row['case_id'],'condition':row['condition'],
            'technical_status':status,'result':derived,'error':error,'raw_record':raw,
            'evaluation':derived['evaluation'] if derived else semantic_pending(cases[row['case_id']]),
            'primary_denominator_retained':True})
    return {'version':'p1b_offline_reconstruction_v1','rows':rows,'planned':192,
            'attempted':len(inventory['attempted_ids']),'pending':len(inventory['pending']),
            'no_model_calls':True,'automatic_retries':False}
