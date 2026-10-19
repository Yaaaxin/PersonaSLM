import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from personaslm_alignment import CELLS,contrasts
from p1_factorial_descriptive import all_descriptive,paired_contrast,cluster_sensitivity


def synthetic():
    return [{'case_id':str(i),'speaker_id':str(i),'condition':c,'evidence_sha256':str(i),'question_sha256':str(i),
             'reference_sha256':str(i),'evaluation_date':'2051-09-15','outcome':bits[2] if c in CELLS else 0,
             'provenance':'SYNTHETIC_TEST_ONLY_NOT_MODEL_OUTPUT'} for i in range(8) for c,bits in list(CELLS.items())+[('N_style',(0,0,0)),('N_history',(0,0,0))]]


def test_known_factorial_signal():
    d=all_descriptive(synthetic(),'outcome')
    assert d['H']['complete_case_mean']==1
    assert d['S']['complete_case_mean']==0 and d['SxH']['complete_case_mean']==0
    assert d['history_S0F0']['complete_case_mean']==1
    assert len(d)==12


def test_H1_not_average_interaction():
    rows=synthetic()
    for x in rows:x['outcome']=int(x['condition']=='C5')
    d=all_descriptive(rows,'outcome')
    assert d['H1_SxH_at_F0']['complete_case_mean']==1
    assert d['SxH']['complete_case_mean']==.5


def test_missing_cells_not_rescaled():
    rows=[{'case_id':'a','speaker_id':'s','condition':'C0','x':0},
          {'case_id':'b','speaker_id':'t','condition':'C0','x':0},
          {'case_id':'b','speaker_id':'t','condition':'C3','x':1}]
    d=paired_contrast(rows,{'C3':1,'C0':-1},'x')
    assert d['complete_cases']==1 and d['complete_case_mean']==1
    assert d['full_assigned_identification_bounds']==[.5,1]


def test_duplicate_and_invariant_guard():
    rows=synthetic();rows[0]['speaker_id']='wrong'
    with pytest.raises(ValueError,match='invariant'):all_descriptive(rows,'outcome')
    with pytest.raises(ValueError,match='Duplicate'):paired_contrast([rows[1],rows[1]],{'C1':1},'outcome')


def test_cluster_reproducibility():
    assert cluster_sensitivity([0,1,.5])==cluster_sensitivity([0,1,.5])
    assert cluster_sensitivity([1]*8)['interval']==[1,1]
