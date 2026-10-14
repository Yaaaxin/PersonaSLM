"""Register only actual adoption of the reviewed P1c package; reuse approved statistics."""
import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path

import p1c_semantic_review as a
import p1c_semantic_analysis as prior
import p1c_semantic_integrity as audit


def sources():
    return {str(p):a.sha(p) for p in (audit.PRIMARY,audit.SECONDARY,
        audit.OUT/'primary_sensitivity_specification_v1.json',audit.OUT/'uncertainty_classification_v1.json',
        prior.REGISTRY,a.POLICY,a.SOURCE,prior.PREP/'analysis_specification_v1.json')}


def template():
    return {'version':'p1c_integrity_annotation_confirmation_v1','reviewer_id':'','review_status':'',
        'decision_source':'','confirmation_statement':'','human_review_timestamp':None,
        'rating_version':'','include_boundary_sensitivity':None,'corrections':[],
        'source_sha256':sources(),
        'allowed_rating_versions':['REVIEWED_RECOMMENDATIONS','ORIGINAL_PROPOSALS'],
        'scope':'Adopt/correct 72 AI proposals and optional eight-prefix sensitivity, including disclosed uncertainty. Original experiment and estimands unchanged.',
        'provenance':'AI-assisted assessment and non-independent reinspection, then actual researcher adoption; no independent human agreement claim.'}


def confirmed(approval):
    a.require(approval.get('reviewer_id')=='Yaxin_ZHENG' and approval.get('review_status')=='RESEARCHER_CONFIRMED','Explicit researcher confirmation missing')
    a.require(approval.get('decision_source')=='researcher_confirmation' and bool(approval.get('confirmation_statement','').strip()),'Confirmation provenance missing')
    a.require(approval.get('rating_version') in ('REVIEWED_RECOMMENDATIONS','ORIGINAL_PROPOSALS'),'Choose the exact rating recommendations')
    a.require(type(approval.get('include_boundary_sensitivity')) is bool,'Boundary sensitivity decision missing')
    a.require(approval.get('source_sha256')==sources(),'Confirmed source hashes differ')
    originals={r['anonymous_response_id']:r for r in a.read(prior.PRIMARY)}
    groups={'primary':a.read(audit.PRIMARY)}
    if approval['include_boundary_sensitivity']:groups['secondary']=a.read(audit.SECONDARY)
    fixes={}
    for fix in approval.get('corrections',[]):
        key=(fix['view'],fix['anonymous_response_id'])
        a.require(key not in fixes and key[0] in groups and key[1] in originals,'Invalid/duplicate correction')
        a.require(fix.get('reason','').strip() and set(fix['ratings']).issubset(a.FIELDS),'Correction lacks reason or valid metrics')
        fixes[key]=fix
    result={}
    for view,rows in groups.items():
        a.require(len(rows)==len({r['anonymous_response_id'] for r in rows})==72,'Wrong reviewed inventory')
        result[view]=[]
        for row in rows:
            rid=row['anonymous_response_id']
            a.require(all(row[k]==v for k,v in originals[rid].items()),'Original proposal or source field changed')
            key='reviewed_AI_ratings' if approval['rating_version']=='REVIEWED_RECOMMENDATIONS' else 'original_AI_ratings' if view=='primary' else 'original_secondary_AI_ratings'
            rating=copy.deepcopy(row[key]);fix=fixes.get((view,rid))
            if fix:rating.update(fix['ratings'])
            prior.validate_rating(rating)
            result[view].append({'anonymous_response_id':rid,'ratings':rating,
                'original_AI_proposal':originals[rid],'reviewed_AI_proposal':row,'researcher_correction':fix,
                'measurement_state_source':row['measurement_state'],
                'measurement_state_note':'Original proposal-state flags retained as provenance; researcher adjudication/correction may resolve interpretation. Never silently recode final labels from flags.',
                'reviewer_id':'Yaxin_ZHENG','review_status':'RESEARCHER_CONFIRMED',
                'annotation_origin':'AI_assisted_condition_masked_review_with_disclosed_prior_exposure',
                'review_method':'Researcher verification and adoption/correction of the explicitly selected AI proposal version.',
                'human_review_timestamp':approval.get('human_review_timestamp')})
    return result


