"""Synthetic integration fixtures only; no test ratings are research annotations."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))
SPEC=importlib.util.spec_from_file_location('semantic_integration',Path(__file__).parents[1]/'tools/p1b_semantic_integration.py')
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)


def unit_rows():
    rows=[]
    for i in range(4):
        for cond in m.contrast_weights()['S']:
            a={'applicable_'+axis:'true' for axis in m.core.AXES}
            a.update(human_factual_consistency='Incorrect',human_temporal_consistency='Correct',
                human_response_relevance_1_to_5='3',human_conversational_coherence_1_to_5='4',
                human_semantic_completeness='COMPLETE')
            rows.append({'case_id':f'UNIT{i}','persona_id':f'UNIT_SPEAKER{i//2}','condition':cond,
                'family':'UNIT_FAMILY','stage_a':a,'stage_b':{'human_reply_unit_confirmed':'PASS','structural_status':'CROSS_TURN'}})
    return rows


def confirmed_fixture(folder):
    a=deepcopy(m.core.csv_records(m.STAGE_A));b=deepcopy(m.core.csv_records(m.STAGE_B))
    for row in a+b:
        row.update(reviewer_id='Yaxin_ZHENG',review_assistance='SYNTHETIC SOFTWARE TEST ONLY',
                   prior_access_to_treatments_or_scores='SYNTHETIC SOFTWARE TEST ONLY')
    for row in a:
        row.update(human_semantic_completeness='UNCERTAIN',human_answer_delivery='UNCERTAIN',
            human_factual_consistency='Unverifiable',human_unverifiable_reason='SYNTHETIC TEST, NOT HUMAN REVIEW',
            human_evidence_quotations='SYNTHETIC TEST, NOT HUMAN REVIEW',
            human_response_relevance_1_to_5='3',human_conversational_coherence_1_to_5='4',
            human_temporal_consistency='Unverifiable' if row['applicable_temporal_consistency']=='true' else 'Not Applicable')
    for row in b:
        row.update(human_reply_unit_confirmed='UNCERTAIN',human_continuation_notes='SYNTHETIC TEST, NOT HUMAN REVIEW')
    pa,pb,pc=folder/'a.csv',folder/'b.csv',folder/'confirmation.json'
    m.write_csv(pa,a);m.write_csv(pb,b)
    c={'version':m.VERSION,'review_status':'RESEARCHER_CONFIRMED','reviewer_id':'Yaxin_ZHENG',
       'final_decision_authority':'researcher','decision_source':'researcher',
       'confirmation_statement':'SYNTHETIC SOFTWARE TEST; NOT A REAL RESEARCHER CONFIRMATION',
       'review_method':'SYNTHETIC SOFTWARE TEST','original_assessment_provenance':'SYNTHETIC SOFTWARE TEST',
       'ai_assisted_structured_coding':True,'stage_a_condition_labels_masked':'UNCERTAIN',
       'stage_b_seen_before_initial_stage_a':'UNCERTAIN','prior_treatment_knowledge':'UNCERTAIN',
       'stage_a_revised_after_stage_b':'NO','confirmed_artifact_sha256':{'stage_a':m.digest(pa),'stage_b':m.digest(pb)},
       'confirmed_response_ids':[r['anonymous_response_id'] for r in a], 'confirmation_utc':None}
    pc.write_text(json.dumps(c),encoding='utf-8')
    return a,b,c,pa,pb,pc


def test_real_package_is_read_only_and_still_blank():
    a,b,mapping,report=m.audit_package()
    assert len(a)==len(b)==len(mapping['responses'])==192
    assert report['eligibility']['temporal_consistency']==88
    assert report['source_prompts_reconstructed']==192
    assert report['structural_statuses']=={'CROSS_TURN':186,'TRUNCATED':5,'AMBIGUOUS':1}
    assert 'structural_status' not in a[0]
    assert report['human_reviews_imported']==0


@pytest.mark.parametrize('key,value', [('review_status','PENDING'),('reviewer_id',''),('decision_source','automated'),
    ('final_decision_authority','automated'),('ai_assisted_structured_coding',None),('confirmation_statement',''),
    ('stage_a_condition_labels_masked',None),('stage_b_seen_before_initial_stage_a',None),('prior_treatment_knowledge',None)])
def test_unconfirmed_or_missing_provenance_cannot_import(local_tmp,key,value):
    a,b,c,pa,pb,pc=confirmed_fixture(local_tmp);c[key]=value
    with pytest.raises(ValueError):m.validate_confirmation(c,a,b,m.digest(pa),m.digest(pb))


def test_confirmation_hash_and_exact_id_set_are_bound(local_tmp):
    a,b,c,pa,pb,pc=confirmed_fixture(local_tmp)
    with pytest.raises(ValueError,match='bind exact'):m.validate_confirmation(c,a,b,'0'*64,m.digest(pb))
    c['confirmed_response_ids'][-1]=c['confirmed_response_ids'][0]
    with pytest.raises(ValueError,match='192 distinct'):m.validate_confirmation(c,a,b,m.digest(pa),m.digest(pb))


def test_import_preserves_original_bytes_corrections_and_unknown_dates(local_tmp):
    a,b,c,pa,pb,pc=confirmed_fixture(local_tmp)
    initial=deepcopy(a);initial[0]['human_response_relevance_1_to_5']='2'
    pi=local_tmp/'initial.csv';m.write_csv(pi,initial)
    out=local_tmp/'registered'
    reg=m.register(pa,pb,pc,out,initial=pi)
    assert (out/'stage_a.csv').read_bytes()==pa.read_bytes()
    assert (out/'stage_a_initial.csv').read_bytes()==pi.read_bytes()
    assert reg['corrected_field_count']==1 and reg['boundary_unresolved']==192
    assert reg['confirmation_provenance']['confirmation_utc'] is None
    assert all(r['reviewed_utc']=='' for r in m.core.csv_records(out/'stage_a.csv'))
    with pytest.raises(FileExistsError):m.register(pa,pb,pc,out)


def test_known_after_stage_b_revisions_require_initial_version(local_tmp):
    a,b,c,pa,pb,pc=confirmed_fixture(local_tmp);c['stage_a_revised_after_stage_b']='YES'
    pc.write_text(json.dumps(c),encoding='utf-8')
    out=local_tmp/'reject'
    with pytest.raises(ValueError,match='initial Stage A'):m.register(pa,pb,pc,out)
    assert not out.exists()


def test_proposed_immutable_material_cannot_be_corrected_silently(local_tmp):
    a,b,c,pa,pb,pc=confirmed_fixture(local_tmp)
    proposed=deepcopy(a);proposed[0]['raw_first_reply']='ALTERED UNIT TEST'
    pp=local_tmp/'proposal.csv';m.write_csv(pp,proposed)
    with pytest.raises(ValueError,match='Immutable source'):m.register(pa,pb,pc,local_tmp/'reject',proposed=pp)


def test_import_and_analysis_gate_keep_uncertain_boundary_unknown(local_tmp):
    a,b,c,pa,pb,pc=confirmed_fixture(local_tmp)
    regdir=local_tmp/'registered';m.register(pa,pb,pc,regdir)
    out=local_tmp/'analysis';m.analyze_registration(regdir,out,replicates=100)
    result=m.core.load(out/'analysis_v1.json')
    row=next(r for r in result['contrasts'] if r['metric']=='factual_consistency' and r['contrast']=='C1-C0' and r['family']=='ALL')
    assert row['eligible_cases']==24 and row['evaluable_cases']==0
    assert row['evaluable_pair_estimate'] is None and row['all_eligible_identification_bounds']==[-1,1]
    assert result['speaker_clusters']==12 and result['responses']==192
    assert 'Algorithmic Opportunity Assessment' in (out/'analysis_report_v1.md').read_text()
    (regdir/'stage_a.csv').write_bytes((regdir/'stage_a.csv').read_bytes()+b'\n')
    with pytest.raises(ValueError,match='changed'):m.analyze_registration(regdir,local_tmp/'reject',replicates=100)


def test_analysis_rejects_pending_registration_before_computing(local_tmp):
    (local_tmp/'registration_v1.json').write_text(json.dumps({'version':m.VERSION,'review_status':'PENDING'}),encoding='utf-8')
    with pytest.raises(ValueError,match='verified researcher'):m.analyze_registration(local_tmp,local_tmp/'reject',replicates=100)


def test_simple_and_average_effect_scales_include_c0_incorrect_cases():
    rows=unit_rows()
    for r in rows:
        if r['condition']=='C1':r['stage_a']['human_factual_consistency']='Correct'
    report=m.compute(rows,replicates=100)
    def find(c):return next(r for r in report['contrasts'] if r['metric']=='factual_consistency' and r['contrast']==c and r['family']=='ALL')
    assert find('C1-C0')['evaluable_pair_estimate']==1
    assert find('S')['evaluable_pair_estimate']==.25
    assert find('SxH')['evaluable_pair_estimate']==-.5
    assert find('SxFxH')['evaluable_pair_estimate']==1
    assert find('C1-C0')['eligible_cases']==4
    assert report['speaker_clusters']==2


def test_unverifiable_missing_incorrect_and_na_stay_distinct():
    rows=unit_rows()
    rows[0]['stage_a']['human_factual_consistency']='Unverifiable'
    rows[8]['stage_a']['human_factual_consistency']=''
    for r in rows:
        if r['case_id']=='UNIT3':
            r['stage_a']['applicable_temporal_consistency']='false'
            r['stage_a']['human_temporal_consistency']='Not Applicable'
    result=m.compute(rows,replicates=100)
    r=next(d for d in result['distributions'] if d['metric']=='factual_consistency' and d['family']=='ALL' and d['condition']=='C0')
    assert r['label_distribution']=={'Unverifiable':1,'MISSING':1,'Incorrect':2}
    assert r['missing_judgments']==1 and r['unverifiable_labels']==1 and r['numerically_evaluable']==2
    t=next(d for d in result['distributions'] if d['metric']=='temporal_consistency' and d['family']=='ALL' and d['condition']=='C0')
    assert t['eligible']==3 and t['not_applicable']==1


def test_zero_weight_unknown_does_not_remove_simple_pair():
    rows=unit_rows()
    next(r for r in rows if r['case_id']=='UNIT0' and r['condition']=='C7')['stage_a']['human_factual_consistency']='Unverifiable'
    report=m.compute(rows,replicates=100)
    subset=[r for r in report['contrasts'] if r['metric']=='factual_consistency' and r['family']=='ALL']
    assert next(r for r in subset if r['contrast']=='C1-C0')['evaluable_cases']==4
    main=next(r for r in subset if r['contrast']=='S')
    assert main['evaluable_cases']==3 and main['unknown_cases']==1
    assert main['all_eligible_identification_bounds']==[0,.0625]


def test_signed_unknown_bounds_apply_to_ordinal_and_binary_values():
    outcomes={'C0':{'value':None,'lo':1,'hi':5},'C1':{'value':4,'lo':1,'hi':5}}
    assert m.bounds(outcomes,{'C0':-1,'C1':1})==(-1,3)


def test_speaker_bootstrap_bundles_both_cases_and_is_reproducible():
    points=[{'persona_id':p,'difference':v} for p,v in [('a',1),('a',1),('b',-1),('b',-1)]]
    a=m.clustered_interval(points,4,100)
    assert a['speaker_clusters']==2 and a['interval']==[-1,1]
    assert m.clustered_interval(points,4,100)==a


@pytest.mark.parametrize('failure',['duplicate','missing','eligibility','speaker'])
def test_factorial_integrity_failures_rejected(failure):
    rows=unit_rows()
    if failure=='duplicate':rows.append(rows[0])
    if failure=='missing':rows.pop()
    if failure=='eligibility':rows[0]['stage_a']['applicable_factual_consistency']='false'
    if failure=='speaker':rows[0]['persona_id']='ALIEN'
    with pytest.raises(ValueError):m.compute(rows,replicates=100)
