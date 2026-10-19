"""Exactly eight newly authorized P5 oracle-package attempts; immutable prior runs."""
import argparse
import ast
import base64
import json
from pathlib import Path
import platform
import subprocess
import time
import p1d_instruct_smoke as s
from p5_oracle_proposal import proof_ids

b=s.b
SOURCE=Path('docs/validation/p5/oracle_evidence_proposed_v1/oracle_evidence_manifest_proposed_v1.json')
SHA='894b7f0604f1f4c6121c1aefa1e24ee25c59a12c9e5be687e6403d9066d3c08e'
OUT=Path('docs/validation/p5/oracle_diagnostic_v1')
ROOT=Path('results/p5_oracle_diagnostic/development_v1')
FROZEN=OUT/'frozen_manifest_v1.json'
AUTH=OUT/'researcher_authorization_v1.json'
load,save,sha,require,th=s.load,s.save,s.sha256,s.require,s.th

def sources():
    return s.sources()|{p.as_posix():sha(p) for p in (Path(__file__).relative_to(Path.cwd()),Path('tools/p5_oracle_proposal.py'))}

def validate(plan):
    require(plan['version']=='p5_oracle_evidence_proposed_v1' and plan['proposed_requests']==8,'Scope mismatch')
    parent=load(s.FROZEN);require(sha(s.FROZEN)==plan['parent_manifest_sha256']==s.SHA,'Parent changed')
    require(plan['model']==parent['model'] and plan['template_sha256']==parent['template_sha256'],'Configuration changed')
    cases={c['case_id']:c for c in load(b.DEV/'development_examples_v5.json')['cases']}
    heldout={c['case_id'] for c in load('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')['cases']}
    rows=plan['requests'];require(len(rows)==len({r['request_id'] for r in rows})==8,'Eight unique requests required')
    require({r['case_id'] for r in rows}==set(b.CASE_IDS) and not heldout.intersection(b.CASE_IDS),'Development identity mismatch')
    changes=[];template=Path(plan['template_path']).read_text(encoding='utf-8')
    require(sha(Path(plan['template_path']))==plan['template_sha256'],'Template mismatch')
    for i,(r,old,log) in enumerate(zip(rows,parent['requests'],plan['native_tokenizer_logs'])):
        require(r['order']==i and r['request_id']=='p5_oracle_dev_v1_'+r['case_id'],'Request identity/order')
        c=cases[r['case_id']];require(c['independent_validation'] is False,'Independent test case prohibited')
        require(r['case_id']==old['case_id'] and r['parent_request_sha256']==old['request_sha256'],'Parent pair mismatch')
        for k in ('reference','reference_sha256','speaker_id','condition','seed','temperature','top_p','cache_prompt','stop','ignore_eos','parse_special','max_new_tokens','split'):
            require(r[k]==old[k],'Frozen setting changed: '+k)
        require(r['condition']=='H_none' and r['max_new_tokens']==96,'Forbidden setting')
        ids=proof_ids(c);require(r['selected_source_ids']==ids,'Oracle sources changed')
        evidence='\n'.join(line for line in c['trusted_evidence'].splitlines() if line.split(']',1)[0][1:] in ids)
        require(evidence==r['trusted_evidence'],'Oracle evidence text changed')
        msg=[dict(x) for x in old['messages']];msg[0]['content']=msg[0]['content'].replace(c['trusted_evidence'],evidence)
        require(r['messages']==msg and s.render(template,msg)==r['prompt'],'Changes outside evidence block')
        require(r['prompt_sha256']==th(r['prompt']) and r['input_token_ids_sha256']==th(str(r['input_token_ids'])),'Prompt/token hashes')
        require(r['request_sha256']==th(json.dumps({k:v for k,v in r.items() if k!='request_sha256'},sort_keys=True,separators=(',',':'))),'Request hash')
        require(len(r['input_token_ids'])==r['input_tokens'] and r['context_remaining']==4096-96-r['input_tokens'],'Capacity mismatch')
        require(sha(Path(log['path']))==log['sha256'],'Native log changed')
        native=load(log['path']);require(ast.literal_eval(native['stdout'].strip())==r['input_token_ids'] and native['prompt']==r['prompt'],'Native IDs mismatch')
        changes.append({'case_id':c['case_id'],'old_request_id':old['request_id'],'new_request_id':r['request_id'],
            'old_input_tokens':old['input_tokens'],'new_input_tokens':r['input_tokens'],
            'old_evidence_rows':len(c['facts']),'new_evidence_rows':len(ids),'source_ids':ids,
            'literal_required_values_in_oracle':{x['key']:x['value'] in evidence for x in c['required_components']},
            'changed_fields':['trusted_evidence','prompt','messages','input_token_ids','token_count','positions','request identity'],
            'answer_sufficiency':'Both full and reduced ledgers are sufficient; oracle is selected with reference witnesses.',
            'reference_changed':False})
    return changes

