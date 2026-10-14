"""Provisional semantic budget diagnostics, never official E/V factorial effects.

Exactly the completed authorized calibration is required. All semantic inputs
remain AI proposals, with empty human-adoption fields and separate evidence.
"""
from collections import Counter,defaultdict
import argparse
import csv
import json
from pathlib import Path
import random
import statistics
import platform
import p1d_budget_calibration as b
from p1d_design import csvwrite
from p1d_budget_measurement import OUT as MEASURE
from p1d_budget_ai_assessments import assemble
from p1d_budget_review_groups import current_groups

OUT=b.OUT/'analysis_v1'
SEED=716707
PAIRS=((96,192),(96,256),(192,256))
APPLICABILITY=Path('docs/validation/p1d/proposed_v1/metric_applicability_v2.json')

def readcsv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def quantile(values,p):
    ordered=sorted(values);position=(len(ordered)-1)*p;lo=int(position);hi=min(lo+1,len(ordered)-1)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(position-lo)

def bounds_difference(older,newer,limits=(0.,1.)):
    lo,hi=limits
    a=(lo,hi) if older is None else (older,older)
    c=(lo,hi) if newer is None else (newer,newer)
    return c[0]-a[1],c[1]-a[0]

def metric_values(row):
    # Label incidence is not Correct/(Correct+Incorrect) accuracy.
    values={}
    for field in ('factual','temporal'):
        for label in ('Correct','Incorrect','Unverifiable'):
            values[field+'_'+label+'_label_incidence']=float(row[field]==label)
        values[field+'_unknown_correctness']=1. if row[field]=='Correct' else 0. if row[field]=='Incorrect' else None
    values['task_success']=1. if row['task_success']=='Success' else 0. if row['task_success']=='Failure' else None
    values['semantic_complete']=1. if row['semantic_completeness']=='YES' else 0. if row['semantic_completeness']=='NO' else None
    for key in ('relevance','coherence','persona_fidelity'):values[key]=row[key]
    for name,field in (('component_presence','presence'),('supported_components','support')):
        vals=[1. if c[field]=='PRESENT' else 0. if c[field]=='ABSENT' else None for c in row['components']]
        values[name]=statistics.mean(vals) if vals and None not in vals else None
    values.update({'first_response_identifiable':float(row['unit_identifiable']),
        'cross_turn_incidence':float(row['structural_status']=='CROSS_TURN'),
        'ambiguous_incidence':float(row['structural_status']=='AMBIGUOUS'),
        'budget_termination_incidence':float(row['stop_reason']=='length'),
        'eos_termination_incidence':float(row['stop_reason'] in ('eos','eog')),
        'latency_seconds':row['latency_seconds']})
    return values

def paired_estimates(rows,draws=10000):
    speakers=sorted({r['speaker_id'] for r in rows});assert len(speakers)==8
    by={(r['speaker_id'],r['condition'],r['budget']):r for r in rows}
    assert len(by)==144
    rng=random.Random(SEED);indices=[[rng.randrange(len(speakers)) for _ in speakers] for _ in range(draws)]
    blockrows=[];caserows=[];summaries=[]
    metrics=list(metric_values(rows[0]))
    for a,c in PAIRS:
        for metric in metrics:
            limits=(1.,5.) if metric in ('relevance','coherence','persona_fidelity') else (0.,1.)
            contributions=[];lower=[];upper=[]
            for speaker in speakers:
                points=[];lows=[];highs=[];family=None
                for condition in b.CELLS:
                    old=by[speaker,condition,a];new=by[speaker,condition,c];family=old['family']
                    x=metric_values(old)[metric];y=metric_values(new)[metric]
                    point=None if x is None or y is None else y-x
                    lo,hi=bounds_difference(x,y,limits)
                    blockrows.append({'speaker_id':speaker,'case_id':old['case_id'],'family':family,'condition':condition,
                        'lower_budget':a,'higher_budget':c,'metric':metric,'paired_difference':point,'identification_lower':lo,'identification_upper':hi})
                    points.append(point);lows.append(lo);highs.append(hi)
                point=statistics.mean(points) if None not in points else None
                lo=statistics.mean(lows);hi=statistics.mean(highs)
                caserows.append({'speaker_id':speaker,'case_id':old['case_id'],'family':family,'lower_budget':a,'higher_budget':c,
                    'metric':metric,'paired_case_difference':point,'observed_blocks':sum(x is not None for x in points),
                    'expected_blocks':6,'identification_lower':lo,'identification_upper':hi})
                contributions.append(point);lower.append(lo);upper.append(hi)
            complete=[x for x in contributions if x is not None]
            allknown=len(complete)==8
            point=statistics.mean(complete) if allknown else None
            if allknown:
                boot=[sum(complete[i] for i in sample)/8 for sample in indices];ci=[quantile(boot,.025),quantile(boot,.975)]
                loso=[sum(v for j,v in enumerate(complete) if j!=i)/7 for i in range(8)]
            else:ci=[None,None];loso=[]
            summaries.append({'lower_budget':a,'higher_budget':c,'metric':metric,'all_eligible_paired_estimate':point,
                'speaker_bootstrap_sensitivity_interval':ci,'leave_one_speaker_out':loso,'observed_complete_speakers':len(complete),'eligible_speakers':8,
                'complete_speaker_alternative_mean':statistics.mean(complete) if complete else None,
                'all_eligible_identification_bounds':[statistics.mean(lower),statistics.mean(upper)],
                'positive_speakers':sum(x>0 for x in complete),'negative_speakers':sum(x<0 for x in complete),'zero_speakers':sum(x==0 for x in complete),
                'scale_note':'Ordinal mean differences are descriptive; signs and full distributions retained' if limits==(1.,5.) else 'Specified indicator/fraction or latency',
                'inferential_scope':'Eight constructed development clusters; bootstrap not guaranteed population coverage; no p-values'})
    return blockrows,caserows,summaries

