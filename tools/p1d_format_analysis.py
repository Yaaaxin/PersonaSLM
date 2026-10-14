"""Reconstruct format diagnostics and explicit UNCONFIRMED AI proposals; no generation."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import random
import statistics
import time
import p1d_format_calibration as f
from p1d_design import csvwrite
from p1d_budget_analysis import quantile,bounds_difference
from p1c_boundary_baselines import extract,METHODS

OUT=f.OUT/'analysis_v1'
NOTES={
 'p1d_dev_00_0':('Mira Fenwick','Locker 111 from D00F04, valid April-June; the November Locker 105 is not requested.','A future ledger-use promise does not assert Mira\'s assignment.'),
 'p1d_dev_01_0':('Owen Bellamy','Locker 105 and 10:00-11:00 from D01F04/D01F05, both valid on May 15.','The added generic statement about historical quotation intervals repeats the explicit prompt policy; neither requested attribute is delivered.'),
 'p1d_dev_02_0':('Tessa Northwick','D02F04 gives Locker 113; D02F06 gives Hub 216; D02F07 gives Exit 316 for May 15.','The interval-policy echo supplies neither a starting locker nor the requested hub/exit. The later user question is not an answer.'),
 'p1d_dev_03_0':('Quinn Fairchild','The fixed context resolves that volunteer to Quinn, not persona Nolan. D03F20/D03F21 give Locker 102 and 10:00-11:00.','A generic historical-policy statement does not resolve the contextual referent or provide the required two values.'),
 'p1d_dev_04_1':('Vera Ashcombe','D04F12/D04F13 give Locker 110 and 12:00-13:00 on November 15.','The interval-policy echo is supported as policy, but no November assignment/window is stated.'),
 'p1d_dev_05_1':('Arlo Kingsley','D05F12 -> D05F14 -> D05F15 gives Locker 106 -> Hub 213 -> Exit 316. Arwen is a different entity.','That volunteer in the promise links to Arlo but supplies no chain result. The excluded continuation asks about Arwen; a simulated user question is not an assistant factual assertion.'),
 'p1d_dev_06_1':('Cleo Westlake','The context names Cleo. D06F12/D06F13 give Locker 112 and 12:00-13:00 on November 15.','The promise maintains the contextual referent but neither required value is delivered.'),
 'p1d_dev_07_1':('Ellis Fairmont','D07F12 gives Locker 112 on November 15; D07F04 is the older Locker 113.','The promise does not assert either the requested current locker or an expired alternative.')}

def build():
    integrity=f.audit();f.require(integrity['results']==16,'Incomplete authorized diagnostic')
    f.require(integrity==f.load(f.OUT/'execution_integrity_v1.json'),'Saved audit mismatch')
    cases={c['case_id']:c for c in f.load(f.b.DEV/'development_examples_v5.json')['cases']}
    old={r['request_id']:r for r in f.load(f.b.OUT/'analysis_v1/provisional_analysis_dataset_v1.json')}
    applicability=f.load('docs/validation/p1d/proposed_v1/metric_applicability_v2.json')
    # Exact per-case proposals after reading every saved first reply and evidence.
    # No assertion of condition-blind assessment: diagnostic labels were visible.
    order=list(range(16));random.Random(716711).shuffle(order)
    anon={i:f'FD{j+1:03d}' for j,i in enumerate(order)}
    ratings=[];mapping=[];boundary=[];comparison=[];baselines=[]
    for i,item in enumerate(integrity['rows']):
        q=item['request'];r=item['result'];c=cases[q['case_id']];text=r['response_status']['first_span']['text']
        subject,evidence,interpretation=NOTES[q['case_id']]
        policy='Historical quotations describe their stated intervals.' in text
        header='CURRENT QUESTION' if 'CURRENT QUESTION' in text else 'USER RESPONSE'
        expected=(' I will use the ledger for that volunteer.' if q['case_id'] in ('p1d_dev_05_1','p1d_dev_06_1') else ' I will use the trusted ledger for that date.')
        if policy:expected+=' Historical quotations describe their stated intervals.'
        f.require(text.strip()==(expected+'\n'+header).strip(),'Unreviewed text: do not auto-score a new output')
        components=[{'key':x['key'],'reference_value':x['value'],'source_id':x['source_id'],'presence':'ABSENT','support':'ABSENT',
            'evidence':f"No {x['key']} value is delivered in the frozen first span; requested evidence is {x['source_id']}."} for x in c['required_components']]
        rating={'anonymous_response_id':anon[i],'primary_text':text,'primary_text_sha256':f.th(text),'question':c['question'],
            'requested_date':c['query_date'],'evaluation_date':c['evaluation_date'],'trusted_evidence':c['trusted_evidence'],
            'fixed_context':c['fixed_context'],'persona_profile':c['persona_profile'],'reference_evidence':evidence,
            'factual':'Correct' if policy else 'Unverifiable','factual_reason':interpretation,
            'factual_alternative':'Unverifiable if a generic prompt-policy echo is outside material factual-claim scope.' if policy else 'No contradicted factual assertion; do not infer Incorrect from non-delivery.',
            'temporal':'Unverifiable','temporal_reason':f"No dated entity/value selection is asserted for {subject} on {c['query_date']}; general interval language is not a temporally evaluated answer.",
            'task_success':'Failure','task_reason':evidence+' All requested components are absent; an intention is not a delivered answer.',
            'components':components,'semantic_completeness':'NO','completeness_reason':'The response is a promise followed by a dangling section heading, not a partial or complete final answer.',
            'relevance':3,'relevance_reason':f"Ledger use acknowledges the evidence source for {subject}, but the requested lookup is wholly omitted (materially off-focus/incomplete action).",
            'relevance_alternative':4,'coherence':3,'coherence_reason':f"The promise connects to the fixed context, but the appended {header} heading switches discourse frame without completing that frame. This is separate from factual support and task delivery.",
            'coherence_alternative':'4 for a minor heading defect; 5 if a separately adjudicated heading-excluded prefix is evaluated.',
            'persona_fidelity':4,'persona_reason':('Brief direct wording without metaphor' if 'brief direct' in c['persona_profile'] else 'Calm grammatical sentence without slang')+f'; dangling {header} heading is a minor style defect, assessed independently of correctness.',
            'persona_alternative':5,'answer_truncation':'No visible answer fragment; stopping removes subsequent dialogue, not a demonstrated partly delivered answer.',
            'measurement_states':{'factual':'INTERPRETATION_UNCERTAIN' if policy else 'EVIDENCE_UNVERIFIABLE','temporal':'EVIDENCE_UNVERIFIABLE','task_success':'ASSESSABLE_NON_DELIVERY',
                'boundary':'IDENTIFIABLE_WITH_SECTION_HEADING_SCOPE_LIMITATION','missing':False,'not_applicable':False},
            'metric_applicability':{k:True for k in ('relevance','factual','temporal','coherence','task_success','component_coverage','semantic_completeness','persona_fidelity','structural_status')},
            'confidence':'High for non-delivery; moderate for ordinal anchors and generic-policy claim scope.',
            'annotation_origin':'AI_assisted_diagnostic_review_with_configuration_visible','review_status':'UNCONFIRMED','reviewer_id':'','researcher_decision':'','human_review_timestamp':None,
            'required_human_adjudication':'Review separate endpoints, generic-policy factual scope and heading ownership; no independent human review is claimed.'}
        ratings.append(rating)
        mapping.append({'anonymous_response_id':anon[i],'request_id':q['request_id'],'case_id':q['case_id'],'speaker_id':q['speaker_id'],'family':q['family'],'arm':q['diagnostic_arm'],'raw_text_sha256':r['raw_text_sha256']})
        alt=text.split('\n'+header)[0]
        boundary.append({'anonymous_response_id':anon[i],'original_status':r['response_status']['status'],'unit_identifiable':r['response_status']['unit_identifiable'],
            'raw':r['raw_response'],'native_termination':r['raw_termination'],'first_span':r['response_status']['first_span'],
            'parser_reason':r['response_status']['reasons'],'alternative_heading_excluded_prefix':alt,'alternative_sha256':f.th(alt),
            'interpretation':'Stop-arm AMBIGUOUS means bounded_reply_semantics_not_certified; it does not mean no recoverable first span. A section heading remains a discourse-scope limitation.',
            'alternative_semantic_completeness':'NO','alternative_task_success':'Failure','independent_boundary_truth':None,'researcher_decision':''})
        prev=old[q['historical_comparator_request_id']]
        comparison.append({'request_id':q['request_id'],'historical_request_id':prev['request_id'],'historical_request_sha256':q['historical_comparator_request_sha256'],
            'case_id':q['case_id'],'speaker_id':q['speaker_id'],'family':q['family'],'arm':q['diagnostic_arm'],
            'historical_first_text':prev['primary_text'],'new_first_text':text,'first_content_equal':prev['primary_text'].strip()==text.strip(),
            'historical_AI_factual':prev['factual'],'new_AI_factual':rating['factual'],'historical_AI_task':prev['task_success'],'new_AI_task':'Failure',
            'historical_latency':prev['latency_seconds'],'new_latency':r['latency_seconds'],'historical_vs_new':'NOT_CONTEMPORANEOUS_NOT_INDEPENDENT_REPLICATION'})
        for method in METHODS:
            span=extract(r['raw_response'],r['raw_termination'],method)
            view=r['raw_response'][span[0]:span[1]] if span else None
            baselines.append({'request_id':q['request_id'],'method':method,'candidate_span':span,'candidate_text':view,
                'primary_content_equal':view is not None and view.strip()==text.strip(),'independent_accuracy':None,
                'limitation':'Frozen baseline uses no declared custom stops; abstention on stop-arm outputs is configuration coverage, not empirical boundary error.'})
    joined=[{**r,**m,**{'latency_seconds':item['result']['latency_seconds'],'generated_tokens':item['result']['generated_tokens'],
        'stop_reason':item['result']['stop_reason'],'structural_status':item['result']['response_status']['status'],'unit_identifiable':item['result']['response_status']['unit_identifiable']}}
        for r,m,item in zip(ratings,mapping,integrity['rows'])]
    groups={arm:[r for r in joined if r['arm']==arm] for arm in f.ARMS};summary={}
    for arm,rows in groups.items():
        summary[arm]={'n':len(rows),'structural':dict(Counter(r['structural_status'] for r in rows)),
            'termination':dict(Counter(r['stop_reason'] for r in rows)),'first_response_identifiable':sum(r['unit_identifiable'] for r in rows),
            'generated_tokens':sum(r['generated_tokens'] for r in rows),'mean_latency_seconds':statistics.mean(r['latency_seconds'] for r in rows),
            'distributions':{k:dict(Counter(str(r[k]) for r in rows)) for k in ('factual','temporal','task_success','semantic_completeness','relevance','coherence','persona_fidelity')},
            'supported_components':0,'required_components':sum(len(r['components']) for r in rows),'diagnostic_qualification':False}
    paired=[]
    for case in f.b.CASE_IDS:
        a=next(r for r in joined if r['case_id']==case and r['arm']==f.ARMS[0]);z=next(r for r in joined if r['case_id']==case and r['arm']==f.ARMS[1])
        source=next(x['result']['raw_response'] for x in integrity['rows'] if x['request']['request_id']==a['request_id'])
        stopped=next(x['result']['raw_response'] for x in integrity['rows'] if x['request']['request_id']==z['request_id'])
        hits=[source.index(s) for s in f.STOPS if s in source];shadow=source[:min(hits)] if hits else None
        paired.append({'case_id':case,'speaker_id':a['speaker_id'],'family':a['family'],'first_text_exact_equal':a['primary_text']==z['primary_text'],
            'first_text_strip_equal':a['primary_text'].strip()==z['primary_text'].strip(),'stop_shadow_exact_equal':shadow==stopped,
            'latency_stop_minus_no_stop':z['latency_seconds']-a['latency_seconds'],'tokens_stop_minus_no_stop':z['generated_tokens']-a['generated_tokens'],
            'task_success_difference':0,'completeness_difference':0,'relevance_difference':z['relevance']-a['relevance'],
            'coherence_difference':z['coherence']-a['coherence'],'persona_fidelity_difference':z['persona_fidelity']-a['persona_fidelity'],
            'factual_Correct_label_incidence_difference':int(z['factual']=='Correct')-int(a['factual']=='Correct'),
            'factual_unknown_correctness_bounds':bounds_difference(1 if a['factual']=='Correct' else None,1 if z['factual']=='Correct' else None),
            'temporal_unknown_correctness_bounds':[-1,1]})
    rng=random.Random(716710);draws=[[rng.randrange(8) for _ in range(8)] for _ in range(10000)]
    uncertainty={}
    for metric in ('latency_stop_minus_no_stop','tokens_stop_minus_no_stop','task_success_difference','completeness_difference','factual_Correct_label_incidence_difference','relevance_difference','coherence_difference','persona_fidelity_difference'):
        values=[r[metric] for r in paired];boot=[statistics.mean(values[i] for i in d) for d in draws]
        uncertainty[metric]={'mean':statistics.mean(values),'bootstrap_percentile_95':[quantile(boot,.025),quantile(boot,.975)],
            'leave_one_speaker_out':[statistics.mean(values[:i]+values[i+1:]) for i in range(8)]}
    uncertainty.update(seed=716710,draws=10000,clusters=8,paired_cases=8,scope='Development sensitivity conditional on unconfirmed AI proposals; degenerate zero intervals are not evidence of no population effect. No confirmatory significance.',
        factual_all_eligible_unknown_difference_bounds=[statistics.mean(r['factual_unknown_correctness_bounds'][i] for r in paired) for i in (0,1)],
        temporal_all_eligible_unknown_difference_bounds=[-1,1],missing=0,unverifiable_not_incorrect=True,
        case_pairing='One case per speaker; all paired contributions retained; no available-cell renormalization')
    # Independent metric inputs/justifications are not independently generated ratings.
    metric_diagnostic={'n':16,'relevance_coherence_concordance':sum(r['relevance']==r['coherence'] for r in ratings),
        'factual_correct_task_failure':sum(r['factual']=='Correct' and r['task_success']=='Failure' for r in ratings),
        'variance':{k:statistics.pvariance(r[k] for r in ratings) for k in ('relevance','coherence','persona_fidelity')},
        'limitations':'All three ordinal measures have zero observed variance here. Separate constructs and evidence fields do not prove empirical discriminant validity or independent human scoring.'}
    return {'primary_AI_proposals_UNCONFIRMED_v1.json':sorted(ratings,key=lambda r:r['anonymous_response_id']),
        'withheld_mapping_v1.json':mapping,'boundary_review_v1.json':boundary,'provisional_analysis_dataset_v1.json':joined,
        'historical_exact_id_comparison_v1.json':comparison,'boundary_baseline_comparison_v1.json':baselines,
        'paired_case_contributions_v1.json':paired,'summary_v1.json':summary,'paired_uncertainty_v1.json':uncertainty,
        'metric_discrimination_v1.json':metric_diagnostic,
        'annotation_provenance_v1.json':{'origin':'AI_assisted_configuration_aware_item_review','human_ratings':0,'researcher_adoption':False,
            'masking':'Initial AI assessment was not blind to format arm; subsequent reviewer CSV omits configuration/mapping. Linguistic and whitespace cues can remain.',
            'originals_preserved':True,'applicability_source_sha256':f.sha256(Path('docs/validation/p1d/proposed_v1/metric_applicability_v2.json')),
            'execution_integrity_sha256':f.sha256(f.OUT/'execution_integrity_v1.json'),
            'code_sha256':f.sha256(OUT/'source_snapshot_v1.py') if (OUT/'source_snapshot_v1.py').exists() else f.sha256(Path(__file__)),
            'historical_AI_source_sha256':f.sha256(f.b.OUT/'analysis_v1/primary_AI_proposals_UNCONFIRMED_v1.csv'),
            'rubric_changed':False,'generic_policy_sensitivity':'Factual Correct -> Unverifiable for eight responses if generic policy echoes are excluded from material claims; task remains Failure.'}}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=build()
    for name,value in outputs.items():
        # JSON arrays reconstruct Python tuples as lists; compare canonical JSON values.
        if args.verify:f.require(f.load(OUT/name)==json.loads(json.dumps(value)),'Reconstruction mismatch '+name)
        else:f.save(OUT/name,value)
    if not args.verify:
        for name in ('primary_AI_proposals_UNCONFIRMED_v1','boundary_review_v1','paired_case_contributions_v1','historical_exact_id_comparison_v1'):
            csvwrite(OUT/(name+'.csv'),outputs[name+'.json'])
        blind=[]
        for r in outputs['primary_AI_proposals_UNCONFIRMED_v1.json']:
            blind.append({k:r[k] for k in ('anonymous_response_id','primary_text','question','requested_date','evaluation_date','trusted_evidence','fixed_context','persona_profile')}|
                {k:'' for k in ('reviewer_id','factual','temporal','relevance','coherence','task_success','component_coverage','semantic_completeness','persona_fidelity','claim_evidence','temporal_evidence','delivery_evidence','relevance_evidence','coherence_evidence','uncertainty','adjudication')})
        csvwrite(OUT/'independent_review_without_AI_scores_v1.csv',blind)
    print(json.dumps({'verification_only':args.verify,'outputs':len(outputs),'summary':outputs['summary_v1.json'],'metrics':outputs['metric_discrimination_v1.json']},indent=2))

if __name__=='__main__':main()
