import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))
from english_swda_metadata_qualification_v1_1 import normalized_dates


def test_unpadded_calendar_and_unknown():
    original = {'x': {'talk_day': '1991-10-1'}, 'y': {'talk_day': 'NaT'}, 'z': {'talk_day': '1991-2-30'}}
    result = normalized_dates(original)
    assert result['x']['talk_day'] == '1991-10-01'
    assert original['x']['talk_day'] == '1991-10-1'
    assert result['y']['talk_day'] == 'NaT'
    assert result['z']['talk_day'] == '1991-2-30'
