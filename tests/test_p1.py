"""P1 contracts; strings in these tests are software fixtures, not real outputs."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest
from personaslm.conditioning import FACTORIAL,build_prompt
from personaslm.p1 import PilotCase,validate_dataset,wave_order,neutral_pool,evaluate_pilot,paired_factorial

def module(name):
    spec=importlib.util.spec_from_file_location(name,Path('tools')/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

@pytest.fixture
def data():return module('p1_build').build()

def test_complete_diverse_allocation_and_fixed_order(data):
    assert validate_dataset(data)['prompt_count']==384
    order=wave_order(data);assert len(order)==96 and order==wave_order(deepcopy(data))
    assert len({r['request_id'] for r in order})==96

@pytest.mark.parametrize('mutation',['evidence','identity','history','leak','overlap','applicability','duplicate','style'])
def test_invalid_manipulations_fail_before_inference(data,mutation):
    row=data['cases'][0]
    if mutation=='evidence':row['trusted_evidence']='Missing trusted record'
    if mutation=='identity':row['speaker_name']='Wrong'
    if mutation=='history':row['history_dialogue']=row['history_dialogue'].replace('2026-09-15','2026-10-15')
    if mutation=='leak':row['supplemental_fact']+=' '+row['expected_answer']
    if mutation=='overlap':row['facts'][0]['valid_until']='2026-10-20'
    if mutation=='applicability':row['applicability']['factual_consistency']=False
    if mutation=='duplicate':data['cases'][1]['case_id']=row['case_id']
    if mutation=='style':row['style_only']='Different'
    with pytest.raises(ValueError):validate_dataset(data)

@pytest.mark.parametrize('family',['A','B','C','D'])
def test_frozen_scope_and_manual_routing(data,family):
    c=PilotCase(next(r for r in data['cases'] if r['family']==family))
    raw=f'{c.speaker_name} currently lives in {c.facts[1].value}.'
    result=evaluate_pilot(c,raw,{'stop_type':'limit'})
    assert result['response_completeness']['status']=='TRUNCATED'
    assert result['factual_support']['label']==('Correct' if family in 'AD' else 'Unverifiable' if family=='B' else 'Not Applicable')
    assert result['response_relevance']['rating'] is None
    assert result['temporal_consistency']['label']==('Unverifiable' if family in 'AD' else 'Not Applicable')
    assert result['policy_version']=='separate_axes_policy_v1'

def test_first_span_preserved_without_incomplete_fact_penalty(data):
    c=PilotCase(data['cases'][0]);raw=f'{c.speaker_name} lives in {c.expected_answer}.\nUSER: More?\nAssistant: Something unrelated.'
    r=evaluate_pilot(c,raw,{'stop_type':'limit'});assert r['response_completeness']['status']=='CROSS_TURN'
    assert r['factual_support']['label']=='Correct' and 'Something unrelated' in r['response_completeness']['excluded_tail']

def test_wrong_city_distinct_from_unverifiable(data):
    c=PilotCase(data['cases'][0])
    assert evaluate_pilot(c,f'{c.speaker_name} lives in {c.facts[0].value}.',{'stop_type':'limit'})['factual_support']['label']=='Incorrect'
    assert evaluate_pilot(c,'I cannot establish that.',{'stop_type':'limit'})['factual_support']['label']=='Unverifiable'

@pytest.mark.parametrize('condition,count',[('N_style',36),('N_history',16)])
def test_bounded_candidate_pool_preserves_wrapper(data,condition,count):
    c=PilotCase(data['cases'][0]);pool=neutral_pool(c,condition)
    assert len(pool)==len(set(pool))==count
    for text in pool:
        p=build_prompt(c,condition,neutral_override=text)
        assert c.expected_answer not in text and c.trusted_evidence in p.text and c.question in p.text
        assert ('Speaker style profile:' in p.text)==(condition=='N_style')
    # No approximate tokenizer claim is made by this software test.

def test_simple_and_average_factorial_contrasts_are_different():
    values={c:float(s*h) for c,(s,f,h) in FACTORIAL.items()};r=paired_factorial(values)
    assert r['C1-C0']==0 and r['average_main_effects']['S']==0.5
    assert r['difference_in_differences']['SxH']==1 and r['difference_in_differences']['SxFxH']==0
    with pytest.raises(ValueError):paired_factorial({'C0':0})

def test_resume_never_retries_an_uncertain_attempt(data):
    runner=module('p1_wave');order=wave_order(data);previous=[[{'kind':'p1_generation_started','data':order[0]}]]
    remaining=runner.pending_requests(order,previous)
    assert len(remaining)==95 and order[0] not in remaining
    with pytest.raises(ValueError):runner.pending_requests(order,previous+previous)
