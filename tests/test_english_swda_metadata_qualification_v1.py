import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('swda_meta', Path(__file__).parents[1] / 'tools/english_swda_metadata_qualification_v1.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_partition_and_no_partner_leakage():
    speakers = {str(i): {} for i in range(30)}
    dev = [s for s in speakers if module.partition(s) == 'development']
    val = [s for s in speakers if module.partition(s) == 'reserved']
    rows = {}
    for i in range(4):
        rows[str(i)] = {'from_caller': dev[0], 'to_caller': dev[i+1], 'talk_day': f'1992-03-{i+1:02}', 'filename': 'authored'}
    rows['cross'] = {'from_caller': dev[0], 'to_caller': val[0], 'talk_day': '1992-04-01', 'filename': 'authored'}
    private, public = module.qualify(speakers, rows)
    assert public['cross_split_conversations_excluded'] == 1
    assert public['groups']['development']['speakers_with_four_dates_and_three_partners'] == 1
    assert 'cross' not in private['retained_conversation_metadata']
    assert all(module.partition(r['a']) == module.partition(r['b']) for r in private['retained_conversation_metadata'].values())


def test_unknown_date_is_not_chronology():
    a, b = '1', '2'
    _, public = module.qualify({a: {}, b: {}}, {'authored': {'from_caller': a, 'to_caller': b, 'talk_day': 'NaT', 'filename': 'authored'}})
    assert public['invalid_dates'] == 1
    assert sum(v['within_split_conversations'] for v in public['groups'].values()) == 0


def test_invalid_identity_rejected():
    import pytest
    with pytest.raises(ValueError):
        module.qualify({'1': {}}, {'authored': {'from_caller': '1', 'to_caller': '2', 'talk_day': '1992-01-01', 'filename': 'authored'}})
