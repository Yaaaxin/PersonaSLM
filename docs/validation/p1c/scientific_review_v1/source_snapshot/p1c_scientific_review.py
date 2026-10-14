"""Read-only stimulus audit and new review artifacts; no generation interface."""
import argparse
import ast
from collections import Counter
import csv
import difflib
from itertools import combinations
import json
import math
from pathlib import Path
import re
import subprocess

import p1c_design as d

OUT = Path('docs/validation/p1c/scientific_review_v1')
LOCAL = Path('results/p1c_scientific_review/v1')
V2 = Path('docs/validation/p1c/proposed_v2')
CELLS = tuple(d.CONDITIONS)
RT = CELLS[:4]
APPEND_ONLY = ('docs/research_development_log.md',
               'docs/P1c_algorithmic_opportunity_assessment.md',
               'docs/related_work_novelty_matrix.md')


def contrast_spec():
    weights = {k: {c: v.get(c, 0) for c in CELLS} for k, v in
               d.read(d.PUBLIC/'condition_definitions_v1.json')['weights'].items()}
    for left, right in [('R1T0','R0T0'), ('R1T1','R0T1'), ('R0T1','R0T0'), ('R1T1','R1T0')]:
        weights[left+'-'+right] = {c: int(c == left)-int(c == right) for c in CELLS}
    for left, right in [(c,'N_history') for c in RT]+[(c,'H_none') for c in RT]+[('N_history','H_none')]:
        weights[left+'-'+right] = {c: int(c == left)-int(c == right) for c in CELLS}
    return {'version':'p1c_operational_contrasts_review_v1','status':'PROPOSED_PENDING_RESEARCHER',
        'condition_order':CELLS, 'weights':weights,
        'estimand_scope':'Replacements of specific auxiliary-topic and interval/value packages; no direct answer competition or unique mechanism.',
        'recommendation':'Report four fixed-factor simple contrasts before averaged R/T and secondary operational RxT; no historical hierarchy overwritten.',
        'unit':'Within-case paired contrast; two cases per speaker, six speaker clusters; equal speaker means of case means.',
        'applicable_cases':12,'eligible_per_condition':12,'eligible_per_metric':72,
        'metrics':['response_relevance','factual_consistency','temporal_consistency','conversational_coherence',
                   'task_success','component_coverage','semantic_completeness','structural_status'],
        'persona_fidelity':'Not Applicable: no fidelity target or authorized ground truth.',
        'categorical_policy':'Report Correct/Incorrect/Unverifiable/Not Applicable/Missing separately on frozen eligible denominator. Correct-label incidence is not assessed-only accuracy.',
        'unknown_bounds':'For each unknown cell use [0,1]; choose interval endpoints by the sign of its original weight. Do not reweight cells.',
        'complete_case_sensitivity':'Only assessable required cells; state case/speaker coverage and possible condition-dependent censoring.',
        'structural_policy':'response_status_v1; no later-turn substitution; unidentifiable first reply remains unknown, not Incorrect.',
        'ordinal_policy':'Full 1-5 distributions, paired higher/equal/lower and threshold sensitivities; means descriptive.',
        'uncertainty':{'cluster':'speaker','bootstrap_seed':715004,'replicates':10000,
                       'leave_one_speaker_out':True,'warning':'Six clusters cannot support reliable population-level significance claims.'},
        'multiplicity':'Development: all prespecified estimates, no significance selection. Prior proposed six-test temporal Incorrect/task-success R/T/RxT family remains unapproved; hierarchy must be resolved before independent confirmation.',
        'new_outcomes_or_effects_computed':False}


def unknown_bounds(weights, values):
    lo = hi = 0.0
    for key, w in weights.items():
        if not w: continue
        v = values[key]
        if v is None:
            lo += min(0, w); hi += max(0, w)
        else:
            lo += w*v; hi += w*v
    return lo, hi


def quote(case, fid):
    return next(line for line in case['trusted_evidence'].splitlines() if line.startswith('['+fid+']'))


