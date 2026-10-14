import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_fair_retrieval_baselines as m

def test_bm25_manual_single_occurrence():
    scores=m.bm25(['alpha','beta'],'alpha')
    assert math.isclose(scores[0],math.log(2))
    assert scores[1]==0

def test_tie_unchanged_by_candidate_order():
    p=[{'text':'same','id':str(i)} for i in range(4)]
    q={'text':'same'}
    assert m.ranking(p,q,'binary_overlap_top1')==[0,1,2,3]
    assert m.ranking(p[::-1],q,'bm25_top1')==[0,1,2,3]

def test_exact_entity_interval_inclusive_and_no_fallback():
    p=[{'text':'A','entity':'A','start':'2048-01-01','end':'2048-03-31'},
       {'text':'B','entity':'B','start':'2048-01-01','end':'2048-03-31'}]
    q={'text':'A','entity':'A','date':'2048-03-31'}
    assert m.ranking(p,q,'entity_time_then_bm25_top1')==[0]
    assert m.ranking(p,{**q,'date':'2048-04-01'},'entity_time_then_bm25_top1')==[]
