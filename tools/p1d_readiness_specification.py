"""Bind readiness specifications to adopted plan; no executable generation manifest."""
from collections import Counter
from p1d_design import OUT, CELLS, read, write, sha
from p1d_stimulus_preparation import DEST

def main():
    allocation = read(OUT/'allocation_selection_v1.json')
    subset = set(allocation['instruct_speaker_indices'])
    rows = allocation['allocation']
    matched = [r for r in rows if r['speaker_index'] in subset]
    review_overlap = subset & set(allocation['independent_review_speaker_indices'])
    write(DEST/'model_comparison_estimands_v1.json', {
        'version':'p1d_model_comparison_implementation_v1', 'policy_sha256':sha(OUT/'analysis_policy_proposal_v1.json'),
        'allocation_source_sha256':sha(OUT/'allocation_selection_v1.json'),
        'base':{'speakers':144,'cases':288,'requests':1728},
        'instruct':{'speakers':24,'cases':48,'requests':288,'matched_cells':CELLS,
                    'speaker_indices':sorted(subset),'family_counts':dict(Counter(r['family'] for r in matched)),
                    'date_counts':dict(Counter(r['date_type'] for r in matched))},
        'base_requests_in_matched_comparison':288,'extra_base_requests':0,'unmatched_base_cases':240,
        'cell_estimand':'For each cell c, mean across matched speakers of the within-speaker mean Y_Instruct(c)-Y_Base(c)',
        'contrast_estimand':'For each of the registered 16 w vectors, speaker mean of sum_c w_c [Y_Instruct(c)-Y_Base(c)] on the same 48 cases',
        'interpretation':'Secondary matched-subset configuration sensitivity; not full-cohort model-by-factor estimation or pure post-training effect',
        'missingness':'Original signed contrast bounds separately per model; difference bounds [L_I-U_B,U_I-L_B]; no dropping or cell renormalization',
        'independent_review_overlap':{'speakers':len(review_overlap),'instruct_responses':len(review_overlap)*12},
        'source_family_dependence':'Balanced fixed template bank; speaker resampling is conditional on selected templates. New names do not establish independent template populations.',
        'authorized_inference_requests':0})
    cases=read(DEST/'development_examples_v5.json')['cases']
    chosen=[c for c in cases if int(c['case_id'][-1])==(0 if int(c['speaker_id'][-2:])<4 else 1)]
    assert len(chosen)==8
    budget = {
        'version':'p1d_budget_diagnostic_proposed_v1','status':'PROPOSAL_ONLY_NOT_AUTHORIZED',
        'source_development_examples_sha256':sha(DEST/'development_examples_v5.json'),
        'development_case_ids':[c['case_id'] for c in chosen], 'cases':8,'speakers':8,
        'task_family_counts':dict(Counter(c['family'] for c in chosen)),
        'requested_date_counts':dict(Counter(c['date_type'] for c in chosen)),
        'conditions':CELLS, 'budgets':[96,192,256], 'base_requests_if_separately_authorized':144,
        'optional_instruct_requests_if_separately_authorized_and_ready':144,
        'included_in_main_2016_targets':False,'authorized_requests':0,'executable_manifest':None,
        'base_configuration_reference':str(OUT/'model_configuration_proposal_v1.json'),
        'only_intended_change':'max_new_tokens; same input, model, CPU, seed, order policy and extraction policy',
        'reference_budget':96,'independent_validation_use':'Excluded; eight already inspected development cases',
        'prospective_selection_rule':[
            'Evaluate delivery, components, semantic completeness and boundary adjudicability before viewing factor contrasts',
            'Compare all three budgets on all 48 case-condition pairs, retain every failure and paired change',
            'Operational targets: at least 90% complete replies and at most 5% unresolved boundaries in the development diagnostic; no population guarantee',
            'Prefer the smallest budget meeting both targets; if none meets them, do not freeze a claimed adequate budget',
            'Report task-family losses and uncertain judgments; no selection by desired E/V signs',
            'Any departure from adopted 96-token reference requires a documented prospective amendment in the execution packet, not automatic adoption'],
        'cost':{'source_P1c_seconds_per_request':16.06338447222222,
            'rough_token_scaled_base_hours':48*(96+192+256)/96*16.06338447222222/3600,
            'caveat':'Unmeasured P1d latency. Longer input, prefill, cache and early EOS invalidate simple proportional prediction; allow 1-3x scenario range, not a benchmark'},
        'limitations':'Authored gold replies are 8-24 native tokens, but this does not establish model answer completeness. P1c budget saturation may occur after a complete first reply. No new responses exist.'}
    write(DEST/'output_budget_diagnostic_proposal_v1.json', budget)
    write(DEST/'statistical_implementation_binding_v1.json', {
        'policy_sha256':sha(OUT/'analysis_policy_proposal_v1.json'),
        'contrast_sha256':sha(OUT/'contrast_specification_v1.json'),
        'implementation_sha256':sha('tools/p1d_registered_statistics.py'),
        'registered_comparisons':16,'primary_family_size':6,'resamples':10000,'seed':716201,
        'primary_endpoints':['temporal_Incorrect_label_incidence','task_success'],
        'primary_contrasts':['E','V','ExV'],
        'methods':['paired cases','equal speaker aggregation','normal cluster-SE sensitivity','Bonferroni six-family intervals','whole-speaker percentile bootstrap','leave-one-speaker-out','full category distributions','unknown-outcome bounds','selected assessed-only sensitivity'],
        'implementation_scope':'Bounded categorical outcomes; ordinal distributions/sign/rank and future free-text/human import are still separate integration tasks, not inferred from binary tests',
        'empirical_P1d_analysis_executed':False,'policy_changed':False,
        'no_guarantee':'Sharing parameters in simulations are assumed, not empirical ICC estimates. Template dependencies and nonrandom synthetic population constrain generalization.'})
    write(DEST/'readiness_gate_v1.json',{
        'prospective_protocol':'APPROVED_WITH_SCIENTIFIC_LIMITATIONS',
        'approval_source':'docs/validation/p1d/authorization_v1/researcher_plan_approval_corrected_v1.json',
        'inference_decision':'NO_GO','authorized_requests':0,
        'targets':{'speakers':144,'cases':288,'base_requests':1728,'instruct_requests':288},
        'candidate_dataset_manifest':None,'frozen_request_manifest':None,
        'gates':[
            {'item':'Prospective protocol and corrected binding','status':'PASS'},
            {'item':'Development examples/token matching','status':'PASS_DEVELOPMENT_ONLY_16_CASES'},
            {'item':'Independent 288-case construction and semantic validation','status':'PENDING_NOT_CREATED'},
            {'item':'Procedural control semantic review','status':'PENDING_DIAGNOSTIC_ONLY'},
            {'item':'Independent boundary and construct review','status':'PENDING_HUMAN_DATA'},
            {'item':'Base identity/native vocabulary','status':'PASS'},
            {'item':'Instruct official metadata identity','status':'PASS_METADATA_ONLY'},
            {'item':'Instruct local GGUF/tokenizer/template runtime/RAM/latency','status':'PENDING'},
            {'item':'Empirical output-budget suitability','status':'PENDING_SEPARATELY_AUTHORIZED_DEVELOPMENT_DIAGNOSTIC'},
            {'item':'Bound statistical policy/weights/precision assumptions','status':'PASS_PROSPECTIVE_WITH_LIMITATIONS'},
            {'item':'Final immutable dataset/request freeze','status':'NOT_READY'},
            {'item':'Explicit exact-manifest execution authorization','status':'NOT_GRANTED'}],
        'recommendation':'Continue offline construction and independent measurement preparation. Do not request blanket inference authorization for absent or unvalidated manifests.',
        'S_F_H_link':'Original S/F/H remains the programme. P1d E/V varies auxiliary historical source packages with persona style/facts fixed within each case; it neither replaces S/F/H nor estimates S/F/H interactions.'})
    print({'model_matched_cases':48,'budget_diagnostic_requests_proposed':144,'authorized_requests':0,'execution_readiness':'NO_GO'})

if __name__=='__main__':main()
