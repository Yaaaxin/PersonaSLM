"""Item-specific AI proposals on eight completed outputs; no human adoption or generation."""
from collections import Counter
import json
from pathlib import Path
import random
import statistics
import p1d_instruct_smoke as s
from p1d_design import csvwrite
from p1d_budget_analysis import quantile

OUT=s.OUT/'measurement_v1'
JUDGMENTS={
'p1d_dev_00_0':dict(text='Locker 106',factual='Incorrect',temporal='Incorrect',task='Failure',complete='YES',present=1,supported=0,rr=5,cc=5,lf=5,
 evidence='D00F00 supports Locker 106 only January-March; D00F04 gives Locker 111 for May 15.',
 interpretation='Elliptical direct answer inherits the requested date; it delivers a complete but wrong locker.',
 rr_reason='Directly answers the requested locker without detour.',cc_reason='A short answer fits the collection-note context.',lf_reason='Brief direct wording; no decorative metaphor.'),
'p1d_dev_01_0':dict(text='Owen Bellamy had locker Locker 106 and pickup window 09:00-10:00 on 2048-05-15.',factual='Incorrect',temporal='Incorrect',task='Failure',complete='YES',present=2,supported=0,rr=5,cc=5,lf=5,
 evidence='D01F00/D01F01 are January-March; D01F04/D01F05 give Locker 105 and 10:00-11:00 for May.',
 interpretation='Both requested fields are delivered, but explicitly assigned to the wrong interval.',
 rr_reason='Names the requested subject, date and both fields.',cc_reason='Maintains the fixed referent and grammatical dialogue continuation.',lf_reason='Calm complete sentence without slang.'),
'p1d_dev_03_0':dict(text='On 2048-05-15, Quinn Fairchild had locker Locker 102 and pickup window 10:00-11:00.',factual='Correct',temporal='Correct',task='Success',complete='YES',present=2,supported=2,rr=5,cc=5,lf=5,
 evidence='Fixed context names Quinn, not persona Nolan; D03F20/D03F21 establish Locker 102 and 10:00-11:00 during April-June.',
 interpretation='Resolves the context referent and supplies both supported requested values.',
 rr_reason='All requested information is directly delivered.',cc_reason='Correctly carries that volunteer from the fixed context.',lf_reason='Calm full sentence, no slang.'),
'p1d_dev_04_1':dict(text='Locker 111; pickup window 09:00-10:00.',factual='Incorrect',temporal='Incorrect',task='Failure',complete='YES',present=2,supported=0,rr=5,cc=5,lf=5,
 evidence='D04F00/D04F01 describe January-March. D04F12/D04F13 give Locker 110 and 12:00-13:00 for November.',
 interpretation='A complete two-field answer inherits the current requested November date; obsolete values are incorrect for it.',
 rr_reason='Both requested fields appear without unrelated content.',cc_reason='Ellipsis is coherent with the prior collection request.',lf_reason='Brief direct clauses, no decorative metaphor.'),
'p1d_dev_07_1':dict(text='Based on the trusted ledger for the date 2048-11-15, Ellis Fairmont had locker Locker 112.',factual='Correct',temporal='Correct',task='Success',complete='YES',present=1,supported=1,rr=5,cc=5,lf=5,
 evidence='D07F12 assigns Locker 112 from October 1 through December 31 inclusive.',
 interpretation='The explicit subject/date/value tuple matches the requested interval.',
 rr_reason='Directly provides the requested assignment.',cc_reason='Continues the Ellis collection-note context.',lf_reason='Calm complete sentence without slang.'),
'p1d_dev_05_1':dict(text='On 2048-11-15, Arlo Kingsley was not recorded in the ledger. The trusted evidence only documents his presence in lockers and pickup windows from January 1, 2048, through December 31, 2048. Since the date in question falls outside the range of the available records, no specific locker, hub, or exit can be identified for Arlo Kingsley on that day.',factual='Incorrect',temporal='Incorrect',task='Failure',complete='NO',present=0,supported=0,rr=3,cc=3,lf=5,
 evidence='D05F12 -> D05F14 -> D05F15 establishes Locker 106 -> Hub 213 -> Exit 316 for November. November 15 lies inside January 1-December 31.',
 interpretation='An explicit unnecessary abstention includes demonstrably false evidence-absence and date-range claims; not mere Unverifiable. The refusal is a complete utterance but delivers no requested component.',
 rr_reason='Addresses availability instead of supplying the requested hub and exit.',cc_reason='The outside-range inference contradicts its own stated annual range.',lf_reason='Calm grammatical sentences without slang; factual falsehood is not a style defect.'),
'p1d_dev_02_0':dict(text='Tessa Northwick is not present on 2048-05-15. Her valid records for this date are:\n- Locker 107 (valid 2048-10-01 through 2048-12-31)\n- Pickup window 12:00-13:00\n\nThere is no record of Tessa Northwick at a locker or hub on May 1',factual='Incorrect',temporal='Incorrect',task='Failure',complete='PARTIAL',present=0,supported=0,rr=3,cc=2,lf=2,
 evidence='D02F04 -> D02F06 -> D02F07 establishes Locker 113 -> Hub 216 -> Exit 316 for May. D02F12/D02F13 are October-December, not May.',
 interpretation='False absence assertion and wrong interval assignment precede a visibly unfinished date. True quoted October dates do not repair their false application to May. Truncation is not itself the basis of factual Incorrect.',
 rr_reason='Discusses wrong locker/window information and omits both requested chain outputs.',cc_reason='Inconsistent absence/valid-record claims and unfinished final sentence disrupt discourse.',lf_reason='Extended list and repetition depart from brief direct clauses; no metaphor. Alternative 3 if the list is considered acceptably concise.'),
'p1d_dev_06_1':dict(text='Cleo Westlake is not a volunteer.',factual='Incorrect',temporal='Unverifiable',task='Failure',complete='NO',present=0,supported=0,rr=2,cc=3,lf=5,
 evidence='The fixed prompt persona stipulates Cleo is a fictional volunteer; fixed context requests her collection note. D06F12/D06F13 provide Locker 112 and 12:00-13:00.',
 interpretation='Denies a stipulated role instead of answering. Factual alternative: Unverifiable if the adopted factual scope excludes persona-role stipulations outside ledger attributes. No temporal proposition is asserted.',
 rr_reason='Subject-related denial does not address the locker/window request.',cc_reason='Contradicts the established volunteer referent, although the sentence is intelligible.',lf_reason='Brief direct clause without metaphor; role/factual disagreement is scored separately.')}

