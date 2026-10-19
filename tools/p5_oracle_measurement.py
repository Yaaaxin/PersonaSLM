"""AI-assisted item review of eight immutable P5 outputs, never human adoption."""
from collections import Counter
import argparse
import json
from pathlib import Path
import random
import statistics
import p5_oracle_run as p
from p1d_design import csvwrite
from p1d_budget_analysis import quantile

OUT=p.OUT/'measurement_v1'
REVIEWS={
'p1d_dev_04_1':('Locker 110; 12:00-13:00.',
 'D04F12 and D04F13 jointly support Locker 110 and 12:00-13:00, inclusive October-December.',
 'Elliptical field labels inherit Vera and November 15 from the question. Both requested values are delivered.',
 'Two directly requested fields; no irrelevant expansion.','Parallel clauses fit the collection-note dialogue.',
 'Brief direct clauses without decorative metaphor.'),
'p1d_dev_03_0':('On 2048-05-15, Quinn Fairchild had locker Locker 102 and pickup window 10:00-11:00.',
 'D03F20/D03F21 support both values in April-June; fixed context identifies Quinn rather than persona Nolan.',
 'Correct context referent, explicit requested date, and both required values. This reply is byte-identical to its historical counterpart.',
 'Names exactly the requested date, volunteer and two attributes.','The pronoun that volunteer is resolved consistently.',
 'Calm full sentence without slang; duplicated locker label is a minor lexical redundancy, not incompatible style.'),
'p1d_dev_01_0':('On 2048-05-15, Owen Bellamy was assigned locker 105 and pickup window 10:00-11:00.',
 'D01F04/D01F05 assign Locker 105 and 10:00-11:00 in April-June.',
 'Lower-case locker 105 is a transparent surface variant of Locker 105, not a different entity. Both fields are correct for the explicit date.',
 'Direct answer to both fields.','Subject and date remain consistent with fixed dialogue.',
 'Calm complete sentence without slang.'),
'p1d_dev_07_1':('Based on the trusted evidence provided, Ellis Fairmont was assigned Locker 112 during the period from October 1, 2048, through December 31, 2048. Since November 15, 2048, falls within this timeframe, the locker assigned to Ellis Fairmont on that specific date was Locker 112.',
 'D07F12 states Locker 112 for October 1-December 31; November 15 is inside this closed interval.',
 'The assignment and date-containment claim are both supported. Repeats the answer but still delivers the single requested component.',
 'Interval explanation remains directly relevant; no topic drift. Alternative 4 if redundant restatement is penalized.',
 'The second sentence follows consistently from the first; no invented temporal premise.',
 'Calm complete sentences; verbosity is not prohibited by this original profile.'),
'p1d_dev_05_1':("On 2048-11-15, Arlo Kingsley's locker is Locker 106. Following the path from Locker 106 to Hub 213, the hub is Hub 213. Following the path from Hub 213 to Exit 316, the exit is Exit 316.",
 'D05F12 -> D05F14 -> D05F15 supplies Locker 106 -> Hub 213 -> Exit 316, all valid October-December.',
 'Correct intermediate locker and both requested final chain nodes are supplied. Present tense is scoped by the explicit November date.',
 'Intermediate step supports the requested integration, rather than replacing the answer.',
 'Each sentence follows the previous entity; repeated hub/exit labels do not create contradictions.',
 'Complete calm sentences without slang; repeated path wording is compatible with the narrow style instruction.'),
'p1d_dev_02_0':("Tessa Northwick's locker is Locker 113.\nLocker 113's hub is Hub 216.\nHub 216's exit is Exit 316.",
 'D02F04 -> D02F06 -> D02F07 supplies Locker 113 -> Hub 216 -> Exit 316 for April-June.',
 'The three short statements inherit the requested May 15 date. Both final components appear; no unfinished sentence remains.',
 'All three clauses contribute to the requested chain.','Repeated entity links provide coherent continuity.',
 'Short direct clauses; no decorative metaphor. Line breaks alone are not a fidelity failure.'),
'p1d_dev_06_1':('Locker 112; pickup window 12:00-13:00.',
 'D06F12/D06F13 give Locker 112 and 12:00-13:00 for October-December; fixed context identifies Cleo.',
 'Two complete answer fields inherit the November date. No volunteer-role denial is made, removing the earlier factual-scope dispute for this output.',
 'Both requested fields are supplied without a detour.','Elliptical reference is resolved by the fixed conversation.',
 'Brief direct clauses with no metaphor.'),
'p1d_dev_00_0':('Locker 111.',
 'D00F04 gives Locker 111 for April-June, covering the requested May 15.',
 'A single elliptical locker answer fully satisfies this single-component question. Shortness is not incompleteness.',
 'Exactly the information requested.','A fragment is a coherent direct answer in this context.',
 'Brief direct answer; broader lexical/behavioral fidelity is not identifiable from two words.')}