def register():
    require(sha(SOURCE)==SHA,'Authorized hash mismatch: STOP inference')
    require(not AUTH.exists() and not FROZEN.exists() and not (ROOT/'claim.json').exists(),'Existing registration/execution; no repeat')
    prior=[]
    for p in Path('results').rglob('manifest.json'):
        d=load(p)
        if d.get('claim',{}).get('manifest_sha256')==SHA:prior.append(str(p))
    require(not prior,'Exact previous execution exists: '+str(prior))
    changes=validate(load(SOURCE));OUT.mkdir(parents=True,exist_ok=True)
    with FROZEN.open('xb') as f:f.write(SOURCE.read_bytes())
    save(AUTH,{'version':'p5_oracle_authorization_v1','researcher':'Yaxin ZHENG','decision':'AUTHORIZED',
        'source':'Latest explicit user instruction: P5 Oracle Diagnostic, Core S/F/H Validation Readiness, Persona Fidelity and Algorithmic Novelty Assessment, section 4',
        'human_decision_timestamp':None,'registered_utc':b.utc_now(),'manifest_sha256':SHA,'maximum_attempts':8,
        'requested_path':'docs/validation/p1d/oracle_evidence_proposed_v1/oracle_evidence_manifest_proposed_v1.json',
        'resolved_original_path':SOURCE.as_posix(),'path_resolution':'Original p5 path identified by exact authorized SHA and unchanged preceding decision packet; no file substitution or relocation.',
        'partial_model_lineage':'Previously disclosed partial third-party conversion provenance retained; development only.',
        'time_limit_minutes':45,'no_retries':True,'semantic_adoption':False,'previous_execution_found':False})
    save(OUT/'intervention_difference_inventory_v1.json',changes)
    tracked=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
    previous=Path('docs/validation/p1d/instruct_smoke_v1/reproducibility_manifest_v1.json')
    seal=load(previous);require(all(sha(Path(p))==h for p,h in seal['artifact_sha256'].items()),'Previous milestone changed')
    save(OUT/'preservation_baseline_v1.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'initial_git_status':subprocess.check_output(['git','status','--short'],text=True),
        'tracked_sha256':{p:sha(Path(p)) for p in tracked if p and Path(p).is_file()},
        'previous_seal':previous.as_posix(),'previous_seal_sha256':sha(previous)})
    return {'registered':8,'manifest_sha256':SHA,'prior_execution':False}

def preflight(check_headroom=True):
    require(sha(SOURCE)==sha(FROZEN)==SHA,'Exact oracle hash mismatch')
    auth=load(AUTH);require(auth['decision']=='AUTHORIZED' and auth['manifest_sha256']==SHA and auth['maximum_attempts']==8,'Authorization mismatch')
    changes=validate(load(FROZEN))
    # Reuse the pinned identity/resource checker, not its exhausted authorization.
    identity=s.preflight(check_headroom=check_headroom)
    identity.update(manifest_sha256=SHA,authorization_sha256=sha(AUTH),source_hashes=sources(),
        checks={'requests':8,'cases':8,'speakers':8,'heldout_overlap':0,'oracle_differences':changes},
        server_command=s.command(load(FROZEN)))
    return identity

