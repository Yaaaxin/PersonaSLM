"""Future Stage B only: bounded automatic development gates, no implicit consent.

Stage A may import/test pure decision functions. The run entry requires a real
future activation message and a complete researcher review, revalidated against
the frozen key. Never called by material preparation or tests with real inputs.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time
import p1_blinded_audit as b
import p1_conditional_materials as materials
import p1_recovery_v2 as r
import p1_measurement_scoring_v2 as q0scorer
import p1_temporal_fallback as fallback

s,OUT=r.s,b.OUT
ROOT=Path('results/p1_conditional_sfh/v1')
CLAIM_PREFIX='P1_STAGE_B_V1_'


def automatic(raw,case,package):
    if package in ('D0','D1'):
        v=q0scorer.score(raw,case,True)
        return {'task_success':v['task_success'],'full_score':v,'scorer':'p1_measurement_scoring_v2.score'}
    if package in ('D2','D3'):
        spec=s.load(OUT/'pilot_analysis_and_execution_policy_frozen_v1.json')['Q1_specs'][case['case_id']]
        v=r.d.score_single(raw,spec)
        return {'task_success':v['task_success'],'full_score':v,'scorer':'p1_recovery_design.score_single'}
    state=fallback.endpoint(raw,case)
    label=('Success' if state=='CURRENT_VALUE_ADOPTION' else 'Failure' if state in ('OUTDATED_VALUE_ADOPTION','WRONG_ENTITY_ANSWER','EMPTY_RESPONSE') else 'Missing' if state=='MISSING_RECORD' else 'Uncertain')
    return {'task_success':label,'full_score':{'answer_state':state},'scorer':'p1_temporal_fallback.endpoint; exact current alias only is Success'}


def gate_record(scores,threshold,stage,recorded_utc):
    s.require(len(scores)==8,'Gate requires8 actual attempted case records; no dropped outcomes')
    s.require(len({x['case_id'] for x in scores})==8,'Duplicate case in gate')
    count=sum(x['task_success']=='Success' for x in scores)
    return {'stage':stage,'threshold':threshold,'denominator':8,'automatic_success':count,
        'decision':'AUTOMATIC DEVELOPMENT GATE PASSED' if count>=threshold else 'AUTOMATIC DEVELOPMENT GATE NOT PASSED',
        'proceed':count>=threshold,'case_scores':scores,'recorded_software_utc':recorded_utc,
        'researcher_review_status':'PENDING','scientific_status':'PROVISIONAL_EXECUTION_CONTROL_NOT_VALIDATED_SCIENTIFIC_DECISION',
        'later_adjudication':'Append separately; never overwrite this original automatic gate or conceal sampling consequences.'}


def branch_steps(decision,index):
    if decision['branch']=='A':
        config=decision['selected_configuration'];s.require(config in materials.CONFIGS,'Unknown selected package')
        p=index['manifests'][config]
        return [{'name':'pilot_C0','category':'B_FACTORIAL','manifest':p,'package':config,'slice':[0,8],'threshold':6},
                {'name':'pilot_remaining','category':'B_FACTORIAL','manifest':p,'package':config,'slice':[8,80],'threshold':None}]
    s.require(decision['branch']=='B' and decision['selected_configuration'] is None,'Invalid fallback branch')
    p=index['manifests']['minimal_temporal']
    return [{'name':'fallback_calibration','category':'C_DIAGNOSTIC','manifest':index['manifests']['fallback_calibration'],'package':'minimal_temporal','slice':[0,8],'threshold':7},
            {'name':'pilot_C0','category':'B_FACTORIAL','manifest':p,'package':'minimal_temporal','slice':[0,8],'threshold':6},
            {'name':'pilot_remaining','category':'B_FACTORIAL','manifest':p,'package':'minimal_temporal','slice':[8,80],'threshold':None}]


def authorization_and_decision(review,activation):
    s.require(Path(activation).read_text(encoding='utf-8-sig').strip()==b.PHRASE,'Stage B not activated by exact future researcher message')
    policy=s.load(OUT/'stage_policy_frozen_v1.json')
    s.require(s.sha256(b.KEY)==policy['key_sha256'] and s.sha256(b.SHEET)==policy['blank_sheet_sha256'],'Blind key/sheet integrity')
    s.require(s.sha256(Path(policy['source_snapshot']))==policy['source_snapshot_sha256'],'Original automatic source changed')
    materials.validate_all()
    binding=s.load(OUT/'execution_tools_frozen_v1.json')
    for path,h in binding['source_sha256'].items():s.require(s.sha256(Path(path))==h,'Execution/scoring source changed: '+path)
    rows=b.validate_review(review);_,source=b.read_csv(policy['source_snapshot'])
    joined,decision=b.decide_joined(rows,s.load(b.KEY)['records'],source)
    return {'review_path':str(review),'review_sha256':s.sha256(Path(review)),
        'activation_path':str(activation),'activation_sha256':s.sha256(Path(activation)),
        'researcher':'Yaxin ZHENG','human_review_timestamp':None,'software_recorded_utc':s.b.utc_now(),
        'provenance':'Actual explicit researcher message and researcher-supplied completed sheet required; file existence alone is not proof of human authorship.',
        'rows':joined,'decision':decision,'source_sha256':binding['source_sha256']}


def technical_preflight(plans):
    p=plans[0];cfg=s.config(p);identity=s.b.file_preflight(cfg)
    s.require(identity['status']=='PASS' and identity['model']['sha256']==s.MODEL_SHA and identity['server']['sha256']==p['model']['backend_sha256'],'Model/backend mismatch')
    native=p['native_tokenizer_identity'];folder=Path(cfg.server_file).parent
    s.require(s.sha256(folder/'llama-tokenize.exe')==native['tokenizer_sha256'],'Tokenizer changed')
    s.require({x.name:s.sha256(x) for x in folder.glob('*.dll')}==native['dll_hashes'],'Backend DLLs changed')
    s.require(all(all(v[k]==p[k] for k in materials.SOURCE_KEYS) for v in plans),'Configuration substitution across branch')
    mem=s.memory_observation(os.getpid());s.require(mem['system']['available_physical']>=3*1024**3,'Unchanged3GiB pre-load available-RAM gate failed')
    s.require(shutil.disk_usage('.').free>=1024**3,'Insufficient output disk reserve')
    return {'status':'PASS','identity':identity,'configuration':cfg.as_dict(),'server_command':s.command(p),
        'memory_before':mem,'checked_software_utc':s.b.utc_now(),'stage':'B_ONLY','requests':sum(len(x['requests']) for x in plans)}


def run(review,activation):
    registration=authorization_and_decision(review,activation)
    index=s.load(OUT/'manifest_index_frozen_v1.json');steps=branch_steps(registration['decision'],index)
    paths=list(dict.fromkeys(x['manifest']['path'] for x in steps));plans=[s.load(p) for p in paths]
    with s.b.writer_lock(r.old.ROOT):
        s.require(not list((ROOT/'runs').glob('*')),'Prior Stage B run; no automatic resume/retry')
        s.require(not list((r.old.ROOT/'claims').glob(CLAIM_PREFIX+'*')),'Existing Stage B claim; reconcile, never retry')
        ledger=r.old.cumulative();s.require(ledger['attempted']=={'A_C0':32,'B_FACTORIAL':0,'C_DIAGNOSTIC':40},'Reconcile authorization ledger before Stage B')
        pre=technical_preflight(plans)  # All activation/material/resource gates before claims/generation.
        journal=s.b.RunJournal(ROOT/'runs',{'phase':'P1','stage':'B','registration':registration,
            'candidate_index_sha256':s.sha256(OUT/'manifest_index_frozen_v1.json'),'plans':plans,
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'git_status':subprocess.check_output(['git','status','--short'],text=True),
            'python':platform.python_version(),'platform':platform.platform()})
        for path,h in registration['source_sha256'].items():
            dest=journal.directory/'source_snapshot'/path;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as fp:fp.write(Path(path).read_bytes())
            s.require(s.sha256(dest)==h,'Source snapshot mismatch')
        journal.write('researcher_unblinding',registration);journal.write('preflight',pre)
        tick=time.monotonic();active=None;attempted=0;completed=0;gates=[];status='NOT_STARTED'
        banks=s.load(OUT/'pilot_cases_by_configuration_frozen_v1.json')
        calibration={c['case_id']:c for c in s.load(fallback.OUT/'bank_frozen_v1.json')['cases'] if c['pool']=='fallback_calibration'}
        try:
            with s.Server(plans[0],journal) as server:
                client=s.b.LlamaClient(s.config(plans[0]).endpoint,timeout=180,audit=journal.write)
                props=client.request('/props');v=s.b.validate_server_properties(props,s.config(plans[0]))
                s.require(v['build_info']=='b11573-0f701c882','Runtime build mismatch')
                journal.write('effective_server_defaults',{'props':props,'validation':v})
                for p in plans:
                    for q in p['requests']:
                        native=client.request('/tokenize',{'content':q['prompt'],'add_special':True,'parse_special':True,'with_pieces':False})['tokens']
                        s.require(native==q['input_token_ids'],'Live tokenizer mismatch; no generations')
                        journal.write('live_prompt_verified',{'request_id':q['request_id'],'token_hash':s.th(str(native))})
                for step in steps:
                    plan=s.load(step['manifest']['path']);s.require(s.sha256(Path(step['manifest']['path']))==step['manifest']['sha256'],'Selected manifest changed')
                    lo,hi=step['slice'];qs=plan['requests'][lo:hi];category=step['category']
                    s.require(r.old.cumulative()['remaining_unreserved'][category]>=len(qs),'Category quota exceeded')
                    claim=r.old.ROOT/'claims'/(CLAIM_PREFIX+step['name']+'.json')
                    s.save(claim,{'authorization_id':r.m.AUTH_ID,'category':category,'maximum_attempts':len(qs),
                        'request_ids':[q['request_id'] for q in qs],'manifest_sha256':step['manifest']['sha256'],
                        'activation_sha256':registration['activation_sha256'],'review_sha256':registration['review_sha256'],
                        'branch':registration['decision']['branch'],'step':step['name']})
                    cases=calibration if step['name']=='fallback_calibration' else {c['case_id']:c for c in banks[step['package']]}
                    scores=[]
                    for q in qs:
                        s.require(time.monotonic()-tick<3600,'Frozen60-minute run ceiling');server.assert_running()
                        active=q['request_id'];client.timeout=min(180,3600-(time.monotonic()-tick))
                        s.save(r.old.ROOT/'attempts'/(active+'.json'),{'authorization_id':r.m.AUTH_ID,'category':category,
                            'request_id':active,'request_sha256':q['request_sha256'],'reserved_utc':s.b.utc_now(),'run_directory':journal.directory.as_posix()})
                        attempted+=1;journal.write('p1_generation_started',q);start=time.monotonic()
                        raw=client.request('/completion',s.payload(q));elapsed=time.monotonic()-start
                        journal.write('p1_raw_generation',{'request_id':active,'response':raw,'latency_seconds':elapsed})
                        result=s.f.result(q,raw,elapsed);journal.write('p1_result',result);completed+=1
                        score=automatic(result['raw_response'],cases[q['case_id']],step['package'])|{'case_id':q['case_id'],
                            'request_id':active,'condition':q['condition'],'raw_output_sha256':s.th(result['raw_response']),
                            'original_structural_status':result['response_status']['status'],'source_sha256':registration['source_sha256']}
                        scores.append(score);journal.write('provisional_automatic_score',score)
                        journal.write('memory_observation',s.memory_observation(server.process.pid));active=None
                    if step['threshold'] is not None:
                        gate=gate_record(scores,step['threshold'],step['name'],s.b.utc_now());gates.append(gate)
                        journal.write('provisional_execution_gate',gate)
                        if not gate['proceed']:status='AUTOMATIC DEVELOPMENT GATE NOT PASSED';break
                else:status='AUTHORIZED_BRANCH_COMPLETED'
                for path,h in registration['source_sha256'].items():s.require(s.sha256(Path(path))==h,'Postflight source changed')
        except BaseException as exc:
            status='PARTIAL_OR_BLOCKED';journal.write('failure',{'type':type(exc).__name__,'message':str(exc),'request_id':active,'attempt_consumed':active is not None})
        summary={'status':status,'branch':registration['decision']['branch'],'attempted':attempted,'results':completed,
            'automatic_gates':gates,'researcher_semantic_review_of_new_outputs':'PENDING','retries':0,
            'elapsed_seconds':time.monotonic()-tick,'ledger':r.old.cumulative(),'run_directory':journal.directory.as_posix()}
        journal.finish(**summary);s.save(journal.directory/'summary.json',summary)
        return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run']);p.add_argument('--review',type=Path,required=True)
    p.add_argument('--activation',type=Path,required=True);v=p.parse_args()
    print(json.dumps(run(v.review,v.activation),indent=2))