def cell_record(case, row):
    fact = next((f for f in case['facts'] if f['fact_id'] == row['history_fact_id']), None)
    factors = d.CONDITIONS[row['condition']]
    history = row['history']
    return {'case_id':case['case_id'],'condition':row['condition'],**factors,
        'reference_components':case['reference']['components'], 'required_fact_ids':case['reference']['fact_ids'],
        'history_fact_id':row['history_fact_id'],'source_quote':quote(case, fact['fact_id']) if fact else '',
        'entity':fact['entity'] if fact else case['speaker_name'] if history else None,
        'predicate':fact['predicate'] if fact else None,'value':fact['value'] if fact else None,
        'start':fact['start'] if fact else None,'end':fact['end'] if fact else None,
        'true_in_stated_interval':True if fact else None,
        'valid_at_requested_date':fact['start'] <= case['requested_date'] <= fact['end'] if fact else None,
        'source_used_by_answer_solver':fact['fact_id'] in case['reference']['fact_ids'] if fact else False,
        'answer_strings_present':[v for v in case['reference']['components'] if v.lower() in history.lower()],
        'archive_date':'2042-12-01' if history else None,
        'archive_is_after_requested_date':bool(history and '2042-12-01' > case['requested_date']),
        'turns':2 if history else 0,'speaker_roles':['Archivist',case['speaker_name']] if history else [],
        'explicit_negation':re.findall(r'\b(?:not|never|no|neither)\b',history.lower()),
        'contrastive_cue':'rather than' in history,
        'history_text':history,'history_sha256':d.text_hash(history),'input_tokens':row['input_tokens'],
        'token_ids_sha256':d.canonical(row['input_token_ids']),'prompt_sha256':row['prompt_sha256'],
        'evidence_prefix_tokens':row['evidence_prefix_tokens'],'suffix_start':row['fixed_context_suffix_start_token']}


def counterfactual_checks(case):
    original = d.ground_truth(case)
    auxiliary = [f for f in case['facts'] if f['predicate'] in ('parcel label','music label')]
    retained = [f for f in case['facts'] if f not in auxiliary]
    d.require(d.ground_truth(case,retained) == original,'Auxiliary deletion changes required answer')
    substituted = [{**f,'value':'SYMBOLIC_AUDIT_VALUE'} if f in auxiliary else f for f in case['facts']]
    d.require(d.ground_truth(case,substituted) == original,'Auxiliary substitution changes required answer')
    # Perturb only an internal solver copy. No alternative prompt/dataset is saved.
    required = original['fact_ids'][-1]
    changed = [{**f,'value':'COUNTERFACTUAL_REQUIRED_VALUE'} if f['fact_id']==required else f for f in case['facts']]
    d.require(d.ground_truth(case,changed)['components'] != original['components'],'Required-value perturbation ineffective')
    deletion=[]
    for fid in original['fact_ids']:
        try: d.ground_truth(case,[f for f in case['facts'] if f['fact_id']!=fid])
        except ValueError: deletion.append(fid)
        else: raise ValueError('Required fact dispensable: '+fid)
    return {'case_id':case['case_id'],'auxiliary_deletion_answer_unchanged':True,
        'auxiliary_value_substitution_answer_unchanged':True,'required_value_change_changes_answer':True,
        'required_deletions_make_reference_unanswerable':deletion,
        'direct_answer_leakage_in_selected_history':False,
        'interpretation':'Formal reference-solver dependency only. Does not prove absence of learned lexical shortcuts or psychological topic effects.',
        'stimulus_changed':False}


