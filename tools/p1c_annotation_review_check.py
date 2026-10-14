"""Targeted annotation-gate verification, not annotation adoption or effects."""
from collections import Counter
from datetime import date, datetime, timezone
from itertools import combinations
from pathlib import Path
import copy
import json

import p1c_semantic_review as a
import p1c_semantic_analysis as old
import p1c_semantic_integrity as audit
import p1c_integrity_registration as gate

OUT=a.ROOT/'annotation_gate_v1'
PACKET=Path('docs/P1c_final_annotation_confirmation_packet_v1.md')
PACKET_SHA='4989e36d8d862c5995221b470adb8c9620ba7023ffc8ebf9d492cda18f6fc817'
EXTRA=Path('docs/PersonaSLM_P1c_targeted_scientific_audit_UNCONFIRMED_v1.md')
RUBRIC=Path('docs/annotation_guidelines.md')
EXPECTED={(r,'conversational_coherence',4,5) for r in ('PC004','PC006','PC011','PC027','PC030')}|{('PC006','response_relevance',4,5)}


def concordance(rows):
    itemwise=[]
    for r in rows:
        x=r['reviewed_AI_ratings']
        itemwise.append({'anonymous_response_id':r['anonymous_response_id'],**x,
            'factual_as_C_I_U':{'Correct':1,'Incorrect':0,'Unverifiable':None}[x['factual_consistency']],
            'fact_task_equal_under_explicit_C_I_U_mapping':{'Correct':1,'Incorrect':0,'Unverifiable':None}[x['factual_consistency']]==x['task_success'],
            'relevance_coherence_equal_including_null':x['response_relevance']==x['conversational_coherence'],
            'factual_interpretation':'Mapping describes observed concordance; U is unknown, never Incorrect.'})
    pairs=[]
    for left,right in combinations(a.FIELDS,2):
        joint=Counter((json.dumps(r['reviewed_AI_ratings'][left]),json.dumps(r['reviewed_AI_ratings'][right])) for r in rows)
        pairs.extend({'left_metric':left,'right_metric':right,'left_value':l,'right_value':r,'count':n} for (l,r),n in sorted(joint.items()))
    summaries={m:{'distribution':dict(Counter('NULL' if r['reviewed_AI_ratings'][m] is None else str(r['reviewed_AI_ratings'][m]) for r in rows)),
                  'non_null_distinct_values':sorted({str(r['reviewed_AI_ratings'][m]) for r in rows if r['reviewed_AI_ratings'][m] is not None})} for m in a.FIELDS}
    return itemwise,pairs,summaries