def distributions(rows):
    records=[]
    for budget in (96,192,256):
        for family in ['ALL']+sorted({r['family'] for r in rows}):
            group=[r for r in rows if r['budget']==budget and (family=='ALL' or r['family']==family)]
            d={'budget':budget,'family':family,'requests':len(group),'human_confirmed':0}
            for field in ('factual','temporal','task_success','semantic_completeness','relevance','coherence','persona_fidelity','measurement_state','uncertainty_subtype'):
                d[field]=dict(Counter(str(r[field]) for r in group))
            for field in ('factual','temporal'):
                n=sum(r[field] in ('Correct','Incorrect') for r in group);num=sum(r[field]=='Correct' for r in group)
                d[field+'_assessable_denominator']=n;d[field+'_assessable_correct_fraction']=num/n if n else None
                d[field+'_correct_label_fraction']=num/len(group)
            records.append(d)
    return records

def discrimination(rows):
    tables={}
    for fields in (('factual','task_success','semantic_completeness'),('relevance','coherence'),('coherence','semantic_completeness')):
        table=Counter(tuple(r[k] for k in fields) for r in rows)
        tables['__'.join(fields)]=[{**dict(zip(fields,values)),'count':n} for values,n in sorted(table.items())]
    return {'records':len(rows),'human_confirmed':0,'tables':tables,
        'zero_observed_variance':[k for k in ('factual','temporal','task_success','semantic_completeness','relevance','coherence','persona_fidelity') if len({r[k] for r in rows})==1],
        'ordinal_ceiling_counts':{k:sum(r[k]==5 for r in rows) for k in ('relevance','coherence','persona_fidelity')},
        'method':'Explicit metric-specific AI rationales, not label-to-label conversion. Exact input duplicates share a disclosed assessment.',
        'limit':'Observed discrimination is not construct validation, independent annotation reliability or population variation. Invariant metrics cannot distinguish cells here.'}

def assemble_rows():
    audit=b.load(MEASURE/'execution_integrity_v1.json');assert audit['results']==144
    proposals,missing=assemble();assert not missing,missing
    groups=current_groups();lookup={rid:(a,groups[a['group_id']]) for a in proposals for rid in a['anonymous_members']}
    assert len(lookup)==144
    mapping=b.load(MEASURE/'withheld_treatment_budget_mapping_v1.json')
    applicability={(r['case_id'],r['condition']):{k:v for k,v in r.items() if type(v) is bool} for r in b.load(APPLICABILITY)}
    results={r['request']['request_id']:r['result'] for r in audit['rows']}
    masked=[];rows=[]
    for item in mapping:
        rid=item['anonymous_response_id'];a,g=lookup[rid];r=results[item['request_id']]
        assert a['primary_text_sha256']==b.th(r['response_status']['first_span']['text'] if r['response_status']['unit_identifiable'] else '')
        review={k:v for k,v in a.items() if k!='anonymous_members'}
        review.update(anonymous_response_id=rid,question=g['question'],requested_date=g['requested_date'],evaluation_date=g['evaluation_date'],
            trusted_evidence=g['trusted_evidence'],fixed_context=g['fixed_context'],persona_style=g['persona_style'],
            metric_applicability=applicability[item['case_id'],item['condition']],
            source_group_assessment_reuse='Exact text/evidence/question/date/context/style identity only; not independent scoring replicates',
            answer_truncation_assessment='No visible final-answer fragment in the assessed first span; lack of answer is not attributed to the cap without a counterfactual',
            required_human_adjudication='Review every proposed metric and stated alternative; no researcher adoption registered')
        masked.append(review)
        rows.append({**review,**item,'unit_identifiable':r['response_status']['unit_identifiable'],'structural_status':r['response_status']['status'],
            'stop_reason':r['stop_reason'],'latency_seconds':r['latency_seconds'],'generated_tokens':r['generated_tokens'],
            'raw_text_sha256':r['raw_text_sha256']})
    return proposals,masked,rows

