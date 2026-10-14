"""Prepare a prospective review/freeze candidate from existing evidence; no inference API."""
import argparse
import ast
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import subprocess

import p1c_design as d
import p1c_scientific_review as audit

OUT = Path('docs/validation/p1c/final_review_v1')
LOCAL = Path('results/p1c_final_review/v1')
APPEND = ('docs/research_development_log.md', 'docs/P1c_algorithmic_opportunity_assessment.md')
HUMAN = {'researcher_decision': '', 'researcher_notes': '', 'reviewer_id': '', 'review_timestamp': ''}
SCOPE = 'Specific auxiliary-topic and interval/value package replacement; no isolated temporal, relevance or stale-answer mechanism.'


def check(label, explanation):
    d.require(label in ('PASS', 'FAIL', 'UNCERTAIN'), 'Invalid proposal label')
    return {'label': label, 'explanation': explanation}


def case_proposal(c):
    ref = c['reference']; answer = ' / '.join(ref['components'])
    quotes = '\n'.join(audit.quote(c, f) for f in ref['fact_ids'])
    historical = c['query_mode'] == 'historical'
    route = c['family'] == 'route_integration'
    demand = {'single_retrieval': 'Select one named-person desk within the requested interval.',
              'multiple_components': 'Select the desk and service day within the same requested interval.',
              'route_integration': 'Select the dated route, then join its destination room.'}[c['family']]
    checks = {
        'evidence_sufficiency': check('PASS', f"{c['case_id']}: {quotes} supplies {answer}; no history fact is required."),
        'unique_answer': check('PASS', f"Inclusive interval lookup for {c['speaker_name']} on {c['requested_date']} returns exactly {answer}."),
        'temporal_interpretation': check('PASS', f"Use requested date {c['requested_date']}, not evaluation date {c['evaluation_date']}. " + ('The archive is retrospective, not restricted to information known by the requested date.' if historical else 'The requested date is within the final scheduled interval.')),
        'entity_consistency': check('PASS', f"Question names {c['speaker_name']}; Archive colleague {int(c['persona_id'][-2:])} is a distinct ledger entity; all historical turns keep the target speaker."),
        'question_clarity': check('PASS', f"Exact question: {c['question']} Required delivered components: {answer}."),
        'ground_truth_stability': check('PASS', f"All six prompts retain the same ledger, question, fixed context and reference {ref['fact_ids']}. Removing auxiliary label facts from the solver does not change {answer}."),
        'metric_applicability': check('PASS', f"{c['requested_date']} is essential to selecting the answer interval; all eight declared measurement axes apply. Persona Fidelity has no target and is N/A."),
        'task_demand_description': check('PASS', demand + ' This describes the reference derivation, not measured difficulty.'),
        'absence_of_reasoning_shortcuts': check('UNCERTAIN', f"{answer} follows a small cyclic synthetic assignment scheme. " + ('Multiple destination rooms rule out a unique-terminal shortcut, but a correct room alone cannot prove that the route join was used.' if route else 'Explicit names, dates and literal answer strings make direct retrieval possible; that is a valid baseline, not evidence of deeper reasoning.')),
        'historical_attribution': check('PASS', f"Archive recorded 2042-12-01; {c['speaker_name']} quotes an explicitly bounded auxiliary record. " + ('Recording follows the historical query date; retrospective use must be accepted.' if historical else 'The ledger contains scheduled validity through 2042-12-31.')),
        'isolated_factor_semantics': check('FAIL', 'R replaces parcel-label with music-label content and color; T replaces interval and color. These are bundled interventions, even with identical speaker and token length.'),
        'absence_of_direct_answer_leakage': check('PASS', f"No active history contains the answer components {ref['components']} or references the required source IDs {ref['fact_ids']}; label records already occur in the common ledger."),
        'operational_topical_relevance': check('PASS' if route else 'UNCERTAIN', f"Question: {c['question']} " + ('Parcel collection is explicit; parcel-label content shares that domain but does not supply the room.' if route else 'Collection desk/service day does not explicitly mention parcels; the proposed parcel-topic association is a scenario interpretation requiring confirmation.')),
    }
    risks = ('Color/value coupling; small cyclic templates; family nested within two speakers; auxiliary facts repeated from common ledger; ' +
             ('retrospective archive; ' if historical else '') +
             ('route shortcut cannot be excluded.' if route else 'parcel-domain relevance is assumed, not demonstrated.'))
    return {'case_id': c['case_id'], 'speaker': c['speaker_name'], 'persona_id': c['persona_id'],
        'family': c['family'], 'query_mode': c['query_mode'], 'trusted_evidence': c['trusted_evidence'],
        'current_question': c['question'], 'requested_date': c['requested_date'], 'evaluation_date': c['evaluation_date'],
        'fixed_context': c['fixed_context'], 'expected_answer': answer, 'reference_fact_ids': ref['fact_ids'],
        'reference_derivation': ref['derivation'], 'supporting_source_quotations': quotes,
        'AI_checks': checks, 'AI_case_decision': 'ACCEPT_WITH_RESTRICTED_ESTIMAND',
        'restricted_interpretation': SCOPE, 'known_limitations': risks,
        'required_correction': 'None for the supplied reference answer. Restrict claims and confirm the stated semantic scope; do not edit the stimuli.',
        'unresolved_researcher_question': 'Accept this case for package-level development only, including the stated relevance and temporal interpretation?',
        'source_reference': d.DATA.as_posix() + '#' + c['case_id'], 'provenance': 'AI-assisted scientific proposal; not human approval', **HUMAN}


