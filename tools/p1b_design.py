"""Build or verify the P1b design package offline; never starts inference."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess

from personaslm.journal import read_events
from personaslm.p1 import validate_dataset as validate_wave1
from personaslm.p1b import build_dataset, validate_dataset, precision, hash_text
from personaslm.scientific_closure import reconcile_tokenizations

PUBLIC = Path('docs/validation/p1b')
DATASET = Path('data/synthetic/p1b_development_proposed_v1.json')
P1 = Path('docs/validation/p1')
LOCAL = Path('results/p1b_design/v1')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); rows=list(reader)
    if len(reader.fieldnames) != len(set(reader.fieldnames)) or any(None in r or None in r.values() for r in rows):
        raise ValueError('Malformed CSV')
    return rows


def write_json(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(data,indent=2,ensure_ascii=True,sort_keys=True)+'\n')


def write_csv(path, rows):
    with path.open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def historical_audit():
    """Read actual annotations/case contrasts and replay recorded GGUF tokenization."""
    old = read('data/synthetic/p1_development_v1.json')
    validate_wave1(old)
    analyses = read(P1/'researcher_analysis_dataset_v1.json')['rows']
    cases = {c['case_id']:c for c in old['cases']}
    counts = {}
    for field in ['human_factual_consistency','human_temporal_consistency','human_semantic_completeness','structural_status']:
        counts[field]=dict(Counter(r['annotation'][field] for r in analyses))
    if len(analyses) != 96 or len({r['anonymous_response_id'] for r in analyses}) != 96:
        raise ValueError('Original annotation population mismatch')
    for r in analyses:
        a=r['annotation']
        if hash_text(a['raw_full_continuation']) != a['raw_sha256'] or hash_text(a['raw_first_reply']) != a['first_reply_sha256']:
            raise ValueError('Original output hash mismatch')
        for metric, eligible in cases[r['case_id']]['applicability'].items():
            if a['applicable_'+metric] != str(eligible).lower():
                raise ValueError('Frozen applicability changed')
    contrasts=csv_rows(P1/'researcher_case_contrasts_v1.csv')
    nonzero=Counter(r['family'] for r in contrasts if r['metric'] in ['relevance','coherence']
                    and r['paired_difference'] and float(r['paired_difference']) != 0)
    matching=read(P1/'control_matching_v1.json');manifest=read(P1/'wave1_manifest_v1.json')
    events=read_events(Path(matching['run_directory']))
    expected=[(r['prompt']['text'],r['input_token_ids']) for r in manifest['requests']]
    expected += [(a['prompt']['text'],a['token_ids']) for r in matching['results'] for a in r['attempts']]
    reconciled=reconcile_tokenizations(events,expected)
    form=csv_rows(P1/'control_review_v1.csv');controls=[]
    for r in form:
        match=next(m for m in matching['results'] if m['case_id']==r['case_id'] and m['condition']==r['condition_id'])
        chosen=match['selected']
        ref=next(x for x in manifest['requests'] if x['case_id']==r['case_id'] and x['condition']==r['reference_condition'])
        if not (chosen['difference']==0 and chosen['token_count']==len(chosen['token_ids'])==match['reference_tokens']==len(ref['input_token_ids'])):
            raise ValueError('Saved real-tokenizer count mismatch')
        if hash_text(r['candidate_prompt']) != r['candidate_prompt_sha256'] or r['candidate_prompt'] != chosen['prompt']['text']:
            raise ValueError('Candidate text/hash mismatch')
        if hash_text(r['reference_prompt']) != r['reference_prompt_sha256'] or r['reference_prompt'] != ref['prompt']['text']:
            raise ValueError('Reference text/hash mismatch')
        if any(r[k] for k in r if k.startswith('check_') or k in ['researcher_decision','reviewer_id','reviewed_utc']):
            raise ValueError('New control review found: reassess OPEN status without overwriting it')
        controls.append({k:r[k] for k in ['candidate_id','case_id','condition_id','active_intervention','neutral_text',
                        'trusted_evidence','current_question','fixed_context','reference_date','history_date','expected_answer',
                        'reference_tokens','candidate_tokens','token_difference','permitted_scope','reference_prompt_sha256','candidate_prompt_sha256']})
    if len(controls)!=24:
        raise ValueError('Expected 24 existing controls')
    selected=[c for c in old['cases'] if c['wave1_selected']]
    design=read(P1/'wave1_design_v1.json')
    run_inventory=read(LOCAL/'baseline.json')['historical_run_files']
    if any(digest(path)!=sha for path,sha in run_inventory.items()):
        raise ValueError('Historical run file changed')
    observed={p.as_posix() for p in Path('results/p1_wave1/development_v1/runs').rglob('*') if p.is_file()}
    if observed != set(run_inventory):
        raise ValueError('Historical run inventory changed')
    # Both saved event chains, including the completion run, must still verify.
    chain_sizes={p.as_posix():len(read_events(p)) for p in Path('results/p1_wave1/development_v1/runs').iterdir() if p.is_dir()}
    for key,sha in [('model_file','model_sha256'),('server_file','backend_sha256')]:
        if digest(design['configuration'][key]) != design[sha].lower():
            raise ValueError('Pinned binary changed')
    result={'version':'p1b_historical_inspection_v1','annotation_counts':counts,
            'case_contrast_rows_inspected':len(contrasts),'nonzero_rating_contrasts_by_family':dict(nonzero),
            'selected_case_count':len(selected),'factual_case_units':sum(c['applicability']['factual_consistency'] for c in selected),
            'temporal_case_units':sum(c['applicability']['temporal_consistency'] for c in selected),
            'selected_case_inventory':[{k:c[k] for k in ['case_id','family','question','trusted_evidence','expected_answer','applicability']} for c in selected],
            'original_dataset_sha256':digest('data/synthetic/p1_development_v1.json'),
            'original_annotation_sha256':digest(P1/'output_human_review_researcher_verified_v1.csv'),
            'historical_run_files_unchanged':len(run_inventory),'event_chain_counts':chain_sizes,
            'recorded_native_tokenizations_reconciled':reconciled,'selected_control_matches':len(controls),
            'control_semantic_review':'OPEN','new_tokenizer_requests':0,'new_generation_requests':0,
            'model_sha256':design['model_sha256'],'backend_sha256':design['backend_sha256'],
            'scope':'Offline verification of saved native GGUF requests/responses and current binary hashes; no server launched'}
    return result,controls


def precision_grid():
    rows=[]
    for speakers in (24,48):
        for m,endpoint in [(8,'factual_all_families'),(4,'temporal_C_E_G_H')]:
            for q in (.1,.3,.5):
                for rho in (0,.2,.5):
                    for comparisons in (1,8):
                        row=precision(speakers,m,q,rho,comparisons=comparisons)
                        row['endpoint_allocation']=endpoint
                        rows.append(row)
    return {'version':'p1b_precision_sensitivity_v1','method':'Normal planning approximation, not achieved confidence or power',
            'rows':rows,'cpu_proxy_seconds_per_request':9.427759,
            'costs':[{'speakers':n,'cases':n*8,'requests_per_arm':n*8*8,
                      'historical_rate_hours':n*64*9.427759/3600,
                      'three_times_historical_rate_hours':n*64*9.427759*3/3600} for n in (24,48)]}


def build():
    outputs=[DATASET]+[PUBLIC/n for n in ['offline_validation_v1.json','historical_inspection_v1.json',
        'precision_plan_v1.json','control_review_index_v1.csv','stimulus_review_v1.csv','design_manifest_v1.json']]
    if any(p.exists() for p in outputs):
        raise FileExistsError('Preserve existing design artifacts; use a new version')
    dataset=build_dataset();validation=validate_dataset(dataset)
    historical,controls=historical_audit()
    write_json(DATASET,dataset);write_json(outputs[1],validation);write_json(outputs[2],historical)
    write_json(outputs[3],precision_grid());write_csv(outputs[4],controls)
    review=[]
    for c in dataset['cases']:
        review.append({'review_version':'p1b_stimulus_semantic_review_proposed_v1','case_id':c['case_id'],
            'persona_id':c['persona_id'],'family':c['task_family'],'designed_complexity':c['designed_complexity_level'],
            'trusted_evidence':c['trusted_evidence'],'question':c['question'],'fixed_context':'\n'.join(c['context']),
            'expected_answer':json.dumps(c['expected_answer']['components']),
            'supporting_fact_ids':'; '.join(c['expected_answer']['proof_fact_ids']),
            'style':c['style_only'],'supplemental_fact':c['supplemental_fact'],'history':c['history_dialogue'],
            'applicability':json.dumps(c['applicability']),
            'answer_uniquely_supported':'','english_question_matches_oracle':'','complexity_rationale_valid':'',
            'no_answer_leakage':'','no_unplanned_contradiction':'','speaker_and_context_clear':'',
            'reviewer_id':'','review_assistance':'','reviewed_utc':'','evidence_quotations':'','reviewer_notes':''})
    write_csv(outputs[5],review)
    sources=['src/personaslm/p1b.py','tools/p1b_design.py','docs/research_protocol_v1.1.md',
             'docs/PersonaSLM_Research_Protocol_v1.2_Revised_Proposed_r1.md']
    manifest={'version':'p1b_design_manifest_v1','status':'PROPOSAL_AWAITING_RESEARCHER_APPROVAL',
        'created_utc':datetime.now(timezone.utc).isoformat(),'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_status':subprocess.check_output(['git','status','--short'],text=True),'inference_authorized':False,
        'files':{p.as_posix():digest(p) for p in outputs[:-1]},'sources':{p:digest(p) for p in sources},
        'case_selection':'All 24 fixed prototypes; no outputs inspected, no response-driven replacements',
        'new_token_matching':'Not performed; new prompts require real tokenizer preflight after authorization',
        'initial_calibration_proposal':{'case_count':24,'speakers':12,'factorial_cells_per_case':8,
            'model_arm':'Pinned Base first, conditional separate Instruct arm later','requests':192,'executed':0}}
    write_json(outputs[6],manifest)
    print(json.dumps({'status':'PASS','cases':24,'offline_prompt_checks':validation['prompt_count'],
        'existing_controls_reverified':24,'native_tokenizations_reconciled':historical['recorded_native_tokenizations_reconciled'],
        'new_generations':0,'human_stimulus_review':'OPEN'}))


def verify():
    manifest=read(PUBLIC/'design_manifest_v1.json')
    if any(digest(p)!=h for p,h in manifest['files'].items()):
        raise ValueError('Frozen proposal artifact changed')
    if build_dataset()!=read(DATASET) or validate_dataset(read(DATASET))!=read(PUBLIC/'offline_validation_v1.json'):
        raise ValueError('Design reconstruction mismatch')
    historical,controls=historical_audit()
    if historical!=read(PUBLIC/'historical_inspection_v1.json') or controls!=csv_rows(PUBLIC/'control_review_index_v1.csv'):
        raise ValueError('Historical reconstruction mismatch')
    if precision_grid()!=read(PUBLIC/'precision_plan_v1.json'):
        raise ValueError('Planning calculation mismatch')
    print(json.dumps({'status':'PASS','reconstructed_cases':24,'preserved_historical_run_files':historical['historical_run_files_unchanged'],
                      'new_tokenizer_requests':0,'new_generation_requests':0}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','verify']);args=parser.parse_args()
    {'build':build,'verify':verify}[args.action]()
