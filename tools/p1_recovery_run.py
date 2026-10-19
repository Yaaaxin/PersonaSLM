"""Authorized P1 O/Q diagnostic only; D0 is archived, never generated.

Non-unique Q1 component requests are explicitly blocked, not substituted.
No retries, no factorial execution, no inference outside the global ledger.
"""
import argparse
import ast
import base64
import copy
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import p1_recovery_design as d
s, old, m, OUT, ROOT = d.s, d.old, d.m, d.OUT, d.ROOT
OLD=d.OLD
MANIFEST=OUT/'diagnostic_manifest_frozen_v1.json'
CLAIM=old.ROOT/'claims/C_RECOVERY_2X2_V1.json'


def source_hashes():
    return old.source_hashes() | {p.as_posix():s.sha256(p) for p in [Path('tools/p1_recovery_design.py'),Path('tools/p1_recovery_run.py')]}


def construct(c, condition, qspec):
    modified=copy.deepcopy(c)
    if condition in ('D1','D3'):modified['trusted_evidence']=d.organized_evidence(c)
    if condition in ('D2','D3'):
        modified['question']=qspec['question'];modified['reference']=qspec['reference']
    return modified


def prepare():
    s.require(not MANIFEST.exists(),'Preserve frozen recovery manifest')
    inv=s.load(OUT/'case_inventory_frozen_v1.json'); selected=inv['cases']
    # No researcher tie clarification is inferred from silence. The four
    # affected requests are ineligible under the currently unique-only rule.
    qs={};blocked=[]
    for c in selected:
        if len(d.q1_candidates(c))==1:qs[c['case_id']]=d.q1(c)
        else:
            blocked.extend({'request_id':c['case_id']+'_recovery_'+con,'case_id':c['case_id'],'condition':con,
                'state':'BLOCKED_BEFORE_INFERENCE','reason':'Q1_COMPONENT_PRIORITY_UNRESOLVED',
                'candidate_components':d.q1_candidates(c),'consumes_attempt':False} for con in ('D2','D3'))
    policy={'phase':'P1_ONLY','version':'p1_recovery_2x2_policy_v1','registered_utc':s.b.utc_now(),
        'user_instruction':'P1 Measurement Recovery, Prespecified 2x2 Diagnostic Experiment and Conditional Factorial Pilot Preparation',
        'primary_endpoint':'AUDITED TASK SUCCESS; no official decision from automatic or AI proposals',
        'conditions':{'D0':'Original evidence/question; reuse original C0 outputs','D1':'Entity/date-organized identical facts; original question',
                      'D2':'Original evidence; single-answer question','D3':'Entity/date-organized identical facts; single-answer question'},
        'O1_rule':'Group exact original fact lines by entity in lexical order, then valid_from, valid_to, attribute, source_id; add entity headings only. No fact removed or added.',
        'Q1_rule':'Unique original entity/date component whose entire evidence chain is valid at requested_date; otherwise first original required entity/date component. Multiple eligible components STOP affected Q1 requests; no unapproved tie-break.',
        'Q1_specs':qs,'Q1_blocked':blocked,
        'Q1_normalization':'Unicode NFKC, collapse whitespace, casefold, remove at most one trailing period; whole-answer equality to frozen aliases only. No markdown/prose stripping or substring credit.',
        'Q1_states':'Exact alias -> Success/Correct. Whole wrong bay code -> Failure/Incorrect. Empty observed answer -> Failure/Missing answer. No output record -> Missing. Other prose/contradiction -> Uncertain/Unverifiable, human review. N/A separate.',
        'Q0_scoring':'Original rubric and frozen automatic v2; preserve original labels and all scoring limitations.',
        'decision_rule':{'required_audited_records':32,'success_minimum_per_condition':6,'automatic_exact_agreement_minimum_per_condition':7,
            'denominator':8,'priority':['D0','D1','D2','D3'],'missing_audit':'SCIENTIFIC DECISION PENDING REVIEW',
            'family_zero_of_two':'NOT MEASUREMENT-READY; prospective development restriction only, no permanent scope change'},
        'future_pilot':'Prepare v2 only after audited qualification; 8 disjoint new development cases x10 conditions; separate execution authorization, audit 8 C0 first and proceed72 only at >=6/8 success.',
        'interpretation':'O is organization/position/format/length/salience package. Q changes cardinality and competence; not persona effects or pure retrieval/reasoning.',
        'persona_fidelity':'No S/F/H interventions. Q1 reduces style/behavior opportunity; insufficient opportunity is not zero. No fidelity validation.',
        'allocation_transfer':False,'maximum_new_attempts':24,'blocked_requests_not_replaced':True,
        'scientific_selection':'No future factorial case selection from observed calibration results.'}
    if (OUT/'prospective_policy_v1.json').exists():
        existing=s.load(OUT/'prospective_policy_v1.json')
        s.require({k:v for k,v in existing.items() if k!='registered_utc'}=={k:v for k,v in policy.items() if k!='registered_utc'},'Partial preparation policy changed')
        policy=existing
    else:s.save(OUT/'prospective_policy_v1.json',policy)
    authorization={'researcher':'Yaxin ZHENG','authorization_id':m.AUTH_ID,
        'source':policy['user_instruction']+' sections5,7,10,11,21','human_timestamp':None,'software_registration_utc':s.b.utc_now(),
        'category':'C_DIAGNOSTIC','maximum_new_attempts':24,'semantic_approval':False,'prior_attempts':old.cumulative(),
        'scope':'D1/D2/D3 only on frozen eight original calibration cases; D0 archived. Non-unique Q1 requests must stop.',
        'factorial_inference_authorized_this_execution':False,'no_retries':True}
    if (OUT/'authorization_registration_v1.json').exists():
        existing=s.load(OUT/'authorization_registration_v1.json')
        s.require({k:v for k,v in existing.items() if k!='software_registration_utc'}=={k:v for k,v in authorization.items() if k!='software_registration_utc'},'Partial preparation authorization changed')
    else:s.save(OUT/'authorization_registration_v1.json',authorization)
    parent=s.load(OLD/'A_C0_manifest_v1.json'); originals={r['case_id']:r for r in parent['requests']}
    template=Path(parent['template_path']).read_text(encoding='utf-8')
    sys.path.insert(0,str(Path('results/p1d_final_preparation/v1/tokenizer_runtime').resolve()))
    from tokenizers import Tokenizer
    tok=Tokenizer.from_file('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    exe=Path(parent['model']['backend_file']).with_name('llama-tokenize.exe')
    s.require(s.sha256(exe)==parent['native_tokenizer_identity']['tokenizer_sha256'],'Native tokenizer changed')
    requests=[];logs=[];views=[]
    # Fixed case-major D1,D2,D3 order, independent of labels and outcomes.
    for c in selected:
        for con in ('D0','D1','D2','D3'):
            if con in ('D2','D3') and c['case_id'] not in qs:continue
            cc=construct(c,con,qs.get(c['case_id'])); text=m.content(cc,'C0');prompt=s.render(template,[{'role':'user','content':text}])
            views.append({'case_id':c['case_id'],'condition':con,'question':cc['question'],'reference':cc['reference'],
                'trusted_evidence':cc['trusted_evidence'],'evidence_sha256':s.th(cc['trusted_evidence']),
                'question_sha256':s.th(cc['question']),'prompt_sha256':s.th(prompt),
                'facts_sha256':s.th(json.dumps(cc['facts'],sort_keys=True))})
            if con=='D0':
                s.require(prompt.encode()==originals[c['case_id']]['prompt'].encode(),'Archived D0 prompt changed');continue
            r=copy.deepcopy(originals[c['case_id']]);r.update(request_id=c['case_id']+'_recovery_'+con,condition=con,
                diagnostic_factors={'O':int(con in ('D1','D3')),'Q':int(con in ('D2','D3'))},
                parent_request_id=originals[c['case_id']]['request_id'],parent_request_sha256=originals[c['case_id']]['request_sha256'],
                messages=[{'role':'user','content':text}],prompt=prompt,prompt_sha256=s.th(prompt),
                reference=cc['reference'],reference_sha256=s.th(json.dumps(cc['reference'],sort_keys=True)),
                evidence_sha256=s.th(cc['trusted_evidence']),question_sha256=s.th(cc['question']))
            argv=[str(exe.resolve()),'-m',str(Path(parent['model']['model_file']).resolve()),'--stdin','--ids','--offline']
            proc=subprocess.run(argv,input=prompt.encode(),capture_output=True,timeout=60,
                env={k:v for k,v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            n={'argv':argv,'prompt':prompt,'returncode':proc.returncode,'stdout':proc.stdout.decode('utf-8','replace'),
               'stderr':proc.stderr.decode('utf-8','replace'),'recorded_utc':s.b.utc_now(),'generation_requests':0}
            lp=OUT/'native_tokenizer'/f'{len(requests):03d}.json';s.save(lp,n)
            s.require(proc.returncode==0,'Native tokenizer failed');ids=ast.literal_eval(n['stdout'].strip())
            s.require(ids==tok.encode(prompt,add_special_tokens=True).ids and tok.decode(ids,skip_special_tokens=False)==prompt,'Official/native token or byte reconstruction mismatch')
            r.update(order=len(requests),input_token_ids=ids,input_tokens=len(ids),input_token_ids_sha256=s.th(str(ids)),context_remaining=4096-96-len(ids))
            r.pop('request_sha256');r['request_sha256']=s.th(json.dumps(r,sort_keys=True,separators=(',',':')))
            requests.append(r);logs.append({'path':lp.as_posix(),'sha256':s.sha256(lp)})
    s.save(OUT/'prompt_comparisons_v1.json',views)
    bound=[OUT/'case_inventory_frozen_v1.json',OUT/'original_C0_audit_v1.json',OUT/'prospective_policy_v1.json',OUT/'authorization_registration_v1.json',
           OLD/'A_C0_manifest_v1.json',OLD/'materials_v1.json',OLD/'measurement_policy_v1.json',Path('tools/p1_measurement_scoring_v2.py'),Path('tools/p1_measurement_scoring.py')]
    plan={k:parent[k] for k in ('model','template_path','template_sha256','candidate_metadata_sha256','decoding_policy','native_tokenizer_identity')}
    plan.update(version='p1_recovery_2x2_manifest_v1',phase='P1',category='C_DIAGNOSTIC',authorization_id=m.AUTH_ID,
        independent_validation=False,proposed_requests=len(requests),maximum_authorized=24,requests=requests,blocked_requests=blocked,
        native_tokenizer_logs=logs,bound_sources={p.as_posix():s.sha256(p) for p in bound},
        d0_request_ids=[originals[c['case_id']]['request_id'] for c in selected],
        time_limit_minutes=45,no_retries=True,request_order='case_id ascending; D1,D2,D3; skip prospectively ineligible Q1, never replace')
    s.save(MANIFEST,plan);s.save(OUT/'manifest_binding_v1.json',{'path':MANIFEST.as_posix(),'sha256':s.sha256(MANIFEST)})
    return {'status':'FROZEN_ELIGIBLE_REQUESTS','requests':len(requests),'blocked':len(blocked),'sha256':s.sha256(MANIFEST)}


def validate():
    plan=s.load(MANIFEST);binding=s.load(OUT/'manifest_binding_v1.json')
    s.require(binding['sha256']==s.sha256(MANIFEST),'Recovery manifest changed')
    for p,h in plan['bound_sources'].items():s.require(s.sha256(Path(p))==h,'Bound source changed: '+p)
    parent=s.load(OLD/'A_C0_manifest_v1.json');originals={r['case_id']:r for r in parent['requests']}
    s.require(plan['model']==parent['model'] and plan['native_tokenizer_identity']==parent['native_tokenizer_identity'],'Model/tokenizer substitution')
    s.require(plan['template_sha256']==parent['template_sha256']==s.sha256(Path(plan['template_path'])),'Template changed')
    selected=d.select_cases(d.cases());cs={c['case_id']:c for c in selected};policy=s.load(OUT/'prospective_policy_v1.json')
    expected=[(c['case_id'],con) for c in selected for con in ('D1','D2','D3') if con=='D1' or c['case_id'] in policy['Q1_specs']]
    s.require([(r['case_id'],r['condition']) for r in plan['requests']]==expected,'Altered/reordered inventory')
    s.require(len(plan['requests'])==plan['proposed_requests'] and len(plan['requests'])+len(plan['blocked_requests'])==24,'Scope count')
    s.require(len({r['request_id'] for r in plan['requests']})==len(expected),'Duplicate identity')
    s.require(not plan['independent_validation'] and plan['phase']=='P1' and plan['category']=='C_DIAGNOSTIC','Wrong phase/scope')
    template=Path(plan['template_path']).read_text(encoding='utf-8')
    for i,(r,log) in enumerate(zip(plan['requests'],plan['native_tokenizer_logs'])):
        c=cs[r['case_id']];ref=originals[c['case_id']];cc=construct(c,r['condition'],policy['Q1_specs'].get(c['case_id']))
        s.require(c['pool']=='calibration' and c['independent_validation'] is False,'Not authorized development pool')
        s.require(s.render(template,[{'role':'user','content':m.content(c,'C0')}]).encode()==ref['prompt'].encode(),'D0 mismatch')
        s.require(r['messages']==[{'role':'user','content':m.content(cc,'C0')}] and r['prompt']==s.render(template,r['messages']),'Prompt mismatch')
        s.require(r['reference']==cc['reference'] and r['parent_request_sha256']==ref['request_sha256'],'Reference/comparator mismatch')
        for key in ('seed','temperature','top_p','max_new_tokens','stop','cache_prompt','ignore_eos','parse_special','factors','speaker_id','evaluation_date','context_sha256','applicability','split'):
            s.require(r[key]==ref[key],'Configuration change: '+key)
        s.require(r['order']==i and r['request_id']==c['case_id']+'_recovery_'+r['condition'],'ID/order')
        s.require(r['request_sha256']==s.th(json.dumps({k:v for k,v in r.items() if k!='request_sha256'},sort_keys=True,separators=(',',':'))),'Request hash')
        s.require(r['prompt_sha256']==s.th(r['prompt']) and r['input_token_ids_sha256']==s.th(str(r['input_token_ids'])),'Input hash')
        s.require(r['input_tokens']==len(r['input_token_ids']) and r['context_remaining']==4096-96-r['input_tokens']>0,'Context capacity')
        s.require(s.sha256(Path(log['path']))==log['sha256'],'Native log changed');n=s.load(log['path'])
        s.require(n['returncode']==0 and n['prompt']==r['prompt'] and ast.literal_eval(n['stdout'].strip())==r['input_token_ids'],'Native input mismatch')
    return plan


def preflight(resources=True):
    plan=validate();historical=old.audit('A_C0');s.require(historical['results']==32,'Historical D0 missing')
    cfg=s.config(plan);identity=s.b.file_preflight(cfg)
    s.require(identity['status']=='PASS' and identity['model']['sha256']==s.MODEL_SHA and identity['server']['sha256']==plan['model']['backend_sha256'],'Binary identity')
    native=plan['native_tokenizer_identity'];folder=Path(cfg.server_file).parent
    s.require(s.sha256(folder/'llama-tokenize.exe')==native['tokenizer_sha256'],'Tokenizer binary mismatch')
    s.require({p.name:s.sha256(p) for p in folder.glob('*.dll')}==native['dll_hashes'],'Native DLL mismatch')
    mem=s.memory_observation(os.getpid());available=mem.get('system',{}).get('available_physical',0)
    if resources:s.require(available>=3*1024**3,f'RAM preflight failed: {available}; unchanged requirement 3221225472 bytes')
    s.require(shutil.disk_usage('.').free>=1024**3,'Output disk reserve insufficient')
    return {'status':'PASS_FOR_ELIGIBLE_REQUESTS','checked_utc':s.b.utc_now(),'manifest_sha256':s.sha256(MANIFEST),
        'source_hashes':source_hashes(),'identity':identity,'configuration':cfg.as_dict(),'server_command':s.command(plan),
        'memory_before':mem,'ledger':old.cumulative(),'requests':plan['proposed_requests'],'blocked_requests':plan['blocked_requests'],
        'D0_integrity':'32 original HTTP/request/result reconstructions; eight D0 prompts byte-identical',
        'live_gate':'Exact tokenizer arrays and effective CPU configuration must pass before any generation'}


def run(preflight_path):
    fresh=preflight();stored=s.load(preflight_path);plan=validate()
    for key in ('manifest_sha256','source_hashes','configuration','server_command'):s.require(fresh[key]==stored[key],'Preflight changed: '+key)
    with s.b.writer_lock(old.ROOT):
        ledger=old.cumulative();s.require(not CLAIM.exists(),'Prior claim; no repeat or automatic retry')
        s.require(len(plan['requests'])<=24 and ledger['remaining_unreserved']['C_DIAGNOSTIC']>=len(plan['requests']),'Category cap')
        claim={'authorization_id':m.AUTH_ID,'category':'C_DIAGNOSTIC','maximum_attempts':len(plan['requests']),
            'manifest_sha256':s.sha256(MANIFEST),'preflight_sha256':s.sha256(preflight_path),'source_hashes':fresh['source_hashes']}
        s.save(CLAIM,claim)
        journal=s.b.RunJournal(ROOT/'runs',{'phase':'P1 measurement recovery','category':'C_DIAGNOSTIC','claim':claim,
            'authorization':s.load(OUT/'authorization_registration_v1.json'),'frozen_manifest':plan,'configuration':s.config(plan).as_dict(),
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_status':subprocess.check_output(['git','status','--short'],text=True),'python':platform.python_version(),'platform':platform.platform()})
        for path,digest in fresh['source_hashes'].items():
            dest=journal.directory/'source_snapshot'/path;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(Path(path).read_bytes())
            s.require(s.sha256(dest)==digest,'Source snapshot mismatch')
        tick=time.monotonic();active=None;status='BLOCKED'
        try:
            journal.write('preflight',fresh)
            with s.Server(plan,journal) as server:
                client=s.b.LlamaClient(s.config(plan).endpoint,timeout=180,audit=journal.write)
                props=client.request('/props');v=s.b.validate_server_properties(props,s.config(plan))
                s.require(v['build_info']=='b11573-0f701c882','Runtime backend mismatch')
                journal.write('effective_server_defaults',{'props':props,'validation':v})
                for row in plan['requests']:
                    ids=client.request('/tokenize',{'content':row['prompt'],'add_special':True,'parse_special':True,'with_pieces':False})['tokens']
                    s.require(ids==row['input_token_ids'],'Live tokenizer mismatch; no generation')
                    journal.write('live_prompt_verified',{'request_id':row['request_id'],'token_hash':s.th(str(ids))})
                print(json.dumps({'live_preflight':'PASS','requests':len(plan['requests'])}),flush=True)
                for row in plan['requests']:
                    remaining=2700-(time.monotonic()-tick);s.require(remaining>0,'45-minute ceiling');server.assert_running()
                    active=row['request_id'];client.timeout=min(180,remaining)
                    s.save(old.ROOT/'attempts'/(active+'.json'),{'authorization_id':m.AUTH_ID,'category':'C_DIAGNOSTIC','request_id':active,
                        'request_sha256':row['request_sha256'],'reserved_utc':s.b.utc_now(),'run_directory':journal.directory.as_posix()})
                    journal.write('p1_generation_started',row);start=time.monotonic()
                    response=client.request('/completion',s.payload(row));elapsed=time.monotonic()-start
                    journal.write('p1_raw_generation',{'request_id':active,'response':response,'latency_seconds':elapsed})
                    result=s.f.result(row,response,elapsed);journal.write('p1_result',result)
                    journal.write('memory_observation',s.memory_observation(server.process.pid))
                    print(json.dumps({'completed':row['order']+1,'tokens':result['generated_tokens'],'stop':result['stop_reason'],'seconds':round(elapsed,2)}),flush=True)
                    active=None
                after=preflight(False);s.require(after['identity']==fresh['identity'] and after['source_hashes']==fresh['source_hashes'],'Postflight source/binary change')
                journal.write('postflight',after)
            status='PASS'
        except BaseException as exc:
            status='PARTIAL' if active else 'BLOCKED';journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_id':active})
        a,raw,res=old.inventory(plan,s.b.read_events(journal.directory))
        summary={'status':status,'attempted':len(a),'responses_received':len(raw),'results':len(res),'elapsed_seconds':time.monotonic()-tick,
            'run_directory':journal.directory.as_posix(),'blocked_before_inference':len(plan['blocked_requests']),
            'human_semantic_ratings':0,'cumulative':old.cumulative()}
        journal.finish(**summary);s.save(journal.directory/'summary.json',summary);return summary


def audit():
    plan=validate();runs=list((ROOT/'runs').glob('*'));s.require(len(runs)==1,'Expected one recovery run')
    folder=runs[0];events=s.b.read_events(folder);attempts,raw,res=old.inventory(plan,events)
    sent=[e['data']['payload'] for e in events if e['kind']=='http_request' and e['data']['route']=='/completion']
    s.require(sent==[s.payload(r) for r in plan['requests'][:len(attempts)]],'HTTP/request inventory differs')
    bodies=[json.loads(base64.b64decode(e['data']['body_base64'])) for e in events if e['kind']=='http_response' and e['data']['route']=='/completion' and e['data'].get('status')==200]
    s.require(bodies==[r['response'] for r in raw.values()],'Raw HTTP body preservation')
    rows=[]
    for r in plan['requests']:
        rid=r['request_id'];v=s.f.result(r,raw[rid]['response'],raw[rid]['latency_seconds']) if rid in raw else None
        if rid in res:s.require(v==res[rid],'Result reconstruction differs')
        rows.append({'request':r,'result':v,'state':'COMPLETED' if rid in res else 'ATTEMPTED_UNRESOLVED' if rid in attempts else 'UNATTEMPTED'})
    return {'run_directory':folder.as_posix(),'attempted':len(attempts),'results':len(res),'rows':rows,
        'manifest_sha256':s.sha256(MANIFEST),'blocked_requests':plan['blocked_requests'],'cumulative':old.cumulative()}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','preflight','run','audit']);p.add_argument('--output',type=Path);p.add_argument('--preflight',type=Path);args=p.parse_args()
    try:value=run(args.preflight) if args.action=='run' else globals()[args.action]()
    except Exception as exc:
        value={'status':'BLOCKED','error':str(exc),'recorded_utc':s.b.utc_now(),'new_generations':0,'memory':s.memory_observation(os.getpid())}
        if args.output:s.save(args.output,value)
        print(json.dumps(value,indent=2));raise SystemExit(2)
    if args.output:s.save(args.output,value)
    print(json.dumps({k:v for k,v in value.items() if k not in ('rows','source_hashes','identity')},indent=2))