def build(verify=False):
    def emit(path,value):
        if verify:p.require(p.load(path)==value,'Measurement reconstruction mismatch: '+str(path))
        else:p.save(path,value)
    audit=p.audit();p.require(audit['results']==8,'Do not infer missing observations')
    cases={c['case_id']:c for c in p.load(p.b.DEV/'development_examples_v5.json')['cases']}
    prior=p.load(p.s.OUT/'measurement_v1/AI_proposals_UNCONFIRMED_v1.json')
    mapping=p.load(p.s.OUT/'measurement_v1/withheld_mapping_v1.json')
    old_by_anon={r['anonymous_id']:r for r in prior};old={m['case_id']:old_by_anon[m['anonymous_id']] for m in mapping}
    historical={x['request']['case_id']:x for x in p.s.audit()['rows']}
    rows=[];paired=[];boundaries=[];engineering=[]
    for i,x in enumerate(audit['rows']):
        q=x['request'];r=x['result'];c=cases[q['case_id']];text,evidence,interpretation,rr,cc,lf=REVIEWS[c['case_id']]
        p.require(r['raw_response']==text and r['response_status']['first_span']['text']==text,'Unreviewed or changed span')
        components=[{**v,'present':True,'supported':True,'evidence_id':v['source_id']} for v in c['required_components']]
        row={'review_id':f'OR{i+1:03d}','case_id':c['case_id'],'request_id':q['request_id'],
            'text':text,'text_sha256':r['raw_text_sha256'],'question':c['question'],'requested_date':c['query_date'],
            'evaluation_date':c['evaluation_date'],'trusted_evidence':q['trusted_evidence'],
            'fixed_context':c['fixed_context'],'reference':q['reference'],
            'factual':'Correct','factual_evidence':evidence,'temporal':'Correct','temporal_evidence':interpretation,
            'task_success':'Success','task_evidence':'Requested final components are supplied: '+', '.join(v['key'] for v in components),
            'semantic_completeness':'YES','required_components':components,
            'relevance':5,'relevance_evidence':rr,'coherence':5,'coherence_evidence':cc,
            'narrow_style_fidelity':5,'style_evidence':lf,'linguistic_fidelity_validated':False,
            'behavioral_fidelity':None,'behavioral_state':'NOT_PREDEFINED_IN_THIS_DIAGNOSTIC',
            'original_structural_status':r['response_status']['status'],'identifiable_candidate':r['response_status']['unit_identifiable'],
            'uncertainty':'AI-only; explicit values and intervals strongly supported. Elliptical date/entity scope and ordinal scores remain human-adjudicable.',
            'alternative_interpretation':'Ordinal +/-1 where rubric precision warrants; narrow style compatibility is not independently validated broad Persona Fidelity.',
            'measurement_state':'ASSESSABLE_CANDIDATE_NATIVE_EOS_ALIAS_CAVEAT',
            'provenance':'AI_ASSISTED_ITEM_REVIEW_CONFIGURATION_VISIBLE_NOT_BLIND_INDEPENDENT_HUMAN',
            'researcher_decision':'','reviewer_id':'','human_timestamp':None}
        rows.append(row)
        native={**r['raw_termination'],'stop_type':'eog'};alt=p.b.classify_response(text,native)
        boundaries.append({'request_id':q['request_id'],'original':r['response_status'],'sensitivity_eos_alias':alt,
            'same_evaluated_text':alt['first_span']['text']==text,'generated_last_token':r['generated_token_ids'][-1],
            'independent_boundary_ground_truth':None,'researcher_decision':''})
        o=old[c['case_id']];hr=historical[c['case_id']]['result'];present=sum(v['present'] for v in o['required_components'])
        supported=sum(v['support']=='Supported' for v in o['required_components'])
        paired.append({'case_id':c['case_id'],'speaker_id':c['speaker_id'],'family':c['family'],
            'old_request_id':q['parent_instruct_request_id'],'old_request_sha256':q['parent_request_sha256'],
            'oracle_request_id':q['request_id'],'old_text_sha256':hr['raw_text_sha256'],'new_text_sha256':r['raw_text_sha256'],
            'old_factual':o['factual'],'oracle_factual':row['factual'],'old_temporal':o['temporal'],'oracle_temporal':row['temporal'],
            'old_task':o['task_success'],'oracle_task':row['task_success'],'old_complete':o['semantic_completeness'],
            'oracle_complete':'YES','old_present':present,'old_supported':supported,'oracle_present':len(components),
            'oracle_supported':len(components),'task_difference':1-int(o['task_success']=='Success'),
            'complete_form_difference':1-int(o['semantic_completeness']=='YES'),
            'old_latency_seconds':hr['latency_seconds'],'oracle_latency_seconds':r['latency_seconds'],
            'old_input_tokens':historical[c['case_id']]['request']['input_tokens'],'oracle_input_tokens':q['input_tokens'],
            'original_evidence_sufficient':True,'literal_reference_values_in_oracle':True,
            'inference':'Reference-aware evidence package, not a persona or pure retrieval effect.'})
        engineering.append({'request_id':q['request_id'],'order':q['order'],'seed':q['seed'],
            'prompt_sha256':q['prompt_sha256'],'input_token_ids_sha256':q['input_token_ids_sha256'],
            'input_tokens':q['input_tokens'],'generated_tokens':r['generated_tokens'],'latency_seconds':r['latency_seconds'],
            'native_stop':r['stop_reason'],'native_last_token':r['generated_token_ids'][-1],
            'raw_text_sha256':r['raw_text_sha256'],'request_sha256':r['request_sha256'],'raw_tokens_returned':len(r['generated_token_ids']),
            'original_status':r['response_status']['status'],'identifiable':r['response_status']['unit_identifiable']})
    rng=random.Random(716291);draws=[statistics.mean(rng.choice(paired)['task_difference'] for _ in paired) for _ in range(10000)]
    events=p.b.read_events(Path(audit['run_directory']));mem=[e['data'] for e in events if e['kind']=='memory_observation']
    summary={'version':'p5_oracle_AI_measurement_v1','phase':'P5','status':'AI_PROPOSED_NOT_HUMAN_CONFIRMED',
        'run_directory':audit['run_directory'],'attempts':8,'successful':8,'failed':0,'retries':0,'human_semantic_ratings':0,
        'native_stops':dict(Counter(r['native_stop'] for r in engineering)),
        'original_structural_status':dict(Counter(r['original_status'] for r in engineering)),
        'eos_alias_sensitivity':dict(Counter(r['sensitivity_eos_alias']['status'] for r in boundaries)),
        'identifiable_candidates':sum(r['identifiable'] for r in engineering),'cross_turn_observed':0,'changed_text_under_alias':0,
        'factual':dict(Counter(r['factual'] for r in rows)),'temporal':dict(Counter(r['temporal'] for r in rows)),
        'task_success':dict(Counter(r['task_success'] for r in rows)),'semantic_complete':8,
        'components_present':14,'components_supported':14,'components_required':14,
        'task_difference':statistics.mean(r['task_difference'] for r in paired),
        'speaker_resampling_sensitivity_95':[quantile(draws,.025),quantile(draws,.975)],
        'uncertainty_scope':'Eight purposive speakers, one case each, shared construction; resampling sensitivity is not population coverage or a confirmatory test.',
        'mean_latency_seconds':statistics.mean(r['latency_seconds'] for r in engineering),
        'total_generated_tokens':sum(r['generated_tokens'] for r in engineering),
        'peak_process_working_set_observed':max((m.get('process',{}).get('peak_working_set',0) for m in mem),default=None),
        'memory_observations':len(mem),'oracle_headroom_gate':'AI_PROPOSED_PASS_8_IDENTIFIABLE_COMPLETE_ANSWERS',
        'main_P1d_decision':'NO_GO','causal_identification':'Package-level reference-aware evidence reduction; content/length/positions/salience jointly vary; both evidence sets sufficient.'}
    emit(OUT/'AI_proposals_UNCONFIRMED_v1.json',rows)
    emit(OUT/'paired_historical_comparison_v1.json',paired)
    emit(OUT/'boundary_alias_sensitivity_v1.json',boundaries);emit(OUT/'summary_v1.json',summary)
    emit(p.OUT/'engineering_inventory_v1.json',engineering)
    blind=[{k:r[k] for k in ('review_id','question','requested_date','evaluation_date','trusted_evidence','fixed_context','text')}|
           {k:'' for k in ('factual','temporal','task_success','semantic_completeness','relevance','coherence','evidence_citations','reviewer_id','decision','timestamp')} for r in rows]
    random.Random(716292).shuffle(blind)
    if not verify:
        csvwrite(OUT/'AI_proposals_UNCONFIRMED_v1.csv',rows)
        csvwrite(OUT/'paired_historical_comparison_v1.csv',paired)
        csvwrite(OUT/'independent_review_without_scores_v1.csv',blind)
    print(json.dumps({'reconstruction':'PASS','new_inference':0} if verify else summary,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args();build(args.verify)
