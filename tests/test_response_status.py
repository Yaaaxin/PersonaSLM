"""Development tests only; holdout is evaluated after an explicit hash freeze."""
import json
from pathlib import Path

import pytest

from personaslm.response_status import classify_response, text_hash


def options(row):
    review = None
    if row.get("semantic"):
        review = {"label":row["semantic"],"basis":"Engineered software fixture, not a human judgment",
                  "raw_sha256":text_hash(row["raw"]),"review_id":row["id"]}
    return {"declared_stops":row.get("stops",[]),"literal_delimiters":row.get("literal",False),"semantic_review":review}


DEV = json.loads((Path(__file__).parent/'fixtures/p0_response_status_development_v1.json').read_text())['cases']


@pytest.mark.parametrize('row', DEV, ids=lambda r:r['id'])
def test_independent_development_cases(row):
    result=classify_response(row['raw'],{'stop_type':row['stop'],'stopping_word':row.get('stopping_word')},**options(row))
    assert result['status']==row['expected']
    assert result['first_span']['text']==row['first']
    assert result['removed_prefix']+result['first_span']['text']+result['excluded_tail']==row['raw']
    assert result['factual_judgment_used'] is False


def test_review_cannot_be_reused_for_different_raw_text():
    with pytest.raises(ValueError,match='raw hash'):
        classify_response('Changed.',{'stop_type':'eog'},semantic_review={'label':'COMPLETE','raw_sha256':text_hash('Original.'),'review_id':'test','basis':'test'})


def test_contradictory_backend_termination_is_not_silently_normalized():
    result=classify_response('Done.',{'stop_type':'eog','stopped_limit':True})
    assert result['status']=='AMBIGUOUS' and not result['unit_identifiable']
