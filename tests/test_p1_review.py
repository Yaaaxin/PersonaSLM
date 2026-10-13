"""Importer software tests; fabricated test labels are never research annotations."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('review',Path('tools/p1_review.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)

def fixture():
    row={'candidate_id':'TEST_ONLY','condition_id':'N_style','matching_status':'PASS','token_difference':'0',
        'review_version':review.VERSION,'packet_id':'test-packet','neutral_text':'TEST FIXTURE',
        **{k:'' for k in review.EDITABLE}}
    master={'items':[deepcopy(row)]}
    for q in review.QUESTIONS:row['check_'+q]='PASS'
    row.update(researcher_decision='ACCEPT_NARROW',reviewer_id='SOFTWARE_TEST_ONLY',review_assistance='unaided')
    return master,list(row),[row]

def test_import_contract_with_unknown_review_time():
    master,fields,rows=fixture();result=review.validate(master,fields,rows)
    assert result['annotation_count']==1 and result['rows'][0]['reviewed_utc']==''
    assert result['generation_authorized_by_import'] is False

@pytest.mark.parametrize('issue',['missing','invalid','duplicate','version','reviewer','provenance','text','conflict','missing_quote','style_conflict'])
def test_reject_invalid_or_incomplete_annotations(issue):
    master,fields,rows=fixture();row=rows[0]
    if issue=='missing':row['check_answer_leakage']=''
    if issue=='invalid':row['check_answer_leakage']='yes'
    if issue=='duplicate':rows.append(deepcopy(row))
    if issue=='version':row['review_version']='wrong'
    if issue=='reviewer':row['reviewer_id']=''
    if issue=='provenance':row['review_assistance']=''
    if issue=='text':row['neutral_text']='Changed'
    if issue=='conflict':row.update(check_answer_leakage='FAIL',evidence_quotations='TEST ONLY')
    if issue=='missing_quote':row.update(check_answer_leakage='UNCERTAIN',researcher_decision='UNCERTAIN')
    if issue=='style_conflict':row.update(check_unintended_style='FAIL',evidence_quotations='TEST ONLY')
    with pytest.raises(ValueError):review.validate(master,fields,rows)
