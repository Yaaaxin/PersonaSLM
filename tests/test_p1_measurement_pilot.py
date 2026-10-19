import sys
import json
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1_measurement_materials as m
import p1_measurement_run as run
from p1_measurement_scoring import score,stale_state,signed_bounds,wilson,agreement


@pytest.fixture
def cases():return m.s.load(m.OUT/'materials_v1.json')['cases']


def test_disjoint_and_sufficient(cases):
    assert m.validate_cases(cases)['case_count']==40
    for c in cases:
        facts={r['source_id']:r for r in c['facts']}
        for ref in c['reference']:
            date='2051-03-15' if ref['key']=='march_bay' else c['requested_date']
            for sid in ref['source_ids']:assert facts[sid]['valid_from']<=date<=facts[sid]['valid_to']
            if c['family']=='relational_chain':
                chain=[facts[k] for k in ref['source_ids']]
                assert chain[0]['entity']==c['speaker_name']
                assert all(x['value']==y['entity'] for x,y in zip(chain,chain[1:]))


@pytest.mark.parametrize('category',['A_C0','B_FACTORIAL'])
def test_manifests(category):assert len(run.validate(category)['requests'])==m.CAPS[category]


def test_principal_endpoint_is_unique():
    p=m.policy();assert p['primary_comparison']['name']=='C3-C0'
    assert len(p['primary_comparison']['eligible_cases'])==8
    assert p['readiness']['hard_accuracy_threshold'] is None


@pytest.mark.parametrize('i',range(8))
def test_factorial_reference_invariance(i,cases):
    c=cases[32+i];texts=[m.content(c,k) for k in m.CELLS]
    assert all(c['trusted_evidence'] in t and c['question'] in t for t in texts)
    assert c['history_intervention'] not in texts[0]
    assert c['history_intervention'] in m.content(c,'C3')
    assert c['style_intervention'] not in m.content(c,'C3')


def test_correct_partial_is_not_task_success(cases):
    c=next(c for c in cases if c['family']=='dual_component')
    v=score(c['reference'][0]['value']+'.',c)
    assert v['factual']=='Correct' and v['task_success']=='Failure'
    assert v['semantic_completeness']=='NO' and v['supported']==1


def test_wrong_complete_stays_complete(cases):
    c=cases[32];v=score(c['stale_endpoint']['old_value']+'.',c)
    assert v['factual']=='Incorrect' and v['task_success']=='Failure'
    assert v['semantic_completeness']=='YES' and v['coherence']==5


def test_historical_truth_not_stale(cases):
    c=cases[32];old=c['stale_endpoint']['old_value']
    assert stale_state('On 2051-03-15, '+old+'.',c)=='NOT_ADOPTED'
    assert stale_state('On 2051-09-15, '+old+'.',c)=='ADOPTED'
    assert stale_state('Not '+old+'.',c)=='UNVERIFIABLE'
    assert stale_state(old,c,False)=='BOUNDARY_UNRESOLVED'


def test_two_date_attachment_not_token_presence(cases):
    c=cases[38];old,new=c['stale_endpoint']['old_value'],c['stale_endpoint']['current_value']
    assert score(old+'; '+new,c)['task_success']=='Uncertain'
    good='March: '+old+'; September: '+new+'.'
    wrong='March: '+new+'; September: '+old+'.'
    assert score(good,c)['task_success']=='Success'
    assert score(wrong,c)['task_success']!='Success'
    assert stale_state(good,c)=='NOT_ADOPTED' and stale_state(wrong,c)=='ADOPTED'


def test_noanswer_and_unknown_prose(cases):
    c=cases[32];v=score('I will check the allocation.',c)
    assert v['task_success']=='Failure' and v['factual']=='Unverifiable'
    assert v['behavioral_fidelity'] is None
    v=score(c['reference'][0]['value']+'. The supervisor resigned.',c)
    assert v['factual']=='Unverifiable'


def test_fidelity_separate(cases):
    c=cases[32];bay=c['reference'][0]['value']
    a=score(bay+'. Noted.',c);b=score('Certainly. '+bay+'.',c)
    assert a['task_success']==b['task_success']=='Success'
    assert a['behavioral_fidelity']==5 and b['behavioral_fidelity']==1


def test_missing_NA_and_unknown_distinct(cases):
    assert score(None,cases[0])['factual']=='Missing'
    assert stale_state('',cases[0])=='NOT_APPLICABLE'
    assert score('',cases[0])['factual']=='Unverifiable'


def test_signed_unknowns_no_renormalization():
    assert signed_bounds({'C3':1,'C0':-1},{'C3':1,'C0':None})==[0,1]
    assert signed_bounds({'C3':1,'C0':-1},{'C3':None,'C0':1})==[-1,0]
    assert signed_bounds({'C3':1,'C0':-1},{})==[-1,1]


def test_uncertainty_and_agreement_denominators():
    assert wilson(0,8)[1]>0 and wilson(8,8)[0]<1
    d=agreement(['Correct',None,'Unverifiable'],['Incorrect','Correct','Unverifiable'])
    assert d['paired_comparable']==2 and d['agreement_rate']==.5


