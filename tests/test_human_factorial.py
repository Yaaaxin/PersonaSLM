"""Synthetic software fixtures only; these are not human research annotations."""
from copy import deepcopy
import csv
from pathlib import Path

import pytest

from personaslm.conditioning import FACTORIAL
from personaslm.human_factorial import analyze, material_differences, normalize_confirmed, weights
from personaslm.measurement_audit import HUMAN_FIELDS


def review_fixture():
    with (Path(__file__).parents[1]/'docs/validation/p1/output_human_review_v1.csv').open(encoding='utf-8-sig',newline='') as stream:
        master=list(csv.DictReader(stream))
    proposed=deepcopy(master); ledger=[]
    for row in proposed:
        row.update(human_reply_unit_confirmed='true',human_semantic_completeness='complete',
            human_factual_consistency='correct' if row['applicable_factual_consistency']=='true' else '',
            human_temporal_consistency='correct' if row['applicable_temporal_consistency']=='true' else '',
            human_response_relevance_1_to_5='4',human_conversational_coherence_1_to_5='3',
            human_evidence_quotations='Synthetic test-only evidence',reviewer_notes='Synthetic test note; never imported.',
            reviewer_id='Yaxin_ZHENG',review_assistance='Test-only proposed coding')
        record={k:row[k] for k in ('anonymous_response_id','anonymous_case_id')}
        record['reviewer_original_note']=row['reviewer_notes']
        for old,new in [('reply_unit_confirmed','reply_unit_confirmed'),('semantic_completeness','semantic_completeness'),
                        ('factual_consistency','factual_consistency'),('temporal_consistency','temporal_consistency'),
                        ('response_relevance_1_to_5','response_relevance_1_to_5'),('conversational_coherence_1_to_5','conversational_coherence_1_to_5')]:
            record['proposed_'+old]=row['human_'+new]
        ledger.append(record)
    return master,proposed,ledger


def test_normalization_preserves_every_score_note_and_unknown_time():
    master,proposed,ledger=review_fixture(); before=deepcopy(proposed)
    registered,changes,validation=normalize_confirmed(master,proposed,ledger)
    assert proposed==before and validation['validated_records']==96
    for source,row in zip(proposed,registered):
        assert row['reviewer_notes']==source['reviewer_notes']
        assert row['human_response_relevance_1_to_5']=='4'
        assert row['human_conversational_coherence_1_to_5']=='3'
        assert row['reviewed_utc']==''
        assert row['prior_access_to_treatments_or_scores']=='UNCERTAIN'
        assert len(row)==41
    assert changes


@pytest.mark.parametrize('field',[k for k in review_fixture()[0][0] if k not in HUMAN_FIELDS])
def test_every_frozen_field_is_compared(field):
    master,proposed,_=review_fixture()
    if field=='anonymous_response_id':
        proposed[0][field]='UNKNOWN'
        with pytest.raises(ValueError):material_differences(master,proposed)
    elif field=='anonymous_case_id':
        proposed[0][field]='UNKNOWN'
        with pytest.raises(ValueError):material_differences(master,proposed)
    else:
        proposed[0][field]+='!'
        assert material_differences(master,proposed)[0]['field']==field


@pytest.mark.parametrize('problem',['duplicate','note','applicable_blank','inapplicable_score','unknown_label','ledger_score','reviewer'])
def test_invalid_sources_are_not_registered(problem):
    master,p,l=review_fixture()
    if problem=='duplicate':p[1]=deepcopy(p[0])
    if problem=='note':p[0]['reviewer_notes']='changed'
    if problem=='applicable_blank':
        r=next(r for r in p if r['applicable_factual_consistency']=='true');r['human_factual_consistency']=''
        next(q for q in l if q['anonymous_response_id']==r['anonymous_response_id'])['proposed_factual_consistency']=''
    if problem=='inapplicable_score':
        r=next(r for r in p if r['applicable_factual_consistency']=='false');r['human_factual_consistency']='correct'
        next(q for q in l if q['anonymous_response_id']==r['anonymous_response_id'])['proposed_factual_consistency']='correct'
    if problem=='unknown_label':p[0]['human_semantic_completeness']='maybe'
    if problem=='ledger_score':l[0]['proposed_response_relevance_1_to_5']='5'
    if problem=='reviewer':p[0]['reviewer_id']='invented'
    with pytest.raises(ValueError):normalize_confirmed(master,p,l)