def build_audit():
    data=d.read(d.DATA); selected=d.read(V2/'selected_prompts_v2.json')['records']; cfg=d.read(V2/'configuration_proposal_v2.json')
    d.require(data==d.build_cases(),'Dataset reconstruction mismatch')
    d.validate_cases(data)
    d.require(len(selected)==72 and len({(r['case_id'],r['condition']) for r in selected})==72,'Request identity mismatch')
    d.require({tuple(x) for x in cfg['proposed_order']}=={(r['case_id'],r['condition']) for r in selected},'Order membership differs')
    d.require(cfg['proposed_order']==d.read(d.PUBLIC/'configuration_proposal_v1.json')['proposed_order'],'Original order changed')
    cells=[]; pairs=[]; inventory=[]; dependency=[]; case_forms=[]; text_forms=[]; neutral_forms=[]; repair=[]
    banks={r['case_id']:r for r in d.read(d.PUBLIC/'candidate_bank_v1.json')['cases']}
    attempts=d.read(d.PUBLIC/'candidate_token_attempts_v1.json')['attempts']
    all_fields=set(selected[0])
    for c in data['cases']:
        rs={r['condition']:r for r in selected if r['case_id']==c['case_id']}
        d.require(set(rs)==set(CELLS),'Condition routing missing')
        values={}
        for cond in CELLS:
            r=rs[cond]
            d.require(set(r)==all_fields,'Selected record schema changed')
            d.require(d.render(c,r['history'])==r['prompt'] and d.text_hash(r['prompt'])==r['prompt_sha256'],'Prompt mismatch')
            d.require(len(r['input_token_ids'])==r['input_tokens'] and r['input_tokens']+96<=4096,'Context/count mismatch')
            for field,text in [('evidence_sha256',c['trusted_evidence']),('question_sha256',c['question']),('context_sha256',c['fixed_context'])]:
                d.require(r[field]==d.text_hash(text),'Frozen text hash differs: '+field)
            d.require(r['reference_sha256']==d.canonical(c['reference']),'Answer differs')
            x=cell_record(c,r);cells.append(x);values[cond]=x
            if cond in RT:
                d.require(x['valid_at_requested_date']==bool(d.CONDITIONS[cond]['T']),'Wrong temporal routing')
                d.require(not x['source_used_by_answer_solver'] and not x['answer_strings_present'],'Direct leakage')
        d.require(len({rs[k]['input_tokens'] for k in CELLS if k!='H_none'})==1,'Matching failure')
        # Exhaustive inventory of original selected-record fields, plus linked case/config fields.
        for field in sorted(all_fields):
            vals={k:rs[k][field] for k in CELLS}
            changed=len({d.canonical(v) for v in vals.values()})>1
            inventory.append({'case_id':c['case_id'],'scope':'selected_prompt_record','field':field,'changes':changed,
                'values':vals if field not in ('prompt','input_token_ids') else {k:{'sha256':d.canonical(v),'source_condition':k} for k,v in vals.items()},
                'source':'docs/validation/p1c/proposed_v2/selected_prompts_v2.json'})
        for field in ('trusted_evidence','question','requested_date','evaluation_date','fixed_context','reference','applicability','persona_id'):
            inventory.append({'case_id':c['case_id'],'scope':'linked_dataset','field':field,'changes':False,'values':{k:c[field] for k in CELLS},'source':d.DATA.as_posix()})
        inventory.append({'case_id':c['case_id'],'scope':'linked_configuration','field':'model_and_decoding','changes':False,
            'values':{k:{f:cfg[f] for f in ('primary_arm','backend','threads','threads_batch','n_gpu_layers','n_ctx','n_predict','temperature','seed')} for k in CELLS},'source':(V2/'configuration_proposal_v2.json').as_posix()})
        for a,b in combinations(RT,2):
            x,y=values[a],values[b]
            changed=[f for f in ('predicate','value','start','end','history_fact_id','history_text','token_ids_sha256') if x[f]!=y[f]]
            pairs.append({'case_id':c['case_id'],'cell_a':a,'cell_b':b,'factor_changes':[f for f in ('R','T') if x[f]!=y[f]],
                'shared_ground_truth':True,'same_entity':x['entity']==y['entity'],'same_predicate':x['predicate']==y['predicate'],
                'same_proposition_entity_predicate_value':all(x[f]==y[f] for f in ('entity','predicate','value')),
                'same_interval':all(x[f]==y[f] for f in ('start','end')),'same_value':x['value']==y['value'],
                'changed_history_fields':changed,'source_a':x['source_quote'],'source_b':y['source_quote'],
                'validity_a':x['valid_at_requested_date'],'validity_b':y['valid_at_requested_date'],
                'same_turns_roles_archive_date':all(x[f]==y[f] for f in ('turns','speaker_roles','archive_date')),
                'same_negation_cues':x['explicit_negation']==y['explicit_negation'],
                'topic_a':x['predicate'],'topic_b':y['predicate'],'new_competing_entity':False,'direct_answer_disclosed':False,
                'token_count_a':x['input_tokens'],'token_count_b':y['input_tokens'],'token_difference':y['input_tokens']-x['input_tokens'],
                'evidence_position_equal':x['evidence_prefix_tokens']==y['evidence_prefix_tokens'],
                'question_position_equal':x['suffix_start']==y['suffix_start'],
                'interpretation':'Operational history replacement; predicate/value/date package changes preclude unique semantic mechanism identification.',
                'human_confirmation':'OPEN'})
        dependency.append(counterfactual_checks(c))
        rr=rs['R1T1'];risk=(
            'Parcel versus music is a topic/predicate/value package. '+
            ('Question explicitly says parcel; lexical overlap differs.' if c['family']=='route_integration' else
             'Question says collection desk, not parcel: topical relation is assumed from scenario and requires confirmation.')+
            ' Colors follow a shared cyclic construction; auxiliary labels may cue periods. '+
            ('Archive is recorded after the historical requested date; retrospective records are permitted, not an as-of-information-availability task.' if c['query_mode']=='historical' else
             'Archive predates the requested current date; scheduled validity extends through it.'))
        case_forms.append({'case_id':c['case_id'],'speaker':c['speaker_name'],'family':c['family'],'query_mode':c['query_mode'],
            'trusted_evidence':c['trusted_evidence'],'question':c['question'],'requested_date':c['requested_date'],'evaluation_date':c['evaluation_date'],
            'fixed_context':c['fixed_context'],'expected_answer':c['reference']['components'],
            'source_quotes':[quote(c,f) for f in c['reference']['fact_ids']],
            'scientific_purpose':'Auxiliary topical-history replacement at fixed requested-date answer; all six original conditions.',
            'automated_result':'Reference/dependency/equality/count checks PASS; semantic approval absent.',
            'specific_risks':risk,'AI_assisted_recommendation':'Consider narrow development calibration only; not a stale-answer competition test.',
            'supporting_explanation':c['reference']['derivation']+' Auxiliary source IDs do not intersect required fact IDs.',
            'source_reference':d.DATA.as_posix()+'#'+c['case_id'],
            **{k:'' for k in ('researcher_evidence_and_answer','researcher_topic_definition','researcher_time_interpretation','researcher_narrow_scope','researcher_decision','researcher_notes','reviewer_id')}})
        for cond in CELLS[:-1]:
            x=values[cond];fact=x['source_quote'];neutral=cond=='N_history'
            risks=('Procedural record-reading priming; repeated archive vocabulary; contrastive rather than; no personal validity interval; formal self-referential reply; archive timestamp remains.' if neutral else risk)
            purpose=('Length/format-matched procedural archive comparator; no claim of semantic inertness.' if neutral else
                     f"Auxiliary {'parcel-topic' if x['R'] else 'music-topic'} record, {'valid' if x['T'] else 'expired'} at {c['requested_date']}; no target-answer fact.")
            record={'item_id':c['case_id']+'__'+cond,'case_id':c['case_id'],'condition':cond,'R':x['R'],'T':x['T'],
                'full_history_text':x['history_text'],'trusted_evidence':c['trusted_evidence'],'current_question':c['question'],
                'expected_answer':c['reference']['components'],'requested_date':c['requested_date'],'evaluation_date':c['evaluation_date'],
                'scientific_purpose':purpose,'source_quote':fact,'input_tokens':x['input_tokens'],'matching_difference':x['input_tokens']-rr['input_tokens'],
                'prompt_sha256':x['prompt_sha256'],'specific_semantic_risks':risks,
                'automated_validation':'Identity, source truth (active only), no direct answer string, final-token matching PASS; semantics OPEN.',
                'AI_assisted_recommendation':'REVIEW_REQUIRED; consider only the stated limited replacement comparison.',
                'supporting_explanation':fact if fact else 'Text describes archive organization rather than a personal interval-valued fact; it is not equivalent to an empty history.',
                'source_reference':(V2/'selected_prompts_v2.json').as_posix()+'#'+c['case_id']+'/'+cond,
                **{k:'' for k in ('researcher_no_answer_leakage','researcher_topic_and_time','researcher_speaker_and_coherence','researcher_narrow_comparison','researcher_decision','researcher_notes','reviewer_id')}}
            text_forms.append(record)
            if neutral: neutral_forms.append(record.copy())
        old=banks[c['case_id']]['conditions']['N_history'][7]['text'];new=rs['N_history']['history']
        old_prompt=d.render(c,old);old_tokens=next(a['tokens'] for a in attempts if a['case_id']==c['case_id'] and a['condition']=='N_history' and a['variant_id']==7)
        repair.append({'case_id':c['case_id'],'original_selected_candidate_variant':7,'original_text':old,'repaired_text':new,
            'text_diff':list(difflib.ndiff(old.splitlines(),new.splitlines())),'old_prompt_sha256':d.text_hash(old_prompt),'new_prompt_sha256':rs['N_history']['prompt_sha256'],
            'original_tokens':old_tokens,'repaired_tokens':rs['N_history']['input_tokens'],'reference_tokens':rr['input_tokens'],
            'original_difference':old_tokens-rr['input_tokens'],'repaired_difference':rs['N_history']['input_tokens']-rr['input_tokens'],
            'old_token_source':(d.PUBLIC/'candidate_token_attempts_v1.json').as_posix(),'new_token_ids':rs['N_history']['input_token_ids'],
            'human_approval':'OPEN'})
    precision=d.read(d.PUBLIC/'precision_simulation_v1.json')
    d.require(len(precision['rows'])==135,'Precision grid differs')
    for r in precision['rows']:
        expected=1.96*r['assumed_case_sd']*math.sqrt((1+r['assumed_contrast_ICC'])/(2*r['speakers']))
        d.require(abs(expected-r['analytical_1_96_halfwidth'])<1e-14,'Precision formula mismatch')
    return {'cell_audit':cells,'counterfactual_pairs':pairs,'intervention_difference_inventory':inventory,
        'reference_dependency_checks':dependency,'case_review':case_forms,'history_text_review':text_forms,'neutral_review':neutral_forms,
        'neutral_repair_inventory':repair,'factorial_contrast_specification':contrast_spec(),
        'summary':{'cases':12,'speakers':6,'conditions':list(CELLS),'planned_identities':len(selected),
            'identity_definition':'Original case_id/condition tuple; original configuration has no separate request_id. Order unchanged.',
            'planned_order_sha256':d.canonical(cfg['proposed_order']),'rt_pairs':len(pairs),'rt_cells':48,
            'matched_sets':12,'history_review_items':len(text_forms),'neutral_review_items':len(neutral_forms),
            'same_proposition_pairs':sum(p['same_proposition_entity_predicate_value'] for p in pairs),
            'same_color_cross_topic_pairs':sum(p['same_value'] and not p['same_predicate'] for p in pairs),
            'active_token_range':[min(r['input_tokens'] for r in selected if r['condition']!='H_none'),max(r['input_tokens'] for r in selected)],
            'no_history_token_differences':dict(Counter(rs['input_tokens']-next(x['input_tokens'] for x in selected if x['case_id']==rs['case_id'] and x['condition']=='H_none') for rs in selected if rs['condition']=='R1T1')),
            'precision_configurations_checked':135,'precision_checks':'Saved scenario inputs, analytical formula and provenance; Monte Carlo draws not rerun.',
            'generation_executed':0,'human_review':'OPEN','scientific_decision':'NO_GO_PENDING_RESEARCHER',
            'stimulus_changes':0}}


