"""Finite pre-outcome repair of candidate identity reuse and token mismatches.

Preserves v1/v2. Candidate answers are never used for algorithm tuning. No inference.
"""
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import threading
import subprocess
from p1d_design import read, write, csvwrite, sha, th, CELLS
from p1d_stimulus_preparation import CONTROL_BANK
from p1d_independent_candidates_v2 import validate, prompt as old_prompt
from p1c_tokenize import NativeTokenizer

SOURCE=Path('docs/validation/p1d/independent_candidates_v2')
DEST=Path('docs/validation/p1d/independent_candidates_v3')
LOGS=Path('results/p1d_readiness/v1/candidate_repair_native_calls')
ALIASES=('Neri','Arwen','Marlo','Alwin','Darian','Selma','Petra','Ronan','Orla','Nadia','Elara','Silas',
         'Tarin','Anwen','Keira','Liora','Cora','Leif','Soren','Mabel','Noel','Veda','Oren','Zora')

def render(c,cell):
    return ('SCENARIO\n'+c['case_id']+': an independent fictional scenario. The ledger applies only within this scenario.\n'
            +old_prompt(c,cell))

def main():
    if DEST.exists() or LOGS.exists():raise FileExistsError('Preserve completed or partial repair')
    write(DEST/'finite_repair_plan_v1.json',{'source_manifest_sha256':sha(SOURCE/'candidate_provenance_manifest_v1.json'),
        'aliases':ALIASES,'controls':CONTROL_BANK,'max_native_calls':2600,'workers':4,
        'selection':'Injective alias map with equal native name lengths; first exact procedural candidate from fixed bank; no response or effect-based selection',
        'scenario_scope':'Explicit independent hypothetical case worlds; same speaker style spans two cases, no global factual biography asserted',
        'approved_estimands_changed':False,'code_sha256':sha(__file__),'new_generations':0})
    LOGS.mkdir(parents=True);native=NativeTokenizer();cache={};lock=threading.Lock();count=0
    def tokens(text):
        nonlocal count
        key=th(text)
        with lock:
            if key in cache:return cache[key]
            count+=1
            if count>2600:raise ValueError('Native vocabulary-call cap reached')
        start=datetime.now(timezone.utc).isoformat()
        p=subprocess.run(native.argv,input=text.encode('utf-8'),capture_output=True,timeout=60)
        log={'prompt_sha256':key,'prompt':text,'software_started_utc':start,
            'software_finished_utc':datetime.now(timezone.utc).isoformat(),'exit_code':p.returncode,
            'stdout':p.stdout.decode('utf-8','replace'),'stderr':p.stderr.decode('utf-8','replace'),'generation':False}
        write(LOGS/(key+'.json'),log)
        if p.returncode:raise ValueError('Native tokenizer failed')
        ids=ast.literal_eval(log['stdout'].strip())
        if not isinstance(ids,list) or any(type(i) is not int for i in ids):raise ValueError('Invalid native IDs')
        with lock:cache[key]=ids
        return ids
    cases=read(SOURCE/'candidate_bank_v1.json')['cases']
    firsts=sorted({c['persona_entity'].split()[0] for c in cases})
    probes=['"'+n+' Calder:' for n in firsts+list(ALIASES)]
    with ThreadPoolExecutor(max_workers=4) as pool: lengths=list(pool.map(lambda t:len(tokens(t)),probes))
    lengths=dict(zip(firsts+list(ALIASES),lengths));mapping={};used=set()
    for name in firsts:
        options=[a for a in ALIASES if a not in used and lengths[a]==lengths[name]]
        if not options:raise ValueError('Finite alias bank cannot cover '+name)
        mapping[name]=options[0];used.add(options[0])
    write(DEST/'alias_selection_v1.json',{'lengths':lengths,'mapping':mapping,'limitations':'Name length match alone is not semantic equivalence; all complete prompts checked separately'})
    # Reuse actual pinned tokenizer measurements for unchanged fixed control strings.
    control_lengths=[]
    for i,text in enumerate(CONTROL_BANK):
        p=Path('results/p1d_readiness/v1/tokenizer/native_calls')/f'{i:04d}.json'
        log=read(p)
        if log['prompt']!='"'+text+'"' or log['prompt_sha256']!=th('"'+text+'"') or log['exit_code']!=0:
            raise ValueError('Fixed procedural-bank measurement mismatch')
        control_lengths.append(len(ast.literal_eval(log['stdout'].strip())))
    revisions=[]
    for c in cases:
        old=c['other_person'];first,last=c['persona_entity'].split(' ',1);new=mapping[first]+' '+last
        for field in ('other_person','target_entity','distractor_entity','question','fixed_context','trusted_evidence'):
            c[field]=c[field].replace(old,new)
        for f in c['facts']:
            if f['entity']==old:f['entity']=new
            f['scenario_id']=c['case_id']
        for h in c['histories'].values():h['text']=h['text'].replace(old,new)
        c['scenario_id']=c['case_id'];c['status']='PROSPECTIVE_CANDIDATE_V3_NOT_FROZEN_NOT_VALIDATED'
        revisions.append({'case_id':c['case_id'],'original_other_person':old,'revised_other_person':new,
            'reason':'Distinct paired-speaker other identity; native-length-matched alias. Explicit case-world scope prevents global timeline claims.'})
    def match_control(c):
        target=len(tokens(render(c,'E1V1')))
        original=c['histories']['D_procedural']['text'];prefix='Archived quotation by '+c['persona_entity']+': "'
        c['histories']['D_procedural']['text']=prefix+CONTROL_BANK[0]+'"'
        base=len(tokens(render(c,'D_procedural')));desired=target-base+control_lengths[0]
        attempts=[];chosen=None
        for i,n in enumerate(control_lengths):
            if n!=desired:continue
            c['histories']['D_procedural']['text']=prefix+CONTROL_BANK[i]+'"'
            measured=len(tokens(render(c,'D_procedural')))
            attempts.append({'candidate_index':i,'full_prompt_tokens':measured})
            if measured==target:chosen=i;break
        if chosen is None:c['histories']['D_procedural']['text']=original
        c['histories']['D_procedural']['status']='DIAGNOSTIC_ONLY_SEMANTIC_REVIEW_PENDING'
        return {'case_id':c['case_id'],'target_tokens':target,'selected_control_index':chosen,
                'attempts':attempts,'original_text':original,'selected_text':c['histories']['D_procedural']['text']}
    with ThreadPoolExecutor(max_workers=4) as pool:controls=list(pool.map(match_control,cases))
    print({'cases_with_candidate_control_match':sum(c['selected_control_index'] is not None for c in controls),'native_calls':count},flush=True)
    summary=validate(cases)
    if len({c['other_person'] for c in cases})!=144:raise ValueError('Other identities still shared across speakers')
    write(DEST/'candidate_bank_v1.json',{'version':'p1d_independent_candidate_bank_v3','cases':cases,
        'freeze_status':'NOT_FROZEN','approval_status':'MATERIALS_UNREVIEWED','algorithm_tuning_permitted':False})
    rows=[]
    for c in cases:
        for cell in CELLS:
            text=render(c,cell)
            rows.append({'candidate_request_id':c['case_id']+'_'+cell,'case_id':c['case_id'],'speaker_id':c['speaker_id'],
                'condition':cell,'prompt':text,'prompt_sha256':th(text),'trusted_evidence_sha256':th(c['trusted_evidence']),
                'question_sha256':th(c['question']),'reference':c['required_components'],'fixed_context_sha256':th(c['fixed_context']),
                'generation_authorized':False})
    def measure(r):
        ids=tokens(r['prompt']);p=LOGS/(r['prompt_sha256']+'.json')
        return {k:r[k] for k in ('candidate_request_id','case_id','condition','prompt_sha256')}|{
            'input_tokens':len(ids),'token_ids_sha256':th(str(ids)),'native_call_log':p.as_posix(),'native_call_sha256':sha(p),
            'context_fit_96':len(ids)+96<=4096,'context_fit_256':len(ids)+256<=4096}
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for r in pool.map(measure,rows):
            results.append(r)
            if len(results)%288==0:print({'candidate_prompts_verified':len(results),'native_calls':count,'new_generations':0},flush=True)
    checks=[]
    for c in cases:
        ns={r['condition']:r['input_tokens'] for r in results if r['case_id']==c['case_id']}
        checks.append({'case_id':c['case_id'],'counts':ns,'active_equal':len({ns[s] for s in CELLS[:4]})==1,
            'control_equal':len({ns[s] for s in CELLS[:5]})==1,'semantic_review':'PENDING'})
    write(DEST/'base_candidate_prompts_v1.json',rows)
    write(DEST/'native_tokenizer_validation_v1.json',{'identity':native.identity,'rows':results,'cases':checks,
        'source_sha256':sha(DEST/'base_candidate_prompts_v1.json'),'native_calls':count,'new_generations':0,
        'active_matches':sum(c['active_equal'] for c in checks),'control_matches':sum(c['control_equal'] for c in checks),
        'context_fit_256':all(r['context_fit_256'] for r in results),
        'input_token_range':[min(r['input_tokens'] for r in results),max(r['input_tokens'] for r in results)]})
    write(DEST/'revision_inventory_v1.json',{'identities':revisions,'controls':controls})
    write(DEST/'construction_validation_v1.json',summary|{'other_person_count':144,'other_identity_cross_speaker_reuse':False,
        'case_world_scope':'Explicit independent hypothetical scenario; not global biographies','human_validity_decisions':0})
    review=[{'case_id':c['case_id'],'family':c['family'],'domain':c['domain']['id'],'persona':c['persona_profile'],
        'question':c['question'],'fixed_context':c['fixed_context'],'trusted_evidence':c['trusted_evidence'],
        'requested_date':c['query_date'],'reference':c['required_components'],'source_trace':c['derivation_source_ids'],
        'histories':c['histories'],'scenario_id':c['scenario_id'],'evidence_sufficiency':'','temporal_truth':'',
        'control_validity':'','undeclared_leakage':'','shortcut_risk':'','researcher_decision':'','reviewer_id':'','actual_timestamp':''} for c in cases]
    csvwrite(DEST/'material_review_candidate_v1.csv',review)
    write(DEST/'metric_applicability_candidate_v1.json',read(SOURCE/'metric_applicability_candidate_v1.json'))
    write(DEST/'candidate_provenance_manifest_v1.json',{'source_v2_manifest_sha256':sha(SOURCE/'candidate_provenance_manifest_v1.json'),
        'code_sha256':sha(__file__),'artifact_sha256':{p.as_posix():sha(p) for p in sorted(DEST.iterdir()) if p.is_file()},
        'freeze_status':'NOT_FROZEN','execution_manifest':None,'authorized_inference_requests':0,
        'algorithm_tuning_permitted':False,'semantic_independence':'Human material review and template-population generalization are not established'})
    print({'active_matches':sum(c['active_equal'] for c in checks),'control_matches':sum(c['control_equal'] for c in checks),'new_generations':0},flush=True)

if __name__=='__main__':main()
