"""Versioned adoption of researcher-confirmed AI coding and offline analysis.

No generation entry point. Original semantic/structural masters and old importer
are unchanged. No human boundary adjudication is manufactured.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import random
import re
import statistics

import p1b_semantic_integration as prior
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.human_factorial import quantile

core = prior.core
digest = prior.digest
VERSION = 'p1b_confirmed_ai_adoption_v1'
ANALYSIS = 'p1b_confirmed_factorial_v2'
PUBLIC = Path('docs/validation/p1b/confirmed_analysis_v1')
LOCAL = Path('results/p1b_confirmed_analysis/v1')
SOURCE = prior.AUDIT/'review_support/PersonaSLM_P1b_192_AI_suggestions_UNCONFIRMED_v1.csv'
SOURCE_SHA = 'a546180e8ad03cb13ac4e22fd4998ebb1001231150fea6bd72cad726f5d0ef88'
FINAL = Path('docs/validation/p1b/researcher_confirmed_annotation_v1.csv')
FIELDS = {
    'factual_consistency':'ai_candidate_factual_consistency',
    'temporal_consistency':'ai_candidate_temporal_consistency',
    'response_relevance':'ai_candidate_relevance_1_to_5',
    'conversational_coherence':'ai_candidate_coherence_1_to_5',
    'semantic_completeness':'ai_candidate_semantic_completeness',
    'answer_delivery':'ai_candidate_delivery',
    'component_coverage':'ai_reference_component_coverage'}
DELIVERY = {'FULL_ANSWER','WRONG_ANSWER_DELIVERED','PARTIAL_ANSWER','PARTIAL_WITH_FALSE_CLAIM','NO_FINAL_ANSWER'}
PROVENANCE = {
    'reviewer_id':'Yaxin_ZHENG','review_status':'RESEARCHER_CONFIRMED',
    'decision_source':'researcher_confirmation','final_decision_authority':'researcher',
    'annotation_origin':'AI_assisted_condition_masked_review',
    'review_method':'Researcher verification and adoption of condition-masked AI-assisted semantic annotations.'}


def write_csv(path, rows):
    if not rows:
        raise ValueError('Empty CSV result')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader()
        w.writerows({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v,(dict,list)) else v
                    for k,v in row.items()} for row in rows)


def validate_proposals(master, rows):
    expected, actual = prior.unique(master), prior.unique(rows)
    if len(rows)!=192 or set(expected)!=set(actual):
        raise ValueError('Expected exactly 192 source response IDs')
    for rid,r in actual.items():
        for k,v in expected[rid].items():
            if r.get(k)!=v:
                raise ValueError('Original field mismatch: '+rid+'/'+k)
        for axis in ('factual_consistency','temporal_consistency'):
            allowed={'Correct','Incorrect','Unverifiable'} if r['applicable_'+axis]=='true' else {'Not Applicable'}
            if r[FIELDS[axis]] not in allowed:
                raise ValueError('Invalid frozen applicability/label: '+rid+'/'+axis)
        if r[FIELDS['semantic_completeness']] not in {'YES','PARTIAL','NO'} or r[FIELDS['answer_delivery']] not in DELIVERY:
            raise ValueError('Missing/invalid completeness or delivery: '+rid)
        for axis in ('response_relevance','conversational_coherence'):
            if r[FIELDS[axis]] not in {'1','2','3','4','5'}:
                raise ValueError('Invalid ordinal score: '+rid)
        match=re.fullmatch(r'(\d+)/(\d+)',r[FIELDS['component_coverage']])
        if not match:
            raise ValueError('Missing component record: '+rid)
        numerator,denominator=map(int,match.groups())
        expected_components=len(json.loads(r['reference_answer_json'])['components'])
        if not 0<=numerator<=denominator or denominator!=expected_components:
            raise ValueError('Component denominator differs: '+rid)
        for field in ('ai_case_specific_evidence','ai_candidate_reasoning','ai_review_method'):
            if not r[field].strip():raise ValueError('Missing actual supporting material: '+rid+'/'+field)
        if any(q not in r['trusted_evidence'] for q in r['ai_case_specific_evidence'].split(' | ')):
            raise ValueError('Evidence quotation is not verbatim: '+rid)
    return {'records':192,'original_fields_verified_per_record':len(master[0]),'source_quote_verification':'PASS',
            'distributions':{axis:dict(Counter(r[field] for r in rows)) for axis,field in FIELDS.items()}}


def registration_rows(rows):
    """Copy every source field, including blank human fields; append adopted values."""
    return [{**r, **{'confirmed_'+axis:r[field] for axis,field in FIELDS.items()},
             **{'registration_'+k:v for k,v in PROVENANCE.items()},
             'registration_version':VERSION,'registration_confirmation_basis':'Explicit researcher instruction in current task',
             'registration_review_timestamp':'',
             'supporting_notes_origin':'AI-assisted source, subsequently adopted by researcher; not independently authored human notes'} for r in rows]


def specification():
    return {'version':ANALYSIS,'created_utc':utc_now(),'weights':prior.contrast_weights(),
        'bootstrap_seed':714005,'bootstrap_replicates':10000,
        'timing':'Post-generation and source-label inspection; before treatment join in this analysis. Exploratory, not preregistration.',
        'categorical_policy':'Report all label categories on frozen eligibility. Category-membership contrasts are not latent accuracy; Unverifiable stays its own observed category.',
        'binary_sensitivity':'Correct=1/Incorrect=0; Unverifiable unknown, with signed unknown bounds and evaluable-only estimates.',
        'boundary_policies':{
            'boundary_conservative':'Original AMBIGUOUS unit remains unknown numerically, with its adopted rating retained in distributions. Other 191 units use existing identifiable spans, not invented human Stage B PASS labels.',
            'confirmed_span_sensitivity':'All 192 adopted semantic judgments on the original unmodified supplied spans; not new boundary adjudication.'},
        'legacy_importer':'Separate versioned semantic-only adoption adapter: user confirms existing 48-column proposals, not previously unfilled Stage B fields. Old two-stage importer/contract retained unchanged.',
        'task_success':'Exploratory diagnostic: FULL_ANSWER AND Correct AND complete source component coverage; never substitutes for factual consistency.',
        'component_limit':'Source numerator/denominator adopted unchanged; occurrences in an uncommitted promise do not establish delivery or support.',
        'ordinal_sensitivity':'Score thresholds >=2, >=3, >=4, >=5 under all nine contrasts. Monotone ordinal sensitivity, not an interval-scale assumption.',
        'sampling':'24 paired cases in 12 whole-speaker bundles; 11 temporal cases in 9 speakers. Case-weighted mean; no C0-correct filter.',
        'unknowns':'Missing label, Unverifiable, frozen N/A, incompleteness and boundary ambiguity are distinct; no unknowns imputed as errors.',
        'uncertainty':'Exploratory empirical percentile intervals, no multiplicity/significance/population guarantee. Also leave-one-speaker-out and family contribution tables.',
        'neutral_controls':'OPEN; no neutral-adjusted contrasts','source_hashes':{**prior.source_hashes(),str(Path(__file__).resolve().relative_to(Path.cwd())).replace('\\','/'):digest(Path(__file__))}}


def register(output=PUBLIC, final=FINAL):
    if output.exists() or final.exists():raise FileExistsError('Refuse to overwrite annotation registration')
    a,b,_,packet=prior.audit_package()
    if digest(SOURCE)!=SOURCE_SHA:raise ValueError('Confirmed source bytes differ from inspected proposal')
    rows=core.csv_records(SOURCE)
    check=validate_proposals(a,rows)
    identity=core.offline_preflight()  # File hashing and saved tokenizer reconciliation only.
    inventory=core.load(prior.OLD/'execution_inventory_v1.json')
    for path,pin in inventory['run_artifact_hashes'].items():
        if digest(Path(path))!=pin:raise ValueError('Original calibration artifact differs: '+path)
    # Source confirmation is expressly supplied by the researcher in this task.
    output.mkdir(parents=True,exist_ok=False)
    write_csv(final,registration_rows(rows))
    sources=[SOURCE,prior.STAGE_A,prior.STAGE_B,
        prior.AUDIT/'review_support/PersonaSLM_P1b_priority_semantic_review_UNCONFIRMED_v1.csv',
        Path('docs/PersonaSLM_P1b_AI_semantic_review_audit_UNCONFIRMED_v1.md')]
    instruction={'version':VERSION,**PROVENANCE,'confirmation_source':'Current researcher instruction; no signature or independent authentication claimed',
        'verbatim_authorization_excerpt':'The researcher, Yaxin ZHENG, has explicitly reviewed and approved all 192 proposed semantic annotation records.',
        'confirmed_response_ids':[r['anonymous_response_id'] for r in rows],'confirmed_source_sha256':digest(SOURCE),
        'human_review_timestamp':None,'condition_labels_masked':True,'perfect_blinding':False,
        'independent_human_annotators':1,'inter_annotator_agreement':None,
        'prior_experimental_knowledge':'Not independently established','boundary_adjudication':'No additional Stage B human ratings supplied; do not infer them',
        'notes_origin':'Original AI-assisted notes/uncertainties/evidence adopted as supplied; source blank human fields retained'}
    atomic_json(output/'researcher_confirmation_v1.json',instruction)
    atomic_json(output/'offline_identity_v1.json',identity)
    atomic_json(output/'factorial_specification_v2.json',specification())
    reg={'version':VERSION,'registered_utc':utc_now(),**PROVENANCE,'count':192,'packet_integrity':packet,'validation':check,
        'sources':{p.as_posix():digest(p) for p in sources},'final_annotation':{'path':final.as_posix(),'sha256':digest(final)},
        'dataset_sha256':core.DATA_SHA,'dataset_version':core.load(core.DATA).get('version'),
        'evaluation_policy':'separate_axes_policy_v1','response_policy':'response_status_v1',
        'semantic_routing':'p1b_manual_semantic_routing_proposed_v1','git':prior.git_state(),
        'files':{p.name:digest(p) for p in output.iterdir() if p.is_file()},'source_hashes':specification()['source_hashes'],
        'calibration_artifact_hashes_verified':len(inventory['run_artifact_hashes']),
        'new_inference':0,'treatment_join_performed':False}
    atomic_json(output/'registration_v1.json',reg)
    return {'registered':192,'annotation_sha256':digest(final),'treatment_join_performed':False}


def load_registered(folder=PUBLIC):
    reg=core.load(folder/'registration_v1.json')
    if reg.get('version')!=VERSION or reg.get('review_status')!='RESEARCHER_CONFIRMED':
        raise ValueError('Registered researcher confirmation required before unblinding')
    for p,h in reg['sources'].items():
        if digest(Path(p))!=h:raise ValueError('Original review source changed: '+p)
    for name,h in reg['files'].items():
        if Path(name).name!=name or digest(folder/name)!=h:raise ValueError('Registration metadata changed')
    final=Path(reg['final_annotation']['path'])
    if digest(final)!=reg['final_annotation']['sha256']:raise ValueError('Final annotation hash differs')
    a,b,mapping,packet=prior.audit_package()
    source=core.csv_records(SOURCE);validate_proposals(a,source)
    rows=core.csv_records(final)
    if rows!=registration_rows(source):raise ValueError('Adopted source decisions differ')
    spec=core.load(folder/'factorial_specification_v2.json')
    if spec['weights']!=prior.contrast_weights():raise ValueError('Contrast weights changed')
    for path,h in spec['source_hashes'].items():
        if digest(Path(path))!=h:raise ValueError('Frozen analysis dependency changed: '+path)
    byrow=prior.unique(rows); byb=prior.unique(b);cases={r['case_id']:r for r in core.load(core.DATA)['cases']}
    joined=[{**byrow[x['anonymous_response_id']],**x,'family':cases[x['case_id']]['family'],
             'designed_level':cases[x['case_id']]['designed_complexity_level'],
             'task_family':cases[x['case_id']]['task_family'],
             'structural_status':byb[x['anonymous_response_id']]['structural_status'],
             'raw_full_continuation':byb[x['anonymous_response_id']]['raw_full_continuation'],
             'raw_sha256':byb[x['anonymous_response_id']]['raw_sha256'],
             'boundary_evidence':'Frozen response_status_v1 and existing offline audit; not a new human structural annotation'} for x in mapping['responses']]
    return joined,spec


METRICS = ['factual_correct_label','factual_incorrect_label','factual_unverifiable_label',
    'temporal_correct_label','temporal_incorrect_label','temporal_unverifiable_label',
    'factual_assessable_binary','temporal_assessable_binary','response_relevance','conversational_coherence',
    'semantic_complete','task_success','component_coverage']
METRICS += [axis+'_ge_'+str(k) for axis in ('response_relevance','conversational_coherence') for k in range(2,6)]
METRICS += ['structural_'+s for s in ('COMPLETE','TRUNCATED','CROSS_TURN','AMBIGUOUS')]


def outcome(row,metric,policy):
    temporal=metric.startswith('temporal_')
    eligible=not temporal or row['applicable_temporal_consistency']=='true'
    lo,hi=(1,5) if metric in ('response_relevance','conversational_coherence') else (0,1)
    val=None;state='not_applicable'
    if eligible:
        state='scored'
        if metric.startswith('structural_'):
            val=float(row['structural_status']==metric[len('structural_'):])
        elif policy=='boundary_conservative' and row['structural_status']=='AMBIGUOUS':
            state='boundary_unresolved'
        elif metric.startswith(('factual_','temporal_')):
            axis='temporal_consistency' if temporal else 'factual_consistency'
            label=row['confirmed_'+axis]
            if not label:state='missing_judgment'
            elif metric.endswith('_binary'):
                if label=='Unverifiable':state='unverifiable'
                else:val=float(label=='Correct')
            else:
                target={'correct':'Correct','incorrect':'Incorrect','unverifiable':'Unverifiable'}[metric.split('_')[1]]
                val=float(label==target)
        elif '_ge_' in metric:
            axis,k=metric.rsplit('_ge_',1);val=float(int(row['confirmed_'+axis])>=int(k))
        elif metric in ('response_relevance','conversational_coherence'):
            val=float(row['confirmed_'+metric])
        elif metric=='semantic_complete':val=float(row['confirmed_semantic_completeness']=='YES')
        else:
            num,den=map(int,row['confirmed_component_coverage'].split('/'))
            if metric=='component_coverage':val=num/den
            elif metric=='task_success':
                val=float(row['confirmed_answer_delivery']=='FULL_ANSWER' and row['confirmed_factual_consistency']=='Correct' and num==den)
            else:raise ValueError('Unknown metric: '+metric)
    return {'eligible':eligible,'value':val,'state':state,'lo':lo,'hi':hi}


def interval(points,seed,repeats):
    """Fast whole-speaker resampling of sums/counts equals concatenated case sampling."""
    groups=defaultdict(list)
    for p in points:groups[p['persona_id']].append(p['difference'])
    blocks=[(sum(v for v in groups[k] if v is not None),sum(v is not None for v in groups[k])) for k in sorted(groups)]
    n=len(blocks); rng=random.Random(seed); values=[];empty=0
    if sum(c for _,c in blocks)==0 or n<2:return {'lower':None,'upper':None,'valid_resamples':0,'empty_resamples':0,'degenerate':None}
    for _ in range(repeats):
        sample=[blocks[rng.randrange(n)] for _ in range(n)]; count=sum(c for _,c in sample)
        if count:values.append(sum(v for v,_ in sample)/count)
        else:empty+=1
    values.sort();lo=quantile(values,.025);hi=quantile(values,.975)
    return {'lower':lo,'upper':hi,'valid_resamples':len(values),'empty_resamples':empty,'degenerate':lo==hi}


def summarize(points,metric,contrast,policy,family,all_cases,seed,repeats):
    eligible=[p for p in points if p['eligible']];values=[p['difference'] for p in eligible if p['difference'] is not None]
    ci=interval(eligible,seed,repeats) if family=='ALL' else {'lower':None,'upper':None,'valid_resamples':0,'empty_resamples':0,'degenerate':None}
    mean=lambda v:sum(v)/len(v) if v else None
    return {'policy':policy,'metric':metric,'contrast':contrast,'family':family,
        'eligible_cases':len(eligible),'evaluable_cases':len(values),'inapplicable_cases':all_cases-len(eligible),
        'unknown_cases':len(eligible)-len(values),'speaker_clusters':len({p['persona_id'] for p in eligible}),
        'evaluable_speaker_clusters':len({p['persona_id'] for p in eligible if p['difference'] is not None}),
        'estimate':mean(values),'positive_cases':sum(v>1e-12 for v in values),'negative_cases':sum(v< -1e-12 for v in values),
        'zero_cases':sum(abs(v)<=1e-12 for v in values),'unknown_lower':mean([p['unknown_lower'] for p in eligible]),
        'unknown_upper':mean([p['unknown_upper'] for p in eligible]),**ci,
        'uncertainty_scope':'Exploratory empirical cluster interval; not significance, population or simultaneous coverage. Unknown bounds are not confidence intervals.'}


def analyze_rows(rows,spec,repeats=None):
    seed=spec['bootstrap_seed'];repeats=repeats or spec['bootstrap_replicates']
    cells=defaultdict(dict)
    for r in rows:
        if r['condition'] in cells[r['case_id']]:raise ValueError('Duplicate factorial cell')
        cells[r['case_id']][r['condition']]=r
    for block in cells.values():
        if set(block)!=set(prior.contrast_weights()['S']):raise ValueError('Missing factorial cells')
        if len({(r['persona_id'],r['family']) for r in block.values()})!=1:raise ValueError('Case identity differs')
        for axis in core.AXES:
            if len({r['applicable_'+axis] for r in block.values()})!=1:raise ValueError('Within-case eligibility differs')
    points=[];summaries=[];loso=[]
    for policy in spec['boundary_policies']:
        for metric in METRICS:
            for contrast,weights in spec['weights'].items():
                blockpoints=[]
                for cid,block in sorted(cells.items()):
                    values={cond:outcome(r,metric,policy) for cond,r in block.items()}
                    eligible=all(v['eligible'] for v in values.values());needed=[c for c,w in weights.items() if w]
                    evaluable=eligible and all(values[c]['value'] is not None for c in needed)
                    lower,upper=prior.bounds(values,weights) if eligible else (None,None)
                    p={'policy':policy,'metric':metric,'contrast':contrast,'case_id':cid,
                       'persona_id':block['C0']['persona_id'],'family':block['C0']['family'],'eligible':eligible,'evaluable':evaluable,
                       'difference':sum(weights[c]*values[c]['value'] for c in needed) if evaluable else None,
                       'unknown_lower':lower,'unknown_upper':upper,'outcomes':values}
                    blockpoints.append(p)
                points.extend(blockpoints)
                for family in ['ALL']+sorted({p['family'] for p in blockpoints}):
                    subset=[p for p in blockpoints if family=='ALL' or p['family']==family]
                    summaries.append(summarize(subset,metric,contrast,policy,family,len(subset),seed,repeats))
                for speaker in sorted({p['persona_id'] for p in blockpoints}):
                    left=[p for p in blockpoints if p['persona_id']!=speaker and p['eligible']]
                    vals=[p['difference'] for p in left if p['evaluable']]
                    loso.append({'policy':policy,'metric':metric,'contrast':contrast,'omitted_speaker':speaker,
                        'eligible_cases':len(left),'evaluable_cases':len(vals),'remaining_speakers':len({p['persona_id'] for p in left}),
                        'estimate':sum(vals)/len(vals) if vals else None,
                        'unknown_lower':statistics.mean(p['unknown_lower'] for p in left) if left else None,
                        'unknown_upper':statistics.mean(p['unknown_upper'] for p in left) if left else None})
    coverage=[];groups=[]
    for groupfield in ('ALL','condition','family','case_id'):
        for group in (['ALL'] if groupfield=='ALL' else sorted({r[groupfield] for r in rows})):
            subset=[r for r in rows if groupfield=='ALL' or r[groupfield]==group]
            summary={'group_type':groupfield,'group':group,'responses':len(subset),'cases':len({r['case_id'] for r in subset}),
                'speakers':len({r['persona_id'] for r in subset}),
                **{axis:dict(Counter(r['confirmed_'+axis] for r in subset)) for axis in FIELDS},
                'structure':dict(Counter(r['structural_status'] for r in subset)),
                'task_success':sum(outcome(r,'task_success','confirmed_span_sensitivity')['value'] for r in subset)}
            groups.append(summary)
            for metric in METRICS:
                for policy in spec['boundary_policies']:
                    vals=[outcome(r,metric,policy) for r in subset]
                    scored=[v['value'] for v in vals if v['value'] is not None]
                    coverage.append({'group_type':groupfield,'group':group,'policy':policy,'metric':metric,
                        'eligible':sum(v['eligible'] for v in vals),'numerically_evaluable':len(scored),
                        'not_applicable':sum(not v['eligible'] for v in vals),'analysis_states':dict(Counter(v['state'] for v in vals)),
                        'mean_evaluable':sum(scored)/len(scored) if scored else None})
    cross=[]
    for axis in ('semantic_completeness','answer_delivery','factual_consistency','temporal_consistency'):
        for (status,label),n in sorted(Counter((r['structural_status'],r['confirmed_'+axis]) for r in rows).items()):
            cross.append({'axis':axis,'structural_status':status,'semantic_label':label,'count':n})
    joint=[{'factual':k[0],'delivery':k[1],'completeness':k[2],'structure':k[3],'count':n}
           for k,n in sorted(Counter((r['confirmed_factual_consistency'],r['confirmed_answer_delivery'],r['confirmed_semantic_completeness'],r['structural_status']) for r in rows).items())]
    return {'version':ANALYSIS,'responses':len(rows),'cases':len(cells),'speakers':len({r['persona_id'] for r in rows}),
        'seed':seed,'repeats':repeats,'case_contrasts':points,'effect_summary':summaries,'speaker_sensitivity':loso,
        'metric_coverage':coverage,'group_summaries':groups,'structural_semantic_crosstabs':cross,'joint_table':joint,
        'factual_temporal_overlap':dict(Counter(r['confirmed_factual_consistency']+' / '+r['confirmed_temporal_consistency'] for r in rows)),
        'new_inference':0,'neutral_adjusted_contrasts':False,'significance_claims':False}


def temporal_errors(rows):
    records=[]
    for r in rows:
        if r['confirmed_temporal_consistency']!='Incorrect':continue
        # Descriptive error taxonomy is keyed to independently known task definitions,
        # not the treatment assignment. Quotations/claims retained in full for audit.
        family=r['family']
        kind={'C':'Incorrect interval/boundary-state selection',
              'E':'Outdated residence or linked hub/day selected',
              'G':'Wrong past/current pickup-site selection',
              'H':'Outdated follow-up desk selected'}.get(family,'Other temporal contradiction; inspect source')
        records.append({'response_id':r['anonymous_response_id'],'case_id':r['case_id'],'condition':r['condition'],
            'family':family,'question':r['current_question'],'evaluation_date':r['evaluation_date'],
            'trusted_evidence':r['trusted_evidence'],'expected_components':r['reference_answer_json'],
            'model_claim_verbatim':r['raw_first_reply'],'source_quotes_verbatim':r['ai_case_specific_evidence'],
            'adopted_explanation':r['ai_candidate_reasoning'],'source_uncertainty':r['ai_candidate_uncertainty'],
            'error_description':kind,'description_origin':'Post-review tool-assisted task-family grouping; not new human labels or a causal mechanism'})
    return records


def analyze(output,registration=PUBLIC):
    if output.exists():raise FileExistsError('Refuse to overwrite analysis')
    rows,spec=load_registered(registration)
    result=analyze_rows(rows,spec)
    output.mkdir(parents=True,exist_ok=False)
    atomic_json(output/'analysis_v1.json',result)
    atomic_json(output/'unblinded_analysis_dataset_v1.json',{'version':ANALYSIS,'rows':rows})
    for key in ('case_contrasts','effect_summary','speaker_sensitivity','metric_coverage','group_summaries','structural_semantic_crosstabs','joint_table'):
        write_csv(output/(key+'_v1.csv'),result[key])
    write_csv(output/'temporal_error_evidence_v1.csv',temporal_errors(rows))
    manifest={'version':ANALYSIS,'created_utc':utc_now(),'registration_sha256':digest(registration/'registration_v1.json'),
        'specification_sha256':digest(registration/'factorial_specification_v2.json'),'git':prior.git_state(),
        'files':{p.name:digest(p) for p in output.iterdir()},'source_sha256':digest(Path(__file__)),'new_inference':0}
    atomic_json(output/'analysis_reproducibility_manifest_v1.json',manifest)
    return {k:result[k] for k in ('responses','cases','speakers','new_inference')}


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('register')
    a=sub.add_parser('analyze');a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(register() if args.action=='register' else analyze(args.output)))