def test_known_polynomial_contrast_scaling():
    # y=10+2S+3F+5H+7SF+11SH+13FH+17SFH
    values={c:10+2*s+3*f+5*h+7*s*f+11*s*h+13*f*h+17*s*f*h for c,(s,f,h) in FACTORIAL.items()}
    expected={'C1-C0':2,'C3-C0':5,'S':15.25,'F':17.25,'H':21.25,'SxF':15.5,'SxH':19.5,'FxH':21.5,'SxFxH':17}
    for contrast,value in expected.items():
        assert sum(w*values[c] for c,w in weights(contrast).items())==value
        assert sum(weights(contrast).values())==0


def analysis_fixture():
    result=[]
    for i,family in enumerate('ABCD'):
        for cond,bits in FACTORIAL.items():
            s,f,h=bits
            annotation={'human_response_relevance_1_to_5':str(2+s+f+h),
                'human_conversational_coherence_1_to_5':'4','human_semantic_completeness':'COMPLETE',
                'human_factual_consistency':'Correct' if family!='C' else 'Not Applicable',
                'human_temporal_consistency':'Correct' if family in 'AD' else 'Not Applicable',
                'applicable_response_relevance':'true','applicable_conversational_coherence':'true',
                'applicable_factual_consistency':str(family!='C').lower(),
                'applicable_temporal_consistency':str(family in 'AD').lower(),'structural_status':'CROSS_TURN'}
            result.append({'case_id':str(i),'persona_id':str(i),'family':family,'condition':cond,'factors':bits,'annotation':annotation})
    return result


def test_complete_cases_not_independent_responses_and_ceiling_warning():
    data=analyze(analysis_fixture(),replicates=50)
    assert data['contrasts']['relevance']['S']['estimate']==1
    assert data['contrasts']['relevance']['S']['evaluable_cases']==4
    assert data['contrasts']['relevance']['SxH']['estimate']==0
    fact=data['contrasts']['factual']['C1-C0']
    assert fact['eligible_cases']==3 and fact['estimate']==0
    assert fact['uncertainty']['bootstrap_degenerate']
    assert data['contrasts']['temporal']['H']['eligible_cases']==2


def test_unverifiable_is_missing_not_incorrect_and_only_needed_cells_required():
    rows=analysis_fixture(); rows[7]['annotation']['human_factual_consistency']='Unverifiable'
    data=analyze(rows,replicates=50)
    assert data['contrasts']['factual']['C1-C0']['evaluable_cases']==3
    assert data['contrasts']['factual']['S']['evaluable_cases']==2
    assert data['contrasts']['factual']['S']['eligible_cases']==3
    assert data['conditions']['factual']['C7']['unscorable']==1


def test_c0_incorrect_case_is_retained():
    rows=analysis_fixture();rows[0]['annotation']['human_factual_consistency']='Incorrect'
    data=analyze(rows,replicates=50)
    assert data['contrasts']['factual']['C1-C0']['estimate']==pytest.approx(1/3)
    assert data['contrasts']['factual']['C1-C0']['evaluable_cases']==3


@pytest.mark.parametrize('problem',['duplicate','missing','factors','speaker','applicability'])
def test_invalid_unblinded_dataset_rejected(problem):
    rows=analysis_fixture()
    if problem=='duplicate':rows.append(deepcopy(rows[0]))
    if problem=='missing':rows.pop()
    if problem=='factors':rows[0]['factors']=(1,1,1)
    if problem=='speaker':
        for r in rows:r['persona_id']='same'
    if problem=='applicability':rows[0]['annotation']['applicable_factual_consistency']='false'
    with pytest.raises(ValueError):analyze(rows,replicates=10)


def test_bootstrap_is_deterministic_and_source_is_unchanged():
    rows=analysis_fixture(); before=deepcopy(rows)
    assert analyze(rows,replicates=50)==analyze(rows,replicates=50)
    assert rows==before


def test_saved_prompt_object_hash_not_dictionary_hash():
    import importlib.util
    from personaslm.response_status import text_hash
    spec=importlib.util.spec_from_file_location('human_analysis_tool',Path(__file__).parents[1]/'tools/p1_human_analysis.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    saved={'prompt':{'text':'Independent synthetic prompt.'},'prompt_sha256':text_hash('Independent synthetic prompt.')}
    module.verify_saved_prompt(saved)
    saved['prompt']['text']+='altered'
    with pytest.raises(ValueError,match='Prompt hash mismatch'):module.verify_saved_prompt(saved)
