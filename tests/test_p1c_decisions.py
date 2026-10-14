"""Synthetic decision fixtures are test-only; none are research annotations."""
import copy
import csv
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_decisions as p
import p1c_design as d


@pytest.fixture
def confirmed():
    # Artificial unit-test input in memory / pytest temporary directories only.
    rows=p.expected_rows();approval=p.approval_template()
    for r in rows:
        r.update(researcher_decision='ACCEPT_WITH_RESTRICTED_ESTIMAND',
                 restriction_reason='TEST FIXTURE: auxiliary package only, not a pure mechanism.',
                 reference_answer_valid='YES',no_material_answer_leakage='YES')
        if r['is_matched_control']=='YES':
            r.update(control_assessment_decision='DIAGNOSTIC_ONLY',control_assessment_reason='TEST FIXTURE: procedural priming remains.')
    approval.update(reviewer_id='Yaxin_ZHENG',review_status='RESEARCHER_CONFIRMED',decision_source='researcher',
        review_method='Researcher review of AI-assisted scientific proposals',confirmation_statement='TEST FIXTURE ONLY: not actual human approval.')
    for r in approval['policy_decisions']:r.update(decision='APPROVE',reason='TEST FIXTURE: development scope only.')
    return rows,approval


def test_empty_actual_master_is_not_confirmation():
    _,rows=p.csv_rows(p.PACKAGE/'researcher_item_decisions_v2.csv')
    with pytest.raises(p.DecisionError,match='missing/invalid mandatory decision'):
        p.validate_decisions(rows,p.approval_template())


def test_unique_decision_count_and_subset(confirmed):
    result=p.validate_decisions(*confirmed)
    assert result['valid_unique_item_decisions']==72
    assert result['case_decisions']==12 and result['history_text_decisions']==60
    assert result['control_assessments']==12 and result['control_assessments_are_subset']
    assert result['scientific_gate']=='PASS'


@pytest.mark.parametrize('field,value',[
    ('researcher_decision',''),('researcher_decision','PASS'),('researcher_decision','ACCEPT_WITH_LIMITATIONS'),
    ('restriction_reason',''),('reference_answer_valid',''),('no_material_answer_leakage','PASS'),
    ('source_item_sha256','changed'),('AI_proposal_original','ACCEPT'),('case_id','p1c_99_current'),
    ('item_type','history_text'),('original_condition_id','R0T0')])
def test_invalid_or_changed_decision_field_rejected(confirmed,field,value):
    rows,approval=confirmed;rows[0][field]=value
    with pytest.raises(p.DecisionError):p.validate_decisions(rows,approval)


@pytest.mark.parametrize('failure',['duplicate','missing','unknown','extra_column','missing_column'])
def test_schema_and_identity_fail_closed(confirmed,failure):
    rows,approval=confirmed
    if failure=='duplicate':rows[-1]=copy.deepcopy(rows[0])
    elif failure=='missing':rows.pop()
    elif failure=='unknown':rows[-1]['item_id']='unknown'
    elif failure=='extra_column':rows[0]['invented']='YES'
    else:rows[0].pop('researcher_notes')
    with pytest.raises(p.DecisionError):p.validate_decisions(rows,approval)


@pytest.mark.parametrize('field',['reference_answer_valid','no_material_answer_leakage'])
@pytest.mark.parametrize('value',['NO','UNCERTAIN'])
def test_material_failures_cannot_be_accepted(confirmed,field,value):
    rows,approval=confirmed;rows[0][field]=value
    with pytest.raises(p.DecisionError,match='acceptance contradicts'):p.validate_decisions(rows,approval)
    rows[0]['researcher_decision']='REVISION_REQUIRED'
    result=p.validate_decisions(rows,approval)
    assert result['scientific_gate']=='NO_GO'
    assert any('REVISION_REQUIRED' in b for b in result['blockers'])


