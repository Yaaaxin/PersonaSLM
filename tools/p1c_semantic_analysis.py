"""Gated semantic registration and paired P1c analysis; no inference capability."""
import argparse
from collections import Counter,defaultdict
import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import random
import statistics
import p1c_semantic_review as a
import p1c_paired_statistics as stats

PREP=a.OUT/'analysis_preparation'
REGISTRY=Path('docs/validation/p1c/final_review_v1/estimand_registry_proposed_v1.json')
MAPPING=a.ROOT/'measurement_v1/protected_treatment_mapping_v1.json'
PRIMARY=a.OUT/'stage_a/semantic_proposals_UNCONFIRMED_v1.json'
SECONDARY=a.OUT/'stage_b/boundary_sensitivity_proposals_UNCONFIRMED_v1.json'


def validate_rating(rating):
    a.require(set(rating)==set(a.FIELDS),'Seven independent endpoints required')
    for field in ('factual_consistency','temporal_consistency'):
        a.require(rating[field] in ('Correct','Incorrect','Unverifiable','Missing'),'Invalid applicable categorical rating')
    for field in ('response_relevance','conversational_coherence'):
        value=rating[field];a.require(value is None or type(value) is int and 1<=value<=5,'Invalid ordinal rating')
    a.require(rating['task_success'] is None or type(rating['task_success']) is int and rating['task_success'] in (0,1),'Invalid task success')
    value=rating['component_coverage'];a.require(value is None or type(value) in (float,int) and 0<=value<=1,'Invalid component coverage')
    a.require(rating['semantic_completeness'] in ('YES','PARTIAL','NO','UNCERTAIN','Missing'),'Invalid semantic completeness')


def template():
    return {'version':'p1c_semantic_confirmation_v1','decision':'','reviewer_id':'','review_status':'',
        'decision_source':'','confirmation_statement':'','review_timestamp':None,
        'primary_source':str(PRIMARY),'primary_sha256':a.sha(PRIMARY),
        'secondary_source':str(SECONDARY),'secondary_sha256':a.sha(SECONDARY),
        'corrections':[],'boundary_rejections':[],
        'interpretation':'Primary frozen spans remain primary. Eight recovered prefixes are separately versioned sensitivity only. Entity-versus-time and calendar/attribute uncertainties must be explicitly adopted or corrected.',
        'allowed_decisions':['ADOPT_PRIMARY_AND_SECONDARY_AS_SENSITIVITY','ADOPT_PRIMARY_ONLY'],
        'scope':'AI-assisted proposals adopted/corrected by researcher; not independent blind human annotation.'}


def prepare():
    a.require(not PREP.exists(),'Preserve existing preparation')
    registry=a.read(REGISTRY)
    plan=a.read('docs/validation/p1c/final_review_v1/calibration_manifest_candidate_v1.json')
    units={r['case_id']:r['persona_id'] for r in plan['requests']}
    a.require(len(units)==12 and len(set(units.values()))==6,'Pair/cluster inventory differs')
    spec={'version':'p1c_semantic_analysis_specification_v1','status':'READY_NOT_EXECUTED_PENDING_CONFIRMED_ANNOTATIONS',
        'original_registry_sha256':a.sha(REGISTRY),'weights':registry['weights'],'condition_order':registry['condition_order'],
        'cases':units,'case_unit':'All original cells within case; never select by baseline correctness.',
        'aggregation':'Average two case contrasts within speaker, then six speakers equally.',
        'bootstrap':{'unit':'whole speaker with both cases/all cells','seed':715004,'replicates':10000},
        'leave_one_speaker_out':True,'category_distribution_denominator':72,'per_condition_denominator':12,
        'unverifiable':'A separate observed label. Correct-label incidence is not Correct-versus-Incorrect accuracy.',
        'unknown':'No surviving-cell reweighting. Original signed weights and outcome ranges define identification bounds.',
        'ordinal':'Full categories, descriptive mean-score contrasts, >=2/3/4/5 threshold contrasts and paired sign distributions; no interval-scale validity claim.',
        'multiplicity':'Disclose all 16 contrasts for each separate endpoint; no significance selection or population claims.',
        'boundary':'Primary frozen spans; approved secondary prefix sensitivity never replaces primary.',
        'controls':'N_history is diagnostic procedural content; H_none is shorter.',
        'scientific_scope':'Package effects only; six synthetic clusters are development material.',
        'human_gate':'Registration must validate explicit confirmation and freeze annotations before treatment join.'}
    a.write(PREP/'analysis_specification_v1.json',spec)
    a.write_csv(PREP/'case_contrast_specifications_v1.csv',[{'case_id':cid,'speaker_id':speaker,'contrast':name,'weights':weights,'observed_value':None}
                for cid,speaker in sorted(units.items()) for name,weights in registry['weights'].items()])
    a.write(PREP/'researcher_confirmation_request_v1.json',template())
    a.write(PREP/'applicability_verification_v1.json',{'source_sha256':a.sha('docs/validation/p1c/final_review_v1/applicability_matrix_v1.json'),
        'all_seven_semantic_axes':72,'structural_status':72,'persona_fidelity':0,'not_applicable_semantic_records':0,
        'approval':'Existing applicability remains approved; no new applicability vote is requested.'})
    return {'contrasts':len(registry['weights']),'case_contrast_specifications':12*len(registry['weights']),
            'speaker_clusters':6,'actual_semantic_condition_effects':0,'confirmation':'PENDING'}


