"""Prospective review risks and freeze inventory; no runtime execution plan adoption."""
from pathlib import Path
import ast
import json
import math
import p1c_design as d
import p1c_scientific_review as r


def build():
    audit=r.build_audit();cfg=d.read(r.V2/'configuration_proposal_v2.json')
    risks=[
        ('R_SCOPE','All 12','R changes parcel/music predicate and value; neither is the answer property. Eight questions do not explicitly say parcel.',
         'Accept auxiliary-topic replacement only; confirm intended topic relation case by case.','RESEARCHER_SCOPE_APPROVAL'),
        ('T_BUNDLE','All 12','Every T contrast changes value and validity dates, repeating a different existing ledger fact.',
         'Interpret interval/value selection package, not an isolated temporal tag.','RESEARCHER_SCOPE_APPROVAL'),
        ('CYCLIC_CUE','All 12','Colors follow a deterministic cyclic assignment. Historical R1T1 equals R0T0 color; current R0T1 equals R1T0 color.',
         'Retain as documented calibration limitation; future independent validation needs separately generated and counterbalanced values.','LIMITATION'),
        ('DATE_OVERLAP','All 12','T1 repeats the requested month in interval start; T0 does not. Date-token similarity changes with validity.',
         'No pure recency/attention/temporal mechanism claim.','LIMITATION'),
        ('ARCHIVE_TIME','Six historical cases','Archive recording date is later than the question date; facts are retrospectively available in identical trusted schedules.',
         'Approve historical-state question interpretation, not knowledge-available-as-of-date evaluation.','RESEARCHER_TIME_APPROVAL'),
        ('R0_PERSONAL','All 12','Music is answer-unrelated but concerns the same named person; personal/entity relevance remains.',
         'Use task-topic unrelated, not globally irrelevant.','LIMITATION'),
        ('NEUTRAL_PRAGMATICS','All 12 neutral texts','Self-referential procedural reply, formal archive vocabulary, contrastive phrase and archive date can prime record reading.',
         'Review naturalness and limited comparison suitability; token match is not approval.','MANDATORY_SEMANTIC_REVIEW'),
        ('CONTROL_CONTENT','All active-neutral contrasts','Active personal assertion and embedded interval are replaced by procedural text lacking those fields.',
         'No claim that neutral contrast isolates topicality, temporal status or length alone.','LIMITATION'),
        ('NO_HISTORY','All 12','H_none is 65 tokens shorter in ten cases and 66 in two; no two-turn dialogue.',
         'Total addition contrast only.','LIMITATION'),
        ('BANK_STRUCTURE','All 12','Two cases share each speaker/ledger; task family is nested within two speakers. Lexical realizations are limited.',
         'Six clusters; do not count 12 independent speakers or 72 independent observations.','LIMITATION'),
        ('BOUNDARY_BUDGET','All planned outputs','Base continuation and 96-token censoring are plausible; P1c outcomes do not exist.',
         'Retain frozen structural policy and unknown units. Optional separate budget diagnostic, never effect-sign tuning.','LIMITATION'),
        ('HUMAN_REVIEW','12 cases and 60 texts','No new human decisions or reliability estimates supplied.',
         'Complete scientific review and approve prospective scoring plan before authorization.','MANDATORY_REVIEW'),
        ('EXECUTION','72 proposed identities','Configuration proposal is not an authorized run manifest; no separate original request_id exists.',
         'Pin ordered case-condition identities and source hashes; create execution manifest only after explicit approval.','MANDATORY_AUTHORIZATION')]
    d.write_json(r.OUT/'experimental_risk_inventory_v1.json',{'version':'p1c_risk_v1','records':[
        dict(zip(('risk_id','scope','observation','resolution','disposition'),x)) for x in risks]})
    changes=[
        'Add a prospective P1 Track A auxiliary-history diagnostic, separate from unchanged S/F/H C0-C7 and from Track B.',
        'Define R as parcel-versus-music auxiliary topic replacement and T as selection of historically true valid-versus-expired interval/value records at the explicitly requested date.',
        'Permit only operational package interpretation of R/T/RxT; do not claim stale-answer competition or independent semantic mechanisms.',
        'Score historical questions at their requested fact-validity date; evaluation and archive recording dates do not force the newest answer. No past scores change.',
        'Retain six original condition IDs, 12 cases/six speakers, 72 explicit ordered identities, exact active/neutral final-token matching; shorter H_none is a total-addition baseline.',
        'Require explicit case and text reviews, including narrow neutral comparison approval. AI-assisted recommendations are not human decisions.',
        'Preserve response_status_v1, separate_axes_policy_v1 and all distinct outcomes/unknown states. Approve endpoint hierarchy and annotation plan prospectively.',
        'Report fixed-factor simple contrasts alongside average R/T and secondary operational RxT. Keep original unapproved six-test future hierarchy visible; decide it before independent confirmation.',
        'Retain 96-token Base configuration and original order. Budget, presentation, answer competition and Instruct arms require separate proposals and authorization.',
        'Development material is never the independent confirmatory set. New speakers/templates and useful precision goals need a separate confirmatory freeze.'
    ]
    d.write_json(r.OUT/'prospective_protocol_addendum_proposal_v1.json',{
        'version':'p1c_identification_addendum_proposed_v1','status':'PROPOSED_NOT_ADOPTED',
        'recommended_document_type':'Prospective addendum plus standalone operational plan; no edit/adoption of either protocol.',
        'historical_protocol_sha256':d.sha('docs/research_protocol_v1.1.md'),
        'prospective_reference_sha256':d.sha('docs/PersonaSLM_Research_Protocol_v1.2_Revised_Proposed_r1.md'),
        'justification':'Additional operational R/T estimands, requested-date scoring and review/freeze governance need explicit prospective authority.',
        'changes':changes,'researcher_decision':'','reviewer_id':'','approval_time':None,
        'execution_authorized':False,'historical_decisions_changed':False})
    d.write_json(r.OUT/'calibration_freeze_candidate_v1.json',{
        'version':'p1c_calibration_input_review_snapshot_v1','status':'INPUT_SNAPSHOT_ONLY_NOT_EXECUTION_FREEZE',
        'dataset_sha256':d.sha(d.DATA),'selected_prompts_sha256':d.sha(r.V2/'selected_prompts_v2.json'),
        'original_configuration_sha256':d.sha(r.V2/'configuration_proposal_v2.json'),
        'condition_definitions_sha256':d.sha(d.PUBLIC/'condition_definitions_v1.json'),
        'planned_order':cfg['proposed_order'],'planned_order_sha256':d.canonical(cfg['proposed_order']),
        'planned_identity_policy':'Ordered original case_id/condition pairs, not invented historical request IDs.',
        'request_count':72,'new_generation_count':0,'generation_authorized':False,
        'runtime':{k:cfg[k] for k in ('model_sha256','backend_sha256','primary_arm','backend','threads','threads_batch','n_gpu_layers','n_ctx','n_predict','temperature','seed','order_seed','response_policy','evaluation_policy')},
        'required_gates':['case_review','history_and_neutral_review','narrow_estimand_and_date_scope','prospective_addendum','measurement_and_resume_plan','explicit_execution_authorization'],
        'researcher_decision':'','reviewer_id':''})
    mean=d.read(r.OUT/'p1b_evidence_recheck_v2.json')['runtime']['mean_response_seconds']
    d.write_json(r.OUT/'output_budget_sensitivity_proposal_v1.json',{
        'status':'OPTIONAL_NOT_AUTHORIZED_NOT_A_NEW_MANDATORY_GATE','version':'p1c_budget_proposal_v1',
        'case_ids':['p1c_01_historical','p1c_03_current','p1c_05_historical'],'selection_rule':'First speaker in each existing task family; historical/current/historical alternation; no output observed.',
        'conditions':r.CELLS,'budgets':[96,192,256],'candidate_requests':54,'actual_requests':0,
        'all_other_configuration':'Same original prompts/IDs, temperature, seeds, policies; randomize future arm order under separately frozen seed 715006.',
        'compare':['first_reply_delivery','component_coverage','native_termination','structural_status','extraction_validity','latency'],
        'no_selection_by':['factual_effect_sign','R_effect_sign','T_effect_sign','interaction_sign'],
        'response_minutes_proxy':18*mean*(1+2+256/96)/60,
        'cost_limits':'Linear output-budget scaling of old total latency is an illustration, not a measured token-speed or upper bound; prefill and early stopping differ.',
        'scope':'Three cases cannot select a universally adequate budget. All conditions compared at each cap; any later adoption applies to a new entire arm.',
        'original_96_token_configuration_unchanged':True})
    # Preserve precise links to both old and repaired native IDs, rather than retokenizing failed candidates.
    native_index={}
    for p in (d.LOCAL/'native_calls').glob('*.json'):
        log=d.read(p);native_index[log['prompt_sha256']]=(p,log)
    links=[]
    for row in audit['neutral_repair_inventory']:
        p,log=native_index[row['old_prompt_sha256']];ids=ast.literal_eval(log['stdout'].strip())
        d.require(len(ids)==row['original_tokens'],'Old token count mismatch')
        links.append({'case_id':row['case_id'],'original_native_log':p.as_posix(),'original_log_sha256':d.sha(p),
            'original_prompt_sha256':row['old_prompt_sha256'],'original_input_token_ids':ids,
            'repaired_prompt_sha256':row['new_prompt_sha256'],'repaired_input_token_ids':row['new_token_ids'],
            'original_difference':row['original_difference'],'repaired_difference':row['repaired_difference']})
    d.write_json(r.OUT/'neutral_native_evidence_links_v1.json',{'records':links})
    return {'risk_records':len(risks),'addendum_changes':len(changes),'old_native_links':len(links),'new_generations':0}


if __name__=='__main__':print(json.dumps(build()))
