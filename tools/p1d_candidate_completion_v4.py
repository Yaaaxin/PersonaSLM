"""Targeted final finite repair after FULL-prompt validation, not isolated lengths.

Preserve the 24 Marek/Selma mismatches and six short-control failures in v3.
No model responses or scientific estimand changes. Human validity stays pending.
"""
import copy
import csv
from pathlib import Path
from p1d_design import read,write,csvwrite,sha,th,CELLS
from p1d_stimulus_preparation import CONTROL_BANK
from p1d_candidate_material_repair import render
from p1d_independent_candidates_v2 import validate
import p1c_tokenize as native_module

SOURCE=Path('docs/validation/p1d/independent_candidates_v3')
DEST=Path('docs/validation/p1d/independent_candidates_v4')
ALIASES=('Petra','Ronan','Orla','Elara','Silas','Anwen','Keira','Liora','Leif','Veda','Oren','Zora')

def renamed(c,alias):
    c=copy.deepcopy(c);old=c['other_person'];new=alias+' '+old.split(' ',1)[1]
    for key in ('other_person','target_entity','distractor_entity','question','fixed_context','trusted_evidence'):
        c[key]=c[key].replace(old,new)
    for f in c['facts']:
        if f['entity']==old:f['entity']=new
    for h in c['histories'].values():h['text']=h['text'].replace(old,new)
    return c

