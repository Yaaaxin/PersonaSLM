import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from personaslm_alignment import *
import pytest

def contrast(name,ys):return sum(w*ys[c] for c,w in contrasts()[name]['weights'].items())

def test_registered_cell_identities():
    assert CELLS['C3']==(0,0,1) and CELLS['C5']==(1,0,1) and CELLS['C4']==(1,1,0)

def test_simple_interaction_not_average_interaction():
    y={c:s*h*(1-f) for c,(s,f,h) in CELLS.items()}
    assert contrast('H1_SxH_at_F0',y)==1
    assert contrast('SxH',y)==.5

@pytest.mark.parametrize('factor,index',[('S',0),('F',1),('H',2)])
def test_main_effect_on_additive_surface(factor,index):
    y={c:sum((i+1)*v for i,v in enumerate(x)) for c,x in CELLS.items()}
    assert contrast(factor,y)==index+1
    assert contrast('SxH',y)==0

def test_three_way_scale_and_constant_invariance():
    assert contrast('SxFxH',{c:s*f*h for c,(s,f,h) in CELLS.items()})==1
    for name in list(contrasts())[:8]:assert contrast(name,{c:7 for c in CELLS})==0

def test_no_fidelity_from_short_or_correct_answer():
    assert not features('L2.')['sufficient_style_opportunity']
    assert features('Locker L2. Noted.')==features('Locker L9. Noted.')
    assert all(not r['human_rating'] for r in examples())
