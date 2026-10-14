import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from p1d_format_diagnostic_proposal import reframe,source_format_audit,b

def test_reframe_preserves_everything_except_question_role_marker():
    p='EVIDENCE\nFact.\nFIXED CONTEXT\nUser: Hi.\nAssistant: OK.\nCURRENT QUESTION\nWhich?\nAssistant:'
    q=reframe(p,'Which?')
    assert q.replace('CURRENT QUESTION\nUser: Which?','CURRENT QUESTION\nWhich?')==p
    assert q.count('User:')==2

def test_refuse_unexpected_tail():
    with pytest.raises(ValueError):reframe('CURRENT QUESTION\nWhich?\n','Which?')

def test_actual_frozen_tail_and_historical_comparison():
    cases={c['case_id']:c for c in b.load(b.DEV/'development_examples_v5.json')['cases']}
    rows=b.load(b.FROZEN)['requests']
    for r in rows:
        text=reframe(r['prompt'],cases[r['case_id']]['question'])
        assert text.replace('\nCURRENT QUESTION\nUser: ','\nCURRENT QUESTION\n')==r['prompt']
        assert text.endswith('\nAssistant:') and not text.endswith('\n')
    a=source_format_audit()
    assert a['p1c_current_question_with_User_marker']==a['p1c_requests']==72
    assert a['p1d_current_question_without_User_marker']==a['p1d_requests']==144