def text_proposal(c, x, native):
    neutral = x['condition'] == 'N_history'
    answer = ' / '.join(c['reference']['components'])
    route = c['family'] == 'route_integration'
    if neutral:
        source = x['history_text']
        checks = {
            'no_direct_answer_clue': check('PASS', f"The text discusses archiving a question/reply, not {answer}; no required fact ID or answer value appears."),
            'no_additional_personal_fact': check('PASS', f"The turn attributed to {c['speaker_name']} asserts a document procedure, not a new biographical assignment."),
            'information_equivalence': check('FAIL', 'Procedural archive content replaces colored personal-label records; information content and temporal interval detail are different.'),
            'absence_of_topic_or_style_priming': check('FAIL', 'The phrases "this question before its reply" and "rather than separating its two distinct parts" emphasize response organization; they are not an inert placebo.'),
            'role_and_authority_matching': check('PASS', f"Same archive header, Archivist question and {c['speaker_name']} reply; two turns. The authority cue is held, not removed."),
            'chronological_equivalence': check('FAIL', f"Archive date 2042-12-01 remains but no fact-validity interval is stated for query date {c['requested_date']}."),
            'naturalness': check('UNCERTAIN', f"{c['speaker_name']}'s long procedural answer to an archived-entry question is grammatical but possibly overexplicit; its effect on the {c['family']} response is unknown."),
            'reference_answer_stability': check('PASS', f"The common evidence still entails {answer} on {c['requested_date']}; neutral text asserts no conflicting assignment."),
            'full_prompt_matching': check('PASS', f"{x['input_tokens']} tokens; all four active cells equal this count; complete native input IDs previously reverified."),
        }
        overall = 'UNCERTAIN'
        risk = f"{c['case_id']}: procedural/format priming replaces personal dated content. It may influence first-reply structure independently of the requested {answer}. No strict semantic neutrality claim is supportable."
        purpose = 'Length/turn/wrapper-matched procedural-content comparator only; not information-equivalent or behaviorally inert.'
    else:
        f = next(f for f in c['facts'] if f['fact_id'] == x['history_fact_id'])
        source = audit.quote(c, f['fact_id'])
        relevance = 'PASS' if not x['R'] or route else 'UNCERTAIN'
        checks = {
            'historical_truth': check('PASS', source),
            'operational_relevance': check(relevance, f"{f['predicate']} = {f['value']} versus question '{c['question']}'. " + ('Music labeling is outside the collection assignment; same speaker identity alone is not topical relevance.' if not x['R'] else 'Parcel topic is explicit in the question.' if route else 'Parcel association is implicit for a desk/service question; accept only this implemented topical contrast.')),
            'temporal_assignment': check('PASS', f"{f['start']} through {f['end']} is " + ('valid' if x['T'] else 'expired') + f" at {c['requested_date']}. Expired does not mean false in its stated interval."),
            'same_proposition_across_T': check('FAIL', f"Predicate '{f['predicate']}' and entity remain; replacing {f['value']} and its interval changes the proposition. T cannot isolate date cues alone."),
            'speaker_and_format': check('PASS', f"Two turns: Archivist then {c['speaker_name']}; archive header and speaker attribution unchanged across all four cells."),
            'no_direct_answer_support_or_competition': check('PASS', f"Source {f['fact_id']} supplies a {f['predicate']}, not required answer {answer}; it is outside solver source IDs {c['reference']['fact_ids']}. Indirect learned color associations remain possible."),
            'no_new_fact_availability': check('PASS', f"{f['fact_id']} already occurs verbatim in every common trusted ledger. History changes repetition and salience, not the available reference facts."),
            'chronology': check('PASS', f"Recorded 2042-12-01 for interval {f['start']}..{f['end']}; query is {c['requested_date']}. Retrospective/scheduled records, not a simulation of knowledge available at query time."),
            'reference_answer_stability': check('PASS', f"The same reference {answer} follows from {c['reference']['fact_ids']} in every cell."),
            'full_prompt_matching': check('PASS', f"{x['input_tokens']} complete-prompt tokens and unchanged evidence prefix; IDs match saved native evidence for {c['case_id']}/{x['condition']}."),
        }
        overall = relevance
        risk = f"{c['case_id']}/{x['condition']}: {f['predicate']}={f['value']} at {f['start']}..{f['end']}; color changes with T, attribute/color with R. " + ('Requested historical date precedes archive recording. ' if c['query_mode']=='historical' else '') + ('Parcel relevance is implicit. ' if x['R'] and not route else '') + 'No isolated mechanism or answer-competition claim.'
        purpose = f"Operational R={x['R']}, T={x['T']} auxiliary-record package; answer remains {answer}."
    return {'item_id': c['case_id'] + '/' + x['condition'], 'case_id': c['case_id'],
        'condition': x['condition'], 'R': x['R'], 'T': x['T'], 'full_text': x['history_text'],
        'source_quote': source, 'current_question': c['question'], 'expected_answer': answer,
        'requested_date': c['requested_date'], 'case_evidence_reference': 'final_case_review_proposed_v1.csv#'+c['case_id'],
        'scientific_purpose': purpose, 'AI_checks': checks, 'AI_overall_judgment': overall,
        'AI_disposition': 'ACCEPT_WITH_LIMITATIONS', 'known_limitations': risk,
        'input_tokens': x['input_tokens'], 'token_difference_from_active': 0,
        'prompt_sha256': x['prompt_sha256'], 'native_evidence_reference': native,
        'unresolved_researcher_question': ('Accept only as a procedural-content comparator, despite failed strict-neutrality criteria?' if neutral else 'Accept this source association and operational factor assignment with the stated restrictions?'),
        'provenance': 'AI-assisted scientific proposal; not human approval', **HUMAN}