def publish():
    d.require(not (OUT/'audit_summary_v1.json').exists(),'Refuse overwrite')
    audit=build_audit()
    for key,value in audit.items():
        if key=='summary': d.write_json(OUT/'audit_summary_v1.json',value)
        elif key.endswith('_review'): d.write_csv(OUT/(key+'_v1.csv'),value)
        else: d.write_json(OUT/(key+'_v1.json'),{'records':value} if isinstance(value,list) else value)
    d.write_csv(OUT/'counterfactual_comparison_matrix_v1.csv',audit['counterfactual_pairs'])
    evidence=d.history_evidence();d.require(evidence==d.history_evidence(),'Prior contrasts not deterministic')
    d.write_json(OUT/'p1b_evidence_recheck_v2.json',evidence)
    return audit['summary']


def native_verify():
    import p1c_tokenize as t
    t.LOCAL=LOCAL/'tokenizer_recheck'
    native=t.NativeTokenizer()
    d.require(native.identity['tokenizer_sha256']==d.read(V2/'tokenizer_validation_v2.json')['identity']['tokenizer_sha256'],'Tokenizer binary changed')
    records=d.read(V2/'selected_prompts_v2.json')['records']; checks=[]
    for r in records:
        ids=native.tokens(r['prompt']);d.require(ids==r['input_token_ids'],'Saved native IDs differ')
        checks.append({'case_id':r['case_id'],'condition':r['condition'],'prompt_sha256':r['prompt_sha256'],
                       'input_tokens':len(ids),'all_ids_equal':True})
    result={'identity':native.identity,'records':checks,'actual_native_calls':len(native.calls),'new_generations':0,
            'scope':'All 72 final prompts retokenized with vocabulary-only utility. No model completion or server launched.'}
    d.write_json(OUT/'native_reverification_v1.json',result)
    return {'prompts':len(checks),'ids_equal':True,'native_calls':len(native.calls),'new_generations':0}


