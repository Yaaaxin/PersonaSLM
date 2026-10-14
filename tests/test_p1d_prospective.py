import copy
import json
import random
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from p1d_design import OUT,CELLS,WEIGHTS,FAMILIES,examples,derive,check_case,allocation,read,sha,th
from p1d_analysis import case_contrast,cluster_summary,boundary_errors
from p1d_offline_baselines import select,fixtures,verify_structured
from p1d_precision import one

@pytest.mark.parametrize('case',examples(),ids=lambda c:c['case_id'])
def test_reference_and_intervention(case):
    assert check_case(case)
    assert len(case['required_components'])==(1 if case['family']=='single_fact' else 2)
    assert case['histories']['E1V1']['answer_supporting']
    assert not case['independent_validation']
    assert case['human_validity_decision']==''

@pytest.mark.parametrize('n',[48,96,144])
def test_balanced_cluster_allocation(n):
    rows=allocation(n);assert len(rows)==2*n
    for f in FAMILIES:
        group=[r for r in rows if r['family']==f]
        assert len(group)==n//2
        assert len({r['speaker_index'] for r in group})==n//2
        assert sum(r['date_type']=='current' for r in group)==n//4
    for s in range(n):assert len({r['family'] for r in rows if r['speaker_index']==s})==2

def test_name_and_relation_shortcuts_removed():
    cases=examples();names={c['target_entity'] for c in cases}
    assert not names & {c['other_entity'] for c in cases}
    for case in cases:
        edges=[f for f in case['facts'] if f['predicate']=='hub']
        assert not all(int(f['value'].split()[-1])-int(f['entity'].split()[-1])==100 for f in edges)

def test_conflicting_truth_rejected():
    case=examples()[0];f=copy.deepcopy(next(f for f in case['facts'] if f['entity']==case['target_entity'] and f['predicate']=='locker' and f['start']<=case['query_date']<=f['end']))
    f['value']='Different';case['facts'].append(f)
    with pytest.raises(ValueError):derive(case)

def test_snapshot_reconstruction():
    assert read(OUT/'development_examples_v3.json')['cases']==examples()
    prompts=read(OUT/'development_prompts_v3.json')
    assert len(prompts)==96
    for case in examples():
        rows=[r for r in prompts if r['case_id']==case['case_id']]
        assert {r['condition'] for r in rows}==set(CELLS)
        for field in ('evidence_sha256','question_sha256','reference','fixed_context_sha256','query_date'):
            assert all(r[field]==rows[0][field] for r in rows)
        assert all(th(r['prompt'])==r['prompt_sha256'] for r in rows)

@pytest.mark.parametrize('c',list(WEIGHTS))
def test_contrast_no_rescaling(c):
    assert sum(WEIGHTS[c].values())==0
    assert case_contrast(dict.fromkeys(CELLS,1),c)['complete_case_contrast']==0
    x=case_contrast(dict.fromkeys(CELLS,None),c)
    assert x['complete_case_contrast'] is None and x['lower']<0<x['upper']

def test_known_factorial_function():
    # y=.2 + .1 E + .2 V + .3 EV: averaged E=.25, V=.35, interaction=.3.
    v=dict(zip(CELLS,(.2,.4,.3,.8,0,0)))
    assert case_contrast(v,'E')['complete_case_contrast']==pytest.approx(.25)
    assert case_contrast(v,'V')['complete_case_contrast']==pytest.approx(.35)
    assert case_contrast(v,'ExV')['complete_case_contrast']==pytest.approx(.3)
    v['E1V1']=None;x=case_contrast(v,'ExV');assert x['lower']==pytest.approx(-.5) and x['upper']==pytest.approx(.5)

def test_speaker_resampling_deterministic():
    rows=[{'speaker_id':str(s),'value':v} for s,v in enumerate((-.5,0,.5)) for _ in range(2)]
    assert cluster_summary(rows,repeats=100)==cluster_summary(rows,repeats=100)
    assert cluster_summary(rows,repeats=100)['equal_speaker_mean']==0
    with pytest.raises(ValueError):cluster_summary(rows[:2])

@pytest.mark.parametrize('missing',['none','balanced_10','condition_dependent'])
def test_simulation_deterministic_bounds(missing):
    a=one(random.Random(22),48,.5,.4,.25,missing,.05)
    assert a==one(random.Random(22),48,.5,.4,.25,missing,.05)
    assert all(r['realized_complete_data_mean_in_bounds'] for r in a.values())
    assert a['ExV']['truth']==.1