def verify():
    a.require(a.sha(PACKET)==PACKET_SHA,'Exact annotation packet fingerprint differs')
    seal=a.read(audit.OUT/'reproducibility_manifest_v1.json')
    for path,digest in seal['artifact_sha256'].items():a.require(a.sha(path)==digest,'Previous sealed artifact differs '+path)
    approval=a.read('docs/validation/p1c/authorization_v2/researcher_consolidated_approval_v1.json')
    for decision in approval['decisions']:
        for p in decision['documents']:a.require(a.sha(p['path'])==p['sha256'],'Approved policy/manifest changed')
    original={r['anonymous_response_id']:r for r in a.read(old.PRIMARY)}
    reviewed=a.read(audit.PRIMARY); secondary=a.read(audit.SECONDARY)
    a.require(len(reviewed)==len({r['anonymous_response_id'] for r in reviewed})==72,'Primary inventory')
    changes=[]
    for r in reviewed:
        o=original[r['anonymous_response_id']]
        a.require(all(r[k]==v for k,v in o.items()),'Original proposal field changed')
        a.require(a.text_sha(r['raw_first_reply'])==r['first_reply_sha256'],'First-reply integrity')
        for metric in a.FIELDS:
            before=o['AI_'+metric];after=r['reviewed_AI_ratings'][metric]
            if before!=after:
                detail=r['metric_evidence_audit']['relevance' if metric=='response_relevance' else 'coherence']
                changes.append({'anonymous_response_id':r['anonymous_response_id'],'endpoint':metric,'original_rating':before,'revised_proposed_rating':after,
                    'original_supporting_explanation':o['AI_endpoint_explanations'][metric],
                    'original_reply_quotation':r['raw_first_reply'],'question':r['current_question'],
                    'fixed_context':r['fixed_preceding_context'],'original_fact_quotations':r['AI_source_quotations'],
                    'revised_interpretation':detail['reason'],'reason_for_correction':'Keep truth/attribute uncertainty separate from discourse coherence and direct request alignment.',
                    'rubric_consistency':'CONSISTENT_AI_RECOMMENDATION_NOT_HUMAN_VERDICT','rubric_path':str(RUBRIC),'rubric_sha256':a.sha(RUBRIC),
                    'alternative_score':detail['alternative_score'],'confidence':detail['confidence'],'researcher_decision':''})
    a.require({(r['anonymous_response_id'],r['endpoint'],r['original_rating'],r['revised_proposed_rating']) for r in changes}==EXPECTED,'Unexpected rating changes')
    b=a.read(audit.OUT/'boundary_sensitivity_table_v1.json')
    a.require({r['anonymous_response_id'] for r in b}==audit.BOUNDARY,'Eight boundary identities differ')
    for r in b:
        a.require(r['original_structural_status']=='AMBIGUOUS','Frozen structure changed')
        a.require(r['raw_full_continuation'][r['proposed_start']:r['proposed_end']]==r['proposed_evaluation_view'],'Prefix offsets')
        a.require(a.text_sha(r['proposed_evaluation_view'])==r['proposed_view_sha256'],'Prefix hash')
    a.require(a.read(old.PREP/'analysis_specification_v1.json')['weights']==a.read(old.REGISTRY)['weights'],'Contrast weights differ')
    return reviewed,secondary,changes,b