def register(approval_path,output):
    output=Path(output);a.require(not output.exists(),'Cannot overwrite registration')
    approval=a.read(approval_path);rows=confirmed(approval)
    a.write(output/'confirmed_annotations_v1.json',rows)
    a.write(output/'actual_researcher_decision_v1.json',approval)
    a.write(output/'registration_manifest_v1.json',{'version':'p1c_semantic_integrity_registration_v1',
        'software_registered_utc':datetime.now(timezone.utc).isoformat(),'human_review_timestamp':approval.get('human_review_timestamp'),
        'files':{p.name:a.sha(p) for p in output.iterdir()},'source_sha256':sources(),
        'original_approval_sha256':a.sha(approval_path),'mapping_sha256':a.sha(prior.MAPPING),
        'annotation_count_per_view':72,'treatment_join_performed':False})
    return {'registered':72,'treatment_join_performed':False}


def analyze(registration,output):
    registration=Path(registration);output=Path(output);a.require(not output.exists(),'Cannot overwrite analysis')
    manifest=a.read(registration/'registration_manifest_v1.json')
    for name,digest in manifest['files'].items():a.require(a.sha(registration/name)==digest,'Frozen annotation changed')
    decision=a.read(registration/'actual_researcher_decision_v1.json');expected=confirmed(decision)
    a.require(a.read(registration/'confirmed_annotations_v1.json')==expected,'Annotation reconstruction differs')
    a.require(a.sha(prior.MAPPING)==manifest['mapping_sha256'],'Mapping changed')
    mapping={r['anonymous_response_id']:r for r in a.read(prior.MAPPING)['rows']}
    spec=a.read(prior.PREP/'analysis_specification_v1.json')
    families={r['case_id']:r['family'] for r in a.read('data/synthetic/p1c_development_proposed_v1.json')['cases']}
    for view,rows in expected.items():
        joined=[{**r,**{k:mapping[r['anonymous_response_id']][k] for k in ('case_id','persona_id','condition')},
            'family':families[mapping[r['anonymous_response_id']]['case_id']]} for r in rows]
        result=prior.analysis_payload(joined,spec)
        a.require(result==prior.analysis_payload(joined,spec),'Numerical reconstruction differs')
        a.write(output/(view+'_unblinded_dataset_v1.json'),joined);a.write(output/(view+'_analysis_v1.json'),result)
        a.write_csv(output/(view+'_case_contrasts_v1.csv'),[{'metric':x['metric'],'contrast':x['contrast'],**r} for x in result['effects'] for r in x['case_table']])
        a.write_csv(output/(view+'_speaker_sensitivity_v1.csv'),[{'metric':x['metric'],'contrast':x['contrast'],**r} for x in result['effects'] for r in x['speaker_table']])
    a.write(output/'analysis_manifest_v1.json',{'registration_sha256':a.sha(registration/'registration_manifest_v1.json'),
        'files':{p.name:a.sha(p) for p in output.iterdir()},'sources':sources(),
        'code_sha256':a.sha(__file__),'statistics_wrapper_sha256':a.sha('tools/p1c_semantic_analysis.py'),
        'bootstrap_seed':715004,'reconstructed_twice':True,'new_inference':0})
    return {'views':list(expected),'official_analysis_completed':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['template','register','analyze'])
    p.add_argument('--approval',type=Path);p.add_argument('--registration',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.action=='template':a.write(args.output,template())
    elif args.action=='register':
        if not args.approval:p.error('Actual researcher confirmation required')
        print(register(args.approval,args.output))
    else:
        if not args.registration:p.error('Frozen confirmed registration required')
        print(analyze(args.registration,args.output))