def run(preflight_path):
    fresh=preflight();stored=load(preflight_path);plan=load(FROZEN)
    for k in ('manifest_sha256','authorization_sha256','source_hashes','configuration','server_command'):
        require(fresh[k]==stored[k],'Changed preflight binding: '+k)
    with b.writer_lock(ROOT):
        require(not (ROOT/'claim.json').exists() and not list((ROOT/'runs').glob('*')),'Previous attempt: no retry')
        claim={k:fresh[k] for k in ('manifest_sha256','authorization_sha256','source_hashes')}
        claim.update(maximum_attempts=8,preflight_sha256=sha(preflight_path));save(ROOT/'claim.json',claim)
        journal=b.RunJournal(ROOT/'runs',{'phase':'P5 oracle evidence development diagnostic','rq':['RQ4'],
            'estimand':'Oracle evidence package versus exact historical full-ledger Instruct requests',
            'claim':claim,'frozen_manifest':plan,'authorization':load(AUTH),'configuration':s.config(plan).as_dict(),
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_status':subprocess.check_output(['git','status','--short'],text=True),'python':platform.python_version(),'platform':platform.platform()})
        for path,digest in claim['source_hashes'].items():
            dest=journal.directory/'source_snapshot'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(Path(path).read_bytes())
            require(sha(dest)==digest,'Source snapshot changed')
        started=time.monotonic();active=None;status='BLOCKED'
        try:
            journal.write('preflight',fresh)
            with s.Server(plan,journal) as server:
                client=b.LlamaClient(s.config(plan).endpoint,timeout=180,audit=journal.write)
                props=client.request('/props');v=b.validate_server_properties(props,s.config(plan))
                require(v['build_info']=='b11573-0f701c882','Backend identity mismatch')
                journal.write('effective_server_defaults',{'props':props,'validation':v})
                for r in plan['requests']:
                    tokens=client.request('/tokenize',{'content':r['prompt'],'add_special':True,'parse_special':True,'with_pieces':False})['tokens']
                    require(tokens==r['input_token_ids'],'Live prompt token mismatch; no completion permitted')
                    journal.write('live_prompt_verified',{'request_id':r['request_id'],'input_tokens':len(tokens)})
                print(json.dumps({'live_preflight':'PASS','scope':8}),flush=True)
                for r in plan['requests']:
                    remaining=2700-(time.monotonic()-started);require(remaining>0,'Time limit reached')
                    server.assert_running();client.timeout=min(180,remaining);active=r['request_id']
                    journal.write('instruct_generation_started',r)
                    tick=time.monotonic();response=client.request('/completion',s.payload(r));elapsed=time.monotonic()-tick
                    journal.write('instruct_raw_generation',{'request_id':active,'response':response,'latency_seconds':elapsed})
                    result=s.f.result(r,response,elapsed);journal.write('instruct_result',result)
                    print(json.dumps({'order':r['order'],'request':active,'tokens':result['generated_tokens'],'stop':result['stop_reason'],'text':result['raw_response']}),flush=True)
                    active=None
                server.assert_running();b.validate_server_properties(client.request('/props'),s.config(plan))
                after=preflight(False);require(after['identity']==fresh['identity'] and after['source_hashes']==fresh['source_hashes'],'Postflight source/binary change')
                journal.write('postflight',after)
            status='PASS'
        except BaseException as exc:
            status='PARTIAL' if active else 'BLOCKED';journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_id':active})
        events=b.read_events(journal.directory);attempts,raw,results=s.inventory(plan,events)
        summary={'status':status,'attempted':len(attempts),'responses_received':len(raw),'results':len(results),
                 'elapsed_seconds':time.monotonic()-started,'run_directory':journal.directory.as_posix(),'human_semantic_ratings':0}
        journal.finish(**summary);save(journal.directory/'summary.json',summary);return summary

def audit():
    require(sha(SOURCE)==sha(FROZEN)==SHA,'Frozen manifest changed')
    dirs=list((ROOT/'runs').glob('*'));require(len(dirs)==1,'Unexpected run count')
    folder=dirs[0];events=b.read_events(folder);plan=load(FROZEN)
    require(load(folder/'manifest.json')['claim']==load(ROOT/'claim.json'),'Claim mismatch')
    attempts,raw,results=s.inventory(plan,events)
    sent=[x['data']['payload'] for x in events if x['kind']=='http_request' and x['data']['route']=='/completion']
    require(sent==[s.payload(r) for r in plan['requests'][:len(attempts)]],'Actual execution order/settings changed')
    bodies=[json.loads(base64.b64decode(x['data']['body_base64'])) for x in events if x['kind']=='http_response' and x['data']['route']=='/completion' and x['data'].get('status')==200]
    require(bodies==[r['response'] for r in raw.values()],'Raw HTTP mismatch')
    rows=[]
    for r in plan['requests']:
        rid=r['request_id'];v=s.f.result(r,raw[rid]['response'],raw[rid]['latency_seconds']) if rid in raw else None
        if rid in results:require(results[rid]==v,'Result reconstruction mismatch')
        rows.append({'request':r,'result':v,'state':'COMPLETED' if rid in results else 'UNRESOLVED'})
    return {'manifest_sha256':SHA,'run_directory':folder.as_posix(),'attempted':len(attempts),'results':len(results),'rows':rows,'new_generations':0}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','preflight','run','audit']);p.add_argument('--output',type=Path);p.add_argument('--preflight',type=Path);a=p.parse_args()
    if a.action=='register':v=register()
    elif a.action=='run':
        require(a.preflight is not None,'Preflight path required');v=run(a.preflight)
    else:
        require(a.output is not None,'Unused output path required');v=preflight() if a.action=='preflight' else audit();save(a.output,v)
    print(json.dumps({k:x for k,x in v.items() if k not in ('rows','identity','source_hashes','native_identity','memory_before_run','checks')},indent=2))
    if v.get('status') in ('BLOCKED','PARTIAL'):raise SystemExit(2)