def estimands(case_ids):
    spec = audit.contrast_spec()
    entries = []
    for name, weights in spec['weights'].items():
        if name == 'R': definition = 'Mean parcel-minus-music auxiliary record replacement, averaged equally over T.'
        elif name == 'T': definition = 'Mean query-valid-minus-expired interval/value replacement, averaged equally over R.'
        elif name == 'RxT': definition = 'Difference of parcel-minus-music differences across interval/value settings; unscaled difference in differences.'
        elif 'H_none' in name: definition = 'Total added historical/procedural content package versus no history, including added length and wrapper.'
        elif 'N_history' in name: definition = 'Active auxiliary historical content versus procedural archive content with equal length, turns and wrapper.'
        else: definition = 'Replacement of one implemented factor package at the fixed level of the other factor.'
        entries.append({'contrast_id': name, 'weights': weights, 'comparison_cells': [k for k,v in weights.items() if v],
            'target_estimand': definition, 'eligible_case_ids': case_ids, 'eligible_cases': 12,
            'unit': 'Paired case contrast, then equal speaker means of two cases; six clusters.',
            'known_confounders': 'Attribute/color lexical cues; date/value coupling; repeated evidence salience; family/speaker nesting.' + (' Added length and archive formatting.' if 'H_none' in name else '') + (' Procedural and style priming; temporal content differs.' if 'N_history' in name else ''),
            'required_assumptions': 'Approved operational meanings, common answer/evidence, stateless requests, valid first-reply judgments. No silent complete-case reweighting.',
            'supported_interpretation': definition + ' In these reviewed synthetic development cases only.',
            'unsupported_interpretation': 'Pure relevance, pure temporal mechanism, established stale-answer competition, or population causal law.',
            'approval_status': 'PENDING'})
    return {**spec, 'version': 'p1c_final_estimand_registry_proposed_v1', 'registry': entries}


