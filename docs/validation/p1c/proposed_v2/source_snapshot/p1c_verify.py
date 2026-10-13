"""Offline final integrity and reproducibility checks for P1c planning artifacts."""
import argparse
import csv
import json
from pathlib import Path
import re
import subprocess

import p1c_design as d


def supplement():
    rows=d.read(d.PUBLIC/'precision_simulation_v1.json')['rows']
    d.write_json(d.PUBLIC/'precision_grid_v1.json',{'seed':715003,'repeats_per_scenario':1000,
        'speakers':sorted({r['speakers'] for r in rows}),'cases_per_speaker':2,
        'assumed_effects':sorted({r['assumed_effect'] for r in rows}),'contrast_ICC':sorted({r['assumed_contrast_ICC'] for r in rows}),
        'contrast_sd_pairs':sorted({(r['contrast'],r['assumed_case_sd']) for r in rows}),
        'scenario_count':len(rows),'no_empirical_variance_estimates':True,
        'missingness_stress':[{'unknown_fraction_per_cell':q,'main_effect_bound_width':2*q,'interaction_bound_width':4*q,
           'scope':'Worst-case probability bounds with same unknown fraction in every cell, before sampling uncertainty; not observed missingness.'} for q in [0,.1,.25]],
        'independent_validation_material_created':False})
    d.write_json(d.PUBLIC/'review_subset_plan_v1.json',{'status':'PROPOSED','selection_before_inference':True,
        'cases':[f'p1c_{i:02d}_'+('historical' if i%2 else 'current') for i in range(1,7)],
        'all_six_cells_per_case':True,'responses':36,'human_review_completed':0,
        'stage_A_seed_proposed':715005,'cluster_bootstrap_seed_proposed':715004,
        'reviewer_id':'','reviewed_utc':''})


def verify(output):
    base=d.read(d.LOCAL/'baseline.json');failures=[]
    allowed={'docs/research_development_log.md','docs/related_work_novelty_matrix.md'}
    for name,h in base['files'].items():
        if name not in allowed|{'.gitignore'} and d.sha(name)!=h:failures.append('Historical tracked file changed: '+name)
    old_ignore=subprocess.check_output(['git','show',base['git_sha']+':.gitignore'],text=True)
    current_ignore=Path('.gitignore').read_text(encoding='utf-8')
    d.require(current_ignore.replace('!data/synthetic/p1c_development_proposed_v1.json\n','')==old_ignore,'Unexpected ignore-policy change')
    for name,h in base['historical_artifacts'].items():
        if d.sha(name)!=h:failures.append('Historical run changed: '+name)
    for name in allowed:
        original=(d.LOCAL/(Path(name).name+'.before')).read_bytes()
        if not Path(name).read_bytes().startswith(original):failures.append('Historical log prefix changed: '+name)
    data=d.read(d.DATA);d.require(data==d.build_cases(),'Dataset no longer reconstructs')
    checks=d.validate_cases(data);stored=d.read(d.PUBLIC/'manipulation_validation_v1.json')['records']
    d.require(checks==stored,'Manipulation reconstruction differs')
    a=d.history_evidence();b=d.history_evidence();d.require(a==b==d.read(d.PUBLIC/'p1b_evidence_recheck_v1.json'),'Evidence reconstruction differs')
    jsons=list(Path('docs/validation/p1c').rglob('*.json'))+[d.DATA];csvs=list(Path('docs/validation/p1c').rglob('*.csv'))
    for p in jsons:d.read(p)
    blank_review_cells=0
    for p in csvs:
        with p.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);d.require(len(reader.fieldnames)==len(set(reader.fieldnames)),'Duplicate CSV columns')
            for row in reader:
                d.require(None not in row and all(v is not None for v in row.values()),'Invalid CSV row')
                if 'review' in p.name:
                    for k,v in row.items():
                        if k.startswith('review_') or k in ('reviewer_id','reviewed_utc','reviewer_notes'):
                            d.require(v=='','Unprovided human judgment');blank_review_cells+=1
    records=d.read('docs/validation/p1c/proposed_v2/selected_prompts_v2.json')['records']
    d.require(len(records)==72,'Not all selected prompts exist')
    for c in data['cases']:
        rs=[r for r in records if r['case_id']==c['case_id']]
        d.require({r['condition'] for r in rs}==set(d.CONDITIONS),'Missing proposed cell')
        matched=[r for r in rs if r['condition']!='H_none']
        d.require(len({r['input_tokens'] for r in matched})==1,'Length mismatch')
        d.require(len({r['fixed_context_suffix_start_token'] for r in matched})==1,'Question token position differs')
        d.require(len({r['evidence_prefix_tokens'] for r in rs})==1,'Evidence token position differs')
        for r in rs:
            d.require(d.render(c,r['history'])==r['prompt'] and d.text_hash(r['prompt'])==r['prompt_sha256'],'Prompt reconstruction differs')
            d.require(len(r['input_token_ids'])==r['input_tokens'] and r['input_tokens']+96<=4096,'Context/token count error')
            d.require(r['evidence_sha256']==d.text_hash(c['trusted_evidence']),'Evidence changed')
            d.require(r['question_sha256']==d.text_hash(c['question']) and r['reference_sha256']==d.canonical(c['reference']),'Question/reference changed')
    docs=sorted(Path('docs').glob('P1c_*.md'));broken=[]
    for p in docs:
        text=p.read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if link.startswith(('http://','https://','#')):continue
            target=(p.parent/link.split('#')[0]).resolve()
            if not target.exists() and target!=Path(output).resolve():broken.append({'file':str(p),'target':link})
    d.require(not broken,'Broken documentation links: '+str(broken))
    d.require(not failures,'Historical integrity failure: '+str(failures))
    result={'version':'p1c_final_integrity_v1','checked_utc':d.now(),'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_status':subprocess.check_output(['git','status','--short'],text=True),'status':'PASS',
        'tracked_files_compared':len(base['files']),'allowed_append_only_files':sorted(allowed),
        'allowed_configuration_change':'.gitignore: whitelist only the new fictional P1c dataset; existing exclusions preserved',
        'historical_run_files_unchanged':len(base['historical_artifacts']),'journal_scope':'Artifact byte hashes rechecked; previous chain audit evidence preserved, not rerun here.',
        'cases_reconstructed':12,'proposed_prompts_reconstructed':72,'p1b_case_contrasts_reconstructed_twice':480,
        'json_validated':len(jsons),'csv_validated':len(csvs),'blank_human_cells_checked':blank_review_cells,
        'documentation_links':'PASS','new_generations':0,'human_approval':'OPEN',
        'model_sha256':d.read('docs/validation/p1c/proposed_v2/tokenizer_validation_v2.json')['identity']['model_sha256'],
        'backend_sha256':d.read('docs/validation/p1c/proposed_v2/tokenizer_validation_v2.json')['identity']['backend_sha256']}
    d.write_json(output,result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['supplement','verify']);p.add_argument('--output');a=p.parse_args()
    if a.action=='supplement':supplement();print('Supplemental assumptions and blank review subset created')
    else:
        if not a.output:p.error('--output is required')
        print(json.dumps(verify(a.output)))
