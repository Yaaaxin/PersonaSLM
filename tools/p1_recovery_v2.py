"""Q1-v2 compatibility amendment; preserve all twenty executable v1 requests.

Reuses the sealed v1 transport through an isolated module namespace. Its durable
global ledger, claim, no-retry policy and live-token gates are unchanged.
"""
import argparse
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import p1_recovery_design as d
import p1_recovery_run as v1

s, old, m = d.s, d.old, d.m
OUT=Path('docs/validation/p1/measurement_recovery_2x2_v2')
MANIFEST=OUT/'diagnostic_manifest_frozen_v2.json'
ROOT=d.ROOT  # Continuation of the same unexecuted experiment, not a new wave.


def native_tokens(prompt,path,plan):
    exe=Path(plan['model']['backend_file']).with_name('llama-tokenize.exe')
    s.require(s.sha256(exe)==plan['native_tokenizer_identity']['tokenizer_sha256'],'Native tokenizer identity')
    argv=[str(exe.resolve()),'-m',str(Path(plan['model']['model_file']).resolve()),'--stdin','--ids','--offline']
    proc=subprocess.run(argv,input=prompt.encode(),capture_output=True,timeout=60,
        env={k:v for k,v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    log={'argv':argv,'prompt':prompt,'returncode':proc.returncode,'stdout':proc.stdout.decode('utf-8','replace'),
         'stderr':proc.stderr.decode('utf-8','replace'),'recorded_utc':s.b.utc_now(),'generation_requests':0}
    s.save(path,log);s.require(proc.returncode==0,'Native tokenizer error')
    ids=ast.literal_eval(log['stdout'].strip())
    sys.path.insert(0,str(Path('results/p1d_final_preparation/v1/tokenizer_runtime').resolve()))
    from tokenizers import Tokenizer
    tok=Tokenizer.from_file('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    s.require(ids==tok.encode(prompt,add_special_tokens=True).ids and tok.decode(ids,skip_special_tokens=False)==prompt,'Official/native reconstruction mismatch')
    return ids,{'path':path.as_posix(),'sha256':s.sha256(path)}


def prepare():
    s.require(not MANIFEST.exists(),'Preserve v2 manifest')
    s.require(not v1.CLAIM.exists() and not list((ROOT/'runs').glob('*')),'Prior execution must be reconciled; no repeats')
    parent=v1.validate();ledger=old.cumulative()
    s.require(ledger['attempted']=={'A_C0':32,'B_FACTORIAL':0,'C_DIAGNOSTIC':16},'Unexpected cumulative allocation')
    seal=s.load(d.OUT/'reproducibility_manifest_v1.json')
    for p,h in seal['artifact_sha256'].items():s.require(s.sha256(Path(p))==h,'v1 source changed: '+p)
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'research_development_log_before_v2.bin').open('xb') as f:f.write(Path('docs/research_development_log.md').read_bytes())
    selected={c['case_id']:c for c in d.select_cases(d.cases())}
    policy=copy.deepcopy(s.load(d.OUT/'prospective_policy_v1.json'))
    policy.update(version='p1_recovery_2x2_policy_v2',registered_utc=s.b.utc_now(),
        Q1_rule='When several required entity/date components are valid at query date, choose the first qualifying component in the original frozen reference-answer order. Otherwise retain v1 unique/fallback rule.',
        Q1_blocked=[])
    for cid in ('p1_measure_calibration_04','p1_measure_calibration_05'):
        policy['Q1_specs'][cid]=d.q1(selected[cid],ordered_tie_authorized=True)
    s.save(OUT/'prospective_policy_v2.json',policy)
    amendment={'version':'Q1-v2','researcher':'Yaxin ZHENG','decision':'EXPLICIT_PROSPECTIVE_TIE_BREAK_AUTHORIZED',
        'source':'User instruction: P1 Measurement Recovery, Prospective Q1 Repair and Fixed Fallback Execution, section2',
        'verbatim_rule':'When several required components are valid at the query date, select the first qualifying component in the original frozen reference-answer component order.',
        'human_timestamp':None,'registration_utc':s.b.utc_now(),'reason':'Three eligible entities in each chain case lacked a tie priority in Q1-v1.',
        'affected_request_ids':[r['request_id'] for r in parent['blocked_requests']],
        'preserved_executable_request_sha256':{r['request_id']:r['request_sha256'] for r in parent['requests']},
        'v1_manifest_sha256':s.sha256(v1.MANIFEST),'scoring_implementation_sha256':s.sha256(Path('tools/p1_recovery_design.py')),
        'normalization_changed':False,'model_changed':False,'outcomes_used_for_component_selection':False,
        'execution_order':'Original20 entries and order fields unchanged; four repaired entries appended in original blocked-request order.'}
    s.save(OUT/'Q1_amendment_v2.json',amendment)
    auth={'researcher':'Yaxin ZHENG','authorization_id':m.AUTH_ID,'human_timestamp':None,'registered_utc':s.b.utc_now(),
        'source':'Current user instruction sections2-4,7-13; earlier160-category authorization remains binding.',
        'category':'C_DIAGNOSTIC','maximum_OQ_attempts':24,'maximum_conditional_fallback_attempts':8,
        'new_authorization_added':0,'no_retries':True,'semantic_approval':False,'factorial_execution_authorized':False,
        'fallback_conditions':['OQ24 completed plus archived D0','Researcher-confirmed32-condition annotation snapshot',
            'No OQ configuration meets both gates','Frozen16-case fallback bank and fixed8/8 allocation','Complete scientific and engineering preflight'],
        'fallback_gate':'Eight C0 only; researcher-audited >=7/8 before preparing qualified pilot. No automatic80 execution.',
        'prior_cumulative':ledger}
    s.save(OUT/'authorization_registration_v1.json',auth)
    plan=copy.deepcopy(parent);plan['requests']=copy.deepcopy(parent['requests']);plan['native_tokenizer_logs']=copy.deepcopy(parent['native_tokenizer_logs'])
    originals={r['case_id']:r for r in s.load(d.OLD/'A_C0_manifest_v1.json')['requests']}
    template=Path(plan['template_path']).read_text(encoding='utf-8');new_specs=[]
    for block in parent['blocked_requests']:
        c=selected[block['case_id']];con=block['condition'];spec=policy['Q1_specs'][c['case_id']]
        cc=v1.construct(c,con,spec);text=m.content(cc,'C0');prompt=s.render(template,[{'role':'user','content':text}])
        r=copy.deepcopy(originals[c['case_id']]);r.update(request_id=block['request_id'],condition=con,
            diagnostic_factors={'O':int(con=='D3'),'Q':1},parent_request_id=originals[c['case_id']]['request_id'],
            parent_request_sha256=originals[c['case_id']]['request_sha256'],messages=[{'role':'user','content':text}],
            prompt=prompt,prompt_sha256=s.th(prompt),reference=cc['reference'],reference_sha256=s.th(json.dumps(cc['reference'],sort_keys=True)),
            evidence_sha256=s.th(cc['trusted_evidence']),question_sha256=s.th(cc['question']))
        ids,log=native_tokens(prompt,OUT/'native_tokenizer'/f'{len(plan["requests"]):03d}.json',plan)
        r.update(order=len(plan['requests']),input_token_ids=ids,input_tokens=len(ids),input_token_ids_sha256=s.th(str(ids)),context_remaining=4096-96-len(ids))
        r.pop('request_sha256');r['request_sha256']=s.th(json.dumps(r,sort_keys=True,separators=(',',':')))
        plan['requests'].append(r);plan['native_tokenizer_logs'].append(log)
        new_specs.append({'request_id':r['request_id'],'question':cc['question'],'reference':cc['reference'],'aliases':spec['aliases'],
                          'prompt_sha256':r['prompt_sha256'],'request_sha256':r['request_sha256']})
    bound=plan['bound_sources']|{p.as_posix():s.sha256(p) for p in (v1.MANIFEST,OUT/'prospective_policy_v2.json',OUT/'Q1_amendment_v2.json',OUT/'authorization_registration_v1.json')}
    plan.update(version='p1_recovery_2x2_manifest_v2',proposed_requests=24,blocked_requests=[],bound_sources=bound,
                request_order=amendment['execution_order'],v1_manifest_sha256=s.sha256(v1.MANIFEST))
    s.save(MANIFEST,plan);s.save(OUT/'manifest_binding_v2.json',{'path':MANIFEST.as_posix(),'sha256':s.sha256(MANIFEST)})
    s.save(OUT/'Q1_repair_verification_v2.json',{'unchanged_request_objects':plan['requests'][:20]==parent['requests'],
        'unchanged_native_logs':plan['native_tokenizer_logs'][:20]==parent['native_tokenizer_logs'],
        'new_request_specs':new_specs,'D0_regenerated':False,'prior_sealed_files_verified':len(seal['artifact_sha256'])})
    return {'status':'Q1_V2_REGISTERED','requests':24,'preserved_requests':20,'repaired_requests':4,'manifest_sha256':s.sha256(MANIFEST)}


def source_hashes():
    return v1.source_hashes()|{'tools/p1_recovery_v2.py':s.sha256(Path(__file__))}


def validate():
    p=s.load(MANIFEST);s.require(s.sha256(MANIFEST)==s.load(OUT/'manifest_binding_v2.json')['sha256'],'v2 manifest changed')
    for path,h in p['bound_sources'].items():s.require(s.sha256(Path(path))==h,'Bound file changed: '+path)
    previous=v1.validate();s.require(p['requests'][:20]==previous['requests'],'One of20 executable requests changed')
    s.require(p['model']==previous['model'] and p['native_tokenizer_identity']==previous['native_tokenizer_identity'],'Model/native change')
    s.require(len(p['requests'])==len(p['native_tokenizer_logs'])==24 and not p['blocked_requests'],'Incomplete OQ inventory')
    s.require([r['request_id'] for r in p['requests'][20:]]==[r['request_id'] for r in previous['blocked_requests']],'Wrong repaired scope/order')
    cs={c['case_id']:c for c in d.select_cases(d.cases())};policy=s.load(OUT/'prospective_policy_v2.json')
    template=Path(p['template_path']).read_text(encoding='utf-8')
    for r,log in zip(p['requests'],p['native_tokenizer_logs']):
        c=cs[r['case_id']];cc=v1.construct(c,r['condition'],policy['Q1_specs'][c['case_id']])
        d.reference_audit(c)
        s.require(r['prompt']==s.render(template,[{'role':'user','content':m.content(cc,'C0')}]),'Scientific rendering mismatch')
        s.require(r['reference']==cc['reference'],'Reference mismatch')
        if r['condition'] in ('D2','D3'):
            spec=d.q1(c,ordered_tie_authorized=True);s.require(spec==policy['Q1_specs'][c['case_id']],'Q1 rule mismatch')
            s.require('Which bay is assigned' in cc['question'] and spec['reference'][0]['value'] not in cc['question'],'Attribute/answer-leak check')
        s.require(r['request_sha256']==s.th(json.dumps({k:v for k,v in r.items() if k!='request_sha256'},sort_keys=True,separators=(',',':'))),'Request checksum')
        for k,val in {'seed':42,'temperature':0.,'top_p':1.,'max_new_tokens':96,'stop':[],'ignore_eos':False,'cache_prompt':False,'parse_special':True,'factors':[0,0,0]}.items():s.require(r[k]==val,'Setting changed: '+k)
        s.require(s.sha256(Path(log['path']))==log['sha256'],'Native log changed');n=s.load(log['path'])
        s.require(n['returncode']==0 and n['prompt']==r['prompt'] and ast.literal_eval(n['stdout'].strip())==r['input_token_ids'],'Native token mismatch')
        s.require(r['prompt_sha256']==s.th(r['prompt']) and r['input_token_ids_sha256']==s.th(str(r['input_token_ids'])),'Input checksum')
        s.require(r['input_tokens']==len(r['input_token_ids']) and r['context_remaining']==4096-96-r['input_tokens']>0,'Context capacity')
    s.require([r['order'] for r in p['requests']]==list(range(24)),'Execution order')
    s.require(len({r['request_id'] for r in p['requests']})==24,'Duplicate requests')
    return p


def preflight(resources=True):
    p=validate();cfg=s.config(p);identity=s.b.file_preflight(cfg)
    s.require(identity['status']=='PASS' and identity['model']['sha256']==s.MODEL_SHA and identity['server']['sha256']==p['model']['backend_sha256'],'Binary identity')
    folder=Path(cfg.server_file).parent;n=p['native_tokenizer_identity']
    s.require(s.sha256(folder/'llama-tokenize.exe')==n['tokenizer_sha256'],'Tokenizer mismatch')
    s.require({x.name:s.sha256(x) for x in folder.glob('*.dll')}==n['dll_hashes'],'DLL mismatch')
    archived=old.audit('A_C0');s.require(archived['results']==32,'Archived D0 source missing')
    # Original audit performs actual byte reconstruction for all32, without
    # modifying original proposals, model outputs or parser classifications.
    a=d.original_audit();s.require(sum(x['D0_reused_in_2x2'] for x in a)==8,'D0 panel mismatch')
    mem=s.memory_observation(os.getpid());available=mem.get('system',{}).get('available_physical',0)
    if resources:s.require(available>=3*1024**3,f'RAM preflight failed: {available}; unchanged minimum 3221225472 bytes')
    s.require(shutil.disk_usage('.').free>=1024**3,'Output reserve')
    return {'status':'PASS' if resources else 'STATIC_CHECKS_ONLY','checked_utc':s.b.utc_now(),'manifest_sha256':s.sha256(MANIFEST),
        'source_hashes':source_hashes(),'identity':identity,'configuration':cfg.as_dict(),'server_command':s.command(p),
        'memory_before':mem,'ledger':old.cumulative(),'requests':24,'blocked_requests':[],
        'D0_reuse':'8 byte-identical original prompts with original generation configuration; no repeats',
        'live_gate':'All24 token arrays/effective CPU configuration before first completion'}


def transport():
    spec=importlib.util.spec_from_file_location('_p1_recovery_v2_transport',Path(v1.__file__))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.OUT=OUT;module.MANIFEST=MANIFEST;module.ROOT=ROOT
    module.validate=validate;module.preflight=preflight;module.source_hashes=source_hashes
    # Same v1.CLAIM prevents accidental execution via either old or new entry.
    return module


def run(path):return transport().run(path)
def audit():return transport().audit()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','preflight','run','audit']);p.add_argument('--output',type=Path);p.add_argument('--preflight',type=Path);a=p.parse_args()
    try:value=run(a.preflight) if a.action=='run' else globals()[a.action]()
    except Exception as exc:
        value={'status':'BLOCKED','error':str(exc),'recorded_utc':s.b.utc_now(),'new_generations':0,'memory':s.memory_observation(os.getpid())}
        if a.output:s.save(a.output,value)
        print(json.dumps(value,indent=2));raise SystemExit(2)
    if a.output:s.save(a.output,value)
    print(json.dumps({k:v for k,v in value.items() if k not in ('rows','identity','source_hashes')},indent=2))