def main():
    if DEST.exists():raise FileExistsError('Preserve completed/partial repair')
    old=read(SOURCE/'native_tokenizer_validation_v1.json');cases=read(SOURCE/'candidate_bank_v1.json')['cases']
    bad={r['case_id'] for r in old['cases'] if not r['active_equal']}
    expected={c['case_id'] for c in cases if c['persona_entity'].startswith('Marek ')}
    if bad!=expected or len(bad)!=24:raise ValueError('Unexpected active mismatch; stop targeted repair')
    # First maximum-length original procedural candidate, plus one ordinary attribute.
    extra=CONTROL_BANK[26].replace('checking its cover','checking its plain cover')
    bank=CONTROL_BANK+(extra,)
    write(DEST/'finite_material_plan_v1.json',{'case_ids':sorted(bad),'alias_bank':ALIASES,'control_bank':bank,
        'reason':'Isolated quoted-name probes did not predict Marek/Selma full-prompt lengths; use complete prompts. Six controls exceeded old finite-bank range.',
        'max_native_calls':300,'selection':'First full-prompt alias match and first full-prompt control match; no outputs/effects',
        'source_v3_manifest_sha256':sha(SOURCE/'candidate_provenance_manifest_v1.json'),'code_sha256':sha(__file__),
        'scientific_estimands_changed':False,'generation_authorized':False})
    native_module.LOCAL=Path('results/p1d_readiness/v1/candidate_completion_native_calls')
    native=native_module.NativeTokenizer()
    def tokens(text):
        if len(native.calls)>=300:raise ValueError('Finite call cap reached')
        return native.tokens(text)
    # All 65 actual content lengths are checked once, not assumed from words.
    lengths=[len(tokens('"'+s+'"')) for s in bank]
    probe=next(c for c in cases if c['case_id'] in bad);attempts=[];selected=None
    for alias in ALIASES:
        c=renamed(probe,alias)
        ns={s:len(tokens(render(c,s))) for s in ('E0V0','E1V1')}
        attempts.append({'alias':alias,'probe_case':c['case_id'],'full_prompt_counts':ns})
        if len(set(ns.values()))==1:selected=alias;break
    if selected is None:raise ValueError('Finite full-prompt alias bank failed; preserve logs')
    revisions=[];completed=[]
    for original in cases:
        c=renamed(original,selected) if original['case_id'] in bad else copy.deepcopy(original)
        c['status']='PROSPECTIVE_CANDIDATE_V4_NOT_FROZEN_NOT_VALIDATED'
        if c['case_id'] in bad:
            target=len(tokens(render(c,'E1V1')));prefix='Archived quotation by '+c['persona_entity']+': "'
            before=c['histories']['D_procedural']['text']
            c['histories']['D_procedural']['text']=prefix+bank[0]+'"'
            base=len(tokens(render(c,'D_procedural')));desired=target-base+lengths[0]
            chosen=None
            for i,n in enumerate(lengths):
                if n!=desired:continue
                c['histories']['D_procedural']['text']=prefix+bank[i]+'"'
                if len(tokens(render(c,'D_procedural')))==target:chosen=i;break
            if chosen is None:c['histories']['D_procedural']['text']=before
            revisions.append({'case_id':c['case_id'],'old_other_person':original['other_person'],'new_other_person':c['other_person'],
                'old_control':original['histories']['D_procedural']['text'],'new_control':c['histories']['D_procedural']['text'],
                'selected_control_index':chosen,'semantic_review':'PENDING_DIAGNOSTIC_ONLY'})
        completed.append(c)
    validate(completed)
    rows=read(SOURCE/'base_candidate_prompts_v1.json');by_case={c['case_id']:c for c in completed}
    measures={r['candidate_request_id']:r for r in old['rows']};changed=0
    for r in rows:
        c=by_case[r['case_id']];text=render(c,r['condition'])
        if th(text)==r['prompt_sha256']:continue
        if r['case_id'] not in bad:raise ValueError('Unexpected non-targeted prompt change')
        changed+=1;r['prompt']=text;r['prompt_sha256']=th(text)
        r['trusted_evidence_sha256']=th(c['trusted_evidence']);r['question_sha256']=th(c['question']);r['fixed_context_sha256']=th(c['fixed_context'])
        ids=tokens(text)
        # Calls may have been cached earlier; bind the log by exact prompt hash.
        index=next(i for i,log in enumerate(native.calls) if log['prompt_sha256']==r['prompt_sha256'])
        log=native_module.LOCAL/'native_calls'/f'{index:04d}.json'
        measures[r['candidate_request_id']]={k:r[k] for k in ('candidate_request_id','case_id','condition','prompt_sha256')}|{
            'input_tokens':len(ids),'token_ids_sha256':th(str(ids)),'native_call_log':log.as_posix(),'native_call_sha256':sha(log),
            'context_fit_96':len(ids)+96<=4096,'context_fit_256':len(ids)+256<=4096}
    results=[measures[r['candidate_request_id']] for r in rows];checks=[]
    for c in completed:
        ns={r['condition']:r['input_tokens'] for r in results if r['case_id']==c['case_id']}
        checks.append({'case_id':c['case_id'],'counts':ns,'active_equal':len({ns[s] for s in CELLS[:4]})==1,
            'control_equal':len({ns[s] for s in CELLS[:5]})==1,'semantic_review':'PENDING'})
    write(DEST/'candidate_bank_v1.json',{'version':'p1d_independent_candidate_bank_v4','cases':completed,
        'freeze_status':'NOT_FROZEN','approval_status':'MATERIALS_UNREVIEWED','algorithm_tuning_permitted':False})
    write(DEST/'base_candidate_prompts_v1.json',rows)
    write(DEST/'native_tokenizer_validation_v1.json',{'identity':native.identity,'rows':results,'cases':checks,
        'source_sha256':sha(DEST/'base_candidate_prompts_v1.json'),'new_native_calls':len(native.calls),
        'unchanged_v3_token_records':1728-changed,'inherited_source_sha256':sha(SOURCE/'native_tokenizer_validation_v1.json'),
        'new_generations':0,'active_matches':sum(c['active_equal'] for c in checks),'control_matches':sum(c['control_equal'] for c in checks),
        'context_fit_256':all(r['context_fit_256'] for r in results),
        'input_token_range':[min(r['input_tokens'] for r in results),max(r['input_tokens'] for r in results)]})
    with (SOURCE/'material_review_candidate_v1.csv').open(encoding='utf-8',newline='') as f:reviews=list(csv.DictReader(f))
    for r in reviews:
        c=by_case[r['case_id']]
        for key in ('question','fixed_context','trusted_evidence','histories'):r[key]=c[key]
    csvwrite(DEST/'material_review_candidate_v1.csv',reviews)
    write(DEST/'metric_applicability_candidate_v1.json',read(SOURCE/'metric_applicability_candidate_v1.json'))
    write(DEST/'revision_inventory_v1.json',{'alias_attempts':attempts,'selected_alias':selected,'revisions':revisions})
    write(DEST/'construction_validation_v1.json',validate(completed)|{'other_person_count':144,
        'other_identity_cross_speaker_reuse':False,'case_world_scope':'Explicit independent hypothetical scenarios',
        'human_validity_decisions':0})
    write(DEST/'candidate_provenance_manifest_v1.json',{'source_v3_manifest_sha256':sha(SOURCE/'candidate_provenance_manifest_v1.json'),
        'code_sha256':sha(__file__),'artifact_sha256':{p.as_posix():sha(p) for p in sorted(DEST.iterdir()) if p.is_file()},
        'freeze_status':'NOT_FROZEN','execution_manifest':None,'authorized_inference_requests':0,
        'algorithm_tuning_permitted':False,'semantic_validity':'PENDING_RESEARCHER_MATERIAL_REVIEW'})
    print({'selected_alias':selected,'active_matches':sum(c['active_equal'] for c in checks),'control_matches':sum(c['control_equal'] for c in checks),
        'new_native_calls':len(native.calls),'unchanged_token_records_reused':1728-changed,'new_generations':0},flush=True)

if __name__=='__main__':main()