def evaluation_policy():
    return {'version': 'p1c_evaluation_freeze_proposed_v1', 'status': 'PENDING_RESEARCHER',
        'historical_policies_unchanged': ['response_status_v1', 'separate_axes_policy_v1'],
        'primary_descriptive_endpoints': ['response_relevance','factual_consistency','temporal_consistency','conversational_coherence'],
        'separate_diagnostics': ['task_success','component_coverage','semantic_completeness','structural_status'],
        'persona_fidelity': 'Not Applicable; no fidelity reference exists.',
        'denominators': {'cases':12,'speakers':6,'per_condition':12,'per_applicable_axis':72},
        'categories': ['Correct','Incorrect','Unverifiable','Not Applicable'], 'administrative_missing': 'Missing',
        'factual': 'Judge supported factual claims in an identifiable first reply against the common ledger and requested time. A demonstrably false assertion is Incorrect; absent, unsupported or unassessable answers are Unverifiable, not automatically false.',
        'temporal': 'Judge date/interval use against requested_date, not automatically evaluation_date or newest record. All 72 are eligible; missing final answer without assessable temporal claim is Unverifiable.',
        'task_success': 'Exploratory binary delivery diagnostic: 1 only when every required component is delivered, evidence-supported and no incompatible answer is asserted. Known partial/wrong/no-final delivery is 0 task success, not automatically factual Incorrect. Unknown response unit or missing review stays unknown.',
        'component_coverage': 'Count supported requested components / fixed reference-component count; intermediate route is not requested room success. Preserve unsupported, missing and contradictory components separately.',
        'semantic_completeness': 'YES / PARTIAL / NO / UNCERTAIN, independent of truth and backend stopping. A complete wrong answer may be YES.',
        'ordinal': 'Existing 1-5 relevance/coherence rubrics; full categories and paired higher/equal/lower. Means descriptive; threshold/rank sensitivity without interval-scale claims.',
        'unit': 'Frozen first-reply extraction; never select a later correct turn. Stage A cannot see treatment, structural labels, automated predictions or full continuation. Stage B may audit extraction separately, preserving original span and status.',
        'unknowns': 'Report eligible, evaluated, Missing, Unverifiable, structural-unscorable and incomplete counts separately. Categorical incidences retain all eligible records; do not identify non-Correct with Incorrect. Assessed-only sensitivity uses all required assessable cells and discloses selection; signed unknown bounds retain original weights.',
        'statistics': {'bootstrap_unit':'whole speaker','seed':715004,'replicates':10000,'leave_one_speaker_out':True,'population_significance_claims':False},
        'multiplicity': 'Development: report all planned contrasts without significance selection. Independent confirmatory primary family, useful precision margin and adjustment require a later prospective freeze.',
        'annotation_provenance': 'Human fields blank. AI assistance, if used later, must remain separately disclosed. No fictitious second reviewer or agreement.',
        'rule_scope': 'Proposed P1c-specific task application of historical policies, not retroactive rescoring.'}


