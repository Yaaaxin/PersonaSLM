import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_instruct_measurement as m

def test_saved_proposals_reconstruct_without_human_adoption():
    values=m.build()
    for name,value in values.items():assert m.s.load(m.OUT/name)==value
    assert values['summary_v1.json']['human_ratings']==0
    assert values['summary_v1.json']['requests']==8
    assert values['summary_v1.json']['all_condition_SFH_execution_ready'] is False

def test_wrong_complete_answer_separate_from_task_success():
    rows=m.s.load(m.OUT/'AI_proposals_UNCONFIRMED_v1.json')
    wrong_complete=[r for r in rows if r['factual']=='Incorrect' and r['semantic_completeness']=='YES']
    assert len(wrong_complete)==3
    assert all(r['task_success']=='Failure' for r in wrong_complete)
    assert sum(len(r['required_components']) for r in rows)==14

def test_eos_alias_never_rewrites_source_status():
    source=m.s.load(m.s.OUT/'execution_integrity_v1.json')
    assert sum(x['result']['response_status']['status']=='AMBIGUOUS' for x in source['rows'])==7
    assert sum(x['result']['stop_reason']=='eos' for x in source['rows'])==7
    assert all(x['result']['response_status']['unit_identifiable'] for x in source['rows'])

def test_oracle_manifest_is_not_authorization_or_track_a():
    p=m.s.load('docs/validation/p5/oracle_evidence_proposed_v1/oracle_evidence_manifest_proposed_v1.json')
    parent=m.s.load(m.s.FROZEN)
    assert p['authorized_requests']==0 and p['proposed_requests']==8
    for q,r in zip(p['requests'],parent['requests']):
        assert q['case_id']==r['case_id'] and q['reference']==r['reference']
        assert q['seed']==r['seed'] and q['max_new_tokens']==r['max_new_tokens']==96
        assert q['prompt_sha256']!=r['prompt_sha256']
        assert q['input_tokens']<r['input_tokens']
        assert q['split']=='DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION'
