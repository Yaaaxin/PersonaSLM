import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from p1d_boundary_locality import inspect

def test_later_heading_does_not_change_candidate_prefix():
    short='Locker 111.\nUser: Next?'
    long=short+'\nSummary: More dialogue.'
    a=inspect(short,{'stop_type':'limit'});b=inspect(long,{'stop_type':'limit'})
    assert a['original_identifiable'] and not b['original_identifiable']
    assert a['local_prefix_candidate']==b['local_prefix_candidate']
    assert b['marker_locations'][0]['relative_to_first_role']=='after'

def test_heading_inside_first_reply_is_not_silently_removed():
    r=inspect('Answer: Locker 111.\nUser: Next?',{'stop_type':'limit'})
    assert r['local_prefix_candidate'] is None

def test_fenced_or_quoted_role_remains_uncertain():
    for raw in ('Example:\n```\nUser: literal\n```','The string User: is literal.\nUser: Next?'):
        assert inspect(raw,{'stop_type':'limit'})['local_prefix_candidate'] is None

def test_no_native_generation_or_semantic_accuracy_claim():
    r=inspect('Locker 111.',{'stop_type':'eog'})
    assert r['local_prefix_candidate'] is None
    assert r['independent_boundary_accuracy'] is None

def test_leading_assistant_prefix_offsets_are_original():
    raw=' Assistant: Locker 111.\nUser: Next?'
    span=inspect(raw,{'stop_type':'limit'})['local_prefix_candidate']
    assert raw[span['start']:span['end']]==span['text']=='Locker 111.\n'