def test_rejection_is_registered_valid_decision_not_go(confirmed):
    rows,approval=confirmed;rows[0]['researcher_decision']='REJECT'
    result=p.validate_decisions(rows,approval)
    assert result['valid_unique_item_decisions']==72 and result['scientific_gate']=='NO_GO'


@pytest.mark.parametrize('value',['ACCEPT','PASS','VALIDATED_NEUTRAL',''])
def test_neutrality_cannot_be_upgraded(confirmed,value):
    rows,approval=confirmed;r=next(r for r in rows if r['is_matched_control']=='YES')
    r['control_assessment_decision']=value
    with pytest.raises(p.DecisionError,match='unvalidated control'):p.validate_decisions(rows,approval)


def test_conflicting_control_assessment_rejected(confirmed):
    rows,approval=confirmed;r=next(r for r in rows if r['is_matched_control']=='YES')
    r['control_assessment_decision']='REJECT'
    with pytest.raises(p.DecisionError,match='contradicts control'):p.validate_decisions(rows,approval)
    r['researcher_decision']='REJECT'
    assert p.validate_decisions(rows,approval)['scientific_gate']=='NO_GO'


@pytest.mark.parametrize('field,value',[('reviewer_id',''),('review_status','PENDING'),('decision_source','AI'),
    ('review_method','two independent humans'),('confirmation_statement',''),('manifest_sha256','wrong'),
    ('review_timestamp','not a date')])
def test_provenance_invalid_rejected(confirmed,field,value):
    rows,approval=confirmed;approval[field]=value
    with pytest.raises(p.DecisionError):p.validate_decisions(rows,approval)


def test_timestamp_optional_and_policy_decline_blocks_go(confirmed):
    rows,approval=confirmed;assert approval['review_timestamp'] is None
    approval['policy_decisions'][0]['decision']='DECLINE'
    result=p.validate_decisions(rows,approval)
    assert result['scientific_gate']=='NO_GO'


@pytest.mark.parametrize('mutation',['duplicate','missing','changed_hash','blank_reason'])
def test_policy_binding_and_completeness(confirmed,mutation):
    rows,approval=confirmed;ps=approval['policy_decisions']
    if mutation=='duplicate':ps[-1]=copy.deepcopy(ps[0])
    elif mutation=='missing':ps.pop()
    elif mutation=='changed_hash':ps[0]['source_sha256']='wrong'
    else:ps[0]['reason']=''
    with pytest.raises(p.DecisionError):p.validate_decisions(rows,approval)


@pytest.fixture
def registered(tmp_path,monkeypatch,confirmed):
    monkeypatch.setattr(p,'verify_sources',lambda: {'status':'PASS'})
    items=tmp_path/'input.csv';approval=tmp_path/'approval.json';out=tmp_path/'registration'
    d.write_csv(items,confirmed[0]);d.write_json(approval,confirmed[1]);p.register(items,approval,out)
    return items,approval,out


def test_registration_preserves_sources_and_corrections(registered):
    items,approval,out=registered
    assert (out/'researcher_decisions_source.csv').read_bytes()==items.read_bytes()
    assert (out/'scientific_approval_source.json').read_bytes()==approval.read_bytes()
    assert d.read(out/'registration_v1.json')['review_timestamp'] is None
    assert p.load_registration(out/'registration_v1.json')['scientific_gate']=='PASS'
    with pytest.raises(FileExistsError):p.register(items,approval,out)


