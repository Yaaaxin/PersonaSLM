import json
from dataclasses import replace
from pathlib import Path

import pytest

from personaslm.evaluation_policy import category_accounting, evaluate_response
from personaslm.schemas import Case


@pytest.fixture
def case():
    value=json.loads((Path(__file__).parent/'fixtures/p0_evaluation_dev_v3.json').read_text())
    return Case.from_dict(value['case_definition'])


@pytest.mark.parametrize('raw,expected',[
    ('Morgan currently lives in Bristol.','Correct'),
    ('Morgan currently lives in Chester.','Incorrect'),
    ('Morgan is an architect.','Unverifiable'),
])
def test_cap_does_not_determine_factual_category(case,raw,expected):
    result=evaluate_response(case,raw,{'stop_type':'limit'})
    assert result['response_completeness']['status']=='TRUNCATED'
    assert result['factual_support']['label']==expected
    assert result['response_relevance']['rating'] is None
    assert result['temporal_consistency']['label']=='Unverifiable'


def test_generated_continuation_is_not_part_of_the_scored_first_reply(case):
    result=evaluate_response(case,'Morgan lives in Bristol.\nUSER: Where?\nAssistant: Morgan lives in Chester.',{'stop_type':'limit'})
    assert result['response_completeness']['status']=='CROSS_TURN'
    assert result['factual_support']['label']=='Correct'
    assert 'Chester' in result['response_completeness']['excluded_tail']


def test_ambiguous_content_is_not_certified_as_factual(case):
    result=evaluate_response(case,'Morgan lives in Bristol.',{'stop_type':'eog'},literal_delimiters=True)
    assert result['factual_support']['label']=='Unverifiable'


def test_predeclared_inapplicability_and_uncertainty_denominator(case):
    na=replace(case,applicability={k:False for k in case.applicability})
    rows=[evaluate_response(case,'Morgan lives in Bristol.',{'stop_type':'limit'}),
          evaluate_response(case,'An unknown story.',{'stop_type':'eog'}),
          evaluate_response(na,'Anything.',{'stop_type':'limit'})]
    assert rows[-1]['factual_support']['label']=='Not Applicable'
    assert rows[-1]['response_relevance']['label']=='Not Applicable'
    counts=category_accounting(rows)
    assert counts['all_preeligible']==2 and counts['counts']['Unverifiable']==1
    assert counts['uncertain_excluded_from_primary_denominator'] is False