def confirmed_rows(approval):
    a.require(approval.get('decision') in ('ADOPT_PRIMARY_AND_SECONDARY_AS_SENSITIVITY','ADOPT_PRIMARY_ONLY'),'Explicit annotation adoption missing')
    a.require(approval.get('reviewer_id')=='Yaxin_ZHENG' and approval.get('review_status')=='RESEARCHER_CONFIRMED','Human confirmation missing')
    a.require(approval.get('decision_source') in ('researcher','researcher_confirmation') and bool(approval.get('confirmation_statement','').strip()),'Researcher provenance missing')
    for name,path in [('primary',PRIMARY),('secondary',SECONDARY)]:
        a.require(approval.get(name+'_source')==str(path) and approval.get(name+'_sha256')==a.sha(path),'Proposal source binding differs')
    originals={r['anonymous_response_id']:r for r in a.rows(a.SOURCE)}
    groups={'primary':a.read(PRIMARY)}
    if approval['decision']=='ADOPT_PRIMARY_AND_SECONDARY_AS_SENSITIVITY':groups['secondary']=a.read(SECONDARY)
    corrected={};seen=set()
    for correction in approval.get('corrections',[]):
        key=(correction['view'],correction['anonymous_response_id'])
        a.require(key not in seen and key[0] in groups and key[1] in originals,'Invalid/duplicate correction')
        a.require(correction.get('reason','').strip() and set(correction['ratings']).issubset(a.FIELDS),'Correction lacks valid scope/reason')
        seen.add(key);corrected[key]=correction
    rejections=approval.get('boundary_rejections',[])
    boundary_ids={'PC010','PC023','PC033','PC039','PC042','PC044','PC054','PC063'}
    a.require(len(rejections)==len(set(rejections)) and set(rejections).issubset(boundary_ids),'Invalid boundary rejection')
    out={}
    for view,records in groups.items():
        a.require(len(records)==len({r['anonymous_response_id'] for r in records})==72,'Proposal inventory differs')
        out[view]=[]
        for r in records:
            rid=r['anonymous_response_id'];source=originals[rid]
            a.require(all(r[k]==v for k,v in source.items()),'Original non-annotation field differs: '+rid)
            rating={k:r['AI_'+k] for k in a.FIELDS}
            if view=='secondary' and rid in rejections:
                rating={k:None for k in a.FIELDS};rating.update(factual_consistency='Unverifiable',temporal_consistency='Unverifiable',semantic_completeness='UNCERTAIN')
            correction=corrected.get((view,rid));rating.update(correction['ratings'] if correction else {})
            validate_rating(rating)
            out[view].append({'anonymous_response_id':rid,'original_source':source,'original_AI_proposal':r,
                'ratings':rating,'researcher_correction':correction,'boundary_rejected':view=='secondary' and rid in rejections,
                'review_status':'RESEARCHER_CONFIRMED','reviewer_id':'Yaxin_ZHENG','decision_source':approval['decision_source'],
                'annotation_origin':'AI_assisted_condition_masked_assessment','review_method':'Researcher verification/adoption or correction of AI-assisted annotations; not independent blind scoring.'})
    return out


