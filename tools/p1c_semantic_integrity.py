"""Additive audit of AI proposals; no model calls, human approvals or treatment effects."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import copy
import json

import p1c_semantic_review as a
import p1c_semantic_analysis as analysis

OUT = a.ROOT / 'semantic_integrity_v1'
OLD = a.OUT
PRIMARY = OUT / 'reviewed_primary_proposals_UNCONFIRMED_v1.json'
SECONDARY = OUT / 'reviewed_boundary_sensitivity_UNCONFIRMED_v2.json'
BOUNDARY = {'PC010','PC023','PC033','PC039','PC042','PC044','PC054','PC063'}
ATTRIBUTE = {'PC004','PC011','PC027','PC030'}
ENTITY = {'PC011','PC027','PC030','PC035','PC040'}
WRONG = {
    **{f'PC{i:03}':['Laurel'] for i in (9,11,27,30,31,35,40,67)},
    'PC012':['Silver'],
    **{f'PC{i:03}':['Orchid','Thursday'] for i in (16,37,49,53,70)},
    **{f'PC{i:03}':['Maple'] for i in (19,48,65)},
    **{f'PC{i:03}':['Laurel'] for i in (29,58,71)}}


def ratings(row):
    return {k: row['AI_' + k] for k in a.FIELDS}


def states(row, secondary=False):
    rid=row['anonymous_response_id']; unresolved=rid in BOUNDARY and not secondary
    per_metric={k:[] for k in a.FIELDS}
    if unresolved:
        for k in per_metric:per_metric[k]=['BOUNDARY_UNRESOLVED','STRUCTURALLY_UNSCORABLE']
    else:
        if rid in ('PC004','PC006'):
            for k in ('factual_consistency','temporal_consistency','task_success'):
                per_metric[k].append('ANNOTATION_UNCERTAIN')
        if rid in ENTITY or secondary and rid in ('PC033','PC039','PC042'):
            per_metric['temporal_consistency'].append('ANNOTATION_UNCERTAIN')
        if secondary and rid in ('PC039','PC042'):
            per_metric['factual_consistency'].append('EVIDENCE_UNVERIFIABLE')
    return {'version':'p1c_measurement_state_v1','boundary_state':'BOUNDARY_UNRESOLVED' if unresolved else 'ALTERNATIVE_SPAN_PROPOSED' if rid in BOUNDARY else 'IDENTIFIABLE',
        'scoreability':'STRUCTURALLY_UNSCORABLE' if unresolved else 'SCORABLE',
        'metric_uncertainty_flags':per_metric,
        'evidence_gap_detail':('Friday is absent from the ledger; a separate contradicted desk claim still makes overall factual Incorrect.' if secondary and rid in ('PC039','PC042') else
            'Conditional only: calendar-date weekday or desk-as-room reading requires adjudication, not a proven absence of the requested reference.' if rid in ('PC004','PC006') else ''),
        'AI_review_missing':False,'official_human_annotation_state':'MISSING',
        'persona_fidelity_state':'NOT_APPLICABLE',
        'note':'Flags describe different levels and may overlap; they do not replace original categorical labels or change denominators.'}


def primary_record(row):
    r=copy.deepcopy(row);rid=r['anonymous_response_id']; required=json.loads(r['required_answer_components'])
    unknown=rid in BOUNDARY
    claims=[] if unknown else WRONG.get(rid,required)
    supported=[x for x,y in zip(claims,required) if x==y]
    # A transcription of independently checked delivery/components, not a copy of factual labels.
    task=None if unknown or rid=='PC006' else int(claims==required)
    coherence=None if unknown else 5
    relevance=None if unknown else 4 if rid in ATTRIBUTE else 5
    reviewed=ratings(r)
    reviewed.update(task_success=task,response_relevance=relevance,conversational_coherence=coherence)
    a.require(task==r['AI_task_success'],'Task reinspection differs; explicit new adjudication required')
    changes=[{'metric':k,'original':r['AI_'+k],'recommended':v,
        'reason':'Use question alignment for relevance and fixed-context integration for coherence; attribute/calendar factual ambiguity does not itself establish discourse incoherence.'}
        for k,v in reviewed.items() if v!=r['AI_'+k]]
    model=r['raw_first_reply'];context=r['fixed_preceding_context'];question=r['current_question']
    audit={
        'factual':{'claim_quotation':model,'reference_quotations':a.supporting_quotes(r),
            'material_asserted_values':claims,'required_values':required,'supported_requested_values':supported,
            'claim_evaluation':r['AI_endpoint_explanations']['factual_consistency'],
            'alternative':r['AI_alternative_interpretation']},
        'task':{'question_quotation':question,'delivered_values':claims,'required_values':required,
            'answer_delivered':'UNRESOLVED' if unknown else 'YES',
            'intermediate_only':False if not unknown else None,
            'complete_requested_field_attempt':not unknown,
            'supported_component_fraction':None if unknown else len(supported)/len(required),
            'independently_checked_success':task,
            'reason':f'{rid}: '+('Unknown primary reply unit.' if unknown else 'All fields are explicitly attempted in a finished answer; delivery alone is not success. Compare the named target values and requested date, and retain the calendar ambiguity separately.'),
            'not_derived_from_factual_label':True},
        'relevance':{'question_quotation':question,'reply_quotation':model,'recommended_score':relevance,
            'reason':f'{rid}: '+('No identifiable primary unit to rate.' if unknown else
                'The question asks for a destination room, but the reply explicitly names a collection desk; the assignment topic is addressed with an attribute mismatch.' if rid in ATTRIBUTE else
                f'The reply directly attempts the requested assignment fields {required}; correctness is evaluated on another axis.'),
            'alternative_score':None if unknown else 5 if rid in ATTRIBUTE else 4,
            'alternative_basis':'A stricter alignment reading could lower a score, or accept desk as destination paraphrase; no change merely to add variation.',
            'confidence':'LOW' if unknown else 'MODERATE' if rid in ATTRIBUTE or rid=='PC006' else 'HIGH'},
        'coherence':{'context_quotation':context,'question_quotation':question,'reply_quotation':model,'recommended_score':coherence,
            'reason':f'{rid}: '+('Unknown primary boundary prevents attributing one coherent reply.' if unknown else
                'The context establishes a dated schedule and requests an assignment to check. This named-target declarative assignment continues that topic; no dangling reference or discourse transition failure is evident. A false assignment remains a factual failure.'),
            'alternative_score':None if unknown else 4,
            'alternative_basis':'A stricter context-integration reading could penalize attribute/calendar wording. The frozen context itself is generic and supplies no conflicting assignment.',
            'confidence':'LOW' if unknown else 'MODERATE' if rid in ATTRIBUTE or rid=='PC006' else 'HIGH'}}
    r.update(audit_version='p1c_semantic_integrity_review_v1',reviewed_AI_ratings=reviewed,
        original_AI_ratings=ratings(row),reviewed_AI_changes=changes,metric_evidence_audit=audit,
        measurement_state=states(r),review_provenance='Same AI analytical process; separate rubric reinspection, not independent raters or perfect blinding.',
        final_researcher_decision='',final_researcher_corrections='',final_researcher_id='',final_human_review_timestamp='')
    return r


def distribution(rows, key):
    return {m:dict(Counter('NULL' if r[key][m] is None else str(r[key][m]) for r in rows)) for m in a.FIELDS}


def prepare_primary():
    a.require(not OUT.exists(),'Preserve all previous audit versions')
    original=a.read(analysis.PRIMARY)
    frozen=a.read(OLD/'stage_a/freeze_manifest_v1.json')
    for name,digest in frozen['files'].items():a.require(a.sha(OLD/'stage_a'/name)==digest,'Stage A source changed')
    reviewed=[primary_record(r) for r in original]
    a.require(len(reviewed)==72 and len({r['anonymous_response_id'] for r in reviewed})==72,'Wrong inventory')
    a.write(PRIMARY,reviewed);a.write_csv(PRIMARY.with_suffix('.csv'),reviewed)
    a.write(OUT/'primary_audit_freeze_v1.json',{'version':'p1c_semantic_integrity_primary_freeze_v1',
        'software_recorded_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':a.sha(analysis.PRIMARY),
        'files':{p.name:a.sha(p) for p in (PRIMARY,PRIMARY.with_suffix('.csv'))},
        'method':'All masked rows re-read; separate rubric arguments. Original code used joint group defaults/updates, not independent rating passes.',
        'prior_exposure':'Same analyst, prior structural and design knowledge. A schema-inspection command loaded protected mapping keys but failed before printing any record; no semantic treatment join or effect calculation. No independent blinding claim.',
        'human_confirmations':0,'new_inference':0})
    return {'records':72,'original':distribution(reviewed,'original_AI_ratings'),
            'reviewed':distribution(reviewed,'reviewed_AI_ratings'),'changed_fields':sum(len(r['reviewed_AI_changes']) for r in reviewed)}


def prepare_secondary():
    a.require(not SECONDARY.exists(),'Preserve secondary audit')
    primary=a.read(PRIMARY);old={r['anonymous_response_id']:r for r in a.read(analysis.SECONDARY)}
    bounds={r['anonymous_response_id']:r for r in a.read(OLD/'stage_b/ambiguous_boundary_review_UNCONFIRMED_v1.json')}
    structural={r['anonymous_response_id']:r for r in a.rows(a.ROOT/'measurement_v1/structural_review_view_v1.csv')}
    a.require({k for k,v in structural.items() if v['frozen_structural_status']=='AMBIGUOUS'}==BOUNDARY==set(bounds),'Boundary inventory differs')
    # Analyst-only source reconstruction after the reviewed primary snapshot; never a semantic treatment analysis.
    mapping={r['anonymous_response_id']:r for r in a.read(a.ROOT/'measurement_v1/protected_treatment_mapping_v1.json')['rows']}
    executions={r['request_key']:r['result'] for r in a.read(a.ROOT/'measurement_v1/execution_integrity_v1.json')['rows']}
    prompt_audit=[]
    secondary=[];table=[]
    for r in primary:
        rid=r['anonymous_response_id'];s=copy.deepcopy(r)
        s.update(secondary_evaluation_view=r['raw_first_reply'],secondary_view_sha256=r['first_reply_sha256'])
        if rid in BOUNDARY:
            b=bounds[rid];native=b['native_termination'];raw=b['raw_full_continuation']
            a.require(a.text_sha(raw)==b['raw_text_sha256'],'Raw hash differs')
            a.require(raw[b['proposed_start']:b['proposed_end']]==b['proposed_evaluation_view'],'Boundary offsets differ')
            original=executions[mapping[rid]['request_key']];request=original['frozen_request']
            a.require(a.text_sha(request['prompt'])==mapping[rid]['prompt_sha256'],'Original prompt hash differs')
            a.require(original['raw_text_sha256']==b['raw_text_sha256'],'Original raw record differs')
            prompt_audit.append({'anonymous_response_id':rid,'original_prompt':request['prompt'],
                'prompt_sha256':mapping[rid]['prompt_sha256'],'raw_text_sha256':b['raw_text_sha256'],
                'input_token_ids':request['input_token_ids'],
                'notice':'Analyst-only Stage B source audit after primary reinspection; full prompt can reveal intervention cues.'})
            score=ratings(old[rid]);score.update(response_relevance=5,conversational_coherence=5)
            s.update(reviewed_AI_ratings=score,secondary_evaluation_view=b['proposed_evaluation_view'],
                secondary_view_sha256=b['proposed_view_sha256'],measurement_state=states(r,True))
            table.append({**b,'original_primary_ratings':r['original_AI_ratings'],
                **{k:r[k] for k in ('current_question','trusted_evidence','requested_date','evaluation_date','required_answer_components','fixed_preceding_context','reference_fact_ids')},
                'original_secondary_ratings':ratings(old[rid]),'reviewed_secondary_ratings':score,
                'uncertainty_state':states(r,True),'answer_delivered_under_prefix':'YES',
                'defensible_first_reply':'PLAUSIBLE_NOT_CERTIFIED','multiple_interpretations_remain':True,
                'primary_label_change':{k:[r['original_AI_ratings'][k],score[k]] for k in ('factual_consistency','temporal_consistency','task_success')},
                'additional_reinspection':'A self-contained target answer precedes a generated section heading. Delimiter is not native attribution. PC023 service-day wording does not by itself break relevance or fixed-context coherence.',
                'researcher_final_disposition':''})
        s['original_secondary_AI_ratings']=ratings(old[rid])
        s['secondary_recommendation_changes']=[{'metric':k,'original':old[rid]['AI_'+k],'recommended':v} for k,v in s['reviewed_AI_ratings'].items() if v!=old[rid]['AI_'+k]]
        secondary.append(s)
    a.write(SECONDARY,secondary);a.write_csv(SECONDARY.with_suffix('.csv'),secondary)
    a.write(OUT/'protected_boundary_prompt_audit_v1.json',prompt_audit)
    a.write(OUT/'boundary_sensitivity_table_v1.json',table);a.write_csv(OUT/'boundary_sensitivity_table_v1.csv',table)
    a.write(OUT/'uncertainty_classification_v1.json',{'version':'p1c_measurement_state_v1',
        'definitions':{'EVIDENCE_UNVERIFIABLE':'A specified material proposition lacks trusted support; may coexist with a contradicted different claim.',
            'BOUNDARY_UNRESOLVED':'No uniquely approved first-reply unit under frozen extraction.',
            'ANNOTATION_UNCERTAIN':'Interpretation/rubric application requires adjudication, including conditional readings.',
            'STRUCTURALLY_UNSCORABLE':'Evaluation unit unavailable under this view; not model factual falsity.',
            'NOT_APPLICABLE':'Predeclared exclusion for that metric, not decided from outcome.',
            'MISSING':'Administrative absence of a required rating/confirmation, not epistemic uncertainty.'},
        'scope':'Additive metadata only, original labels/weights/denominators unchanged; states can overlap.',
        'primary':[{'anonymous_response_id':r['anonymous_response_id'],**r['measurement_state']} for r in primary],
        'secondary':[{'anonymous_response_id':r['anonymous_response_id'],**r['measurement_state']} for r in secondary]})
    a.write(OUT/'metric_independence_diagnostic_v1.json',{
        'original_primary_distribution':distribution(primary,'original_AI_ratings'),
        'reviewed_primary_distribution':distribution(primary,'reviewed_AI_ratings'),
        'original_secondary_distribution':{m:dict(Counter(str(r['AI_'+m]) for r in old.values())) for m in a.FIELDS},
        'reviewed_secondary_distribution':distribution(secondary,'reviewed_AI_ratings'),
        'factual_task_original_pointwise_equivalence':sum(r['AI_task_success']=={'Correct':1,'Incorrect':0,'Unverifiable':None}[r['AI_factual_consistency']] for r in primary),
        'ordinal_original_pointwise_equivalence':sum(r['AI_response_relevance']==r['AI_conversational_coherence'] for r in primary),
        'source_process':'Joint defaults and group updates; no literal factual-to-task assignment, but procedural independence not demonstrated. Original ordinal pairs set together; canned explanations conditional on assigned scores.',
        'reviewed_task_recomputed_from_delivery_requirements':True,
        'wrong_but_delivered_primary':sorted(WRONG),'correct_but_incomplete_primary':[],
        'correct_intermediate_only_primary':[],
        'complete_semantically_uncertain_primary':['PC006'],
        'boundary_ids':sorted(BOUNDARY),'factual_changes_exactly_ambiguous':sorted(k for k in old if old[k]['AI_factual_consistency']!=next(r for r in primary if r['anonymous_response_id']==k)['AI_factual_consistency'])==sorted(BOUNDARY),
        'new_human_confirmations':0,'new_semantic_condition_effects':0})
    a.write(OUT/'primary_sensitivity_specification_v1.json',{
        'version':'p1c_measurement_integrity_specification_v1','registered_contrasts':a.read(analysis.REGISTRY)['weights'],
        'registry_sha256':a.sha(analysis.REGISTRY),'primary_unit':'Original frozen first reply; eight unresolved remain unscorable.',
        'secondary_unit':'Only eight exact archived prefix offsets; all six conditions and twelve cases retained.',
        'measurement_states':'Explanatory flags do not silently recode categorical endpoints or alter applicability.',
        'primary_ordinal_corrections':'Six proposed field changes in five records, pending the single annotation confirmation.',
        'secondary_additional_corrections':'PC023 relevance/coherence 4 to 5, pending the same confirmation.',
        'uncertainty':'Original signed worst/best bounds; no surviving-cell reweighting; six speaker clusters.',
        'bootstrap_seed':715004,'bootstrap_draws':10000,'official_analysis':'BLOCKED_UNTIL_EXPLICIT_CONFIRMED_SNAPSHOT',
        'primary_proposal_sha256':a.sha(PRIMARY),'secondary_proposal_sha256':a.sha(SECONDARY)})
    return {'secondary_records':72,'boundary_records':len(table),'human_confirmations':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['primary','secondary']);args=parser.parse_args()
    print(json.dumps(prepare_primary() if args.action=='primary' else prepare_secondary(),indent=2))
