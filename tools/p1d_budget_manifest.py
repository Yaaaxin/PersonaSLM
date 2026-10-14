"""Prepare a bounded development-only budget proposal and audit saved outputs.

This module has no HTTP client, subprocess launch or inference entry point.
The candidate manifest is NOT an execution authorization.
"""
from collections import Counter
import csv
from pathlib import Path
import random
from p1d_design import read, write, csvwrite, sha, th, CELLS
from p1d_scientific_audit import DEST

READINESS=Path('docs/validation/p1d/development_readiness_v1')

def historical_budget_audit():
    sources={
        'p1b':Path('results/p1b_calibration/development_v1/runs/20261013T172032-271543cb614847e8ae2ef33cca902701/events'),
        'p1c':Path('results/p1c_calibration/development_v1/runs/20261014T062351-c6724f67d31c4f7e83341957adcc42a4/events')}
    b=read('docs/validation/p1b/confirmed_analysis_v1/analysis_v1/unblinded_analysis_dataset_v1.json')['rows']
    c=read('docs/validation/p1c/confirmed_semantic_v1/registration/confirmed_annotations_v1.json')['primary']
    bmap={r['request_id']:r for r in b}
    smap={r['anonymous_response_id']:r for r in csv.DictReader(open('docs/validation/p1c/calibration_v1/measurement_v1/structural_review_view_v1.csv',encoding='utf-8-sig'))}
    cm={r['anonymous_response_id']:r for r in c}
    mapping=read('docs/validation/p1c/calibration_v1/measurement_v1/protected_treatment_mapping_v1.json')['rows']
    cmap={r['request_key']:cm[r['anonymous_response_id']] for r in mapping}
    rows=[];counts={};seen={}
    for wave,path in sources.items():
        events=[]
        for p in sorted(path.glob('*.json')):
            e=read(p)
            if e['kind']==wave+'_result':events.append((p,e['data']))
        if len(events)!=(192 if wave=='p1b' else 72):raise ValueError('Unexpected saved output count')
        for p,r in events:
            raw=r['raw_response'];key=th(raw)
            if wave=='p1b':
                a=bmap[r['request_id']];status=a['structural_status'];delivery=a['confirmed_answer_delivery'];complete=a['confirmed_semantic_completeness'];rid=a['anonymous_response_id']
                if a['raw_full_continuation']!=raw:raise ValueError('Saved response mismatch')
                first=a['raw_first_reply'];factual=a['confirmed_factual_consistency']
            else:
                a=cmap[r['request_key']];rid=a['anonymous_response_id'];s=smap[rid];status=s['frozen_structural_status'];complete=a['ratings']['semantic_completeness']
                delivery={1:'Success',0:'Failure',None:'Uncertain'}[a['ratings']['task_success']];first=s['raw_first_reply'];factual=a['ratings']['factual_consistency']
                if s['raw_full_continuation']!=raw:raise ValueError('Saved response mismatch')
            rows.append({'wave':wave,'response_id':rid,'raw_event':p.as_posix(),'raw_event_sha256':sha(p),'raw_sha256':key,
                         'native_termination':r['raw_termination'],'output_budget_termination':r['raw_termination']['stop_type']=='limit',
                         'generated_tokens':r['generated_tokens'],'structural_status':status,'semantic_completeness':complete,
                         'answer_delivery':delivery,'factual_consistency':factual,'first_reply_chars':len(first),'raw_chars':len(raw),
                         'raw_continuation':raw if status in ('TRUNCATED','AMBIGUOUS') else '',
                         'interpretation':'Historical confirmed ratings, not newly assigned. Budget saturation does not imply incomplete first answer.'})
        selected=[r for r in rows if r['wave']==wave]
        if len({r['response_id'] for r in selected})!=len(selected):raise ValueError('Repeated identity in annotation join')
        counts[wave]={'n':len(selected),'termination':dict(Counter(str(r['native_termination']['stop_type']) for r in selected)),
            'structural':dict(Counter(r['structural_status'] for r in selected)),
            'budget_and_completeness':dict(Counter(str(r['output_budget_termination'])+'|'+r['semantic_completeness'] for r in selected)),
            'budget_and_delivery':dict(Counter(str(r['output_budget_termination'])+'|'+r['answer_delivery'] for r in selected))}
    return rows,counts

