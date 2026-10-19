import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import pytest
import core_sfh_readiness as c
import persona_fidelity_distinction as f

@pytest.fixture(scope='module')
def materials():
    return c.s.load(c.OUT/'core_sfh_manifest_proposed_v1.json'),c.s.load(c.OUT/'candidate_materials_v1.json')['cases']

def test_candidate_inventory_and_not_authorized(materials):
    p,cs=materials;r=c.validate(p,cs)
    assert r['requests']==80 and r['cases']==8 and r['speakers']==8
    assert set(r['families'].values())=={2}
    assert p['authorized_requests']==0 and not p['independent_validation_authorized']
    assert p['source_code_sha256']==c.s.sha256(Path('tools/core_sfh_readiness.py'))

def test_native_records_and_rendering(materials):
    p,_=materials;template=Path(p['template_path']).read_text(encoding='utf-8')
    for r,log in zip(p['requests'],p['native_tokenizer_logs']):
        assert c.s.sha256(Path(log['path']))==log['sha256']
        native=c.s.load(log['path'])
        assert native['generation_requests']==0 and native['returncode']==0
        assert c.ast.literal_eval(native['stdout'].strip())==r['input_token_ids']
        assert c.s.render(template,r['messages'])==r['prompt']
        assert c.s.th(r['prompt'])==r['prompt_sha256']
        assert r['request_sha256']==c.s.th(json.dumps({k:v for k,v in r.items() if k!='request_sha256'},sort_keys=True,separators=(',',':')))

@pytest.mark.parametrize('field',['trusted_evidence_sha256','reference_sha256','question_sha256','fixed_context_sha256','seed'])
def test_changed_paired_inputs_rejected(materials,field):
    p,cs=copy.deepcopy(materials);p['requests'][0][field]='changed'
    with pytest.raises(ValueError):c.validate(p,cs)

def test_sfh_routing_is_not_ev_or_h_none(materials):
    p,cs=materials
    assert c.CELLS=={'C0':(0,0,0),'C1':(1,0,0),'C2':(0,1,0),'C3':(0,0,1),
        'C4':(1,1,0),'C5':(1,0,1),'C6':(0,1,1),'C7':(1,1,1)}
    for row in p['requests']:
        case=next(x for x in cs if x['case_id']==row['case_id'])
        if row['condition'] not in c.CELLS:continue
        for field,on in zip(('style_intervention','personal_facts_intervention','history_intervention'),c.CELLS[row['condition']]):
            assert (case[field] in row['prompt'])==bool(on)
        assert all(v not in case['history_intervention'] for v in [x['value'] for x in case['required_components']])

def test_h1_is_not_average_interaction(materials):
    p,_=materials;con=p['contrasts'];values={k:0 for k in c.CELLS};values['C7']=1
    dot=lambda w:sum(values.get(k,0)*v for k,v in w.items())
    assert dot(con['H1_SxH_at_F0']['weights'])==0
    assert dot(con['SxH']['weights'])==.5
    assert con['style_vs_diagnostic']['weights']=={'C1':1,'N_style':-1}
    assert con['history_vs_diagnostic']['weights']=={'C3':1,'N_history':-1}
    assert len(con)==12 and all(abs(sum(v['weights'].values()))<1e-10 for v in con.values())

def test_fidelity_panels_no_keys_or_made_up_reviews():
    rows=f.examples();pf,q=f.panels(rows)
    assert len(rows)==len(pf)==len(q)==8
    for r in pf:
        assert 'trusted_evidence' not in r and 'authored_expected' not in r
        assert r['linguistic_fidelity']==r['behavioral_fidelity']==r['reviewer_id']==r['timestamp']==''
    assert all('profile' not in r and 'authored_expected' not in r for r in q)
    cases={x['challenge']:x['authored_expected'] for x in rows}
    assert cases['correct_history_only']['factual_support'] and not cases['correct_history_only']['requested_answer_present']
    assert cases['wrong_correct_persona']['linguistic_alignment'] and not cases['wrong_correct_persona']['factual_support']
    assert cases['history_recall_behavior_mismatch']['linguistic_alignment'] and not cases['history_recall_behavior_mismatch']['behavioral_alignment']