def test_invalid_import_creates_no_registration(tmp_path,monkeypatch,confirmed):
    monkeypatch.setattr(p,'verify_sources',lambda: {'status':'PASS'})
    rows,approval=confirmed;rows[0]['researcher_decision']=''
    d.write_csv(tmp_path/'input.csv',rows);d.write_json(tmp_path/'approval.json',approval)
    with pytest.raises(p.DecisionError):p.register(tmp_path/'input.csv',tmp_path/'approval.json',tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_registration_tampering_rejected(registered):
    _,_,out=registered
    with (out/'researcher_decisions_source.csv').open('a') as stream:stream.write('changed')
    with pytest.raises(ValueError,match='Registered file changed'):p.load_registration(out/'registration_v1.json')


def authorized_fixture(registration):
    auth=p.authorization_template()
    auth.update(registration_sha256=d.sha(registration),authorization_decision='AUTHORIZE_72_REQUESTS',
                reviewer_id='Yaxin_ZHENG',decision_source='researcher',authority_statement='TEST FIXTURE ONLY: no real authorization.')
    return auth


def test_scientific_approval_is_not_execution_authorization(registered):
    _,_,out=registered;r=p.gate(out/'registration_v1.json')
    assert r['status']=='NO_GO' and r['valid_registered_unique_decisions']==72
    assert r['checks']['authorization']['status']=='PENDING_OR_NOT_GRANTED'


@pytest.mark.parametrize('field,value',[('request_count',73),('request_count','72'),('request_count',True),
    ('manifest_sha256','wrong'),('registration_sha256','wrong'),('authorization_decision','APPROVE'),
    ('authority_statement',''),('reviewer_id',''),('decision_source','AI')])
def test_authorization_must_be_explicit_and_exact(registered,field,value):
    _,_,out=registered;path=out/'registration_v1.json';auth=authorized_fixture(path);auth[field]=value
    with pytest.raises(p.DecisionError):p.validate_authorization(auth,d.sha(path))


def test_all_gates_are_required_and_go_does_not_generate(registered,tmp_path,monkeypatch):
    _,_,out=registered;path=out/'registration_v1.json';authpath=tmp_path/'auth.json'
    d.write_json(authpath,authorized_fixture(path));result=p.gate(path,authpath)
    assert result['status']=='GO' and result['generation_requests_executed']==0
    assert result['checks']['authorization']['source_sha256']==d.sha(authpath)
    def failed():raise ValueError('mandatory identity mismatch')
    monkeypatch.setattr(p,'verify_sources',failed)
    assert p.gate(path,authpath)['status']=='NO_GO'


def test_pending_gate_reports_unique_missing_counts(monkeypatch):
    monkeypatch.setattr(p,'verify_sources',lambda: {'status':'PASS'})
    result=p.gate()
    assert result['status']=='NO_GO'
    assert result['unregistered_unique_decisions']==72
    assert result['unregistered_control_assessments_subset']==12
    assert result['valid_registered_unique_decisions']==0


def test_analysis_metadata_keeps_original_labels_and_weights():
    spec=d.read(p.PACKAGE/'analysis_restrictions_v1.json');original=d.read(p.SOURCE/'estimand_registry_proposed_v1.json')
    assert spec['original_weights_unchanged']==original['weights']
    assert all(c['original_condition_id']=='N_history' and c['analysis_control_class']==p.CONTROL_CLASS for c in spec['control_rows'])
    assert spec['statistics']['speaker_clusters']==6
    assert not spec['statistics']['unverifiable_is_incorrect']


def test_csv_duplicate_headers_and_ragged_rows_rejected(tmp_path):
    for text in ['item_id,item_id\na,b\n','a,b\nx\n','a\nx,y\n']:
        path=tmp_path/'bad.csv';path.write_text(text)
        with pytest.raises(p.DecisionError):p.csv_rows(path)


@pytest.mark.parametrize('text',['{"decision":"REJECT","decision":"ACCEPT"}', '{"x":{"decision":"NO","decision":"YES"}}'])
def test_duplicate_json_fields_cannot_silently_replace_decisions(tmp_path,text):
    path=tmp_path/'ambiguous.json';path.write_text(text)
    with pytest.raises(p.DecisionError,match='Duplicate JSON field'):p.decision_json(path)


def test_invalid_policy_id_type_is_a_validation_error(confirmed):
    rows,approval=confirmed;approval['policy_decisions'][0]['policy_id']=[]
    with pytest.raises(p.DecisionError,match='Policy ID must be a string'):p.validate_decisions(rows,approval)
