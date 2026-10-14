"""Offline P1c reconstruction, frozen structural contrasts and masked review packet."""
import argparse
import base64
from collections import Counter
import json
from pathlib import Path

import p1c_calibration as c
import p1c_paired_statistics as stats
import p1c_design as d
from personaslm.scientific_closure import reconcile_tokenizations

MASK_SEED=715005
PRESENTATION_SEED=715005


def frozen_review_order(plan):
    source=c.p.SOURCE/'protected_treatment_mapping_proposed_v1.json'
    mapping=c.load(source)
    d.require(mapping['seed']==MASK_SEED,'Frozen review seed differs')
    indexed={r['sequence_index']:r for r in plan['requests']}
    records=mapping['records']
    d.require(len(records)==72 and len({r['sequence_index'] for r in records})==72,'Frozen review mapping is not bijective')
    d.require(len({r['anonymous_response_id'] for r in records})==72,'Duplicate frozen review ID')
    for record in records:
        row=indexed[record['sequence_index']]
        d.require(record['request_identity']==[row['case_id'],row['condition']] and record['persona_id']==row['persona_id'],
                  'Frozen masked review assignment differs')
    return records


def prepare(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve prior analysis/review versions')
    audit=c.audit();audit2=c.audit()
    d.require(audit==audit2,'Offline reconstruction not reproducible')
    d.require(audit['attempted']==audit['raw_responses']==audit['results']==72,'Incomplete wave: retain partial run and report it first')
    source_check=c.p.verify_sources()
    claim=c.load(c.RUN_ROOT/'claim.json')
    d.require(c.sources()==claim['source_hashes'],'Execution source changed')
    d.require(d.sha(c.AUTHORIZATION)==claim['authorization_sha256'] and d.sha(c.REGISTRATION)==claim['registration_sha256'],
              'Approved registration changed')
    d.require(not c.approvals.validate_approval(c.load(c.AUTHORIZATION),c.REGISTRATION),'Approval no longer validates')
    plan=c.load(c.p.MANIFEST);data=c.load(plan['dataset']);cases={r['case_id']:r for r in data['cases']}
    transport_checks=[]
    for segment in audit['segments']:
        for name,digest in claim['source_hashes'].items():
            d.require(d.sha(Path(segment['path'])/'source_snapshot'/name)==digest,'Execution source snapshot changed: '+name)
        events=c.read_events(Path(segment['path']))
        starts=[e['data'] for e in events if e['kind']=='p1c_generation_started']
        sent=[e['data']['payload'] for e in events if e['kind']=='http_request' and e['data']['route']=='/completion']
        bodies=[json.loads(base64.b64decode(e['data']['body_base64']).decode('utf-8')) for e in events
                if e['kind']=='http_response' and e['data']['route']=='/completion' and e['data'].get('status')==200]
        native=[e['data']['response'] for e in events if e['kind']=='p1c_raw_generation']
        d.require(sent==[{**c.DECODING,'prompt':row['input_token_ids']} for row in starts],'Completion payload order/config differs')
        d.require(bodies==native,'Ordered raw HTTP bytes/native response differ')
        # The historical helper is deliberately tokenizer-only. Completion
        # payloads and raw bytes are audited separately above; retain the full
        # immutable journal and give this helper only its documented route.
        token_events=[e for e in events if e['kind'] in ('http_request','http_response') and e['data']['route']=='/tokenize']
        n=reconcile_tokenizations(token_events,[(r['prompt'],r['input_token_ids']) for r in plan['requests']])
        d.require(n==72,'Incomplete live tokenizer reconciliation')
        transport_checks.append({'segment':segment['path'],'token_arrays_verified':n,'ordered_raw_bytes_verified':len(bodies),'payloads_verified':len(sent)})
    rows=[r['result'] for r in audit['rows']]
    d.write_json(output/'execution_integrity_v1.json',audit)
    original_mapping=frozen_review_order(plan)
    ids={c.key(plan['requests'][r['sequence_index']]):r['anonymous_response_id'] for r in original_mapping}
    case_order=list(dict.fromkeys(r['request_identity'][0] for r in original_mapping))
    case_ids={x:f'CC{n+1:02d}' for n,x in enumerate(case_order)}
    semantic=[];structural=[];mapping=[]
    for result in rows:
        row=result['frozen_request'];case=cases[row['case_id']];rid=ids[result['request_key']]
        boundary=result['response_status']
        public={'review_version':'p1c_condition_masked_semantic_v1','anonymous_response_id':rid,
            'anonymous_case_id':case_ids[row['case_id']],'current_question':case['question'],
            'trusted_evidence':case['trusted_evidence'],'evaluation_date':case['evaluation_date'],
            'requested_date':case['requested_date'],'required_answer_components':case['reference']['components'],
            'reference_fact_ids':case['reference']['fact_ids'],'ground_truth_derivation':case['reference']['derivation'],
            'fixed_preceding_context':case['fixed_context'],'raw_first_reply':result['parsed_response'],
            'first_reply_sha256':result['first_reply_sha256'],
            **{'applicable_'+k:v for k,v in row['applicability'].items() if k!='structural_status'},
            'applicable_persona_fidelity':False,
            **{k:'' for k in ('human_response_relevance_1_to_5','human_factual_consistency','human_temporal_consistency',
                'human_conversational_coherence_1_to_5','human_task_success','human_component_coverage',
                'human_semantic_completeness','human_evidence_quotations','human_uncertainty','reviewer_notes',
                'reviewer_id','review_method','researcher_confirmation','review_timestamp')}}
        semantic.append(public)
        structural.append({'review_version':'p1c_structural_review_v1','anonymous_response_id':rid,
            'anonymous_case_id':public['anonymous_case_id'],'raw_first_reply':result['parsed_response'],
            'first_reply_sha256':result['first_reply_sha256'],'raw_full_continuation':result['raw_response'],
            'raw_text_sha256':result['raw_text_sha256'],'frozen_structural_status':boundary['status'],
            'unit_identifiable':boundary['unit_identifiable'],'native_termination':result['raw_termination'],
            'generated_tokens':result['generated_tokens'],'parser_trace':boundary,
            'human_extraction_validity':'','human_boundary_notes':'','human_disposition':'','reviewer_id':'','review_timestamp':''})
        mapping.append({'anonymous_response_id':rid,'anonymous_case_id':public['anonymous_case_id'],
            'request_key':result['request_key'],'case_id':row['case_id'],'persona_id':row['persona_id'],
            'condition':row['condition'],'factor_assignment':row['factor_assignment'],
            'prompt_sha256':row['prompt_sha256'],'first_reply_sha256':result['first_reply_sha256']})
    by_semantic_id={r['anonymous_response_id']:r for r in semantic}
    semantic=[by_semantic_id[r['anonymous_response_id']] for r in original_mapping]
    byid={r['anonymous_response_id']:r for r in structural}
    structural=[byid[r['anonymous_response_id']] for r in semantic]
    d.write_csv(output/'semantic_scoring_view_v1.csv',semantic)
    d.write_csv(output/'structural_review_view_v1.csv',structural)
    d.write_json(output/'protected_treatment_mapping_v1.json',{'access_policy':'Analysis-only. Keep separate from Stage A review distribution; this is file separation, not encryption.',
        'mask_seed':MASK_SEED,'presentation_seed':PRESENTATION_SEED,
        'original_mapping_sha256':d.sha(c.p.SOURCE/'protected_treatment_mapping_proposed_v1.json'),'rows':mapping})
    registry=c.load(c.p.SOURCE/'estimand_registry_proposed_v1.json')
    metrics={s:(lambda r,s=s:float(r['response_status']['status']==s)) for s in ('COMPLETE','TRUNCATED','CROSS_TURN','AMBIGUOUS')}
    metrics['first_reply_identifiable']=lambda r:float(r['response_status']['unit_identifiable'])
    metrics['budget_termination']=lambda r:float(r['stop_reason']=='length')
    comparisons=[]
    for metric,extract in metrics.items():
        units=[]
        for cid,case in sorted(cases.items()):
            values={r['frozen_request']['condition']:extract(r) for r in rows if r['frozen_request']['case_id']==cid}
            d.require(len(values)==6,'Six cells required')
            units.append({'case_id':cid,'speaker_id':case['persona_id'],'values':values})
        for name,weights in registry['weights'].items():
            calculated=stats.summarize(units,weights)
            d.require(calculated==stats.summarize(units,weights),'Statistical reconstruction differs')
            comparisons.append({'metric':metric,'contrast':name,**calculated})
    d.write_json(output/'structural_contrasts_v1.json',{'version':'p1c_structural_package_contrasts_v1','rows':comparisons,
         'semantic_effects_computed':False,'contrast_registry_sha256':d.sha(c.p.SOURCE/'estimand_registry_proposed_v1.json')})
    d.write_csv(output/'structural_case_contrasts_v1.csv',[{'metric':r['metric'],'contrast':r['contrast'],**case} for r in comparisons for case in r['case_table']])
    summary={'version':'p1c_measurement_summary_v1','planned':72,'successful':len(rows),'failed':72-len(rows),
        'cases':12,'speakers':6,'structural_status':dict(Counter(r['response_status']['status'] for r in rows)),
        'first_replies_identifiable':sum(r['response_status']['unit_identifiable'] for r in rows),
        'termination':dict(Counter(r['stop_reason'] for r in rows)),
        'native_stop_types':dict(Counter(r['raw_termination'].get('stop_type','unavailable') for r in rows)),
        'actual_generated_tokens':sum(r['generated_tokens'] for r in rows),
        'inference_latency_seconds_sum':sum(r['latency_seconds'] for r in rows),
        'semantic_human_judgments':0,'semantic_effects_computed':False,
        'metric_eligible':{k:sum(r['frozen_request']['applicability'][k] for r in rows) for k in rows[0]['frozen_request']['applicability']},
        'conditions':{cond:dict(Counter(r['response_status']['status'] for r in rows if r['frozen_request']['condition']==cond)) for cond in registry['condition_order']},
        'families':{family:dict(Counter(r['response_status']['status'] for r in rows if cases[r['frozen_request']['case_id']]['family']==family)) for family in sorted({v['family'] for v in cases.values()})},
        'reconstructed_twice':True,'no_additional_generation':True}
    summary['transport_checks']=transport_checks
    summary['source_integrity']=source_check
    summary['statistical_reconstruction_twice']=True
    d.write_json(output/'measurement_summary_v1.json',summary)
    forbidden={'condition','factor_assignment','raw_full_continuation','frozen_structural_status','response_status','prompt','native_termination'}
    d.require(not forbidden.intersection(semantic[0]),'Stage A contains prohibited diagnostic/treatment columns')
    d.require(len({r['anonymous_response_id'] for r in semantic})==72,'Review ID mismatch')
    for row in semantic:d.require(d.text_hash(row['raw_first_reply'])==row['first_reply_sha256'],'Masked first reply changed')
    d.write_json(output/'review_integrity_v1.json',{'version':'p1c_review_integrity_v1','records':72,'case_ids':12,
        'mask_seed':MASK_SEED,'presentation_seed':PRESENTATION_SEED,'first_reply_hashes':'PASS',
        'frozen_review_ids_and_presentation_order_preserved':True,
        'stage_A_forbidden_columns_absent':True,'blank_human_fields':True,
        'masking_limit':'Speaker names and linguistic/answer cues can reveal information; do not claim perfect blinding.',
        'files':{f.name:d.sha(f) for f in output.iterdir() if f.is_file()},
        'source_code_sha256':d.sha(Path(__file__)),'statistics_code_sha256':d.sha(Path('tools/p1c_paired_statistics.py')),
        'created_utc':d.now(),'new_generations':0})
    return summary


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',type=Path,required=True)
    print(json.dumps(prepare(a.parse_args().output),indent=2))