def build():
    data=d.read(d.DATA); cfg=d.read(audit.V2/'configuration_proposal_v2.json'); a=audit.build_audit()
    selected=d.read(audit.V2/'selected_prompts_v2.json')['records']; cases={c['case_id']:c for c in data['cases']}
    native_path=audit.OUT/'native_reverification_v1.json'; native=d.read(native_path)
    forms=[case_proposal(c) for c in data['cases']]
    texts=[text_proposal(cases[x['case_id']],x,native_path.as_posix()) for x in a['cell_audit'] if x['condition']!='H_none']
    neutral=[r for r in texts if r['condition']=='N_history']
    for name, rows in [('final_case_review_proposed_v1',forms),('final_history_review_proposed_v1',texts),('final_neutral_review_proposed_v1',neutral)]:
        d.write_csv(OUT/(name+'.csv'), rows)
        d.write_json(OUT/(name+'.json'), rows)
    confirmation=[{'item_type': 'case' if 'AI_case_decision' in r else 'history_text',
        'item_id':r.get('item_id',r['case_id']), 'AI_recommendation':r.get('AI_case_decision',r.get('AI_disposition')),
        'question':r['unresolved_researcher_question'],**HUMAN} for r in forms+texts]
    for key, question in [
        ('operational_scope','Approve package-level R/T interpretations, implicit parcel relevance for desk/day cases, and retrospective ledger semantics?'),
        ('neutral_scope','Approve all 12 texts only as matched procedural comparators, not inert or information-equivalent controls?'),
        ('evaluation_and_statistics','Approve the proposed P1c task rubric, fixed applicability, all 16 contrasts and descriptive clustered analysis?'),
        ('protocol_addendum','Approve the P1c addendum without modifying historical v1.1 or adopting v1.2?'),
        ('execution_authorization','Separately authorize exactly the 72 frozen requests at 96 tokens only after item decisions and technical preflight pass?')]:
        confirmation.append({'item_type':'global','item_id':key,'AI_recommendation':'RESEARCHER_DECISION_REQUIRED','question':question,**HUMAN})
    d.write_csv(OUT/'researcher_confirmation_form_v1.csv',confirmation)
    registry=estimands(list(cases)); d.write_json(OUT/'estimand_registry_proposed_v1.json',registry)
    d.write_csv(OUT/'estimand_registry_proposed_v1.csv',registry['registry'])
    d.write_json(OUT/'evaluation_policy_proposed_v1.json',evaluation_policy())
    d.write_json(OUT/'intervention_confound_inventory_v1.json',{'version':'p1c_final_confounds_v1',
        'exhaustive_original_field_inventory':a['intervention_difference_inventory'],
        'case_decisions':[{k:r[k] for k in ('case_id','AI_case_decision','known_limitations','restricted_interpretation','required_correction')} for r in forms],
        'counterfactual_pairs':a['counterfactual_pairs']})
    lookup={(r['case_id'],r['condition']):r for r in selected}; requests=[]
    for i, key in enumerate(cfg['proposed_order']):
        r=lookup[tuple(key)];c=cases[key[0]]
        requests.append({'sequence_index':i, 'request_identity':key, **r,
            'factor_assignment':d.CONDITIONS[key[1]],'evaluation_date':c['evaluation_date'],
            'requested_date':c['requested_date'],'reference':c['reference'],'applicability':c['applicability']})
    prior=d.read(Path('docs/validation/p1b/final_review_v1/calibration_manifest_v2.json'))
    manifest={'version':'p1c_calibration_manifest_candidate_v1','status':'FROZEN_CANDIDATE_PENDING_RESEARCHER_APPROVAL',
        'execution_authorized':False,'generations_executed':0,'researcher_approval': '',
        'historical_protocol':'v1.1','prospective_addendum':'p1c_addendum_proposed_v2',
        'dataset':cfg['dataset'],'dataset_sha256':cfg['dataset_sha256'],
        'selected_prompts_sha256':cfg['selected_prompt_sha256'],'source_configuration':str(audit.V2/'configuration_proposal_v2.json'),
        'source_configuration_sha256':d.sha(audit.V2/'configuration_proposal_v2.json'),
        'prompt_template':data['cases'][0]['prompt_template_version'],
        'model_file':'models/gguf/Qwen3.5-2B-Base.Q4_K_M.gguf','backend_file':'bin/llama.cpp/llama-b11573-bin-win-cpu-x64/llama-server.exe',
        'configuration':{k:cfg[k] for k in ('primary_arm','backend','model_sha256','backend_sha256','threads','threads_batch','n_gpu_layers','n_ctx','n_predict','temperature','seed','order_seed')},
        'generation_parameters':prior['generation_parameters'],'state_policy':prior['state_policy'],'resume_policy':prior['resume_policy'],
        'runtime_policy_source':'docs/validation/p1b/final_review_v1/calibration_manifest_v2.json',
        'runtime_policy_source_sha256':d.sha(Path('docs/validation/p1b/final_review_v1/calibration_manifest_v2.json')),
        'tokenizer_identity':native['identity'],'tokenizer_evidence':native_path.as_posix(),'tokenizer_evidence_sha256':d.sha(native_path),
        'evaluation_policy_sha256':d.sha(OUT/'evaluation_policy_proposed_v1.json'),
        'estimand_registry_sha256':d.sha(OUT/'estimand_registry_proposed_v1.json'),
        'response_policy':'response_status_v1','evaluation_policy':'separate_axes_policy_v1',
        'requests':requests,'planned_order_sha256':d.canonical(cfg['proposed_order']),
        'request_identity_definition':'Original (case_id, condition) tuple plus original order index; no re-randomization or invented prior request IDs.',
        'raw_logging_requirements':['append-only new P1c run directory','prompt bytes and hashes','input token IDs','native response JSON and raw output bytes','output IDs where available','native stop and budget flags','first reply and excluded continuation','parser operations','latency and errors','model/backend/source hashes','actual run Git state'],
        'execution_gate':'This file cannot authorize execution. Register exact reviewed item decisions and explicit 72-request authorization; recheck hashes, runtime token IDs, context/disk/logging and resume before running.',
        'immutability':'Exclusive creation; external SHA-256 receipt. Any substantive input change requires a new version and renewed approval.',
        'entry_git_sha':d.read(LOCAL/'baseline.json')['git_sha'],'entry_git_dirty':bool(d.read(LOCAL/'baseline.json')['git_status'])}
    d.write_json(OUT/'calibration_manifest_candidate_v1.json',manifest)
    d.write_json(OUT/'calibration_manifest_sha256_v1.json',{'path':(OUT/'calibration_manifest_candidate_v1.json').as_posix(),'sha256':d.sha(OUT/'calibration_manifest_candidate_v1.json')})
    # Empty future outcome forms, distinct from stimulus review. No outputs or ratings exist.
    order=list(requests);random.Random(715005).shuffle(order); stage_a=[];stage_b=[]; mapping=[]
    for n,r in enumerate(order,1):
        c=cases[r['case_id']]; anonymous=f'PC{n:03d}'
        stage_a.append({'anonymous_response_id':anonymous,'question':c['question'],'trusted_evidence':c['trusted_evidence'],
            'requested_date':c['requested_date'],'evaluation_date':c['evaluation_date'],'fixed_context':c['fixed_context'],
            'required_answer_components':c['reference']['components'],'reference_source_quotes':'\n'.join(audit.quote(c,f) for f in c['reference']['fact_ids']),
            'metric_applicability':c['applicability'],'first_reply':'',
            'human_relevance':'','human_factual':'','human_temporal':'','human_coherence':'','human_task_success':'',
            'human_component_coverage':'','human_semantic_completeness':'','human_evidence_and_notes':'','reviewer_id':''})
        stage_b.append({'anonymous_response_id':anonymous,'raw_full_continuation':'','original_extracted_reply':'','original_structural_status':'',
            'native_stop_reason':'','budget_termination':'','parser_operations':'','human_boundary_disposition':'','human_notes':'','reviewer_id':''})
        mapping.append({'anonymous_response_id':anonymous,'request_identity':r['request_identity'],'sequence_index':r['sequence_index'],
            'persona_id':r['persona_id'],'condition':r['condition'],'R':r['factor_assignment']['R'],'T':r['factor_assignment']['T']})
    d.write_csv(OUT/'stage_a_semantic_template_v1.csv',stage_a);d.write_csv(OUT/'stage_b_structure_template_v1.csv',stage_b)
    d.write_json(OUT/'protected_treatment_mapping_proposed_v1.json',{'seed':715005,'purpose':'Analyst-only separation, not filesystem encryption. Empty future forms, not completed annotations.','records':mapping})
    d.write_json(OUT/'applicability_matrix_v1.json',[{'case_id':c['case_id'],'condition':cond,**c['applicability'],'persona_fidelity':False} for c in cases.values() for cond in audit.CELLS])
    d.write_json(OUT/'protocol_addendum_proposed_v2.json',{'version':'p1c_addendum_proposed_v2','status':'PENDING_RESEARCHER',
        'base_protocol_unchanged':'v1.1','v1_2_adopted':False,'new_hypotheses':['Operational topical package effect','Operational valid/expired package effect','Operational R by T difference in differences'],
        'interventions':d.CONDITIONS,'conditions_unchanged':True,'estimands':str(OUT/'estimand_registry_proposed_v1.json'),
        'evaluation':str(OUT/'evaluation_policy_proposed_v1.json'),'budget':96,'design_size':{'speakers':6,'cases':12,'requests':72},
        'limitations':[r['known_limitations'] for r in forms],
        'independent_validation':'New speakers/templates and counterbalanced attribute values; review and precision/family approval before any confirmatory freeze. Current materials remain development.',
        'answer_competition_note':'Separate future experiment would repeat actual answer-bearing facts with query-valid versus expired intervals, plus auxiliary-topic controls; identical sufficient ledger and historical/current questions. Not a new P1c cell or authorized implementation.',
        'required_decisions':confirmation[-5:], 'reviewer_id':'','approval':''})
    d.write_json(OUT/'proposal_summary_v1.json',{'case_decisions':dict(Counter(r['AI_case_decision'] for r in forms)),
        'history_AI_labels':dict(Counter(r['AI_overall_judgment'] for r in texts)),
        'neutral_AI_labels':dict(Counter(r['AI_overall_judgment'] for r in neutral)),
        'human_approved_items':0,'unique_review_items':72,'neutral_subset_not_extra_items':12,
        'global_decisions':5,'planned_requests':72,'stimulus_changes':0,'new_generations':0,
        'source_audit':a['summary'],'manifest_sha256':d.sha(OUT/'calibration_manifest_candidate_v1.json')})
    print(json.dumps(d.read(OUT/'proposal_summary_v1.json'),indent=2))