def register(approval_path,output):
    output=Path(output);a.require(not output.exists(),'Registration cannot overwrite')
    approval=a.read(approval_path);records=confirmed_rows(approval)
    a.write(output/'confirmed_annotations_v1.json',records)
    a.write(output/'researcher_confirmation_source_v1.json',approval)
    a.write(output/'registration_manifest_v1.json',{'version':'p1c_confirmed_semantic_registration_v1',
        'registered_utc':datetime.now(timezone.utc).isoformat(),'human_review_timestamp':approval.get('review_timestamp'),
        'files':{p.name:a.sha(p) for p in output.iterdir()},'original_approval_file_sha256':a.sha(approval_path),
        'masked_source_sha256':a.sha(a.SOURCE),'primary_proposal_sha256':a.sha(PRIMARY),'secondary_proposal_sha256':a.sha(SECONDARY),
        'original_contrast_registry_sha256':a.sha(REGISTRY),'protected_mapping_sha256':a.sha(MAPPING),
        'analysis_specification_sha256':a.sha(PREP/'analysis_specification_v1.json'),'records':72,
        'treatments_joined':False,'official_semantic_effects_computed':False})
    return {'registered_records':72,'treatments_joined':False}


def scalar_metrics(rating):
    out={}
    for metric in ('factual_consistency','temporal_consistency'):
        label=rating[metric]
        for cat in ('Correct','Incorrect','Unverifiable'):
            out[metric+'__'+cat+'_incidence']=(None if label=='Missing' else float(label==cat),0,1)
        out[metric+'__assessed_C_vs_I_sensitivity']=(1.0 if label=='Correct' else 0.0 if label=='Incorrect' else None,0,1)
    for metric in ('response_relevance','conversational_coherence'):
        score=rating[metric];out[metric+'__descriptive_score']=(score,1,5)
        for threshold in (2,3,4,5):out[metric+f'__at_least_{threshold}']=(None if score is None else float(score>=threshold),0,1)
    for metric in ('task_success','component_coverage'):out[metric]=(rating[metric],0,1)
    for cat in ('YES','PARTIAL','NO','UNCERTAIN'):
        label=rating['semantic_completeness'];out['semantic_completeness__'+cat+'_incidence']=(None if label=='Missing' else float(label==cat),0,1)
    return out


def analysis_payload(joined,spec,replicates=10000):
    """Pure analysis function; CLI invokes it only after verified registration."""
    coverage={};distributions={};effects=[]
    for metric in a.FIELDS:
        values=[r['ratings'][metric] for r in joined]
        coverage[metric]={'eligible':len(values),'recorded':sum(v is not None and v!='Missing' for v in values),
            'unknown_or_missing':sum(v is None or v=='Missing' for v in values),'unverifiable':sum(v=='Unverifiable' for v in values),'not_applicable':0}
        coverage[metric]['administrative_missing_label']=sum(v=='Missing' for v in values)
        coverage[metric]['null_rating_with_preserved_reason']=sum(v is None for v in values)
        coverage[metric]['boundary_unscorable_source_records']=sum(
            r.get('original_AI_proposal',{}).get('AI_primary_unit_status')=='UNRESOLVED' for r in joined)
        coverage[metric]['reason_note']='Boundary source flag describes original extraction, not automatic failure or absence of an adjudicated secondary rating. Every null retains the original proposal explanation and researcher corrections.'
        distributions[metric]={group:{v:dict(Counter('Missing' if r['ratings'][metric] is None else str(r['ratings'][metric]) for r in joined if r[group]==v)) for v in sorted({r[group] for r in joined})} for group in ('condition','family')}
    metrics={name:(lo,hi) for name,(_,lo,hi) in scalar_metrics(joined[0]['ratings']).items()}
    for metric,(lo,hi) in metrics.items():
        cases=[]
        for cid in sorted(spec['cases']):
            cells=[r for r in joined if r['case_id']==cid]
            a.require(len(cells)==6 and len({r['condition'] for r in cells})==6,'Complete case routing required')
            cases.append({'case_id':cid,'speaker_id':spec['cases'][cid],
                'values':{r['condition']:scalar_metrics(r['ratings'])[metric][0] for r in cells}})
        for contrast,weights in spec['weights'].items():
            calculated=stats.summarize(cases,weights,seed=715004,replicates=replicates,lower=lo,upper=hi)
            calculated['unknown_bound_cluster_sensitivity']=bound_sensitivity(calculated,replicates)
            families={r['case_id']:r['family'] for r in joined}
            calculated['task_family_case_contributions']={family:[r for r in calculated['case_table'] if families[r['case_id']]==family] for family in sorted(set(families.values()))}
            calculated['paired_signs']=dict(Counter('unknown' if r['estimate'] is None else 'positive' if r['estimate']>0 else 'negative' if r['estimate']<0 else 'zero' for r in calculated['case_table']))
            effects.append({'metric':metric,'contrast':contrast,**calculated})
    return {'coverage':coverage,'distributions':distributions,'effects':effects,
            'warning':'Exploratory package contrasts, not pure mechanisms. Unknown bounds are not sampling intervals; six clusters can yield unstable or degenerate bootstrap intervals.'}