def test_structured_checks_construct_separation():
    case=examples()[0];bank=fixtures(case)
    for f in bank:
        out=verify_structured(f['payload'],case['facts'],f['query'])
        assert out['factual']==f['authored_expected_factual']
        assert out['task_success']==f['authored_expected_success']
    for name in ('correct_partial','promise_with_correct_mentions'):
        f=next(x for x in bank if x['id']==name);r=verify_structured(f['payload'],case['facts'],f['query'])
        assert r['factual']=='Correct' and not r['task_success']

def test_boundary_does_not_invent_truth():
    assert boundary_errors((0,10),[(0,10)],False)['accuracy'] is None
    assert boundary_errors((0,10),[(0,10),(0,12)],True)['unique_gold'] is False
    assert boundary_errors((0,12),[(0,10)],True)['over_extraction_chars']==2
    assert boundary_errors((0,8),[(0,10)],True)['under_extraction_chars']==2
    assert boundary_errors(None,[],True)['accuracy']==1

def test_tokenizer_records_and_actual_failures_preserved():
    t=read(OUT/'tokenizer_validation_v1.json')
    assert t['new_generations']==0 and t['context_fit_all']
    assert len(t['rows'])==96
    assert sum(r['active_equal'] for r in t['matches'])==14
    assert sum(r['control_equal'] for r in t['matches'])==0
    for r in t['rows']:assert len(r['input_token_ids'])==r['input_tokens']

def test_frozen_p1c_seal():
    manifest=read('docs/validation/p1c/confirmed_semantic_v1/reproducibility_manifest_v1.json')
    for p,h in manifest['artifact_sha256'].items():assert sha(p)==h,p
    assert sha('docs/P1c_final_annotation_confirmation_packet_v1.md')=='4989e36d8d862c5995221b470adb8c9620ba7023ffc8ebf9d492cda18f6fc817'

def test_all_p1d_json_csv_and_no_approval():
    import csv
    for path in OUT.rglob('*.json'):read(path)
    for path in OUT.rglob('*.csv'):
        with path.open(encoding='utf-8',newline='') as f:
            for r in csv.DictReader(f):assert None not in r,path
    config=read(OUT/'model_configuration_proposal_v1.json')
    assert config['requests']['authorized_now']==0
    assert config['requests']['frozen_request_manifest'] is None
    assert len(WEIGHTS)==16
    assert len(read(OUT/'metric_applicability_v2.json'))==96

def test_prospective_subset_reconstruction():
    from p1d_allocation import selection
    selected=read(OUT/'allocation_selection_v1.json')
    assert selected==selection()
    assert len(set(selected['independent_review_speaker_indices']))==36
    assert len(set(selected['instruct_speaker_indices']))==24
    assert {s%24 for s in selected['instruct_speaker_indices']}==set(range(24))

def test_exact_prospective_approval_objects():
    packet=read(OUT/'researcher_decision_packet_v1.json')
    assert packet['researcher_decision']=='' and packet['human_review_timestamp'] is None
    assert packet['proposed_scope']['authorized_now']==0
    for p,h in packet['bound_documents_sha256'].items():assert sha(p)==h,p
    assert 'E/V' in Path('docs/P1d_protocol_addendum_proposed.md').read_text(encoding='utf-8')

def test_published_baseline_provenance():
    summary=read(OUT/'offline_baselines_v2/summary_v1.json')
    assert summary['source_sha256']==sha('tools/p1d_offline_baselines.py')
    assert summary['independent_accuracy'] is None
    old=read(OUT/'offline_baselines/summary_v1.json')
    assert old['source_sha256']==sha(OUT/'offline_baselines/source_v1.py')
    assert all(not r['implementation_replicated'] for r in read(OUT/'related_work_matrix_v4.json')['papers'])

def test_stress_reconstruction_and_policy_counts():
    assert read(OUT/'precision_stress_reconstruction_v1.json')['rows_equal']
    policy=read(OUT/'analysis_policy_proposal_v1.json')
    assert policy['eligible']['per_arm_responses']==policy['eligible']['cases']*6
    assert policy['eligible']['speakers_per_family']==72
    assert len(policy['primary_endpoints'])*len(policy['primary_contrasts'])==6