def build():
    integrity=s.audit();s.require(integrity['results']==8,'Do not score absent outputs')
    cases={c['case_id']:c for c in s.load(s.b.DEV/'development_examples_v5.json')['cases']}
    old={r['request_id']:r for r in s.load(s.b.OUT/'analysis_v1/provisional_analysis_dataset_v1.json')}
    rows=[];mapping=[];boundary=[];paired=[]
    ids=list(range(8));random.Random(716801).shuffle(ids)
    for i,item in enumerate(integrity['rows']):
        q=item['request'];r=item['result'];c=cases[q['case_id']];j=JUDGMENTS[q['case_id']]
        s.require(r['raw_response']==j['text'],'Unreviewed output: refuse scoring')
        anon=f'IS{ids[i]+1:03d}'
        components=[]
        for k,comp in enumerate(c['required_components']):
            components.append({**comp,'present':k<j['present'],'support':'Supported' if k<j['supported'] else 'Contradicted' if k<j['present'] else 'Absent'})
        rows.append({'anonymous_id':anon,'primary_text':r['response_status']['first_span']['text'],'text_sha256':r['first_reply_sha256'],
            'question':c['question'],'requested_date':c['query_date'],'evaluation_date':c['evaluation_date'],
            'trusted_evidence':c['trusted_evidence'],'fixed_context':c['fixed_context'],'persona_profile':c['persona_profile'],
            'factual':j['factual'],'temporal':j['temporal'],'task_success':j['task'],'semantic_completeness':j['complete'],
            'required_components':components,'relevance':j['rr'],'relevance_evidence':j['rr_reason'],'coherence':j['cc'],
            'coherence_evidence':j['cc_reason'],'narrow_style_fidelity':j['lf'],'fidelity_evidence':j['lf_reason'],
            'behavioral_fidelity':None,'behavioral_state':'NOT_PREDEFINED_IN_THIS_SMOKE_NO_RETROACTIVE_APPLICABILITY',
            'supporting_evidence':j['evidence'],'interpretation':j['interpretation'],
            'alternatives':'Ordinal scores +/-1 require independent rubric adjudication. Arlo/Cleo refusals can be complete utterances while requested semantic answer completeness is NO. Cleo factual scope alternative is Unverifiable; Tessa remains Incorrect independent of its missing final span.',
            'uncertainty':'High confidence in literal values/component absence; human interpretation of completeness, role scope and ordinals remains pending.',
            'measurement_states':{'factual':'ROLE_SCOPE_INTERPRETATION' if q['case_id']=='p1d_dev_06_1' else 'ASSESSABLE',
                'temporal':'NO_TEMPORAL_CLAIM' if q['case_id']=='p1d_dev_06_1' else 'ASSESSABLE',
                'boundary':'BUDGET_CENSORED' if r['stop_reason']=='length' else 'NATIVE_EOS_TERMINATED',
                'annotation_missing':False},
            'review_status':'UNCONFIRMED','annotation_origin':'AI_assisted_item_review_model_configuration_visible',
            'reviewer_id':'','researcher_decision':'','human_review_timestamp':None})
        mapping.append({'anonymous_id':anon,'request_id':q['request_id'],'case_id':q['case_id'],'speaker_id':q['speaker_id'],'family':c['family']})
        native=dict(r['raw_termination'])
        if native.get('stop_type')=='eos':native['stop_type']='eog'
        compatible=s.b.classify_response(r['raw_response'],native)
        boundary.append({'anonymous_id':anon,'raw':r['raw_response'],'original':r['response_status'],
            'native_eos_token_present':r['generated_token_ids'][-1:]==[248046],
            'native_stop_alias_sensitivity':compatible,
            'sensitivity_changes_text':compatible['first_span']['text']!=r['response_status']['first_span']['text'],
            'note':'New runtime reports eos whereas frozen parser expects eog; normalization is a separately labeled sensitivity, not a historical-label replacement.',
            'independent_boundary_truth':None,'researcher_decision':''})
        previous=old[q['historical_base_request_id']]
        paired.append({'case_id':q['case_id'],'speaker_id':q['speaker_id'],'family':c['family'],
            'base_request_id':previous['request_id'],'base_request_sha256':q['historical_base_request_sha256'],
            'instruct_request_id':q['request_id'],'base_text':previous['primary_text'],'instruct_text':j['text'],
            'base_AI_task':previous['task_success'],'instruct_AI_task':j['task'],
            'task_difference':int(j['task']=='Success')-int(previous['task_success']=='Success'),
            'complete_answer_form_difference':int(j['complete']=='YES')-int(previous['semantic_completeness']=='YES'),
            'base_latency':previous['latency_seconds'],'instruct_latency':r['latency_seconds'],
            'causal_scope':'Noncontemporaneous model/template/quantization package; not pure post-training or persona effect.'})
    rng=random.Random(716802)
    draws=[statistics.mean(rng.choice(paired)['task_difference'] for _ in paired) for _ in range(10000)]
    summary={'requests':8,'successes':8,'failures':0,'native_stops':dict(Counter(x['result']['stop_reason'] for x in integrity['rows'])),
        'original_structural_status':dict(Counter(x['result']['response_status']['status'] for x in integrity['rows'])),
        'recoverable_first_spans':sum(x['result']['response_status']['unit_identifiable'] for x in integrity['rows']),
        'AI_distributions':{key:dict(Counter(str(r[key]) for r in rows)) for key in ('factual','temporal','task_success','semantic_completeness','relevance','coherence','narrow_style_fidelity')},
        'required_components':sum(len(r['required_components']) for r in rows),
        'present_components':sum(c['present'] for r in rows for c in r['required_components']),
        'supported_components':sum(c['support']=='Supported' for r in rows for c in r['required_components']),
        'mean_latency_seconds':statistics.mean(x['result']['latency_seconds'] for x in integrity['rows']),
        'generated_tokens':sum(x['result']['generated_tokens'] for x in integrity['rows']),
        'semantic_feasibility':'NOT_MET_AI_PROVISIONAL','main_validation':'NO_GO','human_ratings':0,
        'all_condition_SFH_execution_ready':False,'persona_effect_estimated':False,
        'paired_AI_task_difference':statistics.mean(r['task_difference'] for r in paired),
        'bootstrap_sensitivity':{'seed':716802,'draws':10000,'clusters':8,'interval':[quantile(draws,.025),quantile(draws,.975)],
            'limitation':'Purposive development speakers; descriptive sensitivity only, not population coverage or human-confirmed semantic effects.'},
        'leave_one_speaker_out_task':[statistics.mean(r['task_difference'] for r in paired if r['speaker_id']!=x['speaker_id']) for x in paired],
        'families':{family:{'n':sum(p['family']==family for p in paired),'AI_task_success':sum(p['family']==family and p['instruct_AI_task']=='Success' for p in paired)} for family in sorted({p['family'] for p in paired})}}
    return {'AI_proposals_UNCONFIRMED_v1.json':rows,'withheld_mapping_v1.json':mapping,
        'boundary_alias_sensitivity_v1.json':boundary,'matched_Base_comparison_v1.json':paired,'summary_v1.json':summary}

def main(verify=False):
    values=build()
    for name,value in values.items():
        if verify:s.require(s.load(OUT/name)==value,'Reconstruction differs: '+name)
        else:s.save(OUT/name,value)
    if not verify:
        csvwrite(OUT/'AI_proposals_UNCONFIRMED_v1.csv',values['AI_proposals_UNCONFIRMED_v1.json'])
        fields=('reviewer_id','factual','temporal','task_success','semantic_completeness','relevance','coherence','narrow_style_fidelity','evidence','uncertainty','decision')
        blank=[{**{k:r[k] for k in ('anonymous_id','primary_text','question','requested_date','trusted_evidence','fixed_context','persona_profile')},**{k:'' for k in fields}} for r in values['AI_proposals_UNCONFIRMED_v1.json']]
        csvwrite(OUT/'independent_review_without_scores_v1.csv',blank)
    print(json.dumps(values['summary_v1.json'],indent=2))

if __name__=='__main__':
    import sys
    main('--verify' in sys.argv)