def test_independent_caps_and_duplicates(tmp_path,monkeypatch):
    monkeypatch.setattr(run,'ROOT',tmp_path)
    def fixture_write(path,data):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data),encoding='utf-8')
    fixture_write(tmp_path/'claims'/'A.json',{'category':'A_C0','maximum_attempts':32})
    for i in range(32):fixture_write(tmp_path/'attempts'/f'{i}.json',{'category':'A_C0','request_id':str(i),'authorization_id':m.AUTH_ID})
    d=run.cumulative();assert d['remaining_authorization']=={'A_C0':0,'B_FACTORIAL':80,'C_DIAGNOSTIC':48}
    fixture_write(tmp_path/'attempts'/'dup.json',{'category':'A_C0','request_id':'0','authorization_id':m.AUTH_ID})
    with pytest.raises(ValueError,match='Duplicate'):run.cumulative()


def test_no_gate_from_materials_only():
    assert m.s.load(m.OUT/'authorization_v1.json')['semantic_adoption'] is False
    assert m.s.load(m.OUT/'stimulus_validation_v1.json')['human_confirmations']==0


def test_v2_distinguishes_wrong_entity_from_expired_value(cases):
    from p1_measurement_scoring_v2 import score as revised
    c=cases[32]
    wrong_entity=next(f['value'] for f in c['facts'] if f['entity'].startswith('Record-holder') and f['valid_from']=='2051-07-01')
    v=revised(wrong_entity,c)
    assert v['factual']=='Incorrect' and v['temporal']=='Unverifiable'
    old=revised(c['stale_endpoint']['old_value'],c)
    assert old['temporal']=='Incorrect'


def test_v2_explicit_labels_not_silent_semantic_repair(cases):
    from p1_measurement_scoring_v2 import score as revised,canonical_syntax
    c=cases[32]
    code=c['reference'][0]['value'].split()[-1]
    assert revised('Bay: '+code,c)['task_success']=='Success'
    assert 'not' in canonical_syntax('Not Bay: '+code).lower()
    assert revised('Not Bay: '+code,c)['factual']=='Unverifiable'
    assert revised('Not Bay: '+code,c)['task_success']=='Uncertain'


def test_diagnostic_keeps_evidence_and_factorial_pool_isolated():
    plan=run.validate('C_DIAGNOSTIC')
    old={r['case_id']:r for r in run.validate('A_C0')['requests']}
    for row in plan['requests']:
        assert row['condition']=='C0'
        for field in ('evidence_sha256','reference_sha256','question_sha256','context_sha256','speaker_id','evaluation_date'):
            assert row[field]==old[row['case_id']][field]
        assert row['case_id'].startswith('p1_measure_calibration_')
    assert len(plan['requests'])==16


@pytest.mark.parametrize('category,n',[('A_C0',32),('C_DIAGNOSTIC',16)])
def test_actual_execution_and_AI_provenance(category,n):
    audit=run.audit(category)
    assert audit['attempted']==audit['results']==n
    dest=m.OUT/category/'measurement_v1'
    ai=m.s.load(dest/'AI_proposals_UNCONFIRMED_v1.json')
    masked={x['review_id']:x for x in m.s.load(dest/'masked_evidence_v1.json')}
    assert len(ai)==len({x['review_id'] for x in ai})==n
    for x in ai:
        assert x['researcher_decision']=='' and x['human_timestamp'] is None
        assert x['evaluation_text']==masked[x['review_id']]['raw_output']
        assert x['raw_sha256']==m.s.th(x['evaluation_text'])
        assert 0<=x['supported']<=x['delivered']<=x['required']


def test_pilot_scientific_gate_blocks_actual_execution():
    with pytest.raises(ValueError,match='Scientific readiness gate not passed'):
        run.preflight('B_FACTORIAL',resources=False)


def test_actual_cumulative_scope_includes_later_oq_recovery():
    ledger=run.cumulative()
    # The original measurement-pilot audit above remains 16 requests.  The
    # cumulative authorization ledger also includes the later 24-request O/Q
    # recovery (D1-D3), so the current C_DIAGNOSTIC total is 40, not 16.
    assert ledger['attempted']=={'A_C0':32,'B_FACTORIAL':0,'C_DIAGNOSTIC':40}
    assert ledger['total_attempted']==72 and ledger['total_remaining']==88
    assert ledger['remaining_authorization']=={'A_C0':0,'B_FACTORIAL':80,'C_DIAGNOSTIC':8}


def test_paired_diagnostic_uncertainty_supersedes_pooled_interval():
    d=m.s.load(m.OUT/'C_DIAGNOSTIC/measurement_v1/summary_v2.json')
    assert d['Wilson_95_descriptive_iid_approximation'] is None
    assert d['actual_experimental_units']['cases']==8
    assert d['paired_sensitivity']['concise']['clusters']==8
    assert d['selected_arm'] is None
