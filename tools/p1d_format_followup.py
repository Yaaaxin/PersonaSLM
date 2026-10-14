"""Bounded offline baseline/measurement checks and targeted material-risk accounting."""
from collections import Counter
from pathlib import Path
import os
import statistics
import time
import p1d_format_calibration as f
from p1d_design import csvwrite
from p1c_boundary_baselines import extract,METHODS,fixture_bank
from personaslm.observations import memory_observation

OUT=f.OUT/'followup_v1'

def stop_shadow(raw,stops):
    hits=[raw.index(s) for s in stops if s in raw]
    return raw[:min(hits)] if hits else None

def main():
    rows=f.load(f.OUT/'execution_integrity_v1.json')['rows']
    times={}
    for method in METHODS:
        batches=[]
        for _ in range(5):
            started=time.process_time_ns()
            for _ in range(100):
                for r in rows:extract(r['result']['raw_response'],r['result']['raw_termination'],method)
            batches.append((time.process_time_ns()-started)/(100*16))
        times[method]={'cpu_ns_per_record_batches':batches,'median_cpu_ns':statistics.median(batches)}
    negative=[]
    for fixture in fixture_bank():
        view=stop_shadow(fixture['raw'],f.STOPS)
        negative.append({'fixture_id':fixture['fixture_id'],'candidate':view,
            'authored_reference':fixture['authored_reference_content'],'matches_authored_content':view is not None and view.strip()==fixture['authored_reference_content'].strip(),
            'premature_cut':view is not None and len(view.strip())<len(fixture['authored_reference_content'].strip()),
            'source':'Existing p1c_boundary_baselines.fixture_bank; authored software fixture, not independent boundary labels'})
    f.save(OUT/'offline_stop_baseline_v1.json',{'actual_pairs':8,'exact_shadow_vs_generated_stop_matches':8,
        'independent_accuracy':None,'timing':times,'fixture_checks':negative,
        'negative_result':'Conventional stops reproduce observed cuts, but cannot supply missing task content. Literal role strings can cut fenced examples.',
        'new_algorithm':False,'new_generation':0,'source_sha256':f.sha256(Path(__file__))})
    applicability={(r['case_id'],r['condition']):r for r in f.load('docs/validation/p1d/proposed_v1/metric_applicability_v2.json')}
    proposal=f.load(f.OUT/'analysis_v1/provisional_analysis_dataset_v1.json');verified=[]
    for r in proposal:
        registered=applicability[r['case_id'],'H_none']
        f.require(all(registered[k]==v for k,v in r['metric_applicability'].items()),'Applicability differs')
        verified.append({'request_id':r['request_id'],'case_id':r['case_id'],'all_nine_metrics_match_frozen_matrix':True})
    f.save(OUT/'metric_applicability_verification_v1.json',verified)
    bank=Path('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')
    prompts=bank.with_name('base_candidate_prompts_v1.json')
    f.require(f.sha256(bank)=='170e43772e0e45753638228a8c2fc2bf2d5a9f06830374b22887a5929486afbd','Candidate bank changed')
    f.require(f.sha256(prompts)=='af6836fdbd0f9a7b7d72603bbb6c05b5326c8c023c0f12f9992164c8de00b45e','Candidate prompts changed')
    cases=f.load(bank)['cases'];ps=f.load(prompts);bycase={c['case_id']:[p for p in ps if p['case_id']==c['case_id']] for c in cases}
    risk=[]
    for c in cases:
        context=c['fixed_context'];assistant=context.rsplit('Assistant:',1)[-1].strip()
        unmarked=sum(p['prompt'].endswith('\nCURRENT QUESTION\n'+c['question']+'\nAssistant:') for p in bycase[c['case_id']])
        risk.append({'case_id':c['case_id'],'speaker_id':c['speaker_id'],'family':c['family'],'fixed_assistant_text':assistant,
            'current_question_unmarked_cells':unmarked,'expected_cells':6,'AI_scientific_validity':'VALID_WITH_LIMITATIONS_UNCHANGED',
            'new_material_risk':'Shares promise-like fixed assistant context and unmarked current question with unsuccessful development configuration. Transfer risk, not proven cause.',
            'control_policy':'LENGTH_MATCHED_DIAGNOSTIC_CONTROL','correction':'No stimulus edit. Require a qualified output/model configuration before main freeze.',
            'researcher_decision':'','reviewer_id':''})
    csvwrite(OUT/'candidate_format_risk_inventory_v1.csv',risk)
    f.save(OUT/'candidate_format_risk_summary_v1.json',{'case_count':len(cases),'prompts':len(ps),'unmarked_current_question_prompts':sum(r['current_question_unmarked_cells'] for r in risk),
        'fixed_assistant_statements':dict(Counter(r['fixed_assistant_text'] for r in risk)),'source_sha256':{bank.as_posix():f.sha256(bank),prompts.as_posix():f.sha256(prompts)},
        'new_scientific_approvals':0,'no_reference_answers_used_for_algorithm_tuning':True,'scope':'Targeted prompt-format propagation audit; previous full scientific reference/control audits retained, not redundantly rerun.'})
    f.save(OUT/'postrun_memory_observation_v1.json',memory_observation(os.getpid()))
    print({'offline_methods':len(METHODS),'existing_authored_fixtures':len(negative),'applicability_checked':16,'candidate_format_risks':len(risk),'new_inference':0})

if __name__=='__main__':main()
