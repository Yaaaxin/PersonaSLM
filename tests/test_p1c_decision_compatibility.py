"""Synthetic approvals only in temporary tests; no fixture is human authorization."""
import copy
import json
from pathlib import Path
import shutil
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_decision_compatibility as c
import p1c_decisions as p
import p1c_design as d


def test_actual_bundle_lossless_counts():
    summary,rows,_=c.inspect_bundle(c.BUNDLE)
    assert summary['entries']==77 and summary['confirmed_scoped_decisions']==74
    assert summary['derived_legacy_categories']==48 and summary['unresolved_compatibility_records']==[]
    assert summary['non_annotation_fields_compared']==1772
    assert len(summary['pending_decisions'])==3 and not summary['inference_authorized']
    legacy=[r for r in rows if r['original_researcher_decision']=='ACCEPT_WITH_LIMITATIONS']
    assert len(legacy)==48
    for row in legacy:
        assert row['operational_category']=='ACCEPT_WITH_RESTRICTED_ESTIMAND'
        assert row['original_record']['researcher_decision']=='ACCEPT_WITH_LIMITATIONS'
        assert row['basis_verbatim']==row['original_record']['researcher_notes']
    assert sum(r['item_id'].endswith('/N_history') for r in rows)==12


@pytest.mark.parametrize('field,value',[
    ('AI_scope_v1','PURE_MECHANISM_APPROVED'),('researcher_notes','Accepted without restrictions'),
    ('AI_case_specific_reason_v1','Missing scoped source'),('item_type','case'),('item_id','example/N_history')])
def test_unsupported_legacy_mapping_keeps_original(field,value):
    _,rows,_=c.inspect_bundle(c.BUNDLE)
    original=copy.deepcopy(next(r['original_record'] for r in rows if r['original_researcher_decision']=='ACCEPT_WITH_LIMITATIONS'))
    original[field]=value
    result=c.derive(original)
    assert result['operational_category'] is None and result['issue'].startswith('UNRESOLVED')
    assert result['original_record']==original and result['original_researcher_decision']=='ACCEPT_WITH_LIMITATIONS'


def test_pending_cannot_be_derived_as_approval():
    _,rows,_=c.inspect_bundle(c.BUNDLE)
    for row in rows:
        if row['item_id'] in c.PENDING:
            assert row['operational_category'] is None
            assert row['original_confirmation_status']=='RESEARCHER_ACKNOWLEDGED_PENDING'


@pytest.fixture
def registration(tmp_path,monkeypatch):
    monkeypatch.setattr(p,'verify_sources',lambda: {'status':'PASS','test_fixture_only':True})
    out=tmp_path/'registered'
    c.register(c.BUNDLE,out)
    return out/'registration_v1.json'


def test_registration_sources_immutable_and_subcriteria_not_invented(registration):
    record=c.load_registration(registration)
    assert record['validation']['confirmed_scoped_decisions']==74
    assert p.decision_json(registration.parent/'registered_decisions_v1.json')['review_timestamp'] is None
    m=p.decision_json(c.BUNDLE/c.MANIFEST_REL)
    for key in ('cases','history','unified','confirmation'):
        assert (registration.parent/(key+'.csv')).read_bytes()==(c.BUNDLE/m['relative_repository_destination'][key]).read_bytes()
    with pytest.raises(FileExistsError):c.register(c.BUNDLE,registration.parent)


def test_snapshot_tamper_rejected(registration):
    with (registration.parent/'history.csv').open('a') as f:f.write('tamper')
    with pytest.raises(ValueError,match='Snapshot changed'):c.load_registration(registration)


def test_source_text_mismatch_rejected_even_with_rehashed_supplied_csv(tmp_path):
    root=tmp_path/'bundle';shutil.copytree(c.BUNDLE,root)
    mp=root/c.MANIFEST_REL;m=p.decision_json(mp);path=root/m['relative_repository_destination']['cases']
    fields,rows=p.csv_rows(path)
    field=next(k for k in fields if k not in ('case_id','reviewer_id','review_timestamp') and not k.startswith('researcher_'))
    rows[0][field]='TAMPERED SCIENTIFIC INPUT'
    path.unlink();d.write_csv(path,rows)
    m['generated_csv_sha256']['cases']=d.sha(path);mp.write_text(json.dumps(m),encoding='utf-8')
    with pytest.raises(ValueError,match='Non-annotation mismatch'):c.inspect_bundle(root)


def test_three_pending_only_no_enum_or_subcriteria_gate(registration):
    result=c.gate(registration)
    assert result['status']=='NO_GO' and result['registered_confirmations']==74
    assert result['remaining_gate_items']==list(c.PENDING)
    assert result['mandatory_approval_count']==3 and result['new_generations']==0


def approved_test_fixture(registration):
    record=c.approval_template(registration)
    record.update(reviewer_id='Yaxin_ZHENG',decision_source='researcher',confirmation_statement='TEST ONLY, not actual approval')
    for row in record['decisions']:
        row.update(decision='AUTHORIZE_72_REQUESTS' if row['item_id']=='execution_authorization' else 'APPROVE',reason='TEST ONLY')
    return record


def test_blank_form_is_not_authorization(registration):
    with pytest.raises(p.DecisionError):c.validate_approval(c.approval_template(registration),registration)


def test_all_three_positive_gate_does_not_execute(registration,tmp_path):
    auth=tmp_path/'test_only.json';d.write_json(auth,approved_test_fixture(registration))
    gate=c.gate(registration,auth)
    assert gate['status']=='GO' and gate['new_generations']==0


@pytest.mark.parametrize('field,value',[
    ('request_count',73),('request_count','72'),('request_count',True),
    ('registration_sha256','bad'),('manifest_sha256','bad'),('reviewer_id','other'),
    ('decision_source','inferred'),('confirmation_statement',''),('review_timestamp','unknown')])
def test_invalid_approval_binding(registration,field,value):
    record=approved_test_fixture(registration);record[field]=value
    with pytest.raises(p.DecisionError):c.validate_approval(record,registration)


@pytest.mark.parametrize('kind',['duplicate','missing','document','implicit_execution','reason'])
def test_missing_contradictory_or_implicit_approval_rejected(registration,kind):
    r=approved_test_fixture(registration)
    if kind=='duplicate':r['decisions'][2]=copy.deepcopy(r['decisions'][0])
    elif kind=='missing':r['decisions'].pop()
    elif kind=='document':r['decisions'][0]['documents'][0]['sha256']='bad'
    elif kind=='implicit_execution':r['decisions'][2]['decision']='APPROVE'
    else:r['decisions'][0]['reason']=''
    with pytest.raises(p.DecisionError):c.validate_approval(r,registration)


def test_rejection_only_blocks_the_specific_pending_item(registration):
    record=approved_test_fixture(registration);record['decisions'][1]['decision']='DECLINE'
    assert c.validate_approval(record,registration)==['protocol_addendum: DECLINE']


def test_actual_policy_all_sixteen_weights_and_denominators():
    report=c.policy_audit()
    assert report['contrasts_checked']==16 and report['applicability_rows']==72
    assert report['applicable_counts']['factual_consistency']==72
    assert report['applicable_counts']['temporal_consistency']==72
    assert report['applicable_counts']['persona_fidelity']==0
    assert report['weights']['RxT']==dict(zip(report['condition_ids'],[1,-1,-1,1,0,0]))