def prepare():
    a.require(not OUT.exists(),'Preserve prior verification')
    primary,secondary,changes,boundary=verify()
    a.write(OUT/'six_field_revision_audit_v1.json',changes);a.write_csv(OUT/'six_field_revision_audit_v1.csv',changes)
    pc023=next(r for r in boundary if r['anonymous_response_id']=='PC023')
    a.write(OUT/'PC023_secondary_ordinal_revision_v1.json',{'anonymous_response_id':'PC023','original':pc023['original_secondary_ratings'],
        'reviewed_proposal':pc023['reviewed_secondary_ratings'],'span':pc023['proposed_evaluation_view'],
        'rationale':'Direct assignment answer and coherent named target; service/calendar interpretation is separate from ordinal discourse quality.',
        'primary_unchanged':True,'researcher_decision':''})
    summary={}
    for view,rows in [('primary',primary),('secondary',secondary)]:
        items,pairs,summary[view]=concordance(rows)
        a.write_csv(OUT/(view+'_item_concordance_v1.csv'),items)
        a.write_csv(OUT/(view+'_metric_joint_distributions_v1.csv'),pairs)
    a.write(OUT/'metric_discrimination_summary_v1.json',summary)
    states=[]
    for view,rows in [('primary',primary),('secondary',secondary)]:
        for r in rows:
            src=copy.deepcopy(r['measurement_state']);derived=copy.deepcopy(src['metric_uncertainty_flags'])
            for m,flags in derived.items():derived[m]=['INTERPRETATION_UNCERTAIN' if x=='ANNOTATION_UNCERTAIN' else x for x in flags]
            if view=='secondary' and r['anonymous_response_id']=='PC023':
                for m in ('factual_consistency','temporal_consistency','task_success'):derived[m].append('INTERPRETATION_UNCERTAIN')
            states.append({'view':view,'anonymous_response_id':r['anonymous_response_id'],'original_state':src,'derived_metric_flags':derived,
                'version':'p1c_measurement_state_v2','change_scope':'Interpretation terminology alias; explicitly flag PC023 secondary wording uncertainty already in source prose. No score or estimand change.'})
    a.write(OUT/'derived_measurement_state_v2.json',states)
    calendar=[]
    for rid in ('PC004','PC006','PC011','PC023','PC027','PC030','PC035','PC040'):
        r=next(r for r in primary if r['anonymous_response_id']==rid)
        if rid=='PC023':span=pc023['proposed_evaluation_view']
        else:span=r['raw_first_reply']
        weekday=date.fromisoformat(r['requested_date']).strftime('%A')
        reason=('Calendar interpretation would make Thursday false; service-day interpretation supports both requested attributes. Primary remains U/U/unknown; do not add Gregorian knowledge silently to the trusted ledger.' if rid=='PC006' else
                'The phrase on a Thursday can denote the recurring service attribute. Literal query-date weekday reading would be false. Retain Correct secondary proposal under service-day reading with explicit interpretation uncertainty; primary remains boundary-unresolved.' if rid=='PC023' else
                'Cobalt is the supported route-53 destination; collection desk is not an attested Idris attribute. Alias interpretation retained, strict attribute reading unresolved.' if rid=='PC004' else
                'Laurel belongs to the colleague during the same query interval. Wrong target/attribute is established; wrong interval selection is not. Retain factual Incorrect and temporal Unverifiable, with date-bound-false interpretation separately disclosed.')
        calendar.append({'anonymous_response_id':rid,'span':span,'requested_date':r['requested_date'],'evaluation_date':r['evaluation_date'],
            'gregorian_weekday_computed':weekday,'calculation_method':'Python datetime.date proleptic Gregorian; derived diagnostic only, not added to trusted evidence',
            'reference_components':json.loads(r['required_answer_components']),'trusted_evidence':r['trusted_evidence'],
            'proposed_interpretation':reason,'source_scores_unchanged':True,'researcher_resolution':''})
    a.write(OUT/'temporal_entity_interpretations_v1.json',calendar);a.write_csv(OUT/'temporal_entity_interpretations_v1.csv',calendar)
    p1b_path=Path('docs/validation/p1b/confirmed_analysis_v1/analysis_v1/unblinded_analysis_dataset_v1.json')
    p1b=a.read(p1b_path)['rows']
    p1b_summary={'source':str(p1b_path),'source_sha256':a.sha(p1b_path),'records':len(p1b),
        'factual':dict(Counter(r['confirmed_factual_consistency'] for r in p1b)),
        'delivery':dict(Counter(r['confirmed_answer_delivery'] for r in p1b)),
        'correct_partial':sum(r['confirmed_factual_consistency']=='Correct' and r['confirmed_answer_delivery']=='PARTIAL_ANSWER' for r in p1b),
        'scope':'Historical confirmed coding, separate dataset. No pooling or causal between-wave comparison.'}
    a.write(OUT/'P1b_separate_delivery_comparison_v1.json',p1b_summary)
    a.write(OUT/'verified_snapshot_manifest_v1.json',{'software_verified_utc':datetime.now(timezone.utc).isoformat(),
        'version':'p1c_final_annotation_gate_verification_v1','packet_sha256':a.sha(PACKET),'packet_fingerprint_matches':True,
        'primary_source':str(audit.PRIMARY),'primary_sha256':a.sha(audit.PRIMARY),'primary_csv_sha256':a.sha(audit.PRIMARY.with_suffix('.csv')),
        'secondary_source':str(audit.SECONDARY),'secondary_sha256':a.sha(audit.SECONDARY),'eight_item_csv_sha256':a.sha(audit.OUT/'boundary_sensitivity_table_v1.csv'),
        'supplementary_AI_audit_sha256':a.sha(EXTRA),'source_provenance':'Same-process AI assessment and reinspection; supplementary supplied AI audit is unconfirmed, not an independent human rater.',
        'changes':6,'changed_primary_records':5,'secondary_PC023_changes':2,'official_confirmations':0,
        'original_source_inference':0,'official_semantic_effects':0,'confirmation_template_sha256':a.sha(audit.OUT/'researcher_confirmation_request_v1.json'),
        'files':{p.name:a.sha(p) for p in OUT.iterdir() if p.is_file()}})
    print(json.dumps({'packet_matches':True,'primary_records':72,'boundary_records':8,'primary_changes':6,'registered_annotations':0,'P1b':p1b_summary},indent=2))


if __name__=='__main__':prepare()