def run():
    proposals,masked,rows=assemble_rows();blocks,cases,effects=paired_estimates(rows)
    assert all(all(r['metric_applicability'].values()) for r in rows),'Unexpected N/A requires explicit applicable-case estimator'
    assert (blocks,cases,effects)==paired_estimates(rows),'Deterministic analysis reconstruction failed'
    summary=distributions(rows)
    qualification=[]
    for cap in (96,192,256):
        group=[r for r in rows if r['budget']==cap];complete=sum(r['semantic_completeness']=='YES' for r in group)
        unknown=sum(r['semantic_completeness'] not in ('YES','NO') for r in group);boundary=sum(not r['unit_identifiable'] for r in group)
        qualification.append({'budget':cap,'n':48,'complete_AI_proposals':complete,'unknown_completeness':unknown,'complete_bounds':[complete,complete+unknown],
            'unresolved_boundaries':boundary,'required_complete':44,'maximum_unresolved_boundaries':2,
            'provisional_qualification':complete>=44 and boundary<=2,'human_confirmed':False})
    OUT.mkdir(parents=True,exist_ok=True)
    b.save(OUT/'exact_group_AI_assessments_UNCONFIRMED_v1.json',proposals)
    b.save(OUT/'primary_AI_proposals_UNCONFIRMED_v1.json',masked);csvwrite(OUT/'primary_AI_proposals_UNCONFIRMED_v1.csv',masked)
    b.save(OUT/'provisional_analysis_dataset_v1.json',rows);csvwrite(OUT/'provisional_analysis_dataset_v1.csv',rows)
    csvwrite(OUT/'paired_block_differences_v1.csv',blocks);csvwrite(OUT/'case_speaker_differences_v1.csv',cases)
    b.save(OUT/'cluster_sensitivity_v1.json',effects);b.save(OUT/'distributions_v1.json',summary)
    b.save(OUT/'metric_discrimination_v1.json',discrimination(rows))
    b.save(OUT/'budget_qualification_v1.json',qualification)
    codepaths=['tools/p1d_budget_analysis.py','tools/p1d_budget_ai_assessments.py','tools/p1d_budget_review_groups.py','tools/p1d_budget_measurement.py']
    b.save(OUT/'annotation_analysis_provenance_v1.json',{'version':'p1d_budget_AI_proposed_diagnostics_v1','source_sha256':{p:b.sha256(Path(p)) for p in codepaths},
        'execution_integrity_sha256':b.sha256(MEASURE/'execution_integrity_v1.json'),'records':144,'exact_review_groups':len(proposals),
        'frozen_applicability_source':APPLICABILITY.as_posix(),'frozen_applicability_sha256':b.sha256(APPLICABILITY),
        'numerical_reconstruction':'Two deterministic reconstructions exactly equal; not an independent implementation',
        'human_confirmed':0,'annotation_origin':'AI-assisted assessment; exact-input deduplication explicitly recorded',
        'bootstrap_seed':SEED,'bootstrap_draws':10000,'python_version':platform.python_version(),'random_generator':'Python random.Random; uniform whole-speaker draws',
        'contrast_scope':'Three paired budget contrasts only; no E/V factor-effect selection',
        'masking':'Review fields omit budget and treatment labels; analyst prepared inputs and can access mapping. No independent/perfect blinding.',
        'source_outputs_modified':False,'official_semantic_effects':False,'researcher_adoption_gate':'Pending; cannot register these as human ratings',
        'unknown_policy':'Preserve Unverifiable and measurement states; unknown correctness bounds do not recode labels. No missing-cell renormalization.',
        'multiplicity':'Descriptive development diagnostics across all metrics/three contrasts; no confirmatory significance claims',
        'files':{p.name:b.sha256(p) for p in OUT.iterdir() if p.is_file()}})
    print(json.dumps({'qualification':qualification,'review_groups':len(proposals),'records':len(rows),'human_confirmed':0},indent=2))

def verify():
    proposals,masked,rows=assemble_rows();blocks,cases,effects=paired_estimates(rows)
    assert proposals==b.load(OUT/'exact_group_AI_assessments_UNCONFIRMED_v1.json')
    assert masked==b.load(OUT/'primary_AI_proposals_UNCONFIRMED_v1.json')
    assert rows==b.load(OUT/'provisional_analysis_dataset_v1.json')
    assert effects==b.load(OUT/'cluster_sensitivity_v1.json')
    assert distributions(rows)==b.load(OUT/'distributions_v1.json')
    assert discrimination(rows)==b.load(OUT/'metric_discrimination_v1.json')
    for name,expected in (('primary_AI_proposals_UNCONFIRMED_v1.csv',masked),('provisional_analysis_dataset_v1.csv',rows),
                          ('paired_block_differences_v1.csv',blocks),('case_speaker_differences_v1.csv',cases)):
        projected=[{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else '' if v is None else str(v) for k,v in row.items()} for row in expected]
        assert readcsv(OUT/name)==projected,name
    print(json.dumps({'saved_semantic_and_numerical_outputs_reconstructed':True,'new_generations':0,'human_confirmed':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    verify() if args.verify else run()
