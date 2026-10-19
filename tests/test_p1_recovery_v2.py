import ast
import copy
from collections import Counter
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1_recovery_v2 as r
import p1_temporal_fallback as f
import p1_recovery_gate_v2 as gate


def test_v2_preserves_twenty_complete_request_objects():
    plan=r.validate();prior=r.s.load(r.v1.MANIFEST)
    assert plan['requests'][:20]==prior['requests']
    assert plan['native_tokenizer_logs'][:20]==prior['native_tokenizer_logs']
    assert Counter(x['condition'] for x in plan['requests'])=={'D1':8,'D2':8,'D3':8}
    assert [x['order'] for x in plan['requests']]==list(range(24))


@pytest.mark.parametrize('suffix,answer',[('04','Bay B5238'),('05','Bay B5284')])
def test_only_four_repaired_by_original_reference_order(suffix,answer):
    plan=r.validate();rows=[x for x in plan['requests'][20:] if x['case_id'].endswith(suffix)]
    assert len(rows)==2
    for row in rows:
        assert row['reference'][0]['value']==answer
        assert 'Which bay is assigned' in row['messages'][0]['content'].split('Current question:')[1]
        assert answer not in row['messages'][0]['content'].split('Current question:')[1]


def test_transport_preserves_global_duplicate_and_quota_guards():
    t=r.transport()
    assert t.CLAIM==r.v1.CLAIM and t.old.ROOT==r.old.ROOT
    assert t.validate is r.validate and t.preflight is r.preflight
    assert t.ROOT==r.ROOT and t.OUT==r.OUT
    assert r.v1.OUT==r.d.OUT  # Original namespace never changed.
    assert r.old.cumulative()['attempted']['B_FACTORIAL']==0
    assert r.s.config(r.validate()).max_new_tokens==96


def test_fallback_fixed_balanced_allocation_and_no_overlap():
    bank,a=f.candidate_bank();bank2,a2=f.candidate_bank()
    assert bank==bank2 and a==a2
    assert f.verify_bank(bank)['templates']==8
    assert all(not v for v in f.overlap_audit(bank)['exact_overlap'].values())
    cal={c['case_id'] for c in bank if c['pool']=='fallback_calibration'}
    pilot={c['case_id'] for c in bank if c['pool']=='fallback_pilot'}
    assert len(cal)==len(pilot)==8 and not cal&pilot
    assert len({c['question'] for c in bank})==16
    assert len({c['style_intervention'] for c in bank})==16


def test_fallback_reference_and_leakage_corruption_rejected():
    bank,_=f.candidate_bank();bad=copy.deepcopy(bank);bad[0]['question']+=' '+bad[0]['reference'][0]['value']
    with pytest.raises(ValueError):f.verify_bank(bad)
    bad=copy.deepcopy(bank);bad[0]['requested_date']='2056-01-01'
    with pytest.raises(ValueError):f.verify_bank(bad)


def test_outdated_is_not_missing_unverifiable_or_negated():
    c=f.candidate_bank()[0][0];current=c['reference'][0]['value'];old=c['old_reference']['value']
    assert f.endpoint(current,c)=='CURRENT_VALUE_ADOPTION'
    assert f.endpoint(old,c)=='OUTDATED_VALUE_ADOPTION'
    assert f.endpoint(None,c)=='MISSING_RECORD'
    assert f.endpoint('',c)=='EMPTY_RESPONSE'
    assert f.endpoint('Not '+old,c)=='UNVERIFIABLE_ANSWER'
    assert f.endpoint(old+' was correct last March.',c)=='UNVERIFIABLE_ANSWER'
    assert f.endpoint(current+' and '+old,c)=='CONTRADICTORY_ANSWER_REQUIRES_REVIEW'
    other=next(x for x in c['facts'] if x['entity']!=c['speaker_name'])
    assert f.endpoint(other['value'],c)=='WRONG_ENTITY_ANSWER'


def test_no_ai_trigger_or_implicit_fallback_authorization():
    assert gate.decide([])['status']=='SCIENTIFIC DECISION PENDING REVIEW'
    assert not gate.fallback_ready(gate.decide([]),{'attempted':24,'results':24},True,{'status':'PASS','requests':8})
    assert gate.fallback_result(['Correct']*8)=='SCIENTIFIC DECISION PENDING REVIEW'
    assert gate.fallback_result(['Correct']*7+['Partially correct'],True)=='PREPARE_QUALIFIED_PILOT_ONLY'
    assert gate.fallback_result(['Correct']*6+['Partially correct','Unverifiable'],True)=='STOP_FORMAL_MODEL_FEASIBILITY_REVIEW'
    assert gate.LABELS['Partially correct']=='Partially correct'


def test_fallback_native_inputs_and_full_factorial_controls():
    binding=f.OUT/'manifest_bindings_v1.json'
    if not binding.exists():pytest.skip('Fallback tokenizer preparation still in progress')
    for group,h in r.s.load(binding).items():
        path=f.OUT/(group+'_manifest_candidate_v1.json');assert r.s.sha256(path)==h
        plan=r.s.load(path)
        assert plan['proposed_requests']==(8 if group=='fallback_calibration' else 80)
        for row,log in zip(plan['requests'],plan['native_tokenizer_logs']):
            assert r.s.sha256(Path(log['path']))==log['sha256']
            assert ast.literal_eval(r.s.load(log['path'])['stdout'].strip())==row['input_token_ids']
            assert row['context_remaining']>0
        if group=='fallback_pilot':
            for cid in {x['case_id'] for x in plan['requests']}:
                rows={x['condition']:x for x in plan['requests'] if x['case_id']==cid}
                assert set(rows)==set(r.m.CELLS)|{'N_style','N_history'}
                for k in ('evidence_sha256','question_sha256','reference_sha256','evaluation_date','context_sha256'):
                    assert len({x[k] for x in rows.values()})==1
                assert rows['C1']['input_tokens']==rows['N_style']['input_tokens']
                assert rows['C3']['input_tokens']==rows['N_history']['input_tokens']