def verify():
    baseline=d.read(LOCAL/'baseline.json')
    for path, sha in baseline['files'].items():
        if path in APPEND:
            before=LOCAL/(Path(path).name+'.before')
            d.require(d.sha(before)==sha and Path(path).read_bytes().startswith(before.read_bytes()),'Historical text prefix changed: '+path)
        else: d.require(d.sha(Path(path))==sha,'Entry file changed: '+path)
    for path,sha in baseline['historical_artifacts'].items():
        d.require(d.sha(Path(path))==sha,'Historical artifact changed: '+path)
    old=d.read(audit.OUT/'reproducibility_manifest_v1.json')
    for path,sha in old['native_recheck_logs'].items():
        d.require(d.sha(Path(path))==sha,'Native evidence log changed: '+path)
    saved_by_hash={r['prompt_sha256']:r for r in d.read(audit.V2/'selected_prompts_v2.json')['records']}
    for path in old['native_recheck_logs']:
        log=d.read(path);r=saved_by_hash[log['prompt_sha256']]
        d.require(log['exit_code']==0 and log['prompt']==r['prompt'],'Native prompt mismatch')
        d.require(ast.literal_eval(log['stdout'].strip())==r['input_token_ids'],'Native token IDs differ')
    native=d.read(audit.OUT/'native_reverification_v1.json');cfg=d.read(audit.V2/'configuration_proposal_v2.json')
    root=Path('bin/llama.cpp/llama-b11573-bin-win-cpu-x64')
    for path,sha in [(Path('models/gguf/Qwen3.5-2B-Base.Q4_K_M.gguf'),native['identity']['model_sha256']),
                     (root/'llama-server.exe',native['identity']['backend_sha256']), (root/'llama-tokenize.exe',native['identity']['tokenizer_sha256'])]+[(root/k,v) for k,v in native['identity']['dll_hashes'].items()]:
        d.require(d.sha(path)==sha,'Pinned identity differs: '+str(path))
    a=audit.build_audit();m=d.read(OUT/'calibration_manifest_candidate_v1.json');receipt=d.read(OUT/'calibration_manifest_sha256_v1.json')
    d.require(d.sha(Path(receipt['path']))==receipt['sha256'],'Manifest receipt mismatch')
    d.require([r['request_identity'] for r in m['requests']]==cfg['proposed_order'],'Order changed')
    d.require(not m['execution_authorized'] and m['generations_executed']==0,'Unauthorized status')
    selected={(r['case_id'],r['condition']):r for r in d.read(audit.V2/'selected_prompts_v2.json')['records']}
    for r in m['requests']:
        for k,v in selected[tuple(r['request_identity'])].items():d.require(r[k]==v,'Manifest selected field mismatch: '+k)
    blank=0
    for name,n in [('final_case_review_proposed_v1',12),('final_history_review_proposed_v1',60),('final_neutral_review_proposed_v1',12)]:
        rows=d.read(OUT/(name+'.json'));d.require(len(rows)==n,'Review count')
        for r in rows:
            for h in HUMAN:d.require(r[h]=='','Invented human field');blank+=1
        with (OUT/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:
            csv_rows=list(csv.DictReader(f))
        d.require(len(csv_rows)==n,'CSV count')
        for r,s in zip(rows,csv_rows):
            for k,v in r.items():
                expected=json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else '' if v is None else str(v)
                d.require(s[k]==expected,'CSV/JSON disagreement: '+k)
    for path in OUT.glob('*.json'):d.read(path)
    for path in OUT.glob('*.csv'):
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            for row in reader:d.require(None not in row and all(v is not None for v in row.values()),'Malformed CSV: '+str(path))
    result={'status':'PASS','entry_files_preserved':len(baseline['files']),
        'historical_artifacts_preserved':len(baseline['historical_artifacts']),
        'native_evidence_logs_preserved':len(old['native_recheck_logs']),
        'pinned_model_backend_tokenizer_and_dll_hashes':'PASS','native_tokenizer_evidence_scope':'Reused all 72 previous actual native calls; exact inputs, IDs, logs and binaries revalidated. No new tokenization or inference was needed.',
        'prompts':len(m['requests']),'original_order_preserved':True,'matched_sets':a['summary']['matched_sets'],
        'blank_human_fields_in_primary_and_subset_json':blank,'new_generations':0,
        'case_review_status':'PENDING','neutral_review_status':'OPEN','execution':'NO_GO_PENDING_RESEARCHER',
        'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_status':subprocess.check_output(['git','status','--short','--untracked-files=all'],text=True),
        'verified_utc':datetime.now(timezone.utc).isoformat()}
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','verify']);args=parser.parse_args()
    build() if args.action=='build' else verify()