def build():
    proposal=read(READINESS/'output_budget_diagnostic_proposal_v1.json')
    cases=read(READINESS/'development_examples_v5.json')['cases']
    if sha(READINESS/'development_examples_v5.json')!=proposal['source_development_examples_sha256']:raise ValueError('Development bank differs')
    chosen=proposal['development_case_ids'];cb={c['case_id']:c for c in cases}
    prompts=[p for p in read(READINESS/'development_prompts_v5.json') if p['case_id'] in chosen]
    model=read('docs/validation/p1d/proposed_v1/model_configuration_proposal_v1.json')['base']
    pairs=[(cid,cell) for cid in chosen for cell in CELLS];rng=random.Random(716703);rng.shuffle(pairs)
    lookup={(p['case_id'],p['condition']):p for p in prompts};requests=[]
    for cid,cell in pairs:
        budgets=[96,192,256];rng.shuffle(budgets)
        p=lookup[cid,cell]
        if th(p['prompt'])!=p['prompt_sha256'] or len(p['input_token_ids'])!=p['input_tokens']:raise ValueError('Development prompt/tokens invalid')
        for budget in budgets:
            rid=f'p1d_budget_dev_v1_{cid}_{cell}_b{budget}'
            request={'request_id':rid,'order':len(requests),'case_id':cid,'speaker_id':p['speaker_id'],'condition':cell,
                'family':cb[cid]['family'],'query_date':cb[cid]['query_date'],'prompt':p['prompt'],'prompt_sha256':p['prompt_sha256'],
                'input_token_ids':p['input_token_ids'],'input_token_ids_sha256':th(str(p['input_token_ids'])),
                'input_tokens':p['input_tokens'],'evidence_sha256':p['trusted_evidence_sha256'],'question_sha256':p['question_sha256'],
                'context_sha256':p['context_sha256'],'reference':p['reference'],'reference_sha256':p['reference_sha256'],
                'max_new_tokens':budget,'seed':42,'temperature':0,'top_p':1,'cache_prompt':False,'stop':[],
                'context_remaining':4096-p['input_tokens']-budget,'split':'DEVELOPMENT_ONLY_NEVER_INDEPENDENT_VALIDATION'}
            request['request_sha256']=th(__import__('json').dumps(request,sort_keys=True,separators=(',',':')))
            requests.append(request)
    return {'version':'p1d_budget_manifest_candidate_v1','status':'FROZEN_BYTES_PROPOSAL_NOT_AUTHORIZED',
        'authorized_requests':0,'proposed_requests':144,'max_generated_tokens':sum(r['max_new_tokens'] for r in requests),
        'independent_validation_requests':0,'instruct_requests':0,'model':model,'native_tokenizer_identity':read(READINESS/'tokenizer_validation_v3.json')['identity'],
        'execution_order_seed':716703,'requests':requests,
        'source_sha256':{p.as_posix():sha(p) for p in (READINESS/'development_examples_v5.json',READINESS/'development_prompts_v5.json',READINESS/'output_budget_diagnostic_proposal_v1.json',Path('docs/validation/p1d/proposed_v1/model_configuration_proposal_v1.json'))},
        'prospective_selection_rule':proposal['prospective_selection_rule'],
        'discrete_acceptance_counts':{'per_budget_denominator':48,'minimum_complete_replies':44,'maximum_unresolved_boundaries':2},
        'logging':['write-ahead request ID/hash','full raw HTTP bytes/text','input token audit','generated token IDs if available','native stop reason','latency','process RSS where available','error','frozen response_status_v1 and extracted first span','masked semantic review'],
        'preflight':['Explicit researcher authorization bound to this exact manifest SHA-256','Exact model/backend/DLL/tokenizer and prompt hashes','No independent candidate IDs','CPU-only 4 threads, batch 4, context 4096','Actual backend input token IDs equal saved native IDs; no truncation','Record complete effective decoding defaults before first request','One request attempt per ID; no parameter-changing retry'],
        'stopping':'Finish the fixed 144 attempts unless integrity mismatch, OOM, runtime failure or six-hour wall-clock ceiling. Preserve partial results; no significance/effect-sign stopping. Never retry an uncertain completed request.',
        'resume':'Resume only demonstrably unsent IDs under the same approved manifest after journal reconciliation; no additional retry allocation. Unknown completion requires researcher resolution.',
        'boundary_policy':'Original response_status_v1/extraction retained; independently adjudicated alternative spans reported separately. No new stop sequences in this diagnostic.',
        'budget_comparison':'All 48 case-condition blocks at all three budgets. No effect-sign selection. Compare common-prefix agreement as a runtime diagnostic; temperature zero does not guarantee deterministic backend equivalence.',
        'limitations':['Already inspected synthetic development examples, not held-out data.','Development input lengths are shorter than candidate bank; adequacy cannot guarantee performance on final validation.','Fixed-window patterns can support shortcuts; this diagnostic concerns delivery/boundaries, not reasoning mechanisms.','Any change to main 96-token policy requires a prospective amendment.','No human semantic ratings or execution approval created.']}

def main():
    rows,counts=historical_budget_audit();csvwrite(DEST/'historical_budget_delivery_audit_v2.csv',rows)
    write(DEST/'historical_budget_summary_v2.json',{'counts':counts,'new_ratings':0,'new_generations':0,'raw_result_events_verified':len(rows),'supersedes':'historical_budget_summary_v1.json','correction':'Request identity join replaces non-unique raw-text-hash join; v1 preserved as failed diagnostic, not historical science.'})
    manifest=build()
    path=DEST/'budget_calibration_manifest_candidate_v1.json'
    if path.exists():
        if read(path)!=manifest:raise ValueError('Existing manifest differs; refuse overwrite')
    else:write(path,manifest)
    print({'historical':counts,'proposed_requests':len(manifest['requests']),'manifest_sha256':sha(DEST/'budget_calibration_manifest_candidate_v1.json'),'authorized':0})

if __name__=='__main__':main()
