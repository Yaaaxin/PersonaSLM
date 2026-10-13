"""Analysis contracts on explicit software fixtures, not experimental results."""
import importlib.util
from pathlib import Path
import pytest
from personaslm.conditioning import FACTORIAL

spec=importlib.util.spec_from_file_location('analysis',Path('tools/p1_analyze.py'))
analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)

def rows():
    return [{'case_id':'TEST_'+str(i),'persona_id':'TEST_'+str(i),'family':family,'condition':condition,
        'applicability':{'factual_consistency':family!='C','temporal_consistency':family in 'AD'},
        'evaluation':{'response_completeness':{'status':'TRUNCATED'},'factual_support':{'label':'Not Applicable' if family=='C' else 'Unverifiable'}},
        'generated_tokens':96,'latency_seconds':1.0}
        for i,family in enumerate('ABCD'*3) for condition in FACTORIAL]

def test_uncertainty_and_planned_denominators_preserved():
    result=analysis.summarize(rows())['C0']
    assert result['factual']['primary_denominator']==9 and result['factual']['conclusively_classified']==0
    assert result['factual']['categories']['Unverifiable']==9
    assert result['temporal']['effect_estimate'] is None

@pytest.mark.parametrize('family','ABCD')
def test_family_specific_eligibility_is_not_global(family):
    result=analysis.summarize([r for r in rows() if r['family']==family],family)['C0']
    assert result['planned']==3 and result['factual']['eligible']==(0 if family=='C' else 3)
    assert result['temporal']['eligible']==(3 if family in 'AD' else 0)

def test_missing_cells_not_silently_removed():
    data=rows();partial=analysis.contrasts(data[1:]);bad=[p for p in partial['paired_cases'] if p['status']=='INCOMPLETE']
    assert len(bad)==1 and bad[0]['contrasts'] is None
    assert partial['structural_factorial_summaries']['TRUNCATED']['planned_speakers']==12
    with pytest.raises(ValueError):analysis.contrasts(data+[data[0]])
