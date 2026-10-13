"""Non-generation tests for prospective case validity and analysis conventions."""
from copy import deepcopy
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_design as d
from p1c_tokenize import select_match


@pytest.fixture(scope='module')
def bank():return d.read(d.DATA)


def test_frozen_material_reconstructs(bank):
    assert bank==d.build_cases()
    assert len(d.validate_cases(bank))==72


@pytest.mark.parametrize('case_index',range(12))
def test_reference_requires_every_fact_and_not_newest_shortcut(bank,case_index):
    case=bank['cases'][case_index]
    assert d.ground_truth(case)==case['reference']
    for needed in case['reference']['fact_ids']:
        with pytest.raises(ValueError):d.ground_truth(case,[f for f in case['facts'] if f['fact_id']!=needed])
    if case['query_mode']=='historical':
        assert d.ground_truth({**case,'requested_date':'2042-12-15'})['components']!=case['reference']['components']


@pytest.mark.parametrize('predicate',['collection desk','parcel route'])
def test_entity_foil_does_not_resolve_target(bank,predicate):
    case=next(c for c in bank['cases'] if any(f['predicate']==predicate for f in c['facts']))
    altered=deepcopy(case)
    for f in altered['facts']:
        if f['entity'].startswith('Archive colleague'):f['value']='DIFFERENT FOIL'
    assert d.ground_truth(altered)==case['reference']


def test_interval_endpoints_and_gap(bank):
    c=bank['cases'][0]
    assert d.ground_truth({**c,'requested_date':'2042-04-30'})['components']!=d.ground_truth({**c,'requested_date':'2042-05-01'})['components']
    with pytest.raises(ValueError):d.ground_truth({**c,'requested_date':'2043-01-01'})


def test_duplicate_support_is_rejected(bank):
    c=deepcopy(bank['cases'][0]);c['facts'].append(deepcopy(next(f for f in c['facts'] if f['fact_id']==c['reference']['fact_ids'][0])))
    with pytest.raises(ValueError,match='nonunique'):d.ground_truth(c)


def test_reference_corruption_rejected(bank):
    changed=deepcopy(bank);changed['cases'][0]['reference']['components']=['Wrong']
    with pytest.raises(ValueError,match='Reference'):d.validate_cases(changed)


@pytest.mark.parametrize('case_index',range(12))
def test_all_candidates_keep_track_a_and_temporal_scope(bank,case_index):
    c=bank['cases'][case_index]
    for cell in d.CONDITIONS:
        for v in d.history_candidates(c,cell):
            prompt=d.render(c,v['text'])
            for text in [c['trusted_evidence'],c['question'],c['fixed_context']]:assert prompt.count(text)==1
            assert not any(a.lower() in v['text'].lower() for a in c['reference']['components'])
            if cell.startswith('R'):
                f=d.active_fact(c,**d.CONDITIONS[cell])
                assert (f['start']<=c['requested_date']<=f['end'])==bool(d.CONDITIONS[cell]['T'])


def test_matched_selector_never_relaxes_tolerance():
    counts={c:[100]*16 for c in ['R0T0','R0T1','R1T0','R1T1']};counts['N_history']=[99]*32
    assert select_match(counts) is None
    counts['N_history'][0]=100
    assert select_match(counts)==(0,0)
    counts['R0T0']=[101]*16
    assert select_match(counts) is None


def test_selector_requires_same_question_and_active_variant():
    counts={c:[100]+[103]*15 for c in ['R0T0','R0T1','R1T0','R1T1']};counts['N_history']=[99]*32
    counts['N_history'][8]=100
    assert select_match(counts) is None
    counts['N_history'][8]=103
    assert select_match(counts)==(4,8)


def test_factorial_weights_against_known_polynomial():
    weights=d.read(d.PUBLIC/'condition_definitions_v1.json')['weights']
    values={c:v['R']+2*v['T']+3*v['R']*v['T'] for c,v in d.CONDITIONS.items() if c.startswith('R')}
    for metric,expected in [('R',2.5),('T',3.5),('RxT',3)]:
        assert sum(weights[metric].values())==0
        assert sum(w*values[c] for c,w in weights[metric].items())==expected


def test_simulation_reproducible_and_range_is_contrast_scale():
    a=d.precision_simulations(repeats=10,sizes=(6,));b=d.precision_simulations(repeats=10,sizes=(6,))
    assert a==b
    for row in a['rows']:
        expected=1.96*row['assumed_case_sd']*math.sqrt((1+row['assumed_contrast_ICC'])/12)
        assert row['analytical_1_96_halfwidth']==pytest.approx(expected)
        assert row['bonferroni_6_normal_halfwidth']>expected


def test_exclusive_write_preserves_previous_record(tmp_path):
    p=tmp_path/'record.json';d.write_json(p,{'value':1})
    with pytest.raises(FileExistsError):d.write_json(p,{'value':2})
    assert d.read(p)=={'value':1}


def test_native_selected_prompt_positions_include_empty_history_boundary():
    rows=d.read('docs/validation/p1c/proposed_v2/selected_prompts_v2.json')['records']
    assert len(rows)==72
    for cid in {r['case_id'] for r in rows}:
        cells=[r for r in rows if r['case_id']==cid]
        matched=[r for r in cells if r['condition']!='H_none']
        assert len({r['input_tokens'] for r in matched})==1
        assert len({r['fixed_context_suffix_start_token'] for r in matched})==1
        assert len({r['evidence_prefix_tokens'] for r in cells})==1
        suffixes=[r['input_token_ids'][r['fixed_context_suffix_start_token']:] for r in cells]
        assert all(s==suffixes[0] for s in suffixes)
        for r in cells:
            assert d.text_hash(r['prompt'])==r['prompt_sha256']
            assert len(r['input_token_ids'])==r['input_tokens']


def test_minimal_revision_preserves_active_material(bank):
    rows=d.read('docs/validation/p1c/proposed_v2/selected_prompts_v2.json')['records']
    native=d.read('docs/validation/p1c/proposed_v2/tokenizer_validation_v2.json')
    plan=d.read('docs/validation/p1c/proposed_v2/revision_plan_v2.json')
    assert plan['new_neutral_reply'].replace('two distinct parts','two parts')==plan['old_neutral_reply']
    for case in bank['cases']:
        vi=next(m['active_variant'] for m in native['matches'] if m['case_id']==case['case_id'])
        for r in rows:
            if r['case_id']==case['case_id'] and r['condition'].startswith('R'):
                assert r['history']==d.history_candidates(case,r['condition'])[vi]['text']


def test_original_failed_bank_and_native_probes_preserved():
    old=d.read(d.PUBLIC/'tokenizer_validation_v1.json')
    assert all(m['status']=='FAILED' and m['best_neutral_maximum_absolute_difference']==1 for m in old['matches'])
    assert len(old['historical_id_probes'])==3
    assert all(p['input_token_ids_equal'] for p in old['historical_id_probes'])
    new=d.read('docs/validation/p1c/proposed_v2/tokenizer_validation_v2.json')
    assert new['identity']['model_sha256']==old['identity']['model_sha256']
    assert new['v1_results_sha256']==d.sha(d.PUBLIC/'tokenizer_validation_v1.json')


def test_selected_controls_have_no_invented_human_labels():
    import csv
    with open('docs/validation/p1c/proposed_v2/history_semantic_review_v2.csv',encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==60
    assert len({(r['case_id'],r['condition']) for r in rows})==60
    assert all(v=='' for r in rows for k,v in r.items() if k.startswith('review_') or k in ('reviewer_id','reviewed_utc'))