def verify(output):
    base=d.read(LOCAL/'baseline.json')
    for name,h in base['files'].items():
        if name not in APPEND_ONLY:d.require(d.sha(name)==h,'Existing tracked file changed: '+name)
    for name in APPEND_ONLY:
        d.require(Path(name).read_bytes().startswith((LOCAL/(Path(name).name+'.before')).read_bytes()),'Historical document prefix changed')
    for name,h in base['historical_artifacts'].items():d.require(d.sha(name)==h,'Historical run changed: '+name)
    prior=d.read(V2/'reproducibility_manifest_v1.json')
    for name,h in prior['native_call_logs'].items():d.require(d.sha(name)==h,'Original tokenizer log changed')
    audit=build_audit()
    d.require(d.canonical(audit['summary'])==d.canonical(d.read(OUT/'audit_summary_v1.json')),'Audit reconstruction differs')
    for key in ('cell_audit','counterfactual_pairs','intervention_difference_inventory','reference_dependency_checks','neutral_repair_inventory'):
        d.require(audit[key]==d.read(OUT/(key+'_v1.json'))['records'],'Reconstruction differs: '+key)
    d.require(d.history_evidence()==d.read(OUT/'p1b_evidence_recheck_v2.json'),'P1b evidence changed')
    jsons=list(OUT.rglob('*.json'));csvs=list(OUT.rglob('*.csv'));blank=0
    for p in jsons:d.read(p)
    for p in csvs:
        with p.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);d.require(len(reader.fieldnames)==len(set(reader.fieldnames)),'Duplicate CSV columns')
            for r in reader:
                d.require(None not in r and all(v is not None for v in r.values()),'Invalid CSV row')
                for k,v in r.items():
                    if k.startswith('researcher_') or k=='reviewer_id':d.require(v=='','Human approval invented');blank+=1
    for name in ('case_review','history_text_review','neutral_review'):
        with (OUT/(name+'_v1.csv')).open(encoding='utf-8',newline='') as f: actual=list(csv.DictReader(f))
        expected=[{k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else '' if v is None else str(v)
                   for k,v in row.items()} for row in audit[name]]
        d.require(actual==expected,'Review source content differs: '+name)
    broken=[]
    pending_outputs={Path(output).resolve(),(OUT/'reproducibility_manifest_v1.json').resolve()}
    for p in Path('docs').glob('P1c_*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if not link.startswith(('http:','https:','#')):
                target=(p.parent/link.split('#')[0]).resolve()
                if not target.exists() and target not in pending_outputs:broken.append([str(p),link])
    d.require(not broken,'Broken links: '+str(broken))
    native=d.read(OUT/'native_reverification_v1.json');d.require(len(native['records'])==72 and all(r['all_ids_equal'] for r in native['records']),'Native verification incomplete')
    old_identity=d.read(V2/'tokenizer_validation_v2.json')['identity']
    for key in ('model_sha256','backend_sha256','tokenizer_sha256','dll_hashes'):
        d.require(native['identity'][key]==old_identity[key],'Native identity differs: '+key)
    result={'status':'PASS','checked_utc':d.now(),'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_status':subprocess.check_output(['git','status','--short'],text=True),'tracked_baseline_files':len(base['files']),
        'historical_run_files_unchanged':len(base['historical_artifacts']),'original_native_logs_unchanged':len(prior['native_call_logs']),
        'append_only_documents':APPEND_ONLY,'json_files':len(jsons),'csv_files':len(csvs),'blank_human_cells':blank,
        'reconstructed_prompts':72,'p1b_contrasts':480,'documentation_links':'PASS','native_tokens':'72/72 identical',
        'new_generations':0,'limits':'Historical byte preservation checked; prior chain audits retained, not rerun. Semantic approval remains OPEN.'}
    d.write_json(output,result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','native','verify']);parser.add_argument('--output');a=parser.parse_args()
    result=publish() if a.action=='build' else native_verify() if a.action=='native' else verify(a.output)
    print(json.dumps(result,ensure_ascii=True))
