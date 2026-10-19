"""Measurement regressions. Any confirmed labels below are temporary TEST fixtures."""
import copy
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1_recovery_v2 as r
import p1_recovery_gate_v2 as gate
import p1_recovery_analysis_v2 as analysis
import p1_recovery_measurement_v2 as measurement


@pytest.fixture(scope='module')
def actual():
    return r.audit()


def test_completed_inventory_and_no_unapproved_generation(actual):
    assert actual['attempted']==actual['results']==24
    assert all(x['state']=='COMPLETED' for x in actual['rows'])
    ledger=r.old.cumulative()
    assert ledger['attempted']=={'A_C0':32,'B_FACTORIAL':0,'C_DIAGNOSTIC':40}
    assert ledger['total_attempted']==72 and ledger['total_remaining']==88
    assert not list(r.ROOT.glob('fallback*'))


def test_review_covers_actual_outputs_and_keeps_human_fields_blank(actual):
    rows=analysis.read_rows();assert len(rows)==56
    assert len({x['request_id'] for x in rows})==56
    assert all(not v for x in rows for k,v in x.items() if k.startswith('researcher_'))
    current={x['request']['request_id']:x for x in actual['rows']}
    originals={x['original_request']['request_id']:x for x in r.s.load(r.d.OUT/'original_C0_audit_v1.json')}
    for row in rows:
        if row['request_id'] in current:
            source=current[row['request_id']]['result']
        else:
            old=originals[row['request_id']];source=old['original_result']
            assert row['ai_assisted_label']==old['original_AI']['task_success']
            assert row['AI_factual']==old['original_AI']['factual']
            assert row['AI_temporal']==old['original_AI']['temporal']
            assert row['AI_completeness']==old['original_AI']['semantic_completeness']
            assert row['AI_relevance']==str(old['original_AI']['relevance'])
            assert row['AI_coherence']==str(old['original_AI']['coherence'])
        assert row['model_output']==source['raw_response']
        assert row['raw_output_sha256']==r.s.th(source['raw_response'])
        assert row['original_structural_status']==source['response_status']['status']
        assert Path(row['AI_source']).exists()
    assert [int(x['review_priority']) for x in rows]==sorted(int(x['review_priority']) for x in rows)


def test_masked_assessment_binding_before_join():
    p=r.s.load(r.OUT/'AI_review_provenance_v2.json')
    assert p['assessment_sha256']==r.s.sha256(r.OUT/'masked_AI_reinspection_UNCONFIRMED_v2.json')
    masked=r.s.load(r.OUT/'masked_AI_reinspection_UNCONFIRMED_v2.json')
    assert all('condition' not in x and 'request_id' not in x for x in masked)
    proposals=r.s.load(r.OUT/'AI_proposals_UNCONFIRMED_v2.json')
    assert len(proposals)==32 and len({x['request_id'] for x in proposals})==32
    for x in proposals:
        base=next(y for y in masked if y['review_id']==x['review_id'])
        assert all(x[k]==v for k,v in base.items())
    assert p['independent_human_annotators']==p['researcher_confirmed_records']==0


def test_q1_strict_whole_answer_scoring_and_no_original_two_date_scoring(actual):
    policy=r.s.load(r.OUT/'prospective_policy_v2.json');cs={c['case_id']:c for c in r.d.select_cases(r.d.cases())}
    for x in actual['rows']:
        req=x['request']
        if req['condition'] not in ('D2','D3'):continue
        c=cs[req['case_id']];spec=policy['Q1_specs'][c['case_id']];answer=spec['reference'][0]['value']
        assert r.d.score_single(answer,spec)['task_success']=='Success'
        assert r.d.score_single('  '+answer.upper()+'.  ',spec)['task_success']=='Success'
        for bad in ('Not '+answer,answer+' and Bay B0000','**'+answer+'**'):
            assert r.d.score_single(bad,spec)['task_success']!='Success'
        assert r.d.score_single(None,spec)['task_success']!=r.d.score_single('',spec)['task_success']
        scored=measurement.automatic(req,x['result'],c,req['condition'],policy)
        assert scored['temporal'] is None  # Uncovered, not a fabricated N/A rating.
        assert scored['required']==1


def test_answer_delivery_can_survive_budget_termination(actual):
    ai={x['request_id']:x for x in r.s.load(r.OUT/'AI_proposals_UNCONFIRMED_v2.json')}
    tails=[x for x in actual['rows'] if x['result']['stop_reason']=='length']
    assert len(tails)==2
    for x in tails:
        p=ai[x['request']['request_id']]
        assert p['semantic_completeness']=='YES' and p['supported']==p['delivered']==2
        assert x['result']['response_status']['status']=='TRUNCATED'
        assert 'Human' in p['alternative'] or 'human' in p['alternative']


def fixture_registration(tmp_path,rows):
    # Deliberately test-only data, never saved in research artifacts.
    source=tmp_path/'TEST_ONLY_simulated_message.txt';source.write_text('TEST FIXTURE, not an actual researcher decision.',encoding='utf-8')
    snap=tmp_path/'TEST_ONLY_snapshot.json';snap.write_text(json.dumps(rows),encoding='utf-8')
    return {'researcher':'Yaxin ZHENG','decision':'ANNOTATIONS_CONFIRMED','source_message_path':str(source),
        'source_message_sha256':r.s.sha256(source),'annotation_snapshot_path':str(snap),'annotation_snapshot_sha256':r.s.sha256(snap)}


def test_gate_requires_registered_human_snapshot_and_fixed_priority(tmp_path):
    rows=gate.panel_from_review_csv(r.OUT/'consolidated_researcher_review_v2.csv')
    assert len(rows)==32 and gate.decide(rows)['selected_configuration'] is None
    for con in ('D0','D1','D2','D3'):
        group=sorted([x for x in rows if x['condition']==con],key=lambda x:x['case_id'])
        for i,x in enumerate(group):
            x['researcher_decision']='Correct' if i<(6 if con=='D0' else 8) else 'Incorrect'
            x['automatic_task_success']=gate.LABELS[x['researcher_decision']]
    reg=fixture_registration(tmp_path,rows)
    assert gate.decide(rows,reg)['selected_configuration']=='D0'  # Not the highest accuracy.
    bad=copy.deepcopy(rows);bad[0]['researcher_decision']='Partially correct'
    with pytest.raises(ValueError):gate.decide(bad,reg)


def test_gate_does_not_drop_uncertain_or_partial_denominators(tmp_path):
    rows=gate.panel_from_review_csv(r.OUT/'consolidated_researcher_review_v2.csv')
    for con in ('D0','D1','D2','D3'):
        group=sorted([x for x in rows if x['condition']==con],key=lambda x:x['case_id'])
        for i,x in enumerate(group):
            x['researcher_decision']='Correct' if i<6 else 'Partially correct' if i==6 else 'Missing'
            x['automatic_task_success']='Success' if i<6 else 'Failure'
    out=gate.decide(rows,fixture_registration(tmp_path,rows))
    assert out['status']=='NO_CONFIGURATION_QUALIFIED'
    assert not out['fallback_activated']
    assert all(x['denominator']==8 and x['automatic_agreement']==6 for x in out['condition_counts'].values())


def test_descriptive_readiness_does_not_certify_AI_scores():
    x=r.s.load(r.OUT/'descriptive_analysis_UNCONFIRMED_v2.json')
    assert x['decision']['status']=='SCIENTIFIC DECISION PENDING REVIEW'
    assert all(v['audited_task_success'] is None for v in x['conditions'].values())
    assert x['fidelity']['zero_imputation'] is False
    assert sum(v['n'] for v in x['conditions'].values())==32
