"""One bounded procedural candidate for the six remaining length mismatches.

The fixed candidate adds 'plain' to the cover description. It remains diagnostic,
not semantically neutral. No outcomes, algorithms or held-out scores are consulted.
"""
import ast
import csv
from pathlib import Path
from p1d_design import read,write,csvwrite,sha,th,CELLS
from p1d_stimulus_preparation import CONTROL_BANK
from p1d_candidate_material_repair import render
from p1d_independent_candidates_v2 import validate
import p1c_tokenize as native_module

SOURCE=Path('docs/validation/p1d/independent_candidates_v3')
DEST=Path('docs/validation/p1d/independent_candidates_v4')

def main():
    if DEST.exists():raise FileExistsError('Preserve completed or partial candidate repair')
    old=read(SOURCE/'native_tokenizer_validation_v1.json')
    targets={c['case_id'] for c in old['cases'] if not c['control_equal']}
    expected={f'p1d_candidate_s{s:03d}_c{j}' for s in (50,63,107) for j in (0,1)}
    if targets!=expected or old['active_matches']!=288:raise ValueError('Unexpected material issue; do not force repair')
    lengths=[len(ast.literal_eval(read(Path('results/p1d_readiness/v1/tokenizer/native_calls')/f'{i:04d}.json')['stdout'].strip())) for i in range(64)]
    base_index=lengths.index(max(lengths))
    candidate=CONTROL_BANK[base_index].replace('checking its cover','checking its plain cover')
    write(DEST/'finite_control_plan_v1.json',{'target_case_ids':sorted(targets),'base_control_index':base_index,
        'single_candidate':candidate,'reason':'Remaining six cases require 41 quoted-content tokens; previous finite bank maximum was 40',
        'scope':'Additional folder attribute, not a scientific estimand change; diagnostic-only semantic review remains pending',
        'source_v3_manifest_sha256':sha(SOURCE/'candidate_provenance_manifest_v1.json'),'max_native_calls':7,'new_generations':0})
    native_module.LOCAL=Path('results/p1d_readiness/v1/final_control_native_calls')
    native=native_module.NativeTokenizer()
    quote_tokens=native.tokens('"'+candidate+'"')
    if len(quote_tokens)!=41:raise ValueError('Single candidate failed declared token check; preserve failure')
    cases=read(SOURCE/'candidate_bank_v1.json')['cases'];rows=read(SOURCE/'base_candidate_prompts_v1.json')
    measures={r['candidate_request_id']:r for r in old['rows']}; revisions=[]
    by_id={c['case_id']:c for c in cases}
    for c in cases:
        c['status']='PROSPECTIVE_CANDIDATE_V4_NOT_FROZEN_NOT_VALIDATED'
        if c['case_id'] not in targets:continue
        before=c['histories']['D_procedural']['text']
        c['histories']['D_procedural']['text']='Archived quotation by '+c['persona_entity']+': "'+candidate+'"'
        revisions.append({'case_id':c['case_id'],'before':before,'after':c['histories']['D_procedural']['text'],
            'reason':'Finite length repair; no semantic-neutrality claim'})
    for r in rows:
        c=by_id[r['case_id']];text=render(c,r['condition'])
        if th(text)==r['prompt_sha256']:continue
        if r['case_id'] not in targets or r['condition']!='D_procedural':raise ValueError('Unintended prompt change')
        ids=native.tokens(text);r['prompt']=text;r['prompt_sha256']=th(text)
        log=native_module.LOCAL/'native_calls'/f'{len(native.calls)-1:04d}.json'
        measures[r['candidate_request_id']]={k:r[k] for k in ('candidate_request_id','case_id','condition','prompt_sha256')}|{
            'input_tokens':len(ids),'token_ids_sha256':th(str(ids)),'native_call_log':log.as_posix(),'native_call_sha256':sha(log),
            'context_fit_96':len(ids)+96<=4096,'context_fit_256':len(ids)+256<=4096}
    results=[measures[r['candidate_request_id']] for r in rows];checks=[]
    for c in cases:
        ns={r['condition']:r['input_tokens'] for r in results if r['case_id']==c['case_id']}
        checks.append({'case_id':c['case_id'],'counts':ns,'active_equal':len({ns[s] for s in CELLS[:4]})==1,
            'control_equal':len({ns[s] for s in CELLS[:5]})==1,'semantic_review':'PENDING'})
    summary=validate(cases)
    write(DEST/'candidate_bank_v1.json',{'version':'p1d_independent_candidate_bank_v4','cases':cases,
        'freeze_status':'NOT_FROZEN','approval_status':'MATERIALS_UNREVIEWED','algorithm_tuning_permitted':False})
    write(DEST/'base_candidate_prompts_v1.json',rows)
    write(DEST/'native_tokenizer_validation_v1.json',{'identity':native.identity,'rows':results,'cases':checks,
        'source_sha256':sha(DEST/'base_candidate_prompts_v1.json'),'new_native_calls':len(native.calls),
        'unchanged_v3_token_records':1728-len(targets),'inherited_source_sha256':sha(SOURCE/'native_tokenizer_validation_v1.json'),
        'new_generations':0,'active_matches':sum(c['active_equal'] for c in checks),'control_matches':sum(c['control_equal'] for c in checks),
        'context_fit_256':all(r['context_fit_256'] for r in results),
        'input_token_range':[min(r['input_tokens'] for r in results),max(r['input_tokens'] for r in results)]})
    with (SOURCE/'material_review_candidate_v1.csv').open(encoding='utf-8',newline='') as f:reviews=list(csv.DictReader(f))
    for r in reviews:r['histories']=by_id[r['case_id']]['histories']
    csvwrite(DEST/'material_review_candidate_v1.csv',reviews)
    write(DEST/'metric_applicability_candidate_v1.json',read(SOURCE/'metric_applicability_candidate_v1.json'))
    write(DEST/'revision_inventory_v1.json',revisions)
    write(DEST/'construction_validation_v1.json',summary|{'other_person_count':144,'other_identity_cross_speaker_reuse':False,
        'case_world_scope':'Explicit independent hypothetical scenario; not global biographies','human_validity_decisions':0})
    write(DEST/'candidate_provenance_manifest_v1.json',{'source_v3_manifest_sha256':sha(SOURCE/'candidate_provenance_manifest_v1.json'),
        'code_sha256':sha(__file__),'artifact_sha256':{p.as_posix():sha(p) for p in sorted(DEST.iterdir()) if p.is_file()},
        'freeze_status':'NOT_FROZEN','execution_manifest':None,'authorized_inference_requests':0,
        'algorithm_tuning_permitted':False,'semantic_validity':'PENDING_RESEARCHER_MATERIAL_REVIEW'})
    print({'active_matches':sum(c['active_equal'] for c in checks),'control_matches':sum(c['control_equal'] for c in checks),
           'new_native_calls':len(native.calls),'new_generations':0})

if __name__=='__main__':main()
