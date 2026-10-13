"""Independent constructed examples for measurement boundaries and reviewer integrity."""
from copy import deepcopy
import pytest
from personaslm.measurement_audit import partition,sentence_form,make_packet,validate_annotations,HUMAN_FIELDS
from personaslm.response_status import classify_response


def case(family='A'):
    return {'case_id':'independent_case','speaker_name':'Morgan','family':family,'evaluation_date':'2026-05-12',
            'expected_answer':'Bristol' if family=='A' else 'Elm Reading Circle',
            'question':'Where does Morgan currently live?','trusted_evidence':'Morgan lives in Bristol.',
            'context':['User: Use the current record.'],
            'applicability':{'factual_consistency':True,'temporal_consistency':True,'response_relevance':True,'conversational_coherence':True,'linguistic_fidelity':False,'behavioral_fidelity':False},
            'facts':[{'fact_id':'city','attribute':'current_city','value':'Bristol','valid_from':'2026-05-01','valid_until':None},
                     {'fact_id':'club','attribute':'reading_group','value':'Elm Reading Circle','valid_from':'2025-01-01','valid_until':None}]}


def row(raw=' Morgan currently lives in Bristol.\nUser: Another question',condition='C0'):
    native={'stop_type':'limit','truncated':False};boundary=classify_response(raw,native)
    return {'request_id':'independent_case__'+condition,'case_id':'independent_case','persona_id':'independent_person',
            'condition':condition,'factors':[0,0,0],'raw_response':raw,'raw_termination':native,
            'parsed_response':boundary['first_span']['text'],'generated_tokens':96,'stop_reason':'length',
            'evaluation':{'response_completeness':boundary},'parser_operations':{
                'first_span':boundary['first_span'],'removed_prefix':boundary['removed_prefix'],'excluded_continuation':boundary['excluded_tail']}}


def completed(master):
    records=deepcopy(master)
    for r in records:
        r.update(human_reply_unit_confirmed='YES',human_semantic_completeness='COMPLETE',
                 human_factual_consistency='Correct',human_temporal_consistency='Correct',
                 human_response_relevance_1_to_5='5',human_conversational_coherence_1_to_5='5',
                 reviewer_id='unit_test_identity',review_assistance='unaided',prior_access_to_treatments_or_scores='NO',
                 human_evidence_quotations='Synthetic test quotation, never saved as research annotation.')
    return records


def packet():
    return make_packet([row(),row(condition='C1')],{'independent_case':case()},727)


def test_partition_preserves_internal_newline_and_excluded_turns():
    r=row('Assistant: A first line.\nA second line.\nUSER: Follow-up\nAssistant: Extra')
    audit=partition(r)
    assert audit['first_reply']['text']=='A first line.\nA second line.\n'
    assert len(audit['additional_turns'])==2
    assert audit['semantic_completeness']=='UNREVIEWED'


def test_partition_rejects_silently_changed_span():
    r=row();r['parsed_response']='Bristol.'
    with pytest.raises(ValueError,match='partition'):partition(r)


def test_open_deliberation_is_not_promoted_to_a_quoted_answer():
    text='<think>Perhaps say "Welcome!" but consider'
    assert sentence_form(case(),text)['observed_form']=='OPEN_DELIBERATION_PREFIX'
    assert partition(row(text))['first_reply_budget_censored']


@pytest.mark.parametrize('text',[
    'Morgan does not currently live in Bristol.',
    'Morgan currently lives in Bristol. Morgan also lives in York.',
    'Taylor currently lives in Bristol.',
    'Someone said "Morgan currently lives in Bristol."',
    'Morgan currently lives in Bristol, valid from 2025-05-01 onward.',
    'Morgan currently lives in Bristol or York.',
    'Morgan currently lives in Bristol because',
])
def test_whole_span_binding_rejects_misleading_substrings(text):
    result=sentence_form(case(),text)
    assert not result['whole_span_source_form_match']
    assert result['replacement_score'] is None
    assert result['possible_causes']['contradictory_answer'] is None


def test_date_form_is_diagnostic_without_rescoring():
    result=sentence_form(case(),' Morgan currently lives in Bristol, valid from 2026-05-01 onward.\n')
    assert result['observed_form']=='DATED_CURRENT_CITY_SENTENCE'
    assert result['bound_source_fact']['fact_id']=='city'
    assert result['human_factual_label'] is None and result['semantic_completeness'] is None


def test_outdated_source_interval_is_not_bound_as_current():
    c=case();c['facts'][0]['valid_until']='2026-05-02'
    assert not sentence_form(c,'Morgan currently lives in Bristol.')['whole_span_source_form_match']


def test_membership_route_is_separate_from_city():
    result=sentence_form(case('B'),'The verified record shows that Morgan is a member of the Elm Reading Circle.')
    assert result['observed_form']=='ATTRIBUTED_MEMBERSHIP_SENTENCE'
    assert result['possible_causes']['other_unsupported_task_type']


def test_review_masks_treatment_and_keeps_shared_reference_and_blanks():
    records,key=packet()
    assert len({r['anonymous_case_id'] for r in records})==1
    assert len({r['reference_historical_facts'] for r in records})==1
    assert all(all(r[k]=='' for k in HUMAN_FIELDS) for r in records)
    assert all(not {'condition','request_id','factors','original_factual_label'} & r.keys() for r in records)
    assert {r['condition'] for r in key['rows']}=={'C0','C1'}
    assert packet()==(records,key)


def test_blank_packet_cannot_be_registered_as_completed():
    records,_=packet()
    with pytest.raises(ValueError,match='unit judgment'):validate_annotations(records,records)


@pytest.mark.parametrize('change', ['duplicate','version','evidence','applicability','label','reviewer','masking','quotation','uncertainty'])
def test_review_import_rejects_invalid_or_changed_material(change):
    master,_=packet();records=completed(master)
    if change=='duplicate':records[1]=deepcopy(records[0])
    elif change=='version':records[0]['review_version']='different'
    elif change=='evidence':records[0]['trusted_evidence']='Changed'
    elif change=='applicability':records[0]['human_factual_consistency']='Not Applicable'
    elif change=='label':records[0]['human_semantic_completeness']='PASS'
    elif change=='reviewer':records[0]['reviewer_id']=''
    elif change=='masking':records[0]['prior_access_to_treatments_or_scores']=''
    elif change=='quotation':records[0]['human_evidence_quotations']=''
    else:records[0]['human_factual_consistency']='Unverifiable'
    with pytest.raises(ValueError):validate_annotations(master,records)


def test_valid_import_does_not_invent_review_time_or_blinding():
    master,_=packet();records=completed(master);result=validate_annotations(master,records)
    assert result['validated_records']==2 and result['unavailable_review_times']==2
    assert not result['blind_review_asserted'] and not result['frozen_scores_overwritten']
    assert all(not r['reviewed_utc'] for r in records)