def bound_sensitivity(result,replicates):
    """Resample bound endpoints, without imputing unknown responses or estimating an ICC."""
    clusters=result['speaker_table'];rng=random.Random(715004)
    draws=[]
    for _ in range(replicates):
        sample=rng.choices(clusters,k=len(clusters))
        draws.append((statistics.mean(r['lower_bound'] for r in sample),statistics.mean(r['upper_bound'] for r in sample)))
    loso=[]
    for i,row in enumerate(clusters):
        remaining=clusters[:i]+clusters[i+1:]
        loso.append({'omitted_speaker':row['speaker_id'],
            'identification_bounds':[statistics.mean(r[k] for r in remaining) for k in ('lower_bound','upper_bound')] if remaining else None})
    return {'leave_one_speaker_out_bounds':loso,
        'bootstrap_bound_endpoints':{'lower_percentiles':[stats.quantile([r[0] for r in draws],q) for q in (.025,.975)],
                                    'upper_percentiles':[stats.quantile([r[1] for r in draws],q) for q in (.025,.975)]},
        'interpretation':'Sensitivity of identification-bound endpoints to whole-cluster resampling. NOT a confidence interval for an identified mean. Original cell weights remain fixed.'}


def analyze(registration,output):
    registration=Path(registration);output=Path(output)
    a.require(not output.exists(),'Analysis cannot overwrite')
    manifest=a.read(registration/'registration_manifest_v1.json')
    for name,digest in manifest['files'].items():a.require(a.sha(registration/name)==digest,'Frozen annotation registration changed')
    approval=a.read(registration/'researcher_confirmation_source_v1.json')
    expected=confirmed_rows(approval);records=a.read(registration/'confirmed_annotations_v1.json')
    a.require(records==expected and manifest['records']==72,'Confirmed record reconstruction differs')
    for path,key in [(a.SOURCE,'masked_source_sha256'),(REGISTRY,'original_contrast_registry_sha256'),(MAPPING,'protected_mapping_sha256'),(PREP/'analysis_specification_v1.json','analysis_specification_sha256')]:
        a.require(a.sha(path)==manifest[key],'Frozen analysis input changed')
    # First treatment join occurs only here, after the approval/snapshot checks.
    mapping={r['anonymous_response_id']:r for r in a.read(MAPPING)['rows']}
    spec=a.read(PREP/'analysis_specification_v1.json')
    data=a.read('data/synthetic/p1c_development_proposed_v1.json');families={r['case_id']:r['family'] for r in data['cases']}
    results={}
    for view,rows in records.items():
        joined=[{**r,**{k:mapping[r['anonymous_response_id']][k] for k in ('case_id','persona_id','condition')},'family':families[mapping[r['anonymous_response_id']]['case_id']]} for r in rows]
        result=analysis_payload(joined,spec);a.require(result==analysis_payload(joined,spec),'Numerical reconstruction differs')
        a.write(output/(view+'_unblinded_dataset_v1.json'),joined)
        a.write(output/(view+'_analysis_v1.json'),result)
        a.write_csv(output/(view+'_case_contrasts_v1.csv'),[{'metric':x['metric'],'contrast':x['contrast'],**r} for x in result['effects'] for r in x['case_table']])
        a.write_csv(output/(view+'_speaker_sensitivity_v1.csv'),[{'metric':x['metric'],'contrast':x['contrast'],**r} for x in result['effects'] for r in x['leave_one_speaker_out']])
        results[view]={'contrasts':len(spec['weights']),'records':len(rows)}
    a.write(output/'analysis_manifest_v1.json',{'registration_sha256':a.sha(registration/'registration_manifest_v1.json'),
        'files':{p.name:a.sha(p) for p in output.iterdir()},'source_sha256':a.sha(__file__),'statistics_sha256':a.sha('tools/p1c_paired_statistics.py'),
        'bootstrap_seed':715004,'bootstrap_draws':10000,'reconstructed_twice':True,'new_generations':0})
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','register','analyze'])
    p.add_argument('--approval',type=Path);p.add_argument('--registration',type=Path);p.add_argument('--output',type=Path);args=p.parse_args()
    if args.action=='prepare':result=prepare()
    elif args.action=='register':
        if not args.approval or not args.output:p.error('Explicit approval and fresh output required')
        result=register(args.approval,args.output)
    else:
        if not args.registration or not args.output:p.error('Verified registration and fresh output required')
        result=analyze(args.registration,args.output)
    print(json.dumps(result,indent=2))
